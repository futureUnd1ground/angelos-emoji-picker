import importlib.util, json, os, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('picker',ROOT/'picker.py')
p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)

class BindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        self.config=base/'niri'; self.config.mkdir()
        self.original='binds {\n    Mod+Period { expel-window-from-column; }\n    Mod+T { spawn "foot"; }\n}\n'
        (self.config/'keys.kdl').write_text(self.original)
        (self.config/'config.kdl').write_text('include "keys.kdl"\n')
        self.patch=patch.multiple(p,DATA=base/'data',CONFIG=self.config)
        self.patch.start(); self.addCleanup(self.patch.stop)
        p.DATA.mkdir()
    def test_real_niri_roundtrip_and_other_edits(self):
        p.enable('one')
        keys=self.config/'keys.kdl'
        self.assertIn('"launch"',keys.read_text())
        subprocess.run(['niri','validate','-c',str(self.config/'config.kdl')],check=True)
        keys.write_text(keys.read_text()+'// my unrelated edit\n')
        p.disable('one')
        self.assertEqual(keys.read_text(),self.original+'// my unrelated edit\n')
    def test_old_instance_cannot_remove_new_binding(self):
        p.enable('old'); p.enable('new'); p.disable('old')
        self.assertTrue((p.DATA/'binding.json').exists())
        p.disable('new'); self.assertEqual((self.config/'keys.kdl').read_text(),self.original)
    def test_user_changed_key_is_preserved(self):
        p.enable('one'); keys=self.config/'keys.kdl'
        keys.write_text(self.original.replace('expel-window-from-column','focus-column-right'))
        p.disable('one')
        self.assertIn('focus-column-right',keys.read_text())
    def test_unbound_key_has_reversible_block(self):
        (self.config/'keys.kdl').write_text('binds {\n    Mod+T { spawn "foot"; }\n}\n')
        root=self.config/'config.kdl'; before=root.read_text()
        p.enable('one'); p.disable('one'); self.assertEqual(root.read_text(),before)
    def test_invalid_configuration_is_not_written(self):
        root=self.config/'config.kdl'; root.write_text('this is invalid\n')
        before=root.read_text()
        with self.assertRaises(ValueError): p.enable('one')
        self.assertEqual(root.read_text(),before)
        self.assertFalse((p.DATA/'binding.json').exists())
    def test_duplicate_bindings_are_not_written(self):
        root=self.config/'config.kdl'; root.write_text(root.read_text()+self.original)
        with self.assertRaises(ValueError): p.enable('one')
        self.assertEqual((self.config/'keys.kdl').read_text(),self.original)

class PickerTests(unittest.TestCase):
    def test_data_has_russian_and_multi_codepoint_emoji(self):
        data=json.loads((ROOT/'data/emoji.json').read_text())
        self.assertEqual(len(data),3781)
        self.assertIn('собака',next(e['keywords'] for e in data if e['emoji']=='🐶'))
        self.assertTrue(any('\u200d' in e['emoji'] for e in data))
    def test_cancel_leaves_clipboard_alone(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(p,'DATA',Path(tmp)), patch.object(p.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'')) as run:
            p.launch(); self.assertEqual(run.call_count,1)
    def test_selected_sequence_copied_without_label(self):
        data=json.loads((ROOT/'data/emoji.json').read_text())
        i=next(i for i,e in enumerate(data) if '\u200d' in e['emoji'])
        responses=[subprocess.CompletedProcess([],0,str(i)),subprocess.CompletedProcess([],0),subprocess.CompletedProcess([],0)]
        with tempfile.TemporaryDirectory() as tmp, patch.object(p,'DATA',Path(tmp)), patch.object(p.subprocess,'run',side_effect=responses) as run:
            p.launch(); self.assertEqual(run.call_args_list[1].kwargs['input'],data[i]['emoji'].encode())

class AppearanceTests(unittest.TestCase):
    def test_presets_validate_with_real_fuzzel_and_fonts(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(p, 'DATA', Path(tmp)):
            for theme in ('system','dark','light','rose','custom','wallpaper'):
                for style in ('system','google','twemoji'):
                    with self.subTest(theme=theme,style=style):
                        args,env=p.appearance({'theme':theme,'emojiStyle':style},ROOT)
                        r=subprocess.run(['fuzzel','--check-config']+args,env=env,capture_output=True,text=True)
                        self.assertEqual(r.returncode,0,r.stderr)
            args,env=p.appearance({'emojiStyle':'twemoji'},ROOT)
            match=subprocess.check_output(['fc-match','monospace,Twemoji Mozilla:charset=1f600'],env=env,text=True)
            self.assertIn('Twemoji Mozilla',match)
    def test_wallpaper_colors_follow_accent(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(p, 'DATA', Path(tmp)):
            a,_=p.appearance({'theme':'wallpaper','_accent':'#ff0000'},ROOT)
            b,_=p.appearance({'theme':'wallpaper','_accent':'#0000ff'},ROOT)
            self.assertNotEqual(a,b)
    def test_invalid_settings_fall_back_without_arg_injection(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(p, 'DATA', Path(tmp)):
            a,_=p.appearance({'theme':{},'emojiStyle':[],'fontSize':{},'emojiFont':'bad\n--password'},ROOT)
            self.assertEqual(a,[])
            a,_=p.appearance({'theme':'custom','background':'#zzz','accent':'#123456;bad'},ROOT)
            self.assertIn('1e1e2eff',a)
            self.assertNotIn('#123456;bad',a)

if __name__=='__main__': unittest.main()
