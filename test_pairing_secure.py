import base64
import socket
import unittest
from unittest.mock import patch
from nexus_pairing_secure import comparison_code, _read, _wire, _key

KEY = 'ssh-ed25519 '+base64.b64encode(b'\x00\x00\x00\x0bssh-ed25519'+b'\x00'*40).decode()

class PairingProtocolTests(unittest.TestCase):
    def test_code_deterministic(self):
        n1='a'*32;n2='b'*32
        self.assertEqual(comparison_code(KEY,KEY,n1,n2),comparison_code(KEY,KEY,n1,n2))
        self.assertNotEqual(comparison_code(KEY,KEY,n1,n2),comparison_code(KEY,KEY,n2,n1))
    def test_reject_bad_key(self):
        with self.assertRaises(ValueError):_key('ssh-rsa abc')
    def test_wire(self):
        a,b=socket.socketpair()
        try:
            _wire(a,{'type':'ping','v':1})
            self.assertEqual(_read(b),{'type':'ping','v':1})
        finally:a.close();b.close()
    def test_oversized(self):
        a,b=socket.socketpair()
        try:
            with self.assertRaises(ValueError):_wire(a,{'x':'z'*5000})
        finally:a.close();b.close()

if __name__=='__main__':unittest.main()
