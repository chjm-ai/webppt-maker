#!/usr/bin/env python3
"""检索并复制随技能附带的本地图标；不联网、不覆盖已有素材。"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'assets/icons'


def load_catalog(library):
    if library not in ('lucide', 'phosphor'):
        raise ValueError('不支持的图标库：' + library)
    return json.loads((ROOT / library / 'sources.json').read_text(encoding='utf-8'))


def checked_bytes(path, expected):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError('素材校验失败：' + path.name)
    return content


def export_icons(library, names, output):
    catalog = load_catalog(library)
    entries = {item['name']: item for item in catalog['icons']}
    if not names or len(names) != len(set(names)):
        raise ValueError('请选择至少一个图标，且名称不能重复')
    if any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name not in entries for name in names):
        raise ValueError('图标不在本地目录中；先用 --query 检索名称')
    if output.exists():
        raise FileExistsError('素材目录已存在，请使用新目录：' + str(output))
    source = ROOT / library
    files = {name + '.svg': checked_bytes(source / (name + '.svg'), entries[name]['sha256']) for name in names}
    files['LICENSE'] = checked_bytes(source / 'LICENSE', catalog['license_sha256'])
    selected = dict(catalog, icons=[entries[name] for name in names])
    files['sources.json'] = (json.dumps(selected, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    output.mkdir(parents=True)
    for name, content in files.items():
        (output / name).write_bytes(content)
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', choices=['lucide', 'phosphor'], default='lucide')
    parser.add_argument('--query', default='', help='按英文名称或中文关键词检索；不传则列出全部')
    parser.add_argument('--names', nargs='+', help='按精确名称复制，整组演示使用同一个库')
    parser.add_argument('--out', type=Path, help='内容目录下一个尚不存在的素材子目录')
    args = parser.parse_args()
    if args.names:
        if not args.out:
            parser.error('--names 需要 --out')
        result = export_icons(args.library, args.names, args.out)
    else:
        if args.out:
            parser.error('--out 需要 --names')
        catalog = load_catalog(args.library)
        query = args.query.casefold()
        result = [item for item in catalog['icons'] if query in (item['name'] + ' ' + item['keywords']).casefold()]
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
