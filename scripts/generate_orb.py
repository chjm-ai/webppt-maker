"""生成静态经纬球；纯本地几何，不表示产品架构。"""
from pathlib import Path
from math import sin, cos, pi


def project(x, y, z):
    tilt = -.36
    y, z = y * cos(tilt) - z * sin(tilt), y * sin(tilt) + z * cos(tilt)
    turn = -.43
    x, y = x * cos(turn) - y * sin(turn), x * sin(turn) + y * cos(turn)
    return 500 + x * 285, 480 + y * 285, z


def line_segments(points):
    result = []
    for first, second in zip(points, points[1:]):
        x, y, depth = project(*first)
        u, v, _ = project(*second)
        opacity = .15 if depth < 0 else .3 + .48 * depth
        result.append(f'<path d="M{x:.2f},{y:.2f}L{u:.2f},{v:.2f}" opacity="{opacity:.3f}"/>')
    return ''.join(result)


def grid():
    lines = []
    for index in range(1, 25):
        latitude = -pi / 2 + index * pi / 25
        points = [(cos(latitude)*cos(t*pi/90), sin(latitude), cos(latitude)*sin(t*pi/90)) for t in range(181)]
        lines.append(line_segments(points))
    for index in range(30):
        longitude = index * pi / 15
        points = [(cos(t*pi/180)*cos(longitude), sin(t*pi/180), cos(t*pi/180)*sin(longitude)) for t in range(-90, 91)]
        lines.append(line_segments(points))
    return ''.join(lines)


def make_svg():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 960" fill="none">
<defs><radialGradient id="shade"><stop stop-color="#293440"/><stop offset="1" stop-color="#171c22"/></radialGradient></defs>
<circle cx="500" cy="480" r="285" fill="url(#shade)"/>
<g stroke="#a4b0bf" stroke-width=".85">{grid()}</g>
<g transform="rotate(-28 500 480)"><ellipse cx="500" cy="480" rx="435" ry="115" stroke="#687687" stroke-width="1"/><path d="M65 480 A435 115 0 0 0 935 480" stroke="#344aff" stroke-width="4"/><circle cx="65" cy="480" r="7" fill="#f3f4f6"/><circle cx="935" cy="480" r="7" fill="#344aff"/></g>
<ellipse cx="500" cy="480" rx="360" ry="310" transform="rotate(32 500 480)" stroke="#536170" stroke-width="1" stroke-dasharray="2 10"/>
<circle cx="500" cy="480" r="300" stroke="#667384" stroke-width=".7" stroke-dasharray="1 11"/>
</svg>'''


if __name__ == '__main__':
    target = Path(__file__).resolve().parents[1] / 'example/assets/orb.svg'
    if target.exists():
        raise FileExistsError(target)
    target.write_text(make_svg(), encoding='utf-8')
    print(target)
