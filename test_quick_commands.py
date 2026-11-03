import tempfile, unittest
from pathlib import Path
from nexus_quick_commands import Registry, expand, validate_name
class QuickTests(unittest.TestCase):
 def test_profile(self):
  with tempfile.TemporaryDirectory() as d:
   r=Registry(base=d);r.add_variable('SSH_HOST','127.0.0.1');r.add_command('Connexion','SSH','ssh ${SSH_HOST}')
   n=Registry(base=d);self.assertEqual(len(n.suggestions('Conn')),1);self.assertEqual(n.variables['SSH_HOST'],'127.0.0.1')
   self.assertEqual(n.path.stat().st_mode & 0o777,0o600)
 def test_reserved(self):
  with self.assertRaises(ValueError):validate_name('PATH')
 def test_unknown(self):
  with self.assertRaises(ValueError):expand('echo ${UNKNOWN}',{})
 def test_escaping(self):
  self.assertEqual(expand('echo ${VAL}',{'VAL':'hello; rm -rf /'}),"echo 'hello; rm -rf /'")
 def test_duplicate(self):
  with tempfile.TemporaryDirectory() as d:
   r=Registry(base=d);r.add_variable('TEST_VAR','a')
   with self.assertRaises(ValueError):r.add_variable('TEST_VAR','b')
if __name__=='__main__':unittest.main()
