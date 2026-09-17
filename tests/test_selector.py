"""Pure-Python behavior tests; no models, server or Easy Use installation needed."""
import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / '__init__.py').read_text(encoding='utf-8-sig'))
parts = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
         and n.name in ('read_styles', 'StyleSelectorEnhancement')]
env = {'ROOT': ROOT, 'json': json, 'os': os,
       'io': SimpleNamespace(ComfyNode=object, NodeOutput=lambda *args: args)}
exec(compile(ast.Module(body=parts, type_ignores=[]), '<selector>', 'exec'), env)
Node = env['StyleSelectorEnhancement']


class SelectorTests(unittest.TestCase):
    def test_pairs_and_filenames(self):
        result = Node.execute('example', 'cup', '', 'Watercolor,Pencil Sketch',
                              '多选模式（逐一生成）', 'test')
        self.assertEqual([len(x) for x in result], [2, 2, 2])
        self.assertIn('Watercolor', result[0][0])
        self.assertIn('Graphite', result[0][1])
        self.assertEqual(result[2], ['test_水彩', 'test_铅笔素描'])

    def test_modes(self):
        for mode in ('单选模式', '多选模式（叠加）'):
            self.assertEqual(len(Node.execute('example', select_styles='Watercolor,Pencil Sketch', selection_mode=mode)[0]), 1)
        self.assertEqual(len(Node.execute('example', selection_mode='全选模式')[0]), 3)
        self.assertEqual(Node.execute('example', select_styles='', selection_mode='全选模式'), ([], [], []))

    def test_date_and_safe_suffix(self):
        prefix = Node._filename('test-%date:yyyyMMddhhmmss%', {'x': {'name_cn': '../bad:name'}}, ['x'])
        self.assertRegex(prefix, r'^test-\d{14}_')
        self.assertNotIn('/', prefix)
        self.assertNotIn(':', prefix)

    def test_library_path_rejected(self):
        with self.assertRaises(ValueError):
            env['read_styles']('../LICENSE')


if __name__ == '__main__':
    unittest.main()
