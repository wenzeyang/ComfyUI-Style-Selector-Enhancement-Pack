import ast
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from install import install


def load(name, directory):
    env = {'io': SimpleNamespace(ComfyNode=object, NodeOutput=lambda *args: args),
           'os': os, 'json': json, 'FOOOCUS_STYLES_DIR': directory, 'RESOURCES_DIR': directory}
    exec(compile((ROOT / 'src' / name).read_text(encoding='utf-8'), name, 'exec'), env)
    return env['stylesPromptSelector']


class SelectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        (self.path / 'example.json').write_text(json.dumps([
            {'name': 'A', 'prompt': 'paint {prompt}', 'negative_prompt': 'text'},
            {'name': 'B', 'prompt': 'photo {prompt}', 'negative_prompt': 'blur'},
            {'name': 'C', 'prompt': 'ink', 'negative_prompt': ''}]), encoding='utf-8')
        self.old = load('original_selector.py', self.temp.name)
        self.new = load('enhanced_selector.py', self.temp.name)

    def test_legacy_stack(self):
        for selected in ('', 'A', 'A,B', ['A', 'B', 'C'], 'unknown'):
            old = self.old.execute('example', 'cup', 'noise', selected)
            new = self.new.execute('example', 'cup', 'noise', selected)
            self.assertEqual(new, ([old[0]], [old[1]]))

    def test_separate_pairs(self):
        result = self.new.execute('example', 'cup', 'noise', 'A,B', '多选模式（逐一生成）')
        self.assertEqual(result, (['paint cup', 'photo cup'], ['noise, text', 'noise, blur']))

    def test_single_all_and_empty(self):
        self.assertEqual(self.new.execute('example', 'cup', '', 'A,B', '单选模式')[0], ['photo cup'])
        self.assertEqual(len(self.new.execute('example', selection_mode='全选模式')[0]), 3)
        self.assertEqual(self.new.execute('example', select_styles='', selection_mode='全选模式'), ([], []))
        self.assertEqual(len(self.new.execute('example', select_styles='A,C', selection_mode='全选模式')[0]), 2)

    def test_install_preserves_other_code_and_backs_up(self):
        backend = self.path / 'py/nodes/prompt.py'
        backend.parent.mkdir(parents=True)
        (self.path / 'web_version/v2').mkdir(parents=True)
        original = 'MARKER = 123\n' + (ROOT / 'src/original_selector.py').read_text(encoding='utf-8') + '\nTAIL = 456\n'
        backend.write_text(original, encoding='utf-8')
        install(self.path)
        changed = backend.read_text(encoding='utf-8')
        self.assertTrue(changed.startswith('MARKER = 123\n'))
        self.assertTrue(changed.endswith('TAIL = 456\n'))
        backup = next((self.path / 'style-manager-backups').glob('*/prompt.py'))
        self.assertEqual(backup.read_text(encoding='utf-8'), original)
        install(self.path)
        self.assertEqual(backend.read_text(encoding='utf-8'), changed)


if __name__ == '__main__':
    unittest.main()
