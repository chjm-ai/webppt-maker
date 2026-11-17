# Deepleaper Dark

获准随本仓库分发的 Deepleaper 品牌示例。视觉语言来自 D Dark，本文件是它的**完整快照**：规则与 tokens 都写全，不依赖其他模板文件。基础模板后续更新不会自动传导，需要时手动同步。

品牌名称和 Logo 不表示对任意衍生作品的背书。

## 固定项

- 16:9，基于容器的 `cqw`；中文无衬线。正文可编辑，不把上屏文字烘焙为图片。
- 颜色按用途取用，不混用色阶：底色 `bg` 垫整页；卡片 `surface`；弱蓝色面 `accent-surface`；品牌／主强调色块 `accent` 必须配 `accent-ink` 白字；线条 `accent-line`；强调文字 `accent-text`。**`accent` 原色只能做色块底，不能拿来写深底上的文字、画细线或做小字。**
- **正文右上用品牌字标**，不占标题宽度：完整白色字标，保持原比例，宽 `13.5cqw`、高 `3.66cqw`；长标题不得挤压 Logo，放不下时优先重排或缩小标题一档。
- **封面可用 De 方块做主视觉**：适合放大使用，不能缩成不可辨识的小角标；蓝底与留白属于原图，不自动抠图。
- 封面可满幅斜纹；正文顶部标题区统一斜纹，下方内容区纯底。正文只有需要强调的卡片／色面可选 `.texture-card`，不自动给所有面板加纹理。
- 正文标题左、可选身份标识右，共用同一顶边节奏；无标识时不占位。内容页不加重复项目路径／长页眉。
- **分割线默认不加**。不在列表行、卡片、流程节点上画装饰顶线；只在关系需要时用连接线，表格才用结构线，细则见 `../../references/lines.md`。装饰线不算信息，不得为了“显得整齐”添加。
- 无渐变发光、大圆角、整页高饱和底色。

## 默认可调

- 封面大标题 `5.8cqw / 1.09`，字重400；正文标题 `3cqw / 1.25`，字重500。字体有实际差异时目视调行距，不机械锁死两行换行。
- 水平安全区约5.5%。正文单行主标题顶 `3.1cqw`，副标题顶 `8.1cqw`，纹理区高 `12.4cqw`（约页高22%），正文起点 `16.4cqw`；分别由 `heading-top`、`subtitle-top`、`header-height`、`body-top` 调节。标题组内适度紧凑，主要分区留白放在纹理区与正文之间，但不要拉出明显空白断层。
- 以上是“单行主标题＋一行副标题”的默认节奏，不是固定坐标。标题换行或副标题较长时联动下移副标题、纹理下沿与正文起点；没有副标题时收回空位，不留空槽。Logo 与标题不得相撞。
- 纹理：120°、6px 间隔＋1px 细线，线色 `rgba(205,212,225,.063)`。屏幕出现摩尔纹时放宽间距或减弱，不让纹理抢过正文。
- 对比度检查线（已在 `scripts/check_templates.py` 中自动核验 tokens）：深底正文 ≥4.5:1，承载信息的图形 ≥3:1；装饰性弱线不冒充达标。

## 自由项

主视觉、页型、卡片数量、图表与图片摆位由内容决定；新拟大纲时可按需设置副标题，已确认的页数、副标题与页面分工不得擅改。封面可用主题图、真实素材或几何隐喻，不强制球形、Logo 方块或三栏；色块穿插可用，但不能遮挡信息。不因模板而改写已确认标题或夸大规划能力。

## 素材

| 文件（均在 assets/） | 用途 |
|---|---|
| wordmark-white-transparent.png | 深底正文右上完整白色字标；由黑字白底原图生成的透明白字，不重绘轮廓 |
| wordmark-blue.png | 原始白字蓝底横幅；蓝底与留白属于原图，不自动抠图 |
| monogram-blue.png | 原始白色 De 蓝方块，适合封面主视觉 |
| wordmark-gray.png / wordmark-black.png | 原始完整字标，白底备用 |

均为 PNG 位图，不宣称为路径 SVG。保持比例、不重绘字形、不染色原图。留白至少为字标高度的一半。

## 使用

页面里**直接写文件名**（如 `src="monogram-blue.png"`）即可，构建器会依次在内容目录和本模板 `assets/` 里查找，不必复制副本。`example/pages/` 中的示例页面就是这样引用的。

```sh
python3 scripts/check_templates.py
python3 scripts/build.py --manifest example/deck.json --design designs/deepleaper-dark/design.md --out output/deepleaper-demo.html
```

## 可执行配置

JSON 由构建器读取，自然语言规则由制作者执行。**所有被 `layouts.css` 引用的变量都必须在这里定义**，缺一个构建会直接报错。

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
