import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'paper-to-course/scripts'))
from build import build_file, render, validate_library
from build_library import build_library


class PublicPackageTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'examples/deep-compression.lesson.json').read_text(encoding='utf-8'))

    def test_example_builds_offline_and_escapes_script_termination(self):
        self.data['intro'] = '</script><img src=x onerror=alert(1)>'
        html = render(self.data)
        data = json.loads(re.search(r'id="lesson-data">(.*?)</script>', html, re.S)[1])
        self.assertEqual(data, self.data)
        self.assertNotIn('<img src=x', html)
        self.assertNotRegex(html, r'<script[^>]+src=')
        self.assertNotRegex(html, r'<link[^>]+href=')

    def test_batches_do_not_include_another_batch_or_share_paper_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            keys = []
            for batch in ('one', 'two'):
                data = copy.deepcopy(self.data)
                data['paper']['id'] = batch
                (base / (batch + '.json')).write_text(json.dumps(data), encoding='utf-8')
                manifest = base / (batch + '-batch.json')
                manifest.write_text(json.dumps([dict(lesson=batch+'.json', file='reader.html')]), encoding='utf-8')
                catalog = build_library(manifest, base / batch)
                self.assertEqual([p['id'] for p in catalog], [batch])
                output = base / batch / 'reader.html'
                build_file(data, output)
                html = output.read_text(encoding='utf-8')
                menu = json.loads(re.search(r'id="paper-library">(.*?)</script>', html, re.S)[1])
                self.assertEqual(menu, catalog)
                keys.append(re.search(r"KEY='([^']+)'", html)[1])
            self.assertNotEqual(keys[0], keys[1])

    def test_library_rejects_external_and_parent_paths(self):
        for href in ('https://example.com/x.html', '../reader.html', 'javascript:x.html', '%2f.html'):
            with self.subTest(href=href), self.assertRaises(ValueError):
                validate_library([dict(id='a',title='a',subtitle='a',access='full',href=href)])

    def test_preview_is_static_svg(self):
        svg = ET.parse(ROOT / 'docs/preview.svg').getroot()
        self.assertEqual(svg.tag, '{http://www.w3.org/2000/svg}svg')
        self.assertFalse(svg.findall('.//{http://www.w3.org/2000/svg}script'))


if __name__ == '__main__':
    unittest.main()
