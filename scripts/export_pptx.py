#!/usr/bin/env python3
"""按需将本 skill 的自包含 HTML 导出为可编辑 PPTX 与 JSON 能力报告。"""
from __future__ import annotations

import argparse
import io
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

WIDTH, HEIGHT = 1600, 900
ORIGIN = 'http://pptx.invalid/'
LIMITATIONS = [
    '仅支持本 skill 生成及保存版本的自包含 HTML；不支持任意网站或重新设计。',
    '文字按浏览器最终换行拆成独立文本框；可编辑但不是可重排的原始段落。',
    '字体不嵌入 PPTX；接收设备缺字体、字重替换、字距及中西文基线可能改变外观。',
    'SVG/canvas、旋转、滤镜及复杂效果局部栅格化；不是可编辑矢量或数据图表。',
    'CSS stacking context、伪元素层叠、阴影外延、越界裁剪及 PowerPoint 字体度量可能近似；需人工核对。',
    '不输出动画、交互、超链接、音视频或演讲备注；不会把整页截图称为可编辑。',
]


class ExportError(RuntimeError):
    """可解释的导出失败。"""


def rgba(value):
    """读取 Chromium 计算后的 sRGB；未知颜色宁可失败，不悄悄变黑。"""
    if value == 'transparent':
        return (0, 0, 0, 0.0)
    match = re.fullmatch(r'rgba?\(([^)]+)\)', value)
    if not match:
        raise ExportError('不支持的计算颜色：' + value)
    parts = [v for v in re.split(r'[, /]+', match.group(1)) if v]
    if len(parts) not in (3, 4):
        raise ExportError('无效计算颜色：' + value)
    rgb = tuple(max(0, min(255, round(float(v)))) for v in parts[:3])
    return (*rgb, float(parts[3]) if len(parts) == 4 else 1.0)


def validate_paths(html, out):
    html, out = Path(html).expanduser().absolute(), Path(out).expanduser().absolute()
    report = out.with_suffix('.report.json')
    if out.suffix.lower() != '.pptx':
        raise ExportError('--out 必须为 .pptx')
    if out.exists() or out.is_symlink() or report.exists() or report.is_symlink():
        raise FileExistsError('输出或报告已存在，请使用新文件名')
    if not html.is_file() or html.suffix.lower() not in ('.html', '.htm'):
        raise ExportError('--html 必须为已保存的 HTML 文件')
    if html.stat().st_size > 64 * 1024 * 1024:
        raise ExportError('HTML 超过 64 MiB 限制')
    if not html.read_text(encoding='utf-8').strip():
        raise ExportError('HTML 为空')
    return html, out, report


def dependencies():
    try:
        from playwright.sync_api import sync_playwright
        from pptx import Presentation
    except ImportError as exc:
        raise ExportError('需要现有 Python 环境中的 playwright、python-pptx 及 Chromium；不自动安装：' + str(exc)) from exc
    return sync_playwright, Presentation


def base_report(html, out):
    return {'schema_version': 1, 'status': 'failed', 'input': str(html), 'output': str(out),
            'canvas': {'width': WIDTH, 'height': HEIGHT, 'unit': 'css-px'},
            'notes_included': False, 'pages': [], 'counts': {}, 'warnings': [],
            'failures': [], 'blocked_requests': [], 'limitations': LIMITATIONS}


def counts(items):
    counter = Counter(item['kind'] for item in items)
    return {key: counter[key] for key in ('text', 'shape', 'image', 'rasterized')}


def public_page(data):
    """报告保留对象来源和原因，不复制业务全文或图片字节。"""
    result = {k: data[k] for k in ('id', 'width', 'height', 'warnings', 'normalizedScale')}
    result['counts'] = counts(data['elements'])
    result['elements'] = [
        {**{k: v for k, v in item.items() if k not in ('png', 'font', 'text', 'pseudoColors')},
         'representation': {'text': 'native_text', 'shape': 'native_shape'}.get(item['kind'], item['kind']),
         'editable': item['kind'] in ('text', 'shape')}
        for item in data['elements']]
    native_chars = sum(len(e['text']) for e in data['elements'] if e['kind'] == 'text')
    raster_chars = sum(e.get('textChars', 0) for e in data['elements'])
    result['native_text_characters'] = native_chars
    result['rasterized_text_characters'] = raster_chars
    if data['domTextChars'] and not native_chars:
        raise ExportError(f"页面 {data['id']} 没有原生文字；拒绝截图式成功")
    if not native_chars:
        result['warnings'].append({'reason': '本页源稿无可提取文字；不能称为可编辑文字页'})
    if raster_chars:
        result['warnings'].append({'reason': f'{raster_chars} 字符位于局部栅格化元素内，不可编辑'})
    return result


def configure_browser(browser):
    context = browser.new_context(viewport={'width': WIDTH, 'height': HEIGHT},
                                  device_scale_factor=1, offline=True, service_workers='block',
                                  accept_downloads=False, color_scheme='dark', reduced_motion='reduce')
    # 假 HTTP 源替代 file://，浏览器根本拿不到磁盘路径或相邻文件。
    context.add_init_script("window.open=()=>null; window.alert=()=>{}; window.confirm=()=>false;")
    return context


def render_dom(html, report, sync_playwright):
    markup = html.read_text(encoding='utf-8')
    extractor = Path(__file__).with_name('pptx_extract.js').read_text(encoding='utf-8')
    pages, errors = [], []
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True)
        except Exception as exc:
            raise ExportError('Chromium 无法启动；请使用已有安装环境：' + str(exc)) from exc
        page = None
        try:
            context = configure_browser(browser)
            served = False

            def route_request(route):
                nonlocal served
                request = route.request
                if not served and request.url == ORIGIN and request.is_navigation_request():
                    served = True
                    csp = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                           "img-src data:; font-src data:; media-src data:; connect-src 'none'; "
                           "frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'")
                    route.fulfill(status=200, content_type='text/html; charset=utf-8', body=markup,
                                  headers={'Content-Security-Policy': csp})
                else:
                    report['blocked_requests'].append({'url': request.url[:300], 'type': request.resource_type})
                    route.abort('blockedbyclient')

            context.route('**/*', route_request)
            page = context.new_page()
            # CSP 阻断发生在 request 之前，也必须进入失败报告。
            page.add_init_script("""window.__pptxCsp=[];
                document.addEventListener('securitypolicyviolation', e => {
                  window.__pptxCsp.push({url:e.blockedURI,type:e.violatedDirective});
                });""")
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('requestfailed', lambda request: report['blocked_requests'].append(
                {'url': request.url[:300], 'type': request.resource_type, 'failure': request.failure}))
            page.set_default_timeout(15000)
            page.goto(ORIGIN, wait_until='load', timeout=30000)
            page.evaluate(extractor)
            total = page.evaluate('pptxPrepare()')
            report['expected_pages'] = total
            if total > 200:
                raise ExportError('超过 200 页上限')
            for index in range(total):
                page.evaluate('(index) => pptxActivate(index)', index)
                data = page.evaluate('pptxExtract()')
                if len(data['elements']) > 15000:
                    raise ExportError('单页输出超过 15000 对象上限')
                capture_images(page, data)
                report['pages'].append(public_page(data))
                pages.append(data)
            report['blocked_requests'].extend(page.evaluate('window.__pptxCsp'))
            if errors:
                raise ExportError('页面 JavaScript 错误：' + '; '.join(errors[:5]))
            if report['blocked_requests']:
                raise ExportError('HTML 引用了外部/本地资源，已拒绝；仅支持完整自包含 HTML')
            context.close()
        finally:
            if page is not None and not page.is_closed():
                try:
                    for violation in page.evaluate('window.__pptxCsp || []'):
                        if violation not in report['blocked_requests']:
                            report['blocked_requests'].append(violation)
                except Exception:
                    pass  # 页面已崩溃时，保留原异常而不是掩盖它。
            browser.close()
    return pages


def capture_images(page, data):
    for item in data['elements']:
        if item['kind'] not in ('image', 'rasterized'):
            continue
        locator = page.locator(f'[data-pptx-key="{item["key"]}"]')
        actual = locator.bounding_box()
        if actual is None:
            raise ExportError('局部截图对象消失：' + item['key'])
        x, y = max(0, actual['x']), max(0, actual['y'])
        w = min(WIDTH, actual['x'] + actual['width']) - x
        h = min(HEIGHT, actual['y'] + actual['height']) - y
        if w <= 0 or h <= 0:
            raise ExportError('局部截图不在画布中')
        try:
            page.evaluate('(args)=>pptxCaptureStyle(...args)',
                          [item['key'], item['mode'], item.get('pseudoColors', [])])
            item['png'] = page.screenshot(clip={'x': x, 'y': y, 'width': w, 'height': h},
                                          omit_background=True, animations='disabled')
        finally:
            page.evaluate('pptxClearCapture()')
        # 截图已经裁剪到画布；用真实屏幕坐标反算，避免拉伸整块原区域。
        slide_box = page.locator('[data-pptx-active] .slide').bounding_box()
        item['box'] = {'x': (x-slide_box['x'])*WIDTH/slide_box['width'],
                       'y': (y-slide_box['y'])*HEIGHT/slide_box['height'],
                       'w': w*WIDTH/slide_box['width'], 'h': h*HEIGHT/slide_box['height']}


def xml_alpha(color_element, opacity):
    from pptx.oxml.xmlchemy import OxmlElement
    alpha = OxmlElement('a:alpha')
    alpha.set('val', str(round(max(0, min(1, opacity)) * 100000)))
    color_element.append(alpha)


def set_color(fill, value, opacity=1):
    from pptx.dml.color import RGBColor
    red, green, blue, alpha = rgba(value)
    if alpha * opacity <= 0:
        fill.background()
        return
    fill.solid()
    fill.fore_color.rgb = RGBColor(red, green, blue)
    xml_alpha(fill.fore_color._color._xClr, alpha * opacity)


def emu(px):
    # 1600 px 对应 13 1/3 英寸，1 CSS px = 0.6 pt。
    return round(float(px) * 7620)


def add_shape(slide, item):
    from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
    from pptx.util import Pt
    b = item['box']
    kind = (MSO_AUTO_SHAPE_TYPE.OVAL if item['ellipse'] else
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if item['radius'] else MSO_AUTO_SHAPE_TYPE.RECTANGLE)
    shape = slide.shapes.add_shape(kind, emu(b['x']), emu(b['y']), emu(b['w']), emu(b['h']))
    set_color(shape.fill, item['fill'], item['opacity'])
    if kind == MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE:
        shape.adjustments[0] = min(.5, item['radius'] / max(1, min(b['w'], b['h'])))
    border = item['border']
    if border['width'] and border['style'] != 'none':
        set_color(shape.line.fill, border['color'], item['opacity'])
        shape.line.width = Pt(border['width'] * .6)
    else:
        shape.line.fill.background()
    return shape


def add_text(slide, item):
    from pptx.dml.color import RGBColor
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE
    from pptx.oxml.xmlchemy import OxmlElement
    from pptx.util import Pt
    b, f = item['box'], item['font']
    # 少量余量仅避免 Office 二次换行；文字不自动适配，也不重新决定行位置。
    shape = slide.shapes.add_textbox(emu(b['x']), emu(b['y']), emu(b['w'] + 3), emu(b['h'] + 2))
    tf = shape.text_frame
    tf.clear()
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = False
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = MSO_ANCHOR.TOP
    paragraph = tf.paragraphs[0]
    paragraph.space_before = paragraph.space_after = Pt(0)
    paragraph.line_spacing = 1.0
    run = paragraph.add_run()
    run.text = item['text']
    run.font.name, run.font.size = f['family'], Pt(f['size'] * .6)
    run.font.bold, run.font.italic, run.font.underline = f['bold'], f['italic'], f['underline']
    red, green, blue, alpha = rgba(f['color'])
    run.font.color.rgb = RGBColor(red, green, blue)
    xml_alpha(run.font.color._color._xClr, alpha * f['opacity'])
    props = run._r.get_or_add_rPr()
    props.set('spc', str(round(f['spacing'] * .6 * 100)))
    if f['strike']:
        props.set('strike', 'sngStrike')
    # 同时声明东亚字体，避免仅 latin 字体时中文被 Office 随意替换。
    for tag in ('a:ea', 'a:cs'):
        node = OxmlElement(tag)
        node.set('typeface', f['family'])
        props.append(node)
    return shape


def make_pptx(pages, Presentation):
    presentation = Presentation()
    presentation.slide_width, presentation.slide_height = emu(WIDTH), emu(HEIGHT)
    presentation.core_properties.title = 'HTML 幻灯片按需导出'
    presentation.core_properties.subject = '原生文字与基础形状；局部复杂图形为图片，详见同名 JSON 报告'
    for data in pages:
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        for item in data['elements']:
            b = item['box']
            if not all(math.isfinite(v) for v in b.values()) or b['w'] <= 0 or b['h'] <= 0:
                raise ExportError('无效对象坐标：' + item['key'])
            if item['kind'] == 'text':
                shape = add_text(slide, item)
            elif item['kind'] == 'shape':
                shape = add_shape(slide, item)
            else:
                shape = slide.shapes.add_picture(io.BytesIO(item['png']), emu(b['x']), emu(b['y']), emu(b['w']), emu(b['h']))
            shape.name = f"{item['kind']}:{item['key']}"
    output = io.BytesIO()
    presentation.save(output)
    return output.getvalue()


def write_new(path, content):
    """独占创建；包括同名报告，绝不覆盖旧成果或软链接。"""
    stream = path.open('xb')
    try:
        with stream:
            stream.write(content)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def export(html, out):
    html, out, report_path = validate_paths(html, out)
    report = base_report(html, out)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        sync_playwright, Presentation = dependencies()
        pages = render_dom(html, report, sync_playwright)
        pptx_bytes = make_pptx(pages, Presentation)
        total = Counter()
        for page in report['pages']:
            total.update(page['counts'])
        report['counts'] = dict(total)
        rasterized = total.get('rasterized', 0)
        if rasterized:
            report['warnings'].append(f'{rasterized} 个复杂局部已栅格化，不可编辑；请检查逐对象原因')
        report['status'] = 'completed_with_warnings' if rasterized or any(p['warnings'] for p in report['pages']) else 'completed'
        write_new(out, pptx_bytes)
        try:
            write_new(report_path, json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'))
        except Exception:
            out.unlink()  # 只撤销本次独占创建的输出，报告冲突不留半成品。
            raise
    except Exception as exc:
        report['status'] = 'failed'
        report['failures'].append(str(exc))
        if not report_path.exists() and not report_path.is_symlink():
            write_new(report_path, json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'))
        raise ExportError(f'{exc}；失败报告：{report_path}') from exc
    return report_path, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', required=True, type=Path, help='本 skill 生成或保存版本的自包含 HTML')
    parser.add_argument('--out', required=True, type=Path, help='新的 .pptx 路径（同名 .report.json 也不得存在）')
    args = parser.parse_args(argv)
    try:
        report_path, report = export(args.html, args.out)
    except Exception as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({'status': report['status'], 'output': str(args.out.absolute()), 'report': str(report_path),
                      'pages': len(report['pages']), 'counts': report['counts'], 'warnings': report['warnings'],
                      'manual_review_required': True}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
