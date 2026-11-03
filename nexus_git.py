"""NEXUS Git actions, profile-scoped config, never store tokens or private key content."""
import json,os,re,subprocess,shlex,tempfile
from pathlib import Path
ROOT=Path.home()/'.config/nexus-terminal'
FILE=ROOT/'github.json'
NAME=re.compile(r'^[a-zA-Z0-9_.-]{1,80}$')
DEFAULT={'repositories':[],'ssh_key':'','git_user':'','git_email':'','commands':[
 {'name':'Git Status','argv':['git','status','--short','--branch']},
 {'name':'Git Pull','argv':['git','pull','--ff-only']},
 {'name':'Git Fetch All','argv':['git','fetch','--all','--prune']},
 {'name':'Git Push','argv':['git','push']},
 {'name':'Git Log','argv':['git','log','--oneline','--decorate','-15']},
 {'name':'Git Pull All','builtin':'pull_all'}]}
def load():
 try:
  d=json.loads(FILE.read_text());return {**DEFAULT,**d} if isinstance(d,dict) else DEFAULT.copy()
 except FileNotFoundError:return DEFAULT.copy()
def save(d):
 ROOT.mkdir(parents=True,exist_ok=True,mode=0o700);ROOT.chmod(0o700)
 fd,path=tempfile.mkstemp(dir=ROOT,prefix='.github-')
 try:
  with os.fdopen(fd,'w') as f:json.dump(d,f,indent=2,ensure_ascii=False);f.flush();os.fsync(f.fileno())
  os.chmod(path,0o600);os.replace(path,FILE)
 finally:
  if os.path.exists(path):os.unlink(path)
def key_env(d):
 key=d.get('ssh_key','')
 if not key:return {}
 p=Path(key).expanduser().resolve()
 if not p.is_file() or p.stat().st_mode & 0o077:raise ValueError('Clé privée absente ou permissions trop ouvertes (chmod 600)')
 return {'GIT_SSH_COMMAND':shlex.join(['ssh','-i',str(p),'-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes'])}
def command(d,action,repo):
 commands={c['name']:c for c in d.get('commands',[])}
 if action not in commands:raise ValueError('Commande inconnue')
 c=commands[action]
 if c.get('builtin')=='pull_all':raise ValueError('Git Pull All doit être exécuté depuis le gestionnaire de dépôts')
 argv=c.get('argv')
 if not isinstance(argv,list) or not argv or argv[0]!='git' or any(not isinstance(x,str) or not x or '\x00' in x for x in argv):raise ValueError('Commande invalide')
 if any(x in ('-c','--exec-path','--upload-pack','--receive-pack') for x in argv):raise ValueError('Option Git non autorisée dans les raccourcis')
 root=Path(repo).expanduser().resolve()
 if not (root/'.git').exists():raise ValueError('Dépôt local introuvable : '+str(root))
 env=os.environ.copy();env.update(key_env(d));env['GIT_TERMINAL_PROMPT']='0'
 return argv,root,env
def generate_key(name):
 if not NAME.fullmatch(name):raise ValueError('Nom attendu : métier-rôle-utilisateur (lettres, chiffres, tirets)')
 folder=Path.home()/'.ssh';folder.mkdir(mode=0o700,exist_ok=True);folder.chmod(0o700)
 target=folder/('nexus_'+name)
 if target.exists() or target.with_suffix('.pub').exists():raise FileExistsError('Clé déjà existante')
 # ssh-keygen prompts for passphrase in the user's terminal; never generate a passphrase-free key silently.
 return ['ssh-keygen','-t','ed25519','-a','100','-C',name,'-f',str(target)]
