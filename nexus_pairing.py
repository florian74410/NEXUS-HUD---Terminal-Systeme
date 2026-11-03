"""Opt-in LAN pairing: discovery and user-approved public-key exchange.
No privileged operations, no SSH server installation or automatic startup.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import threading
import time

PORT=43871
MAGIC='N3XV5-PAIR-1'
MAX_PACKET=4096

def config_path():
    return Path.home()/'.config'/'n3xv5-terminal'/'pairing.json'

def enabled():
    try:return json.loads(config_path().read_text()).get('enabled') is True
    except (OSError,ValueError,TypeError):return False

def set_enabled(value):
    p=config_path();p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    p.write_text(json.dumps({'enabled':bool(value)}));p.chmod(0o600)

def public_key():
    from nexus_lan_ssh import key_path
    p=Path(str(key_path())+'.pub')
    if not p.is_file():return None
    value=p.read_text().strip()
    parts=value.split()
    if len(parts)<2 or parts[0]!='ssh-ed25519' or len(value)>1500: return None
    return parts[0]+' '+parts[1]

def approval_code(pub,nonce):
    return hashlib.sha256((pub+'|'+nonce).encode()).hexdigest()[:12].upper()

def authorize_key(pub):
    """Add only a validated public key, never overwrite existing authorized_keys."""
    import base64
    parts=pub.split()
    if len(parts)!=2 or parts[0]!='ssh-ed25519':raise ValueError('Clé Ed25519 invalide')
    try: raw=base64.b64decode(parts[1],validate=True)
    except Exception as e:raise ValueError('Encodage de clé invalide') from e
    if len(raw)>1024 or not raw.startswith(b'\x00\x00\x00\x0bssh-ed25519'):raise ValueError('Format de clé invalide')
    folder=Path.home()/'.ssh'
    if folder.is_symlink():raise ValueError('Dossier SSH symbolique refusé')
    folder.mkdir(mode=0o700,exist_ok=True);folder.chmod(0o700)
    file=folder/'authorized_keys'
    if file.is_symlink():raise ValueError('authorized_keys symbolique refusé')
    existing=file.read_text() if file.exists() else ''
    if any(line.split()[:2]==parts for line in existing.splitlines()):return False
    fd=os.open(str(file),os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW,0o600)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'a') as f:f.write(('' if not existing or existing.endswith('\n') else '\n')+pub+' n3xv5-paired\n')
    except:raise
    return True

class PairingService:
    """Background sockets only enqueue messages; UI thread must handle approval."""
    def __init__(self):
        import queue
        self.events=queue.Queue();self.stop=threading.Event();self.peers={};self._threads=[]
    def start(self):
        if not enabled():return
        self.stop.clear()
        for target in (self._beacon,self._listen):
            t=threading.Thread(target=target,daemon=True);t.start();self._threads.append(t)
    def shutdown(self):self.stop.set()
    def _beacon(self):
        while not self.stop.is_set():
            try:
                s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
                msg=json.dumps({'magic':MAGIC,'host':socket.gethostname()[:64]}).encode()
                s.sendto(msg,('255.255.255.255',PORT));s.close()
            except OSError:pass
            self.stop.wait(5)
    def _listen(self):
        try:
            udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);udp.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            udp.bind(('',PORT));udp.settimeout(0.5)
        except OSError as e:self.events.put(('error',str(e)));return
        while not self.stop.is_set():
            try:
                data,addr=udp.recvfrom(MAX_PACKET)
                obj=json.loads(data)
                if obj.get('magic')==MAGIC and addr[0] not in ('127.0.0.1',):
                    self.peers[addr[0]]={'name':str(obj.get('host','PC'))[:64],'seen':time.monotonic()}
            except (socket.timeout,ValueError,UnicodeDecodeError):continue
            except OSError:break
        udp.close()
