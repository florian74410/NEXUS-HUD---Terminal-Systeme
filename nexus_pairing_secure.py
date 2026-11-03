"""N3XV5 LAN pairing: explicit two-sided confirmation, no private-key transfer.

Discovery is untrusted. Pairing code must be compared on both screens via a
trusted out-of-band channel; it binds both public keys and random nonces.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import secrets
import socket
import threading
import time

from nexus_pairing import public_key, authorize_key

PORT = 43872
MAX_LINE = 4096
TIMEOUT = 90


def _wire(sock, payload):
    data = json.dumps(payload, separators=(',', ':'), ensure_ascii=True).encode() + b'\n'
    if len(data) > MAX_LINE:
        raise ValueError('Message trop volumineux')
    sock.sendall(data)


def _read(sock):
    data = bytearray()
    while len(data) < MAX_LINE:
        b = sock.recv(1)
        if not b:
            raise ConnectionError('Connexion interrompue')
        if b == b'\n':
            obj = json.loads(data)
            if not isinstance(obj, dict):
                raise ValueError('Message invalide')
            return obj
        data.extend(b)
    raise ValueError('Message trop volumineux')


def _key(value):
    if not isinstance(value, str):
        raise ValueError('Clé absente')
    parts = value.split()
    if len(parts) != 2 or parts[0] != 'ssh-ed25519':
        raise ValueError('Clé invalide')
    raw = base64.b64decode(parts[1], validate=True)
    if not 45 <= len(raw) <= 128 or not raw.startswith(b'\x00\x00\x00\x0bssh-ed25519'):
        raise ValueError('Clé Ed25519 invalide')
    return ' '.join(parts)


def _nonce(value):
    if not isinstance(value, str) or len(value) != 32 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('Nonce invalide')
    return value


def comparison_code(key_a, key_b, nonce_a, nonce_b):
    material = json.dumps([_key(key_a), _key(key_b), _nonce(nonce_a), _nonce(nonce_b)], separators=(',', ':'))
    digest = hashlib.sha256(material.encode()).hexdigest().upper()
    return '-'.join(digest[i:i+4] for i in (0, 4, 8))


class Pending:
    def __init__(self, peer, code):
        self.peer = peer
        self.code = code
        self.choice = threading.Event()
        self.approved = False

    def decide(self, approved):
        self.approved = bool(approved)
        self.choice.set()


class PairingServer:
    def __init__(self):
        self.incoming = queue.Queue()
        self.errors = queue.Queue()
        self._stop = threading.Event()
        self._socket = None
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        if not public_key():
            raise RuntimeError('Créer d’abord la clé N3XV5 LAN')
        self._stop.clear()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', PORT))
            s.listen(5)
            s.settimeout(.5)
        except BaseException:
            s.close()
            raise
        self._socket = s
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._socket:
            self._socket.close()
            self._socket = None

    def _serve(self):
        while not self._stop.is_set():
            try:
                conn, addr = self._socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn, addr), daemon=True).start()

    def _handle(self, conn, addr):
        with conn:
            try:
                conn.settimeout(TIMEOUT)
                first = _read(conn)
                if first.get('type') != 'pair.request' or first.get('v') != 1:
                    return
                their_key = _key(first.get('key'))
                their_nonce = _nonce(first.get('nonce'))
                mine = public_key()
                if not mine:
                    return
                my_nonce = secrets.token_hex(16)
                code = comparison_code(their_key, mine, their_nonce, my_nonce)
                _wire(conn, {'v':1, 'type':'pair.challenge', 'key':mine, 'nonce':my_nonce})
                pending = Pending(addr[0], code)
                self.incoming.put(pending)
                if not pending.choice.wait(TIMEOUT) or not pending.approved or self._stop.is_set():
                    _wire(conn, {'v':1, 'type':'pair.denied'})
                    return
                _wire(conn, {'v':1, 'type':'pair.accepted'})
                response = _read(conn)
                if response.get('type') != 'pair.confirm':
                    return
                # Both users confirmed the same comparison code. Public keys only.
                authorize_key(their_key)
                _wire(conn, {'v':1, 'type':'pair.complete'})
            except (OSError, ValueError, ConnectionError, json.JSONDecodeError) as exc:
                self.errors.put(str(exc))


def pair_with(host, approval_callback):
    """Blocking client call: run in worker thread. callback(code, host) -> bool."""
    mine = public_key()
    if not mine:
        raise RuntimeError('Créer d’abord la clé N3XV5 LAN')
    nonce = secrets.token_hex(16)
    with socket.create_connection((host, PORT), timeout=8) as conn:
        conn.settimeout(TIMEOUT)
        _wire(conn, {'v':1, 'type':'pair.request', 'key':mine, 'nonce':nonce})
        challenge = _read(conn)
        if challenge.get('type') != 'pair.challenge':
            raise RuntimeError('Réponse d’appairage invalide')
        their_key = _key(challenge.get('key'))
        code = comparison_code(mine, their_key, nonce, challenge.get('nonce'))
        if not approval_callback(code, host):
            return False
        if _read(conn).get('type') != 'pair.accepted':
            raise RuntimeError('Le PC distant a refusé ou expiré')
        _wire(conn, {'v':1, 'type':'pair.confirm'})
        if _read(conn).get('type') != 'pair.complete':
            raise RuntimeError('Appairage non terminé')
        authorize_key(their_key)
        return True
