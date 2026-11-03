"""Profile-scoped quick commands; no subprocess or shell execution in this module."""
from __future__ import annotations
import json, os, re, shlex
from pathlib import Path

VARIABLE = re.compile(r"^[A-Z][A-Z0-9_]{0,47}$")
PLACEHOLDER = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")
RESERVED = {"PATH","HOME","SHELL","USER","UID","EUID","IFS","ENV","BASH_ENV","LD_PRELOAD","LD_LIBRARY_PATH","PYTHONPATH","PROMPT_COMMAND"}
MAX_BYTES=128*1024

def validate_name(name):
    if not VARIABLE.fullmatch(name) or name in RESERVED or name.startswith(("N3XV5_","BASH_")):
        raise ValueError("Nom invalide ou réservé")
    return name

def expand(command, variables):
    """Expand profile variables as shell arguments, never as raw executable shell syntax."""
    def replace(match):
        key=match.group(1)
        if key not in variables: raise ValueError("Variable inconnue : "+key)
        return shlex.quote(str(variables[key]))
    return PLACEHOLDER.sub(replace,command)

class Registry:
    def __init__(self,profile="default",base=None):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}",profile):raise ValueError("Profil invalide")
        self.path=(Path(base) if base else Path.home()/'.config'/'n3xv5-terminal'/'profiles')/(profile+'.json')
        self.variables={};self.commands=[];self.load()
    def load(self):
        if self.path.exists():
            if self.path.stat().st_size>MAX_BYTES:raise ValueError("Registre trop volumineux")
            data=json.loads(self.path.read_text(encoding='utf-8'))
            self.variables={k:str(v) for k,v in data.get('variables',{}).items() if VARIABLE.fullmatch(k) and k not in RESERVED}
            self.commands=[c for c in data.get('commands',[]) if isinstance(c,dict) and all(k in c for k in ('name','category','command'))][:200]
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        payload=json.dumps({'schema':1,'variables':self.variables,'commands':self.commands},ensure_ascii=False,indent=2)
        if len(payload.encode())>MAX_BYTES:raise ValueError("Registre trop volumineux")
        temp=self.path.with_suffix('.tmp'); fd=os.open(temp,os.O_CREAT|os.O_WRONLY|os.O_TRUNC,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as out:out.write(payload)
        os.replace(temp,self.path);os.chmod(self.path,0o600)
    def add_variable(self,name,value):
        validate_name(name)
        if name in self.variables:raise ValueError("Variable déjà existante")
        if not value or len(value)>512 or any(c in value for c in '\r\n\0'):raise ValueError("Valeur invalide")
        self.variables[name]=value;self.save()
    def add_command(self,name,category,command):
        if not name.strip() or len(name)>80 or not category.strip() or len(category)>48 or not command.strip() or len(command)>2048:raise ValueError("Commande invalide")
        if any(x in name+category+command for x in '\0\r'):raise ValueError("Caractère interdit")
        if any(c['name']==name and c['category']==category for c in self.commands):raise ValueError("Commande déjà enregistrée")
        self.commands.append({'name':name.strip(),'category':category.strip(),'command':command.strip()});self.save()
    def suggestions(self,prefix):
        return [c for c in self.commands if c['name'].casefold().startswith(prefix.casefold()) or c['command'].casefold().startswith(prefix.casefold())][:8]
