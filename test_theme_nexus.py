"""Source/asset contracts; separate from Qt runtime and LAN end-to-end tests."""
import ast
import hashlib
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'assets'/'theme_nexus'


class N3xv5ThemeTests(unittest.TestCase):
    def test_53_original_vector_and_gif_assets(self):
        manifest=json.loads((ASSETS/'manifest.json').read_text())
        files=manifest['assets']
        self.assertEqual(len(files),53)
        self.assertEqual(sum(x['file'].endswith('.svg') for x in files),48)
        self.assertEqual(sum(x['file'].endswith('.gif') for x in files),5)
        for item in files:
            blob=(ASSETS/item['file']).read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(),item['sha256'])

    def test_original_svg_geometry_valid(self):
        for path in ASSETS.rglob('*.svg'):
            with self.subTest(path=path.name):
                self.assertEqual(ElementTree.parse(path).getroot().tag,
                    '{http://www.w3.org/2000/svg}svg')

    def test_code_is_syntactically_valid(self):
        for path in ROOT.glob('*.py'):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding='utf-8'))

    def test_real_terminal_not_replaced_by_svg_mockup(self):
        src=(ROOT/'nexus_workspace.py').read_text()
        self.assertIn('class Terminal(QTermWidget):',src)
        self.assertIn('class TerminalTile(ElectricPulseSurface):',src)
        self.assertIn('self.terminal=Terminal(command,self,',src)
        self.assertIn('QSplitter(orientation)',src)

    def test_top_bar_keeps_features_left_column_blank(self):
        src=(ROOT/'nexus_workspace.py').read_text()
        for func in ('show_scripts','show_sessions','show_settings','show_ssh_menu','show_pairing'):
            self.assertIn('def '+func+'(',src)
        self.assertIn("self.nav=AssetSurface(category='Boxes',name='Performance_Tall.svg')",src)
        self.assertNotIn("button('Terminals',lambda:None",src)

    def test_animation_is_real_qt_not_svg_smil(self):
        src=(ROOT/'nexus_skin.py').read_text()
        self.assertIn('QVariantAnimation',src)
        self.assertIn('QTimer(',src)
        self.assertIn('def set_animated(self,enabled):',src)
        self.assertIn("remove_text=True",src)
        self.assertIn('def set_artwork(',src)
        workspace=(ROOT/'nexus_workspace.py').read_text()
        self.assertIn("QMovie(str(ELECTRIC/'ElectroBlueNEON_pcb_signal.gif'))",workspace)

    def test_critical_module_files_still_present(self):
        for name in ('nexus_quick_commands.py','nexus_pairing_secure.py',
                     'nexus_pairing_dialog.py','nexus_hover.py','nexus_smart_context.py',
                     'nexus_connections.py','nexus_screen_adapter.py','nexus_git.py'):
            self.assertTrue((ROOT/name).is_file())


if __name__=='__main__':unittest.main()
