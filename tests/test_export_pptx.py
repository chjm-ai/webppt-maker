"""标准库单测总是运行；真实 Chromium 回归以 WEBPPT_PPTX_BROWSER=1 开启。"""
import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import export_pptx as exporter
import build

NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}


def fixture():
    # 虚构复杂排版，不包含真实客户信息，也不依赖外部资源。
    png = base64.b64encode(bytes.fromhex(
        '89504e470d0a1a0a0000000d4948445200000001000000010804000000b51c0c02'
        '0000000b4944415478da6364f80f00010501012718e3660000000049454e44ae426082')).decode()
    css = (ROOT / 'runtime/player.css').read_text() + '''
      .slide {position:relative;width:100%;height:100%;overflow:hidden;background:#f6f4ef;
        color:#253044;font:32px/1.5 Arial,sans-serif;padding:80px}
      h1 {font-size:64px;margin:0} p {margin:0} .wrap {width:390px;margin-top:24px}
      .wrap b {color:#a33a2c} .cards {display:flex;gap:30px;margin-top:35px}
      .card {width:360px;height:150px;border:2px solid #345678;border-radius:20px;padding:24px}
      .texture {background:linear-gradient(35deg,#cee,#fac);box-shadow:0 4px 9px #0003}
      .dot {width:60px;height:60px;border-radius:50%;background:#cc7755;position:absolute;right:110px;top:110px}
      .pseudo:before {content:'虚构';display:block;color:#668;font-size:16px}
      .scaled {transform:scale(.5);transform-origin:top left;font-size:40px;position:absolute;top:730px;left:80px;width:600px}
      .hidden {display:none} .visual {position:absolute;right:150px;top:340px;width:150px;height:150px}
      img {position:absolute;right:120px;bottom:100px;width:100px;height:80px;object-fit:contain}
    '''
    first = f'''<article class="slide" data-slide-id="fiction-one" data-layout="fiction">
      <h1>虚构材料保留编辑</h1><p class="wrap">Alpha beta gamma delta epsilon zeta eta theta <b>重点文字</b> tail content</p>
      <div class="cards"><div class="card">基础形状</div><div class="card texture">渐变仍保留文字</div></div>
      <div class="dot"></div><p class="pseudo">伪元素正文</p>
      <svg class="visual" viewBox="0 0 100 100"><path d="M10 80 Q50 5 90 80" stroke="#845" fill="none" stroke-width="6"/></svg>
      <img src="data:image/png;base64,{png}"><p class="scaled">缩放文字四十变二十</p><p class="hidden">不应出现</p>
      </article>'''
    second = '''<article class="slide" data-slide-id="fiction-two" data-layout="fiction">
      <h1>第二页不能漏掉</h1><p style="white-space:pre-wrap;position:absolute;top:220px;left:80px">first line\nsecond line</p>
      <p style="position:absolute;left:80px;top:420px"><span style="font-size:42px;font-style:italic;text-decoration:underline">独立样式</span></p>
      </article>'''
    pages = '\n'.join(f'<section class="deck-page" data-note="秘密备注不导出"><div class="frame">{part}</div></section>' for part in (first, second))
    return build.make_html('虚构 PPTX 回归', css, pages, (ROOT / 'runtime/player.js').read_text())


class UnitTests(unittest.TestCase):
    def test_color(self):
        self.assertEqual(exporter.rgba('rgb(12, 34, 56)'), (12, 34, 56, 1))
        self.assertEqual(exporter.rgba('rgba(1, 2, 3, 0.4)'), (1, 2, 3, .4))
        with self.assertRaises(exporter.ExportError):
            exporter.rgba('color(display-p3 1 0 0)')

    def test_no_overwrite_report_or_pptx(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            html, out = base / 'input.html', base / 'out.pptx'
            html.write_text('<html>hello</html>')
            for existing in (out, out.with_suffix('.report.json')):
                existing.write_bytes(b'untouched')
                with self.assertRaises(FileExistsError):
                    exporter.validate_paths(html, out)
                self.assertEqual(existing.read_bytes(), b'untouched')
                existing.unlink()
            exporter.write_new(out, b'first')
            with self.assertRaises(FileExistsError):
                exporter.write_new(out, b'second')
            self.assertEqual(out.read_bytes(), b'first')

    def test_reject_bad_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            html = base / 'empty.html'
            html.write_text('')
            with self.assertRaises(exporter.ExportError):
                exporter.validate_paths(html, base / 'out.pptx')
            html.write_text('text')
            with self.assertRaises(exporter.ExportError):
                exporter.validate_paths(html, base / 'out.pdf')
            link = base / 'link.pptx'
            link.symlink_to(base / 'absent')
            with self.assertRaises(FileExistsError):
                exporter.validate_paths(html, link)

    def test_report_does_not_claim_raster_text_editable(self):
        data = {'id': 'sample', 'width': 1600, 'height': 900, 'warnings': [],
                'normalizedScale': {'x': 1, 'y': 1}, 'domTextChars': 9,
                'elements': [{'kind': 'text', 'text': 'editable', 'font': {}},
                             {'kind': 'rasterized', 'textChars': 3, 'png': b'private'}]}
        public = exporter.public_page(data)
        self.assertEqual(public['counts']['text'], 1)
        self.assertEqual(public['rasterized_text_characters'], 3)
        self.assertTrue(public['warnings'])
        self.assertNotIn('png', public['elements'][1])
        self.assertNotIn('text', public['elements'][0])
        data['elements'] = data['elements'][1:]
        with self.assertRaises(exporter.ExportError):
            exporter.public_page(data)

    def test_help_does_not_require_optional_dependencies(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/export_pptx.py'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('--html', result.stdout)


@unittest.skipUnless(importlib.util.find_spec('pptx'), '需要现有 python-pptx')
class NativeXmlTests(unittest.TestCase):
    def test_native_objects_and_no_notes(self):
        from pptx import Presentation
        pages = [{'elements': [
            {'kind': 'text', 'key': 'one', 'text': '原生中文', 'box': {'x': 10, 'y': 20, 'w': 200, 'h': 40},
             'font': {'family': 'Arial', 'size': 32, 'bold': True, 'italic': True, 'underline': True,
                      'strike': True, 'spacing': 2, 'color': 'rgba(10, 20, 30, 0.5)', 'opacity': .5, 'scaleX': 1}},
            {'kind': 'shape', 'key': 'two', 'box': {'x': 10, 'y': 100, 'w': 100, 'h': 100},
             'ellipse': True, 'radius': 50, 'fill': 'rgb(20, 40, 60)', 'opacity': 1,
             'border': {'width': 1, 'color': 'rgb(0, 0, 0)', 'style': 'solid'}}]}]
        with zipfile.ZipFile(io.BytesIO(exporter.make_pptx(pages, Presentation))) as package:
            xml = ET.fromstring(package.read('ppt/slides/slide1.xml'))
            self.assertEqual([t.text for t in xml.findall('.//a:t', NS)], ['原生中文'])
            self.assertEqual(len(xml.findall('.//p:sp', NS)), 2)
            self.assertEqual(xml.find('.//a:alpha', NS).get('val'), '25000')
            self.assertFalse(any('notesSlides' in name for name in package.namelist()))
            self.assertEqual(xml.find('.//a:ea', NS).get('typeface'), 'Arial')


@unittest.skipUnless(os.environ.get('WEBPPT_PPTX_BROWSER') == '1', '设置 WEBPPT_PPTX_BROWSER=1 运行真实离线 Chromium 回归')
class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pptx-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.html = self.base / 'complex.html'
        self.html.write_text(fixture(), encoding='utf-8')

    def test_complex_and_saved_html(self):
        from pptx import Presentation
        _, report = exporter.export(self.html, self.base / 'complex.pptx')
        self.assertEqual(report['status'], 'completed_with_warnings')
        self.assertEqual(len(report['pages']), 2)
        self.assertGreater(report['counts']['text'], 10)
        self.assertGreater(report['counts']['shape'], 2)
        self.assertGreater(report['counts']['rasterized'], 1)
        self.assertEqual(report['counts']['image'], 1)
        presentation = Presentation(self.base / 'complex.pptx')
        texts = [shape.text for slide in presentation.slides for shape in slide.shapes if shape.has_text_frame]
        joined = ''.join(texts)
        for expected in ('虚构材料保留编辑', '渐变仍保留文字', '重点文字', '第二页不能漏掉', 'first line', 'second line'):
            self.assertIn(expected, joined)
        self.assertNotIn('不应出现', joined)
        emphasized = next(s for s in presentation.slides[0].shapes if s.has_text_frame and '重点' in s.text)
        self.assertTrue(emphasized.text_frame.paragraphs[0].runs[0].font.bold)
        self.assertEqual(str(emphasized.text_frame.paragraphs[0].runs[0].font.color.rgb), 'A33A2C')
        styled = next(s for s in presentation.slides[1].shapes if s.has_text_frame and '独立样式' in s.text)
        self.assertTrue(styled.text_frame.paragraphs[0].runs[0].font.italic)
        self.assertTrue(styled.text_frame.paragraphs[0].runs[0].font.underline)
        lines = [next(s for s in presentation.slides[1].shapes if s.has_text_frame and s.text == text)
                 for text in ('first line', 'second line')]
        self.assertAlmostEqual((lines[1].top-lines[0].top)/7620, 48, delta=1)
        scaled = next(s for s in presentation.slides[0].shapes if s.has_text_frame and '缩放文字' in s.text)
        self.assertAlmostEqual(scaled.text_frame.paragraphs[0].runs[0].font.size.pt, 12, delta=.2)
        self.assertAlmostEqual(scaled.left / 7620, 80, delta=1)
        self.assertAlmostEqual(scaled.top / 7620, 730, delta=10)
        with zipfile.ZipFile(self.base / 'complex.pptx') as archive:
            self.assertFalse(any('notesSlides' in name for name in archive.namelist()))
            self.assertNotIn('秘密备注', ''.join(archive.read(n).decode(errors='ignore') for n in archive.namelist() if n.endswith('.xml')))
        # 实际调用播放器保存，再消费下载的 HTML，不回到源片段重建。
        sync, _ = exporter.dependencies()
        with sync() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(accept_downloads=True)
            context.route('**/*', lambda route: route.fulfill(body=self.html.read_text(), content_type='text/html') if route.request.url == exporter.ORIGIN else route.abort())
            page = context.new_page()
            page.goto(exporter.ORIGIN)
            page.evaluate("document.querySelector('h1').textContent='保存后改字仍可编辑'; document.querySelectorAll('.deck-page')[1].dataset.note='保存后备注'; deckPlayer.go(1)")
            with page.expect_download() as event:
                page.evaluate('deckPlayer.saveVersion()')
            saved = self.base / 'saved.html'
            event.value.save_as(saved)
            browser.close()
        _, saved_report = exporter.export(saved, self.base / 'saved.pptx')
        self.assertEqual(len(saved_report['pages']), 2)
        saved_pptx = Presentation(self.base / 'saved.pptx')
        self.assertIn('保存后改字仍可编辑', ''.join(s.text for s in saved_pptx.slides[0].shapes if s.has_text_frame))

    def test_ancestor_text_decoration_and_atomic_boundary(self):
        from pptx import Presentation
        markup = '''<div style="position:absolute;left:800px;top:650px">
          <p style="text-decoration:underline"><span>Nested underline</span>
            <span style="display:inline-block">Atomic undecorated</span></p>
          <p style="text-decoration:line-through"><span>Nested strike</span></p></div>'''
        self.html.write_text(fixture().replace('</article>', markup + '</article>', 1))
        exporter.export(self.html, self.base / 'decoration.pptx')
        pptx = Presentation(self.base / 'decoration.pptx')
        runs = {s.text: s.text_frame.paragraphs[0].runs[0]
                for s in pptx.slides[0].shapes if s.has_text_frame and s.text}
        self.assertTrue(runs['Nested underline'].font.underline)
        self.assertFalse(runs['Atomic undecorated'].font.underline)
        self.assertEqual(runs['Nested strike']._r.get_or_add_rPr().get('strike'), 'sngStrike')

    def test_group_opacity_is_composited_as_local_image(self):
        from PIL import Image
        markup = '''<div style="position:absolute;left:800px;top:650px;width:300px;height:100px;background:black;opacity:.5">
          <div style="width:100px;height:100px;background:white"></div></div>'''
        self.html.write_text(fixture().replace('</article>', markup + '</article>', 1))
        sync, _ = exporter.dependencies()
        report = exporter.base_report(self.html, self.base / 'opacity.pptx')
        pages = exporter.render_dom(self.html, report, sync)
        group = next(e for e in pages[0]['elements'] if e.get('reason') == 'group opacity')
        self.assertEqual(group['kind'], 'rasterized')
        self.assertEqual(group['mode'], 'subtree')
        pixels = Image.open(io.BytesIO(group['png'])).convert('RGBA')
        self.assertEqual(pixels.getpixel((50, 50))[:3], (255, 255, 255))
        self.assertEqual(pixels.getpixel((150, 50))[:3], (0, 0, 0))
        self.assertAlmostEqual(pixels.getpixel((50, 50))[3], 128, delta=1)
        self.assertFalse(any(e['kind'] == 'shape' and e['box']['x'] == 800
                             and e['box']['y'] == 650 for e in pages[0]['elements']))

    def test_root_css_scale_is_normalized(self):
        from pptx import Presentation
        text = fixture().replace('</style>', '.slide {width:3200px;height:1800px;transform:scale(.5);transform-origin:0 0}</style>')
        self.html.write_text(text)
        _, report = exporter.export(self.html, self.base / 'scaled.pptx')
        self.assertAlmostEqual(report['pages'][0]['normalizedScale']['x'], .5)
        pptx = Presentation(self.base / 'scaled.pptx')
        title = next(s for s in pptx.slides[0].shapes if s.has_text_frame and '虚构材料' in s.text)
        self.assertAlmostEqual(title.left / 7620, 40, delta=1)
        self.assertAlmostEqual(title.text_frame.paragraphs[0].runs[0].font.size.pt, 19.2, delta=.2)

    def test_reject_whole_page_rasterization(self):
        text = fixture().replace('<h1>', '<div style="position:absolute;inset:0;transform:rotate(1deg)">', 1).replace('</h1>', '</div>', 1)
        self.html.write_text(text)
        out = self.base / 'whole.pptx'
        with self.assertRaisesRegex(exporter.ExportError, '复杂元素覆盖整页'):
            exporter.export(self.html, out)
        self.assertFalse(out.exists())

    def test_network_and_local_assets_fail(self):
        for index, url in enumerate(('https://example.com/image.png', 'file:///etc/passwd', '../private.png')):
            html = self.base / f'blocked-{index}.html'
            html.write_text(fixture().replace('<h1>', f'<img src="{url}"><h1>', 1))
            out = self.base / f'blocked-{index}.pptx'
            with self.assertRaises(exporter.ExportError):
                exporter.export(html, out)
            self.assertFalse(out.exists())
            report = json.loads(out.with_suffix('.report.json').read_text())
            self.assertEqual(report['status'], 'failed')
            self.assertTrue(report['failures'])
            self.assertTrue(report['blocked_requests'])

    def test_arbitrary_html_fails_with_report(self):
        self.html.write_text('<!doctype html><h1>not this skill</h1>')
        out = self.base / 'bad.pptx'
        with self.assertRaises(exporter.ExportError):
            exporter.export(self.html, out)
        self.assertEqual(json.loads(out.with_suffix('.report.json').read_text())['status'], 'failed')
        self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
