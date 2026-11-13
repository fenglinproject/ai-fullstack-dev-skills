'use strict';
let token = null; // intentionally memory-only session in this local demonstration
const $ = (id) => document.getElementById(id);
function tell(msg){ $('message').textContent=msg; }
async function request(path,method='GET',body){
  const response=await fetch(path,{method,headers:{'Content-Type':'application/json',...(token?{'Authorization':'Bearer '+token}:{})},...(body?{body:JSON.stringify(body)}:{})});
  const result=await response.json();
  if(!response.ok) throw new Error(result.error || '请求失败');
  return result;
}
async function auth(action){
  try{
    const result=await request('/api/'+action,'POST',{email:$('email').value,password:$('password').value});
    token=result.token; $('auth').hidden=true;$('tasks').hidden=false;$('password').value='';tell('账号已登录');await refresh();
  }catch(error){tell(error.message);}
}
async function refresh(){
  try{
    const result=await request('/api/tasks');const ul=$('list');ul.replaceChildren();
    for(const task of result.tasks){
      const li=document.createElement('li'); if(task.done)li.classList.add('done');
      const check=document.createElement('input');check.type='checkbox';check.checked=task.done;check.setAttribute('aria-label','标记任务完成');
      check.addEventListener('change',async()=>{try{await request('/api/tasks/'+task.id,'PATCH',{done:check.checked});await refresh();}catch(e){tell(e.message);}});
      const label=document.createElement('span');label.textContent=task.title;
      const del=document.createElement('button');del.textContent='删除';del.addEventListener('click',async()=>{try{await request('/api/tasks/'+task.id,'DELETE');await refresh();}catch(e){tell(e.message);}});
      li.append(check,label,del);ul.appendChild(li);
    }
  }catch(e){tell(e.message);}
}
$('register').addEventListener('click',()=>auth('register'));
$('login').addEventListener('click',()=>auth('login'));
$('newTask').addEventListener('submit',async(e)=>{e.preventDefault();try{await request('/api/tasks','POST',{title:$('title').value});$('title').value='';await refresh();}catch(error){tell(error.message);}});
$('logout').addEventListener('click',()=>{token=null;$('tasks').hidden=true;$('auth').hidden=false;tell('已退出当前会话');});
