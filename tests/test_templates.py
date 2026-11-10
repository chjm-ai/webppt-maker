import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('template_build', ROOT / 'scripts/build.py')
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class TemplateTests(unittest.TestCase):
    def test_public_template_builds_without_private_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            content = Path(temp)
            (content / 'page.html').write_text(
                '<article class="slide" data-slide-id="demo" data-layout="statement">'
                '<h1 class="slide-title">虚构示例：先核对，再交付</h1></article>', encoding='utf-8')
            manifest = content / 'deck.json'
            manifest.write_text(json.dumps({'title': '虚构模板测试', 'pages': [
                {'id': 'demo', 'layout': 'statement', 'file': 'page.html'}
            ]}), encoding='utf-8')
            out = content / 'new.html'
            build.build(argparse.Namespace(manifest=manifest,
                        design=ROOT / 'designs/d-dark/design.md', custom=None, out=out))
            result = out.read_text(encoding='utf-8')
            self.assertIn('--accent: #0a19ff;', result)
            self.assertIn('--accent-line: #5678f5;', result)
            self.assertIn('--cover-leading: 1.09;', result)
            self.assertIn('id="save"', result)
            self.assertNotIn('data/templates/', result)
            self.assertNotIn('<img', result)

    def test_public_template_tokens_support_customization(self):
        config = build.load_design(ROOT / 'designs/d-dark/design.md')
        with tempfile.TemporaryDirectory() as temp:
            custom = Path(temp) / 'custom.json'
            custom.write_text('{"tokens":{"header-height":"17cqw","cover-leading":"1.11"}}')
            css = build.make_tokens(config, custom)
            self.assertIn('--header-height: 17cqw;', css)
            self.assertIn('--cover-leading: 1.11;', css)

    def test_legacy_design_remains_available(self):
        config = build.load_design(ROOT / 'designs/gray-orbit/design.md')
        self.assertEqual(config['name'], 'gray-orbit')
        self.assertTrue((ROOT / 'designs/gray-orbit' / config['layout_css']).is_file())


if __name__ == '__main__':
    unittest.main()
