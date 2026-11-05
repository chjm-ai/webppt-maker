#!/usr/bin/env python3
"""将页面、可替换设计规范和播放层合成离线 HTML；仅依赖 Python 标准库。"""
import argparse
import base64
import html
import json
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN_NAME = re.compile(r'^[a-z][a-z0-9-]*$')


def load_design(path):
    text = path.read_text(encoding='utf-8')
    block = re.search(r'```json\s*\n(.*?)\n```', text, re.S)
    if not block:
        raise ValueError('design.md 缺少 JSON 配置块')
    config = json.loads(block.group(1))
    if not isinstance(config.get('tokens'), dict) or not config['tokens']:
        raise ValueError('设计配置必须包含非空 tokens')
    return config


def make_tokens(config, custom_path):
    tokens = dict(config['tokens'])
    if custom_path:
        custom = json.loads(custom_path.read_text(encoding='utf-8'))
        overrides = custom.get('tokens', {})
        unknown = set(overrides) - set(tokens)
        if unknown:
            raise ValueError('未知定制项：' + ', '.join(sorted(unknown)))
        tokens.update(overrides)
    for key, value in tokens.items():
        if not TOKEN_NAME.fullmatch(key) or not isinstance(value, str):
            raise ValueError(f'无效设计项：{key}')
        if any(char in value for char in '<>{};'):
            raise ValueError(f'设计项含不支持的字符：{key}')
    return ':root {\n' + ''.join(f'  --{key}: {value};\n' for key, value in tokens.items()) + '}\n'


def inline_images(markup, content_dir):
    def replace(match):
        path_text = html.unescape(match.group(1))
        if path_text.startswith('data:'):
            return match.group(0)
        asset = (content_dir / path_text).resolve()
        if not asset.is_relative_to(content_dir.resolve()):
            raise ValueError('图片必须位于内容目录内：' + path_text)
        mime = mimetypes.guess_type(asset.name)[0]
        if not mime or not mime.startswith('image/'):
            raise ValueError('不支持的图片类型：' + path_text)
        encoded = base64.b64encode(asset.read_bytes()).decode('ascii')
        return f'src="data:{mime};base64,{encoded}"'
    return re.sub(r'src="([^"]+)"', replace, markup)


def render_pages(manifest, content_dir):
    seen = set()
    pages = []
    for item in manifest['pages']:
        if item['id'] in seen:
            raise ValueError('重复页面 ID：' + item['id'])
        seen.add(item['id'])
        source = (content_dir / item['file']).resolve()
        if not source.is_relative_to(content_dir.resolve()):
            raise ValueError('页面超出内容目录')
        markup = source.read_text(encoding='utf-8')
        for attribute, expected in [('data-slide-id', item['id']), ('data-layout', item['layout'])]:
            if f'{attribute}="{expected}"' not in markup:
                raise ValueError(f'{item["file"]} 的 {attribute} 与清单不一致')
        pages.append('<section class="deck-page"><div class="frame">' + inline_images(markup, content_dir) + '</div></section>')
    if not pages:
        raise ValueError('至少需要一页内容')
    return '\n'.join(pages)


def make_html(title, styles, pages, script):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{styles}</style></head>
<body><main class="deck" aria-label="幻灯片">{pages}</main>
<nav class="player-controls" aria-label="演示控制">
<button id="previous" aria-label="上一页">←</button>
<select id="jump" aria-label="跳转页面"></select>
<button id="next" aria-label="下一页">→</button>
<span id="status" class="player-status" aria-live="polite"></span>
<button id="overview" aria-pressed="false">总览</button>
<button id="fullscreen">全屏</button></nav>
<div id="message" class="player-message" role="status"></div>
<script>{script}</script></body></html>'''


def build(args):
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    design_path = args.design or (manifest_path.parent / manifest['design']).resolve()
    config = load_design(design_path)
    tokens = make_tokens(config, args.custom)
    layout_path = (design_path.parent / config['layout_css']).resolve()
    styles = '\n'.join([(ROOT / 'runtime/player.css').read_text(), tokens, layout_path.read_text()])
    pages = render_pages(manifest, manifest_path.parent)
    script = (ROOT / 'runtime/player.js').read_text()
    output = args.out.resolve()
    if output.exists():
        raise FileExistsError('输出已存在，请使用新文件名：' + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(make_html(manifest['title'], styles, pages, script), encoding='utf-8')
    print(json.dumps({'output': str(output), 'pages': len(manifest['pages']), 'design': config['name'], 'bytes': output.stat().st_size}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'example/deck.json')
    parser.add_argument('--design', type=Path)
    parser.add_argument('--custom', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    build(parser.parse_args())


if __name__ == '__main__':
    main()
