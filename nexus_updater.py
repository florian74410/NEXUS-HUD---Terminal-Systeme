#!/usr/bin/env python3
"""NEXUS update CLI: no arbitrary commands from manifests."""
import argparse,hashlib,json,os,pathlib,subprocess,sys,tempfile,urllib.request,shutil
APP='nexus-terminal'
DEFAULT='https://raw.githubusercontent.com/florian74410/NEXUS-HUD---Terminal-Systeme/main/Update/stable.json'
def current():
    p=subprocess.run(['dpkg-query','-W','-f=${Version}',APP],capture_output=True,text=True)
    return p.stdout.strip() if p.returncode==0 else None
def manifest(url):
    if not url.startswith('https://'):raise ValueError('HTTPS requis')
    with urllib.request.urlopen(url,timeout=12) as r:
        if r.status!=200:raise ValueError('Manifest indisponible')
        data=json.load(r)
    if data.get('app')!=APP:raise ValueError('Application incorrecte')
    pkg=data.get('package',{})
    if not pkg.get('url','').startswith('https://'):raise ValueError('URL de paquet non HTTPS')
    sha=pkg.get('sha256','')
    if len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha.lower()):raise ValueError('SHA256 invalide')
    if not data.get('version'):raise ValueError('Version absente')
    return data

def verify_package(path):
    if not path.is_file() or path.stat().st_size<500:raise ValueError('Paquet vide ou absent')
    p=subprocess.run(['dpkg-deb','-f',str(path),'Package','Version'],capture_output=True,text=True)
    lines=p.stdout.splitlines()
    if p.returncode or len(lines)<2 or lines[0].strip()!=APP:raise ValueError('Ce fichier n’est pas un paquet NEXUS Terminal valide')
    return lines[1].strip()

def install(path):
    ver=verify_package(path)
    print('Paquet vérifié :',APP,ver,flush=True)
    subprocess.run(['apt-get','install','-y',str(path.resolve())],check=True)

def main():
    a=argparse.ArgumentParser();a.add_argument('action',choices=['check','update','install-file']);a.add_argument('--file');a.add_argument('--manifest',default=os.environ.get('NEXUS_UPDATE_MANIFEST',DEFAULT));args=a.parse_args()
    if args.action=='install-file':
        if not args.file:raise ValueError('--file requis')
        install(pathlib.Path(args.file));return
    data=manifest(args.manifest)
    installed=current();version=data['version'];print('Installée :',installed or 'aucune','| Serveur :',version,flush=True)
    if installed and subprocess.run(['dpkg','--compare-versions',version,'le',installed]).returncode==0:
        print('Déjà à jour');return
    if args.action=='check':print('Mise à jour disponible');return
    with tempfile.TemporaryDirectory(prefix='nexus-update-') as d:
        path=pathlib.Path(d)/'nexus-terminal.deb'
        with urllib.request.urlopen(data['package']['url'],timeout=40) as r,path.open('wb') as f:shutil.copyfileobj(r,f)
        with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
        if sha.lower()!=data['package']['sha256'].lower():raise ValueError('Empreinte SHA256 incorrecte')
        install(path)
if __name__=='__main__':
    try:main()
    except Exception as e:print('NEXUS Update :',e,file=sys.stderr);sys.exit(1)
