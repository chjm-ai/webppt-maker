import argparse
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('build', ROOT / 'scripts/build.py')
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'example', self.root / 'example')
        self.manifest = self.root / 'example/deck.json'
        self.args = argparse.Namespace(
            manifest=self.manifest,
            design=ROOT / 'designs/d-dark/design.md',
            custom=None,
            out=self.root / 'demo.html',
        )

    def update_manifest(self, change):
        content = json.loads(self.manifest.read_text())
        change(content)
        self.manifest.write_text(json.dumps(content))

    def test_build_inlines_all_slides(self):
        build.build(self.args)
        html = self.args.out.read_text()
        self.assertEqual(html.count('<section class="deck-page"'), 4)
        self.assertNotIn('src="assets/', html)
        self.assertNotIn('<img', html)

    def test_notes_are_escaped_and_controls_are_included(self):
        self.update_manifest(lambda m: m['pages'][0].update(notes='讲稿 "<&>\n</textarea><script>alert(1)</script>'))
        build.build(self.args)
        markup = self.args.out.read_text()
        self.assertIn('data-note="讲稿 &quot;&lt;&amp;&gt;', markup)
        self.assertIn('&lt;/textarea&gt;&lt;script&gt;alert(1)&lt;/script&gt;', markup)
        for name in ['edit', 'notes', 'note-text', 'save', 'presenter']:
            self.assertIn(f'id="{name}"', markup)

    def test_non_text_notes_are_rejected(self):
        self.update_manifest(lambda m: m['pages'][0].update(notes={'invalid': True}))
        with self.assertRaisesRegex(ValueError, '演讲备注必须是文字'):
            build.build(self.args)

    def test_notes_are_optional(self):
        self.update_manifest(lambda m: [p.pop('notes', None) for p in m['pages']])
        build.build(self.args)
        self.assertEqual(self.args.out.read_text().count('data-note=""'), 4)

    def test_existing_output_is_not_overwritten(self):
        self.args.out.write_text('原文件')
        with self.assertRaises(FileExistsError):
            build.build(self.args)
        self.assertEqual(self.args.out.read_text(), '原文件')

    def test_custom_token_overrides_design(self):
        self.args.custom = self.root / 'custom.json'
        self.args.custom.write_text('{"tokens":{"title-size":"3.1cqw"}}')
        build.build(self.args)
        self.assertIn('--title-size: 3.1cqw;', self.args.out.read_text())

    def test_unknown_token_is_rejected(self):
        self.args.custom = self.root / 'custom.json'
        self.args.custom.write_text('{"tokens":{"unknown":"1"}}')
        with self.assertRaisesRegex(ValueError, '未知定制项'):
            build.build(self.args)

    def test_duplicate_slide_id_is_rejected(self):
        self.update_manifest(lambda m: m['pages'].append(m['pages'][0]))
        with self.assertRaisesRegex(ValueError, '重复页面 ID'):
            build.build(self.args)

    def test_image_is_found_in_template_assets(self):
        """页面只写文件名，构建器从模板 assets/ 取原件，不在内容目录留副本。"""
        self.args.design = ROOT / 'designs/deepleaper-dark/design.md'
        build.build(self.args)
        self.assertIn('data:image/png;base64,', self.args.out.read_text())

    def test_missing_image_is_reported(self):
        content = self.root / 'example'
        with self.assertRaisesRegex(FileNotFoundError, '找不到图片'):
            build.inline_images('<img src="not-exists.png">', content, [])

    def test_empty_deck_is_rejected(self):
        self.update_manifest(lambda m: m.update(pages=[]))
        with self.assertRaisesRegex(ValueError, '至少需要一页'):
            build.build(self.args)

    def test_asset_cannot_escape_content_directory(self):
        content = self.root / 'example'
        with self.assertRaisesRegex(ValueError, '图片必须位于内容目录或模板目录内'):
            build.inline_images('<img src="../outside.svg">', content)

    def test_layout_reference_deck_builds_for_each_template(self):
        """版式参考页不绑定模板；共享结构 CSS 由构建器统一注入。"""
        for design in ('d-dark', 'deepleaper-dark'):
            out = self.root / f'layouts-{design}.html'
            build.build(argparse.Namespace(
                manifest=ROOT / 'layouts/deck.json',
                design=ROOT / f'designs/{design}/design.md', custom=None, out=out))
            html = out.read_text()
            self.assertEqual(html.count('<section class="deck-page"'), 7)
            self.assertIn('.ly-matrix', html)
            self.assertNotIn('data-template-only', html)


if __name__ == '__main__':
    unittest.main()
