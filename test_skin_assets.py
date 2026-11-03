"""Asset contract tests independent of PySide6 (GUI requires XFCE)."""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'assets'/'theme_nexus'
class SkinContractTests(unittest.TestCase):
    def test_per_terminal_electric_pulse(self):
        src=(ROOT/'nexus_workspace.py').read_text()
        self.assertIn('class TerminalTile(ElectricPulseSurface):',src)
        self.assertTrue((ASSETS/'Boxes/Electric_Pulse_Original.svg').is_file())
        ET.parse(ASSETS/'Boxes/Electric_Pulse_Original.svg')
    def test_curated_assets(self):
        for name in ('Windows/Console.svg','Boxes/Performance_Tall.svg','Popups/Settings.svg','Buttons/OK.svg','Buttons/ANNULER.svg'):
            with self.subTest(name=name):
                ET.parse(ASSETS/name)
    def test_sources_retained(self):
        for name in ('nexus_pairing_secure.py','nexus_pairing_dialog.py','nexus_quick_commands.py','nexus_hover.py','nexus_connections.py','nexus_screen_adapter.py'):
            self.assertTrue((ROOT/name).exists())
    def test_reserved_column_blank(self):
        src=(ROOT/'nexus_workspace.py').read_text()
        self.assertIn('Reserved blank left column',src)
        self.assertNotIn("bar.addWidget(button('Terminals',lambda:None",src)
if __name__=='__main__':unittest.main()
