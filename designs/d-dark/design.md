# D Dark

公共通用示例：近黑冷灰、银白文字、分层蓝色、细斜纹。无公司 Logo、客户文案或真实截图；模板规定视觉语言，不规定页型骨架。

## 固定项

- 16:9，基于容器的 `cqw`；中文无衬线。正文可编辑，不把上屏文字烘焙为图片。
- 底色 `bg`；卡片 `surface`；弱蓝色面 `accent-surface`；品牌／主强调色块 `accent` 配白字。线条用 `accent-line`，强调文字用 `accent-text`，不要把所有蓝色色阶替换成原色。
- 封面可满幅斜纹；正文顶部标题区统一斜纹，下方内容区纯底。正文只有需要强调的卡片／色面可选 `.texture-card`，不自动给所有面板加纹理。
- 正文标题左、可选身份标识右，共用同一顶边节奏；无标识时不占位。内容页不加重复项目路径／长页眉。
- 留白、对齐、开放式列优先；有分组需要再用色面。分割线默认不加，不在每个列表行、卡片或流程节点上画顶线；必要关系线、表格结构线另按 `../../references/lines.md` 处理。无渐变发光、大圆角或整页高饱和底色。

## 默认可调

- 封面大标题 `5.8cqw / 1.09`，轻字重400；正文标题 `3cqw / 1.25`，字重500。字体有实际差异时目视调行距，不机械锁死两行换行。
- 水平安全区约5.5%，正文标题顶约7%；标题区纹理高约27%。长标题／有无副标题时可调整标题区高度，使文字完整落在区内，Logo和标题不相撞。
- 纹理：120°、6px间隔＋1px细线，线色 `rgba(205,212,225,.063)`。先用默认强度；屏幕有摩尔纹时放宽间距或减弱，不以纹理抢过正文。
- 小字与图形需实测对比度：深底上的普通文字以4.5:1为检查线，承载信息的图形以3:1为检查线；弱分隔和装饰不假称达标。原强调蓝不直接用于深底小字。

## 自由项

主视觉、页型、卡片数量、图表与图片摆位由内容决定；新拟大纲时可按需设置副标题，已确认的页数、副标题与页面分工不得擅改。封面可用主题图、真实素材或几何隐喻，不强制球形、Logo方块或三栏；色块穿插可用，但不能遮挡信息。不因模板而改写已确认标题或夸大规划能力。

## 素材

无预置品牌素材。图标按 Skill 的图标参考选用；不编造公司标识。字体使用本机系统字体，不依赖外链字体。

## 可执行配置

JSON 由构建器读取，规则由制作者执行。基础 CSS 只给视觉角色，不限制本次构图；需要时复制到内容工程扩展，使用新 `design.md` 引用扩展 CSS，保留模板 tokens。不要修改模板文件来适配单次内容。

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
    "header-height": "15.2cqw",
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
