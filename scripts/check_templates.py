#!/usr/bin/env python3
"""模板体检：保存模板后必须运行。发现结构错误、缺变量或私有素材外泄时以非零码退出。

检查对象：designs/<name>/（公共）与 data/templates/<name>/（私有）。
只依赖 Python 标准库；退出码 0 = 全部通过。
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import SHARED_LAYOUT_CSS, token_problems  # noqa: E402  与构建器共用同一套 token 规则

PUBLIC_DIR = ROOT / 'designs'
PRIVATE_DIR = ROOT / 'data/templates'
SLUG = re.compile(r'^[a-z][a-z0-9-]*$')
JSON_BLOCK = re.compile(r'```json\s*\n(.*?)\n```', re.S)
IMAGE_REF = re.compile(r'src="([^"]+)"')

CONTRAST = [  # (前景, 背景, 最低对比度, 说明)
    ('ink', 'bg', 4.5, '正文'),
    ('muted', 'bg', 4.5, '次要文字'),
    ('accent-text', 'bg', 4.5, '强调文字'),
    ('accent-ink', 'accent', 4.5, '品牌色块上的文字'),
]


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, template, message):
        self.errors.append(f'[错误] {template}：{message}')

    def warn(self, template, message):
        self.warnings.append(f'[提醒] {template}：{message}')


def read_config(path):
    block = JSON_BLOCK.search(path.read_text(encoding='utf-8'))
    if not block:
        raise ValueError('缺少 ```json 配置块')
    return json.loads(block.group(1))


def luminance(color):
    color = color.lstrip('#')
    if len(color) != 6:
        raise ValueError('不是 6 位十六进制颜色：' + color)
    channels = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(fg, bg):
    high, low = sorted([luminance(fg), luminance(bg)], reverse=True)
    return (high + 0.05) / (low + 0.05)


def is_git_ignored(path):
    result = subprocess.run(['git', 'check-ignore', '-q', str(path)], cwd=ROOT)
    return result.returncode == 0


def check_template(template_dir, public, report):
    name = template_dir.name
    design_md = template_dir / 'design.md'
    if not design_md.is_file():
        report.error(name, '缺少 design.md')
        return
    if not SLUG.fullmatch(name):
        report.error(name, '目录名必须是短横线小写英文（如 my-brand-dark）')
    try:
        config = read_config(design_md)
    except (ValueError, json.JSONDecodeError) as exc:
        report.error(name, f'design.md 配置无法读取：{exc}')
        return
    if config.get('name') != name:
        report.error(name, f'JSON 的 name 是 {config.get("name")!r}，必须与目录名一致')
    if 'extends' in config:
        report.error(name, '不再支持 extends：每个模板要写全自己的规则和 tokens，'
                           '请复制一个完整模板再改')

    tokens = config.get('tokens')
    css_name = config.get('layout_css', 'layouts.css')
    css_path = (template_dir / css_name).resolve()
    css_text = ''
    if not css_path.is_file():
        report.error(name, f'缺少 layout_css：{css_name}')
    else:
        css_text = css_path.read_text(encoding='utf-8')
    css_text += '\n' + SHARED_LAYOUT_CSS.read_text(encoding='utf-8')
    for problem in token_problems(tokens, css_text):
        report.error(name, problem)
    if not isinstance(tokens, dict):
        return

    for fg, bg, minimum, label in CONTRAST:
        fg_value, bg_value = tokens.get(fg, ''), tokens.get(bg, '')
        try:
            ratio = contrast(fg_value, bg_value)
        except ValueError:
            continue
        if ratio < minimum:
            report.error(name, f'{label} {fg}({fg_value}) 在 {bg}({bg_value}) 上对比度 '
                               f'{ratio:.2f}:1，低于 {minimum}:1')

    if public and is_git_ignored(template_dir):
        report.error(name, '公共模板被 Git 忽略，无法随仓库分发')
    check_private_leak(template_dir, name, report)

    if not public:
        tracked = git_tracked(template_dir)
        if tracked:
            report.error(name, '私有模板已有文件进入 Git，提交会外泄：' + ', '.join(tracked[:5]))
        if '固定项' not in design_md.read_text(encoding='utf-8'):
            report.warn(name, '私有模板建议写明固定项／默认可调／自由项三层，便于后续复用')


def is_relative_to_public(path):
    try:
        path.relative_to(PUBLIC_DIR)
        return True
    except ValueError:
        return False


def check_private_leak(template_dir, name, report):
    """公共模板与示例页面里不允许出现指向 data/ 私有目录的引用（按原文判断，不解析路径）。"""
    targets = (list(template_dir.rglob('*.html'))
               + list((ROOT / 'example').rglob('*.html'))
               + list((ROOT / 'layouts').rglob('*.html')))
    for page in targets:
        text = page.read_text(encoding='utf-8')
        for ref in IMAGE_REF.findall(text):
            if 'data/templates/' in ref:
                report.error(name, f'{page.relative_to(ROOT)} 引用了私有模板素材：{ref}')


def git_tracked(path):
    result = subprocess.run(['git', 'ls-files', '--', str(path)], cwd=ROOT,
                            capture_output=True, text=True)
    return [line for line in result.stdout.splitlines() if line.strip()]


def check_examples(report):
    """示例页面属于公共仓库，不得引用私有素材；deck 指向的模板必须存在且可构建。"""
    example = ROOT / 'example'
    for deck in sorted(example.rglob('*.json')):
        if deck.name.startswith('custom'):
            continue
        try:
            manifest = json.loads(deck.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            report.error('example', f'{deck.relative_to(ROOT)} 不是合法 JSON：{exc}')
            continue
        design = (deck.parent / manifest.get('design', '')).resolve() if manifest.get('design') else None
        if design and not design.is_file():
            report.error('example', f'{deck.name} 指向的模板不存在：{manifest["design"]}')
        for page in manifest.get('pages', []):
            source = deck.parent / page.get('file', '')
            if not source.is_file():
                report.error('example', f'{deck.name} 引用的页面不存在：{page.get("file")}')
                continue
            # 同一套页面会被多套模板构建，图片可能来自任一模板的 assets/
            asset_dirs = [deck.parent] + [p.parent / 'assets'
                                          for p in sorted((ROOT / 'designs').glob('*/design.md'))]
            if design:
                asset_dirs.insert(1, design.parent / 'assets')
            for ref in IMAGE_REF.findall(source.read_text(encoding='utf-8')):
                if ref.startswith('data:') or 'data/templates/' in ref:
                    continue
                if not any((d / ref).is_file() for d in asset_dirs):
                    report.error('example', f'{source.name} 引用的文件在内容目录和模板 assets/ 都找不到：{ref}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', help='只检查 designs/ 或 data/templates/ 下的某个模板目录')
    args = parser.parse_args()
    report = Report()
    targets = []
    if args.template:
        target = Path(args.template).resolve()
        if not target.is_dir():
            print(f'找不到模板目录：{target}', file=sys.stderr)
            return 2
        targets.append((target, is_relative_to_public(target)))
    else:
        for base, public in [(PUBLIC_DIR, True), (PRIVATE_DIR, False)]:
            if base.is_dir():
                targets += [(p, public) for p in sorted(base.iterdir()) if p.is_dir()]
    for template_dir, public in targets:
        check_template(template_dir, public, report)
    check_examples(report)
    for line in report.errors + report.warnings:
        print(line)
    print(f'\n检查 {len(targets)} 个模板：{len(report.errors)} 个错误，{len(report.warnings)} 个提醒')
    return 1 if report.errors else 0


if __name__ == '__main__':
    sys.exit(main())
