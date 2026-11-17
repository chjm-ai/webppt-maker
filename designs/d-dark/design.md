# D Dark

公共基础模板：近黑冷灰、银白文字、分层蓝色、细斜纹。无公司 Logo、客户文案或真实截图；规定视觉语言，不规定页型骨架。

**这是深色视觉语言的参考模板。** 其他模板是它的完整快照，各自写全规则和 tokens，不自动跟随；改本文件不会影响已有模板。

## 固定项

- 16:9，基于容器的 `cqw`；中文无衬线。正文可编辑，不把上屏文字烘焙为图片。
- 颜色按用途取用，不混用色阶：底色 `bg` 垫整页；卡片 `surface`；弱蓝色面 `accent-surface`；品牌／主强调色块 `accent` 必须配 `accent-ink` 白字；线条 `accent-line`；强调文字 `accent-text`。**`accent` 原色只能做色块底，不能拿来写深底上的文字、画细线或做小字。**
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

无预置品牌素材。图标按 `references/icons.md` 选用，不编造公司标识。字体只用本机系统字体，不依赖外链字体。

## 可执行配置

JSON 由构建器读取，自然语言规则由制作者执行。基础 CSS 只给视觉角色，不限制本次构图；需要扩展时复制到内容工程，不要直接改模板文件去适配单次内容。

```json
{
  "name": "d-dark",
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
    "logo-height": "2cqw",
    "hairline": ".0625cqw",
    "texture-angle": "120deg",
    "texture-gap": "6px",
    "texture-period": "7px",
    "texture-ink": "rgba(205,212,225,.063)"
  }
}
```
