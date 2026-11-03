import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from nexus_smart_context import safe_query,excluded
class TestContext(unittest.TestCase):
 def test_normal(self):
  self.assertIsNotNone(safe_query('grep','cat app.log | grep ERROR',14,18))
 def test_ip(self):
  self.assertIsNone(safe_query('192.168.1.1'))
  self.assertIsNone(safe_query('2001:db8::1'))
 def test_ports(self):
  self.assertIsNone(safe_query('443','curl http://localhost:443',22,25))
 def test_password(self):
  self.assertIsNone(safe_query('password'))
  self.assertIsNone(safe_query('hunter2','password=hunter2',9,16))
 def test_identity(self):
  self.assertIsNone(safe_query('overflow',known_identities=('overflow',)))
  self.assertIsNone(safe_query('admin','ssh admin@server',4,9))
 def test_no_raw_line(self):
  c=safe_query('grep','grep hello password=hunter2',0,4)
  self.assertNotIn('hunter2',c.query)
if __name__=='__main__':unittest.main()
