"""Source-level regression tests without Qt installed."""
import ast
import unittest
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent
STYLE = (ROOT/'nexus_nova1_style.py').read_text()
WORKSPACE = (ROOT/'nexus_workspace.py').read_text()

class NovaOneAnimatedTests(unittest.TestCase):
    def test_each_pane_has_real_pty_and_original_artwork(self):
        self.assertIn('class TerminalTile(NovaOneTerminalFrame):', WORKSPACE)
        self.assertIn('self.terminal=Terminal(command,self,', WORKSPACE)
        self.assertIn("_raster_asset('01_Electric_Pulse.svg')", STYLE)
        self.assertTrue((ROOT/'assets/theme_nexus/01_Electric_Pulse.svg').is_file())

    def test_asset_only_on_frame_border_never_overlay_on_text(self):
        self.assertIn('if row == 1 and col == 1:', STYLE)
        self.assertIn('_asset_border(painter, self._terminal_art', STYLE)
        self.assertNotIn('setGraphicsEffect(effect)', STYLE)

    def test_native_or_composited_opacity_and_range(self):
        self.assertIn("getattr(self, 'setTerminalOpacity', None)", WORKSPACE)
        self.assertIn('QGraphicsOpacityEffect(self)', WORKSPACE)
        self.assertIn('opacity.setRange(50,100)', WORKSPACE)
        self.assertIn('max(50,min(100', WORKSPACE)
        self.assertIn('for value in (50,60,70,80,90,100):', WORKSPACE)

    def test_buttons_use_original_svg_and_click_animation(self):
        self.assertIn("'Buttons/CONNECTER.svg'", STYLE)
        self.assertIn('strip_text=True', STYLE)
        self.assertIn('self.pressed.connect(self._pulse)', STYLE)
        self.assertIn('self._click_animation.setDuration(380)', STYLE)
        self.assertIn('self.pressed.connect(self._trigger_click)', WORKSPACE)

    def test_animations_can_be_disabled(self):
        self.assertIn('for control in self.findChildren(NovaOneButton):', WORKSPACE)
        self.assertIn('control.set_animated(self.animations_enabled)', WORKSPACE)
        self.assertIn('self.close_button.set_animated(enabled)', WORKSPACE)

    def test_unmodified_nova_architecture(self):
        for method in ('add_session','show_sessions','show_settings','show_scripts',
                       'show_ssh_menu','terminal_menu','run_quick'):
            self.assertIn(f'def {method}(', WORKSPACE)
        for module in ('nexus_pairing','nexus_lan_ssh','nexus_quick_commands',
                       'nexus_ssh_keys','nexus_hover'):
            self.assertTrue((ROOT/f'{module}.py').is_file())
        self.assertIn("self.nav=NeonGlassPanel(accent='#0fa8d0',cut=12)", WORKSPACE)
        self.assertIn('QSplitter(orientation)', WORKSPACE)

    def test_assets_are_well_formed_and_source_parseable(self):
        for name in ('01_Electric_Pulse.svg','Buttons/CONNECTER.svg', 'Buttons/PARAMETRES.svg'):
            ElementTree.parse(ROOT/'assets/theme_nexus'/name)
        for name in ('nexus_workspace.py','nexus_nova1_style.py','nexus_skin.py'):
            ast.parse((ROOT/name).read_text())

if __name__ == '__main__':
    unittest.main()
