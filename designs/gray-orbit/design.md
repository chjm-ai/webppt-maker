# Gray Orbit · 灰阶轨道

独立可替换的现代商务设计：深灰、无衬线、小面积蓝色；不含真实品牌资料。

## 视觉规则

- 16:9，使用 cqw 保持固定画布比例；中文系统无衬线。
- 深灰背景、灰白文字；强调色只点缀轨道、短线和核对关卡。
- 正文标题靠左、标志靠右；封面使用大标题与数学投影经纬球。
- 自绘球形是视觉隐喻，不表示实际技术架构；不靠发光和渐变堆砌正文。
- 图标统一用 Lucide 本地 SVG，来源与许可在 example/assets/icons/；默认线宽2。
- 图片完整 contain；无图页按关系选择流程、分支、对照或层级，不堆同构卡片。
- 五页至少四种主体构图，不靠换颜色或类名冒充差异。
- 所有标题、参数与流程节点保持 HTML 文字；图形仅承载几何。虚构工作台 SVG 的示意文字不作为实际软件证据。

## 可执行配置

本次 custom.json ＞ 本设计配置 ＞ 播放层。自然语言由制作 Skill 执行，构建器只解析本 JSON。

```json
{
  "name": "gray-orbit",
  "layout_css": "layouts.css",
  "tokens": {
    "bg": "#171c22",
    "surface": "#20262d",
    "ink": "#f3f4f6",
    "muted": "#969da5",
    "quiet": "#747d87",
    "line": "#444d58",
    "accent": "#0000ff",
    "font": "'PingFang SC', 'Microsoft YaHei', sans-serif",
    "title-size": "2.9cqw",
    "title-weight": "600",
    "heading-size": "2.25cqw",
    "body-size": "1.25cqw",
    "small-size": "0.96cqw",
    "pad-x": "5.1cqw",
    "pad-y": "4.6cqw",
    "card-radius": "0.9cqw",
    "section-gap": "3.2cqw",
    "logo-width": "10.2cqw"
  }
}
```

## 页型

| data-layout | 主体构图 |
|---|---|
| orb-cover | 大标题＋自绘经纬球、轨道与节点 |
| branch | 输入汇聚到规则，再分发为输出 |
| evidence | 大截图／示意图＋窄旁注 |
| checkpoint | 横向步骤＋放大的人工核对关卡 |
| verdict | 强文字结论＋证据／待核分层 |

小改使用 example/custom.example.json；新设计复制本目录，修改 design.md 与 layouts.css，再用 --design 指定。换色不代表完整换设计。
