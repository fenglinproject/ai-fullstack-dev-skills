#!/usr/bin/env python3
"""V5.0 offline supply-chain policy, provenance statement and opt-in OpenSSL signatures.

SHA-256 and unsigned provenance are NOT authenticity attestations.
The signer MUST supply their own trusted key; no private key is bundled.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, '') and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXPECTED_INTEGRITY = 'sha512-jl1vZzPDinLr9eUt3J/t7V6FgNEw9QjvBPdysz9KfQDD41fQrC2Y4vKQdiaUpFT4bXlb1RHhLpp8wtm6M5TgSw=='
MAX_STATEMENT_BYTES=65536
MAX_ARCHIVE_BYTES=100_000_000
FULL_SHA = re.compile(r'^[a-f0-9]{40}$')
ID = re.compile(r'^[1-9][0-9]{0,18}$')


def _read_json(path:Path, *, max_bytes: int = MAX_STATEMENT_BYTES) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > max_bytes:
        raise ValueError('missing, symlink or oversized JSON file')
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict):raise ValueError('expected JSON object')
    return value


def _new_output(path:Path) -> None:
    if path.exists() or path.is_symlink() or not path.parent.is_dir() or path.parent.is_symlink():
        raise ValueError('output must be a new file in a real existing directory')


def _file_hash(path:Path) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError('not a valid release archive')
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def audit(*, root: Path=ROOT) -> dict:
    root=root.resolve(strict=True)
    pins=_read_json(root/'ci/actions_pins.json')
    wf=(root/'.github/workflows/test.yml').read_text(encoding='utf-8')
    refs=re.findall(r'(?m)^\s*-?\s*uses:\s*([^\s#]+)',wf)
    if not refs:raise ValueError('workflow does not reference any actions')
    seen=set()
    for ref in refs:
        if '@' not in ref:raise ValueError('unversioned action')
        name,revision=ref.split('@',1)
        short=name.removeprefix('actions/')
        if short not in pins or name!='actions/'+short:
            raise ValueError('unapproved action: '+name)
        if not FULL_SHA.fullmatch(revision) or revision!=pins[short]['sha']:
            raise ValueError('mutable or unapproved action SHA: '+name)
        if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+',pins[short]['version']):
            raise ValueError('invalid pinned action version annotation')
        seen.add(short)
    if seen!=set(pins):raise ValueError('expected action missing from workflow')
    # Refuse npm install -g, npm install without lock, third party scripts on dependency install
    if 'npm ci --ignore-scripts --no-audit --no-fund' not in wf or re.search(r'\bnpm install(?:\s+-g)?\b',wf):
        raise ValueError('CI is not using a locked npm ci install')
    p=_read_json(root/'package.json')
    lock=_read_json(root/'package-lock.json')
    pkg=lock.get('packages',{})
    if (p.get('private') is not True or p.get('scripts') or p.get('dependencies') or
            p.get('devDependencies')!={'typescript':'5.9.3'} or
            lock.get('lockfileVersion')!=3 or lock.get('version')!=p.get('version') or
            lock.get('name')!=p.get('name') or
            pkg.get('',{}).get('devDependencies')!=p.get('devDependencies') or
            set(pkg)!={'','node_modules/typescript'}):
        raise ValueError('unexpected or inconsistent package lock')
    ts=pkg['node_modules/typescript']
    if (ts.get('version')!='5.9.3' or
            ts.get('resolved')!='https://registry.npmjs.org/typescript/-/typescript-5.9.3.tgz' or
            ts.get('integrity')!=EXPECTED_INTEGRITY):
        raise ValueError('unlocked TypeScript artifact')
    ci=_read_json(root/'ci/toolchain.json')
    if ci.get('typescript_ci_exact')!='5.9.3' or ci.get('python_third_party_runtime_dependencies')!=[]:
        raise ValueError('toolchain policy inconsistent with lock')
    return {'policy':'v5.0','passed':True,'action_references':len(refs),
            'pinned_action_types':sorted(seen),'locked_npm_packages':['typescript@5.9.3'],
            'python_external_runtime_packages':0,
            'limits':'Checks the committed metadata only; npm package bytes are verified by npm ci when online.'}


def create_provenance(archive:Path, output:Path, *, commit: str|None=None, run_id: str|None=None) -> dict:
    from tools.package_release_v50 import verify_package
    verified=verify_package(archive)
    _new_output(output)
    if commit is not None and not FULL_SHA.fullmatch(commit):raise ValueError('invalid source commit SHA')
    if run_id is not None and not ID.fullmatch(run_id):raise ValueError('invalid CI run ID')
    if (commit is None)!=(run_id is None):raise ValueError('commit and run ID must be supplied together')
    result={'_type':'https://in-toto.io/Statement/v1',
            'subject':[{'name':archive.name,'digest':{'sha256':_file_hash(archive)}}],
            'predicateType':'https://example.org/ai-fullstack/local-release-record/v1',
            'predicate':{'toolkitVersion':'5.0','sourceCommit':commit,'githubRunId':run_id,
                        'issuer':'self-reported','githubPlatformSignatureVerified':False,
                        'localIntegrityVerified':verified['verified_integrity'],
                        'dependencyLockSha256':hashlib.sha256((ROOT/'package-lock.json').read_bytes()).hexdigest(),
                        'actionsPinsSha256':hashlib.sha256((ROOT/'ci/actions_pins.json').read_bytes()).hexdigest(),
                        'meaning':'This document is unsigned local metadata, not a SLSA provenance attestation.'}}
    if output.resolve()==archive.resolve():raise ValueError('output cannot replace archive')
    output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    return {'created':str(output),'subject_sha256':result['subject'][0]['digest']['sha256'], 'signed':False}


def verify_provenance(archive:Path, statement:Path) -> dict:
    from tools.package_release_v50 import verify_package
    verify_package(archive)
    p=_read_json(statement)
    if set(p)!={'_type','subject','predicateType','predicate'} or p['_type']!='https://in-toto.io/Statement/v1' or p['predicateType']!='https://example.org/ai-fullstack/local-release-record/v1':
        raise ValueError('wrong provenance statement format')
    if p['subject']!=[{'name':archive.name,'digest':{'sha256':_file_hash(archive)}}]:
        raise ValueError('archive digest does not match provenance')
    pred=p['predicate']
    if (not isinstance(pred,dict) or set(pred)!={'toolkitVersion','sourceCommit','githubRunId','issuer','githubPlatformSignatureVerified','localIntegrityVerified','dependencyLockSha256','actionsPinsSha256','meaning'} or pred.get('toolkitVersion')!='5.0' or
            pred.get('issuer')!='self-reported' or pred.get('githubPlatformSignatureVerified') is not False or
            pred.get('localIntegrityVerified') is not True or
            pred.get('dependencyLockSha256')!=hashlib.sha256((ROOT/'package-lock.json').read_bytes()).hexdigest() or
            pred.get('actionsPinsSha256')!=hashlib.sha256((ROOT/'ci/actions_pins.json').read_bytes()).hexdigest()):
        raise ValueError('provenance metadata mismatch')
    commit,run_id=pred.get('sourceCommit'),pred.get('githubRunId')
    if (commit is None)!=(run_id is None) or (commit is not None and not FULL_SHA.fullmatch(commit)) or (run_id is not None and not ID.fullmatch(run_id)):
        raise ValueError('malformed release context')
    return {'digest_matches':True,'signed':False,'source_authenticated':False,'file':str(archive)}


def create_sbom(output:Path) -> dict:
    audit()
    _new_output(output)
    result={'bomFormat':'CycloneDX','specVersion':'1.5','version':1,
            'metadata':{'component':{'type':'application','name':'ai-fullstack-dev-skills','version':'5.0'},
                        'properties':[{'name':'integrity_scope','value':'Committed lock metadata only; not an installed dependency scan.'}]},
            'components':[{'type':'library','name':'typescript','version':'5.9.3',
                           'purl':'pkg:npm/typescript@5.9.3',
                           'scope':'required','properties':[{'name':'npm:integrity','value':EXPECTED_INTEGRITY}]}],
            'dependencies':[{'ref':'pkg:npm/typescript@5.9.3','dependsOn':[]}]}
    output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    return {'output':str(output),'known_npm_dependencies':1,'runtime_python_external_dependencies':0}


def sign(archive:Path, key:Path, output:Path, *, approve:bool=False) -> dict:
    if not approve:raise ValueError('must explicitly approve release signing')
    _file_hash(archive)
    if key.is_symlink() or not key.is_file():raise ValueError('invalid key file')
    _new_output(output)
    exe=shutil.which('openssl')
    if not exe:raise ValueError('OpenSSL unavailable')
    cp=subprocess.run([exe,'dgst','-sha256','-sign',str(key),'-out',str(output),str(archive)],
                      capture_output=True,text=True,timeout=30)
    if cp.returncode or not output.is_file():
        output.unlink(missing_ok=True)
        raise ValueError('OpenSSL signing failed; RSA/ECDSA PEM keys only')
    return {'signed':True,'signature':str(output),'subject_sha256':_file_hash(archive),
            'warning':'Verify signature using a trusted public key obtained independently.'}


def verify_signature(archive:Path, key:Path, signature:Path) -> dict:
    _file_hash(archive)
    if key.is_symlink() or not key.is_file() or signature.is_symlink() or not signature.is_file() or signature.stat().st_size > 8192:
        raise ValueError('invalid signature or public key file')
    exe=shutil.which('openssl')
    if not exe:raise ValueError('OpenSSL unavailable')
    cp=subprocess.run([exe,'dgst','-sha256','-verify',str(key),'-signature',str(signature),str(archive)],
                      capture_output=True,text=True,timeout=30)
    if cp.returncode or 'Verified OK' not in cp.stdout:
        raise ValueError('release signature verification failed')
    return {'signature_verified':True,'subject_sha256':_file_hash(archive),
            'trust_note':'Key ownership and identity must be established independently.'}


def run_command(args):
    action=args.action
    if action=='audit':return audit()
    if action=='provenance':
        if not args.archive or not args.output:raise ValueError('--archive and --output are required')
        return create_provenance(args.archive,args.output,commit=args.commit,run_id=args.run_id)
    if action=='verify-provenance':
        if not args.archive or not args.statement:raise ValueError('--archive and --statement are required')
        return verify_provenance(args.archive,args.statement)
    if action=='sbom':
        if not args.output:raise ValueError('--output required')
        return create_sbom(args.output)
    if action=='sign':
        if not args.archive or not args.private_key or not args.output:raise ValueError('archive, private-key and output required')
        return sign(args.archive,args.private_key,args.output,approve=args.approve)
    if action=='verify-signature':
        if not args.archive or not args.public_key or not args.signature:raise ValueError('archive, public-key and signature required')
        return verify_signature(args.archive,args.public_key,args.signature)
    raise ValueError('unknown supply-chain command')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('audit','provenance','verify-provenance','sbom','sign','verify-signature'))
    p.add_argument('--archive',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--statement',type=Path)
    p.add_argument('--commit')
    p.add_argument('--run-id')
    p.add_argument('--private-key',type=Path)
    p.add_argument('--public-key',type=Path)
    p.add_argument('--signature',type=Path)
    p.add_argument('--approve',action='store_true')
    a=p.parse_args(argv)
    try:print(json.dumps(run_command(a),ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,subprocess.SubprocessError,json.JSONDecodeError) as e:
        p.error(str(e))

if __name__=='__main__':raise SystemExit(main())
