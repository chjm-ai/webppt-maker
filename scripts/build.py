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
# 版式参考库对所有模板生效，模板必须提供它用到的全部 token
SHARED_LAYOUT_CSS = ROOT / 'runtime' / 'layouts.css'


class DesignError(ValueError):
    """模板本身有问题：结构、缺变量或路径不对。"""


# CSS 里引用但没给默认值的变量，必须在 tokens 里定义
CSS_VAR = re.compile(r'var\(\s*--([a-z0-9-]+)\s*\)')
# CSS 自己定义的变量（如 --material-texture）不算模板 token
CSS_DEFINE = re.compile(r'--([a-z0-9-]+)\s*:')


def required_tokens(css_text):
    defined = set(CSS_DEFINE.findall(css_text))
    return {name for name in CSS_VAR.findall(css_text) if name not in defined}


def token_problems(tokens, css_text=''):
    """检查 tokens 本身；返回问题清单，构建器和模板体检共用这一套规则。"""
    if not isinstance(tokens, dict) or not tokens:
        return ['tokens 不能为空']
    problems = []
    for key, value in tokens.items():
        if not TOKEN_NAME.fullmatch(key):
            problems.append(f'token 名不合法：{key}')
        elif not isinstance(value, str) or any(char in value for char in '<>{};\n'):
            problems.append(f'token 值不合法：{key}')
    if css_text:
        missing = sorted(required_tokens(css_text) - set(tokens))
        if missing:
            problems.append('样式文件用到但 tokens 没定义：' + ', '.join(missing))
    return problems


def load_design(path):
    """读取单个模板目录的 design.md；模板自包含，不跨目录继承。"""
    path = path.resolve()
    text = path.read_text(encoding='utf-8')
    block = re.search(r'```json\s*\n(.*?)\n```', text, re.S)
    if not block:
        raise DesignError('design.md 缺少 JSON 配置块')
    config = json.loads(block.group(1))
    css_name = config.get('layout_css', 'layouts.css')
    css_path = (path.parent / css_name).resolve()
    if not css_path.is_file():
        raise DesignError(f'找不到样式文件：{css_name}')
    css_text = css_path.read_text(encoding='utf-8') + '\n' + SHARED_LAYOUT_CSS.read_text(encoding='utf-8')
    problems = token_problems(config.get('tokens'), css_text)
    if problems:
        raise DesignError('；'.join(problems))
    config['layout_css_path'] = str(css_path)
    config['asset_dirs'] = [str(path.parent / 'assets')]
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


def resolve_asset(path_text, content_dir, template_dirs):
    """先找内容目录，再按顺序找模板目录（品牌素材直接引用模板里的原件，不必复制副本）。"""
    candidates = [(content_dir, '内容目录')] + [(d, '模板目录') for d in template_dirs]
    outside = []
    for base, label in candidates:
        asset = (base / path_text).resolve()
        if not asset.is_relative_to(base.resolve()):
            outside.append(f'{path_text}（不在{label}内）')
            continue
        if asset.is_file():
            return asset
    if outside:
        raise ValueError('图片必须位于内容目录或模板目录内：' + '、'.join(outside))
    raise FileNotFoundError(f'找不到图片：{path_text}（已查找：'
                            + '、'.join(str(b) for b, _ in candidates) + '）')


def inline_images(markup, content_dir, template_dirs=()):
    def replace(match):
        path_text = html.unescape(match.group(1))
        if path_text.startswith('data:'):
            return match.group(0)
        asset = resolve_asset(path_text, content_dir, template_dirs)
        mime = mimetypes.guess_type(asset.name)[0]
        if not mime or not mime.startswith('image/'):
            raise ValueError('不支持的图片类型：' + path_text)
        encoded = base64.b64encode(asset.read_bytes()).decode('ascii')
        return f'src="data:{mime};base64,{encoded}"'
    return re.sub(r'src="([^"]+)"', replace, markup)


TEMPLATE_ONLY = re.compile(r'<(\w+)[^>]*?\sdata-template-only="([^"]+)"[^>]*>')


def template_shown(only, design_name):
    """!名称 表示“除该模板外显示”。"""
    if only.startswith('!'):
        return design_name != only[1:]
    return design_name == only


def strip_template_only(markup, design_name):
    """一份页面给所有模板共用；只保留当前模板该显示的元素。"""
    while True:
        for match in TEMPLATE_ONLY.finditer(markup):
            if template_shown(match.group(2), design_name):
                continue
            tag = match.group(1)
            depth = 1
            for token in re.finditer(rf'<(/?){tag}\b[^>]*>', markup[match.end():]):
                depth += -1 if token.group(1) else 1
                if depth == 0:
                    end = match.end() + token.end()
                    break
            else:
                raise ValueError('data-template-only 元素未闭合：' + match.group(0))
            markup = markup[:match.start()] + markup[end:]
            break
        else:
            # 全部保留：只摘掉标记属性，其他属性原样保留
            return TEMPLATE_ONLY.sub(lambda m: re.sub(r'\s*data-template-only="[^"]*"', '',
                                                      m.group(0)), markup)


def render_pages(manifest, content_dir, design_name='', template_dirs=()):
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
        markup = strip_template_only(markup, design_name)
        for attribute, expected in [('data-slide-id', item['id']), ('data-layout', item['layout'])]:
            if f'{attribute}="{expected}"' not in markup:
                raise ValueError(f'{item["file"]} 的 {attribute} 与清单不一致')
        notes = item.get('notes', '')
        if not isinstance(notes, str):
            raise ValueError('演讲备注必须是文字：' + item['id'])
        pages.append('<section class="deck-page" data-note="' + html.escape(notes, quote=True)
                     + '"><div class="frame">' + inline_images(markup, content_dir, template_dirs) + '</div></section>')
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
<button id="fullscreen">全屏</button>
<button id="edit" aria-pressed="false">改字</button>
<button id="notes" aria-expanded="false" aria-controls="notes-panel">备注</button>
<button id="presenter">演讲者</button>
<button id="save">保存版本</button></nav>
<aside id="notes-panel" class="notes-panel" aria-label="演讲备注" hidden>
<label for="note-text">当前页备注（保存版本时一并保留）</label>
<textarea id="note-text" rows="5" placeholder="输入这一页的演讲备注"></textarea>
<button id="close-notes">关闭备注</button></aside>
<div id="message" class="player-message" role="status"></div>
<script>{script}</script></body></html>'''


def build(args):
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    design_path = args.design or (manifest_path.parent / manifest['design']).resolve()
    config = load_design(design_path)
    tokens = make_tokens(config, args.custom)
    template_dirs = [Path(d) for d in config.get('asset_dirs', [])]
    layout_path = Path(config['layout_css_path'])
    styles = '\n'.join([
        (ROOT / 'runtime/player.css').read_text(),
        tokens,
        SHARED_LAYOUT_CSS.read_text(encoding='utf-8'),
        layout_path.read_text(),
    ])
    pages = render_pages(manifest, manifest_path.parent, config['name'], template_dirs)
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
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if not args.out:
        parser.error('生成 HTML 需要 --out')
    try:
        build(args)
    except (DesignError, ValueError, FileNotFoundError) as exc:
        parser.exit(1, f'错误：{exc}\n')


if __name__ == '__main__':
    main()
