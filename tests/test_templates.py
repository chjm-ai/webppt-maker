import argparse
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load('template_build', 'scripts/build.py')
check = load('check_templates', 'scripts/check_templates.py')


def base_tokens():
    return dict(build.load_design(ROOT / 'designs/d-dark/design.md')['tokens'])


class TemplateTests(unittest.TestCase):
    def make_template(self, name, tokens=None, extra=None, css='.slide { color: var(--ink); }'):
        """在 designs/ 下建临时模板；测试结束自动删除。"""
        template = ROOT / 'designs' / name
        template.mkdir()
        self.addCleanup(shutil.rmtree, template, True)
        config = {'name': name, 'layout_css': 'layouts.css',
                  'tokens': base_tokens() if tokens is None else tokens}
        if extra:
            config.update(extra)
        (template / 'design.md').write_text(
            '# x\n```json\n' + json.dumps(config, ensure_ascii=False) + '\n```\n', encoding='utf-8')
        (template / 'layouts.css').write_text(css, encoding='utf-8')
        return template

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

    def test_header_spacing_defaults_and_customization(self):
        config = build.load_design(ROOT / 'designs/d-dark/design.md')
        expected = {'heading-top': '3.1cqw', 'subtitle-top': '8.1cqw',
                    'header-height': '12.4cqw', 'body-top': '16.4cqw'}
        for key, value in expected.items():
            self.assertEqual(config['tokens'][key], value)
        with tempfile.TemporaryDirectory() as temp:
            custom = Path(temp) / 'custom.json'
            custom.write_text(json.dumps({'tokens': {
                'subtitle-top': '12cqw', 'body-top': '21cqw'}}))
            css = build.make_tokens(config, custom)
            self.assertIn('--subtitle-top: 12cqw;', css)
            self.assertIn('--body-top: 21cqw;', css)

    def test_brand_template_is_a_complete_snapshot(self):
        brand = build.load_design(ROOT / 'designs/deepleaper-dark/design.md')
        generic = build.load_design(ROOT / 'designs/d-dark/design.md')
        self.assertEqual(brand['name'], 'deepleaper-dark')
        self.assertEqual(set(brand['tokens']), set(generic['tokens']))
        self.assertEqual(brand['tokens']['logo-height'], '3.66cqw')
        self.assertEqual(Path(brand['layout_css_path']),
                         ROOT / 'designs/deepleaper-dark/layouts.css')
        self.assertNotIn('inherits', brand)

    def test_brand_example_is_self_contained(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'brand.html'
            build.build(argparse.Namespace(
                manifest=ROOT / 'example/deck.json',
                design=ROOT / 'designs/deepleaper-dark/design.md', custom=None, out=out))
            result = out.read_text(encoding='utf-8')
            self.assertEqual(result.count('<article class="slide '), 4)
            self.assertIn('data:image/png;base64,', result)
            self.assertIn('虚构示例', result)
            self.assertIn('--accent: #0a19ff;', result)
            self.assertIn('--logo-height: 3.66cqw;', result)
            self.assertNotIn('src="wordmark', result)
            self.assertNotIn('/Users/', result)
            self.assertNotIn('data-template-only', result)

    def test_generic_example_drops_brand_elements(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'generic.html'
            build.build(argparse.Namespace(
                manifest=ROOT / 'example/deck.json',
                design=None, custom=None, out=out))
            result = out.read_text(encoding='utf-8')
            self.assertNotIn('<img', result)
            self.assertNotIn('Deepleaper', result)
            self.assertNotIn('data-template-only', result)
            self.assertIn('texture-card', result)

    def test_template_only_can_be_exclusive(self):
        markup = ('<p>A</p><div data-template-only="!brand"><img src="x.png"></div>'
                  '<div data-template-only="brand" class="b"><p>B</p></div>')
        generic = build.strip_template_only(markup, 'base')
        self.assertIn('<img src="x.png">', generic)
        self.assertNotIn('>B<', generic)
        self.assertNotIn('data-template-only', generic)
        branded = build.strip_template_only(markup, 'brand')
        self.assertNotIn('<img', branded)
        self.assertIn('class="b"><p>B</p>', branded)

    def test_unclosed_template_only_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '未闭合'):
            build.strip_template_only('<div data-template-only="x"><p>A</p>', 'base')

    def test_real_templates_pass_check(self):
        report = check.Report()
        for template_dir in sorted((ROOT / 'designs').iterdir()):
            check.check_template(template_dir, check.is_relative_to_public(template_dir), report)
        check.check_examples(report)
        self.assertEqual(report.errors, [])

    def test_checker_rejects_missing_design_md(self):
        template = ROOT / 'designs' / 'zz-empty'
        template.mkdir()
        self.addCleanup(shutil.rmtree, template, True)
        report = check.Report()
        check.check_template(template, True, report)
        self.assertIn('缺少 design.md', '\n'.join(report.errors))

    def test_checker_rejects_bad_tokens_and_contrast(self):
        tokens = base_tokens()
        tokens['accent-ink'] = '#0a19ff'
        tokens['Bad Key'] = '1cqw'
        template = self.make_template('zz-bad', tokens=tokens)
        report = check.Report()
        check.check_template(template, True, report)
        joined = '\n'.join(report.errors)
        self.assertIn('对比度', joined)
        self.assertIn('token 名不合法', joined)

    def test_checker_rejects_missing_token(self):
        tokens = base_tokens()
        del tokens['ink']
        template = self.make_template('zz-missing', tokens=tokens)
        report = check.Report()
        check.check_template(template, True, report)
        self.assertIn('tokens 没定义：ink', '\n'.join(report.errors))
        with self.assertRaisesRegex(build.DesignError, 'ink'):
            build.load_design(template / 'design.md')

    def test_checker_rejects_extends(self):
        template = self.make_template('zz-ext', extra={'extends': '../d-dark/design.md'})
        report = check.Report()
        check.check_template(template, True, report)
        self.assertIn('不再支持 extends', '\n'.join(report.errors))

    def test_checker_rejects_page_that_reads_private_assets(self):
        template = self.make_template('zz-leak')
        (template / 'page.html').write_text(
            '<img src="../data/templates/acme/logo.png">', encoding='utf-8')
        report = check.Report()
        check.check_template(template, True, report)
        self.assertIn('私有模板素材', '\n'.join(report.errors))

    def test_required_tokens_ignores_css_locals_and_fallbacks(self):
        css = (':root{--local:1} .a{color:var(--ink);background:var(--local);'
               'width:var(--optional, 10px)}')
        self.assertEqual(build.required_tokens(css), {'ink'})

    def test_contrast_helper(self):
        self.assertAlmostEqual(check.contrast('#ffffff', '#000000'), 21, places=2)
        self.assertLess(check.contrast('#0a19ff', '#121419'), 3)


if __name__ == '__main__':
    unittest.main()
