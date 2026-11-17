# Deepleaper Dark

获准随本仓库分发的 Deepleaper 品牌示例：近黑冷灰、银白文字、分层蓝色、细斜纹。仅提供规范与品牌素材，不携带真实客户稿、截图或讲稿。品牌名称和 Logo 不表示对任意衍生作品的背书。


## 固定项

- 16:9，基于容器的 `cqw`；中文无衬线。正文可编辑，不把上屏文字烘焙为图片。
- 底色 `bg`；卡片 `surface`；弱蓝色面 `accent-surface`；品牌／主强调色块 `accent` 配白字。线条用 `accent-line`，强调文字用 `accent-text`，不要把所有蓝色色阶替换成原色。
- 封面可满幅斜纹；正文顶部标题区统一斜纹，下方内容区纯底。正文只有需要强调的卡片／色面可选 `.texture-card`，不自动给所有面板加纹理。
- 正文标题左、品牌 Logo 右，共用同一顶边节奏；使用完整字标，保持原比例；长标题不得挤压 Logo。内容页不加重复项目路径／长页眉。
- 留白、对齐、开放式列优先；有分组需要再用色面。分割线默认不加，不在每个列表行、卡片或流程节点上画顶线；必要关系线、表格结构线另按 `../../references/lines.md` 处理。无渐变发光、大圆角或整页高饱和底色。

## 默认可调

- 封面大标题 `5.8cqw / 1.09`，轻字重400；正文标题 `3cqw / 1.25`，字重500。字体有实际差异时目视调行距，不机械锁死两行换行。
- 水平安全区约5.5%。正文单行主标题顶 `3.1cqw`，副标题顶 `8.1cqw`，纹理区高 `12.4cqw`（约页高22%），正文起点 `16.4cqw`；分别由 `heading-top`、`subtitle-top`、`header-height`、`body-top` 调节。标题组适度紧凑，主要分区留白在纹理区与正文之间，但不拉出明显空白断层。
- 上述是单行主标题＋一行副标题的默认节奏，不是固定坐标骨架。标题换行或副标题较长时联动下移副标题、纹理下沿与正文起点；没有副标题时收回其空位，不留空槽。正文仍可用不同构图，Logo和标题不相撞。
- 纹理：120°、6px间隔＋1px细线，线色 `rgba(205,212,225,.063)`。先用默认强度；屏幕有摩尔纹时放宽间距或减弱，不以纹理抢过正文。
- 小字与图形需实测对比度：深底上的普通文字以4.5:1为检查线，承载信息的图形以3:1为检查线；弱分隔和装饰不假称达标。原强调蓝不直接用于深底小字。

## 自由项

主视觉、页型、卡片数量、图表与图片摆位由内容决定；新拟大纲时可按需设置副标题，已确认的页数、副标题与页面分工不得擅改。封面可用主题图、真实素材或几何隐喻，不强制球形、Logo方块或三栏；色块穿插可用，但不能遮挡信息。不因模板而改写已确认标题或夸大规划能力。

## 素材与用法

| 文件（均在 assets/） | 用途 |
|---|---|
| wordmark-white-transparent.png | 深底正文右上完整白色字标；由提供的黑字白底原图生成透明白字，不重绘轮廓 |
| wordmark-gray.png | 原始灰色完整字标，白底 |
| wordmark-black.png | 原始黑色完整字标，白底 |
| wordmark-blue.png | 原始白字蓝底横幅；蓝底与留白属于原图，不应自动抠图 |
| monogram-blue.png | 原始白色 De 蓝方块，适合品牌主视觉；不要把它缩成不可辨识的小角标 |

这些是 PNG 位图，不宣称为路径 SVG。保持比例、不重绘字形、不染色原图。白色透明版是明确标注的派生素材。封面可采用 De 方块或其他主题主视觉，不强制一套构图。字标推荐宽 13.5cqw、高 3.66cqw；object-fit:contain。留白至少为字标高度的一半。封面使用字标时可放大，不让品牌只剩角落里的小字。

先把选中的素材复制到本次内容目录，再以相对路径引用；构建器不跨目录读取图片。不把真实截图、客户信息或讲稿拷入公共模板。随附 example/deepleaper/ 为虚构品牌流程演示，可使用下述命令构建；不代替本次内容的自由构图。

```sh
python3 scripts/build.py --manifest example/deepleaper/deck.json --out output/deepleaper-demo.html
```

## 可执行配置

基础 CSS 提供视觉角色，不是固定页面库；本次构图扩展应写入独立内容工程，不回写公共模板。模板规范与 D Dark 共用已确认色阶；品牌原蓝 #0A19FF 仅用于色块，辅助线／文字使用分层蓝色。

```json
{
  "name": "deepleaper-dark",
  "layout_css": "layouts.css",
  "tokens": {
    "bg": "#121419",
    "surface": "#1b1f28",
    "ink": "#f1f3f7",
    "muted": "#b6bfce",
    "quiet": "#a2adbe",
    "line": "#414957",
    "accent": "#0a19ff",
    "accent-surface": "#151c46",
    "accent-line": "#5678f5",
    "accent-text": "#9db5ff",
    "accent-ink": "#ffffff",
    "font": "'PingFang SC', 'Microsoft YaHei', sans-serif",
    "cover-size": "5.8cqw",
    "cover-weight": "400",
    "cover-leading": "1.09",
    "title-size": "3cqw",
    "title-weight": "500",
    "title-leading": "1.25",
    "heading-size": "2cqw",
    "body-size": "1.4cqw",
    "small-size": "1.05cqw",
    "pad-x": "5.5cqw",
    "pad-y": "3.9cqw",
    "heading-top": "3.1cqw",
    "subtitle-top": "8.1cqw",
    "header-height": "12.4cqw",
    "body-top": "16.4cqw",
    "section-gap": "2cqw",
    "card-radius": "0cqw",
    "logo-width": "13.5cqw",
    "logo-height": "3.66cqw",
    "hairline": ".0625cqw",
    "texture-angle": "120deg",
    "texture-gap": "6px",
    "texture-period": "7px",
    "texture-ink": "rgba(205,212,225,.063)"
  }
}
```
