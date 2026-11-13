"""Dependency-free TODO demo. Local educational sample; not production auth infra."""
from __future__ import annotations
import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit

class Store:
    def __init__(self, database):
        self.database=str(database)
        self.tokens={}
        self.lock=RLock()
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                  salt TEXT NOT NULL, password_digest TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                  id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL,
                  title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0,
                  FOREIGN KEY(owner_id) REFERENCES users(id)
                );
            ''')
    def connect(self):
        connection=sqlite3.connect(self.database,timeout=5)
        connection.execute('PRAGMA foreign_keys=ON')
        return connection

class ApiError(Exception):
    def __init__(self,status,message):super().__init__(message);self.status=status

def need_str(data,key,max_len):
    v=data.get(key)
    if not isinstance(v,str) or not v.strip() or len(v)>max_len:
        raise ApiError(400,f'{key} must be a nonempty string of at most {max_len} chars')
    return v.strip()

def authenticate(headers,store):
    value=headers.get('authorization','')
    if not value.startswith('Bearer '): raise ApiError(401,'Authorization required')
    with store.lock: uid=store.tokens.get(value[7:])
    if uid is None:raise ApiError(401,'Invalid session')
    return uid

def handle(store, method, url, headers=None, data=None):
    headers={k.lower():v for k,v in (headers or {}).items()}
    data=data or {}
    try:
        if not isinstance(data,dict):raise ApiError(400,'JSON object required')
        path=urlsplit(url).path
        if method=='POST' and path in ('/api/register','/api/login'):
            email=need_str(data,'email',254).casefold()
            password=need_str(data,'password',256)
            if len(password)<8:raise ApiError(400,'password must be 8 or more characters')
            if '@' not in email:raise ApiError(400,'email is not valid')
            if path.endswith('register'):
                salt=secrets.token_bytes(16)
                hashed=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,180000)
                try:
                    with store.connect() as db:
                        cur=db.execute('INSERT INTO users(email,salt,password_digest) VALUES(?,?,?)',
                                       (email,salt.hex(),hashed.hex()))
                        uid=cur.lastrowid
                except sqlite3.IntegrityError:raise ApiError(409,'email is already registered')
                status=201
            else:
                with store.connect() as db:
                    user=db.execute('SELECT id,salt,password_digest FROM users WHERE email=?',(email,)).fetchone()
                if not user:raise ApiError(401,'Invalid credentials')
                uid,salt_hex,hash_hex=user
                supplied=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt_hex),180000)
                if not hmac.compare_digest(supplied,bytes.fromhex(hash_hex)):
                    raise ApiError(401,'Invalid credentials')
                status=200
            token=secrets.token_urlsafe(32)
            with store.lock:store.tokens[token]=uid
            return status,{'token':token}
        if not path.startswith('/api/tasks'):raise ApiError(404,'Unknown route')
        user_id=authenticate(headers,store)
        if path=='/api/tasks':
            if method=='GET':
                with store.connect() as db:
                    data=db.execute('SELECT id,title,done FROM tasks WHERE owner_id=? ORDER BY id',(user_id,)).fetchall()
                return 200,{'tasks':[{'id':row[0],'title':row[1],'done':bool(row[2])} for row in data]}
            if method=='POST':
                title=need_str(data,'title',120)
                with store.connect() as db:
                    cur=db.execute('INSERT INTO tasks(owner_id,title) VALUES(?,?)',(user_id,title))
                    return 201,{'id':cur.lastrowid,'title':title,'done':False}
            raise ApiError(405,'Unsupported method')
        parts=path.split('/')
        if len(parts)!=4 or not parts[3].isdigit():raise ApiError(404,'Unknown route')
        task_id=int(parts[3])
        if method=='PATCH':
            done=data.get('done')
            if not isinstance(done,bool):raise ApiError(400,'done must be a boolean')
            with store.connect() as db:
                result=db.execute('UPDATE tasks SET done=? WHERE id=? AND owner_id=?',
                                  (int(done),task_id,user_id))
                if result.rowcount==0:raise ApiError(404,'Task not found')
            return 200,{'id':task_id,'done':done}
        if method=='DELETE':
            with store.connect() as db:
                result=db.execute('DELETE FROM tasks WHERE id=? AND owner_id=?',(task_id,user_id))
                if result.rowcount==0:raise ApiError(404,'Task not found')
            return 200,{'deleted':True}
        raise ApiError(405,'Unsupported method')
    except ApiError as e:return e.status,{'error':str(e)}
