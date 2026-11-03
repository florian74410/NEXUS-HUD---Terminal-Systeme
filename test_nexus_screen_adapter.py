import unittest
from unittest.mock import patch
from nexus_screen_adapter import TmuxScreenAdapter

class AdapterTests(unittest.TestCase):
    def test_bad_session_rejected(self):
        self.assertIsNone(TmuxScreenAdapter('bad;rm -rf /').snapshot())
    def test_word(self):
        a=TmuxScreenAdapter('local')
        with patch.object(a,'snapshot',return_value=['git status --short']):
            self.assertEqual(a.word_at(0,5)[0],'status')
    def test_out_of_bounds(self):
        a=TmuxScreenAdapter('local')
        with patch.object(a,'snapshot',return_value=['git status']):
            self.assertIsNone(a.word_at(20,1))
    def test_unavailable(self):
        a=TmuxScreenAdapter('local')
        with patch.object(a,'snapshot',return_value=None):
            self.assertIsNone(a.word_at(0,0))

if __name__=='__main__':unittest.main()
