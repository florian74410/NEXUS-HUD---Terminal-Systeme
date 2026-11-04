"""Static UI regression contracts, no Qt dependency needed."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class RefinedTests(unittest.TestCase):
    def test_close_pane_uses_compact_control(self):
        skin=(ROOT/'nexus_nova1_style.py').read_text()
        ws=(ROOT/'nexus_workspace.py').read_text()
        self.assertIn('class NovaOneCloseButton(NovaOneButton):',skin)
        self.assertIn('close_button=NovaOneCloseButton(self)',ws)
        self.assertNotIn("button('×',lambda:self.closed.emit())",ws)

    def test_menu_anchored_to_topbar(self):
        ws=(ROOT/'nexus_workspace.py').read_text()
        self.assertIn('self.display_btn.mapToGlobal(self.display_btn.rect().bottomLeft())',ws)

    def test_remote_tmux_creates_or_attaches(self):
        ws=(ROOT/'nexus_workspace.py').read_text()
        self.assertIn("tmux new-session -A -s ",ws)

    def test_svg_originals_retained_renderer_cache_is_per_widget(self):
        skin=(ROOT/'nexus_skin.py').read_text()
        self.assertIn('@lru_cache(maxsize=128)',skin)
        self.assertIn('return QSvgRenderer(QByteArray(payload))',skin)
        self.assertIn('electric_only=True',skin)

if __name__ == '__main__':unittest.main()
