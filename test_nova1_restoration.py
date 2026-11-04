"""Verify original NOVA 1.0 style is active without Qt or a running SSH server."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT/'nexus_workspace.py').read_text()
STYLE = (ROOT/'nexus_nova1_style.py').read_text()

class Nova1RestoreTests(unittest.TestCase):
    def test_native_nova1_bevel_geometry_restored(self):
        for fragment in ('class NeonGlassPanel(QFrame):',
                         'grad.setColorAt(.45, QColor(3, 16, 29, 242))',
                         'for width, alpha in ((8, 14), (4, 28), (2, 85)):',
                         'painter.drawLine(start, 3, min(start + 37, w - 17), 3)'):
            self.assertIn(fragment,STYLE)
    def test_no_svg_surface_over_live_terminal(self):
        self.assertIn('class TerminalTile(NovaOneTerminalFrame):',SOURCE)
        self.assertIn('self.terminal=Terminal(command,self,',SOURCE)
        self.assertNotIn('class TerminalTile(ElectricPulseSurface):',SOURCE)
    def test_original_nova1_color_palette(self):
        self.assertIn("QWidget#root {background:#020b16;}",SOURCE)
        self.assertIn("QWidget#terminalHost {background:#041725;}",SOURCE)
        self.assertIn("QSplitter::handle {background:rgba(0,155,207,110);",SOURCE)
    def test_no_feature_imports_removed(self):
        for module in ('nexus_pairing','nexus_quick_commands',
                       'nexus_hover','nexus_lan_ssh','nexus_smart_context'):
            self.assertTrue((ROOT/(module+'.py')).is_file(),module)
        for method in ('show_ssh_menu','show_sessions','show_scripts',
                       'show_settings','show_pairing','_commands_menu'):
            self.assertIn('def '+method+'(',SOURCE)
    def test_left_column_empty_and_actions_top(self):
        self.assertIn("self.nav=NeonGlassPanel(accent='#0fa8d0',cut=12)",SOURCE)
        self.assertIn("self.ssh_btn=button('SSH ▾'",SOURCE)
        self.assertIn("self.scripts_btn=button('Scripts ▾'",SOURCE)
    def test_previous_svg_theme_preserved_as_optional_source(self):
        self.assertTrue((ROOT/'nexus_skin.py').is_file())
        self.assertTrue((ROOT/'assets'/'theme_nexus'/'manifest.json').is_file())
    def test_no_runtime_dependency_in_static_contracts(self):
        for file in ROOT.glob('*.py'):
            with self.subTest(path=file.name):
                ast.parse(file.read_text())

if __name__ == '__main__':
    unittest.main()
