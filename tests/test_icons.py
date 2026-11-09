import base64
import hashlib
import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


icons = load_module('icons')
build = load_module('build')


class IconTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'icons'

    def test_bundled_svgs_have_valid_hashes_and_full_license(self):
        for library in ('lucide', 'phosphor'):
            catalog = icons.load_catalog(library)
            source = ROOT / 'assets/icons' / library
            license_text = icons.checked_bytes(source / 'LICENSE', catalog['license_sha256']).decode()
            self.assertEqual(len(catalog['revision']), 40)
            self.assertEqual(len(catalog['icons']), 24)
            for entry in catalog['icons']:
                data = icons.checked_bytes(source / (entry['name'] + '.svg'), entry['sha256'])
                svg = ET.fromstring(data)
                metadata = svg.find('{http://www.w3.org/2000/svg}metadata').text
                self.assertIn(license_text, metadata)
                self.assertIn(catalog['revision'], entry['url'])
                self.assertEqual(svg.tag, '{http://www.w3.org/2000/svg}svg')

    def test_export_contains_only_selected_icons_and_provenance(self):
        selected = icons.export_icons('phosphor', ['sun', 'drop'], self.output)
        self.assertEqual(set(p.name for p in self.output.iterdir()), {'sun.svg', 'drop.svg', 'LICENSE', 'sources.json'})
        self.assertEqual([i['name'] for i in selected['icons']], ['sun', 'drop'])
        self.assertEqual(json.loads((self.output / 'sources.json').read_text()), selected)

    def test_unknown_library_and_invalid_names_rejected_before_writing(self):
        with self.assertRaises(ValueError):
            icons.load_catalog('../lucide')
        for names in ([], ['sun', 'sun'], ['../LICENSE'], ['not-an-icon']):
            with self.assertRaises(ValueError):
                icons.export_icons('lucide', names, self.output)
            self.assertFalse(self.output.exists())

    def test_existing_output_is_untouched(self):
        self.output.mkdir()
        (self.output / 'keep.txt').write_text('保留')
        with self.assertRaises(FileExistsError):
            icons.export_icons('lucide', ['sun'], self.output)
        self.assertEqual((self.output / 'keep.txt').read_text(), '保留')
        self.assertEqual(len(list(self.output.iterdir())), 1)

    def test_tampered_asset_is_rejected(self):
        path = Path(self.temp.name) / 'changed.svg'
        path.write_text('changed')
        with self.assertRaisesRegex(ValueError, '校验失败'):
            icons.checked_bytes(path, hashlib.sha256(b'original').hexdigest())

    def test_build_preserves_embedded_license_for_both_libraries(self):
        for library, name in [('lucide', 'mail'), ('phosphor', 'envelope')]:
            directory = Path(self.temp.name) / library
            icons.export_icons(library, [name], directory)
            markup = build.inline_images(f'<img src="{name}.svg">', directory)
            encoded = markup.split('base64,', 1)[1].split('"', 1)[0]
            svg = ET.fromstring(base64.b64decode(encoded))
            metadata = svg.find('{http://www.w3.org/2000/svg}metadata').text
            self.assertIn((directory / 'LICENSE').read_text(), metadata)


if __name__ == '__main__':
    unittest.main()
