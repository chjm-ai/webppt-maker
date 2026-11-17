# 按需导出可编辑 PPTX

## 调用时机

默认交付并验收 HTML，不预先生成 PPTX。只有用户确认页面后明确说“导出 PPT / PPTX”，才调用本导出器。直接消费已确认的 HTML，包括播放器“保存版本”下载后含修改的 HTML；不重新构建源片段，不改写内容，不重新设计。

这是有限的 DOM → PowerPoint 对象转换，不是任意 HTML 的无损转换。禁止将整页截图版描述为可编辑 PPT。

## 命令与环境

在已具备 `playwright`、`python-pptx` 及匹配 Chromium 的 Python 3.11+ 环境运行：

```sh
python scripts/export_pptx.py --html output/confirmed.html --out output/confirmed-editable.pptx
```

- 可从任意工作目录调用脚本绝对路径。
- 先探测当前及已有虚拟环境的依赖；导出器不安装 Python 包、浏览器、字体或 Office，也不联网转换。
- `--html` 为本 skill 构建器生成的完整自包含 HTML，不是页面片段、网址或任意网页；不要求存在原 `deck.json`。
- `--out` 必须为新 `.pptx` 文件；同时生成 `confirmed-editable.report.json`。任一目标已存在（包括软链接）则拒绝，不覆盖。
- 返回码 `0` 表示产物与报告已写出，不代表无损；`completed_with_warnings` 必须复核。返回码 `2` 表示失败，标准错误输出 JSON。路径/输入预检失败只输出错误 JSON；进入导出后失败另写报告，不留下成功 PPTX。
- 标准输出 JSON 给出实际输出、报告路径、页数、分类计数与警告，始终要求人工复核。不要只看文件存在就报成功。

## 输入与离线边界

必须保持 `main.deck > section.deck-page > .frame > article.slide[data-slide-id][data-layout]` 契约，页面 ID 不重复。固定 1600×900 浏览器画布和 16:9 PPTX，逐页激活（不依赖首页或播放器当前页），隐藏播放、改字、备注、提示 UI，冻结 CSS 动画，等待字体及本页图片加载后读取最终 DOM。字体与图片加载超时/错误会失败。CSS 缩放后的坐标、字号、字距归一化；`.slide` 的最终边界必须填满 frame，整页偏移/缩小不是已支持契约。

HTML 由内存通过临时假 HTTP 源交给 Chromium，绝不以 `file://` 打开，也不运行本地服务器：

- 仅首次主文档请求获准；其余请求阻断。
- CSP 仅允许内嵌脚本/样式与 `data:` 图片、字体、媒体，禁止外部脚本、连接、框架、表单等；上下文关闭网络和 service worker。
- 不读取相邻文件、不跟随相对路径、绝对本地路径或远程资源。资源须先由正常构建流程嵌入。实际发生的网络/本地资源引用阻断或缺图会失败，并报告原因，不偷偷输出缺资源版。
- 本机已安装字体可由浏览器正常排版。字体不会嵌入 PPTX，交付设备需安装相同字体。
- 本工具只消费本 skill 的可信生成物；会执行其内嵌脚本以获得最终 DOM，不是面向恶意 HTML/脚本的安全沙箱。

上限：HTML 64 MiB、200 页、单页遍历 5000 元素、原生文字路径 50000 字符、输出 15000 对象。超过即失败，不截断后冒充成功。

## 对象能力

| 报告分类 | PPTX 表示 | 编辑能力与边界 |
|---|---|---|
| `text` / `native_text` | 原生文本框，按浏览器最终文字行与内联样式拆分 | 可编辑文字；保存行位置、字号、字体、颜色/透明度、粗斜体、下划线、删除线、字距、简单缩放。不是一个可自动重排的原段落 |
| `shape` / `native_shape` | 原生矩形、圆角矩形、圆/椭圆 | 可编辑填充/透明度、均一实线边框、几何与尺寸 |
| `image` | 嵌入 PNG 图片 | 原 HTML 图片在浏览器 `object-fit` 等排版后的局部图像；可以移动缩放，不是可编辑像素或矢量 |
| `rasterized` | 明确标记原因的局部透明 PNG | SVG/canvas、旋转/倾斜/3D、非等比文字缩放、蒙版/裁切、滤镜、整组透明度、文字效果及复杂图形等；局部文字可能不可编辑。渐变/阴影/伪元素可只截图背景层，正文继续原生输出 |

不会把整页复杂效果直接截图降级：整页效果或覆盖近整页的复杂子树将失败。正文存在却没有原生文字也会失败。大面积的纯背景纹理可以是背景图片，其上的文字仍为原生对象。

## 报告与限制

报告包含：

- `status`、`failures`、`blocked_requests`、统一画布、`notes_included: false`。
- 总体与逐页 `counts`：`text`、`shape`、`image`、`rasterized`。
- 逐对象 DOM key/tag、坐标、`representation`、`editable`；局部截图的 `reason`、`mode`，以及栅格化文字数量。
- 每页原生/栅格化字符数、缩放、警告与全局限制。不复制完整业务文字、图片数据或备注到报告。

已知近似：PowerPoint 与 Chromium 字形度量/基线不同，连续字重映射为粗体开关，接收端字体替换会改变外观；复杂 CSS stacking context、伪元素前后层叠、阴影超出元素边界、跨元素裁剪等不保证一致。列表默认 marker 尚未原生转换，会在逐页报告中明确警告，不应把缺 marker 的输出当作完整复刻。建议源稿以显式 HTML 标签表达重要标记。图表/SVG 不转换成可编辑数据图表。动画、交互、超链接与音视频不保留；视频只能作为明确报告的静态局部截图。默认不带演讲备注，本版没有开启备注的参数。

交付时同时给出 PPTX 与报告，说明哪些是原生、哪些是图片、哪些内容栅格化，要求逐页复核。没有实际在 PowerPoint/LibreOffice 打开并渲染过，必须明确说明，不能以 ZIP/XML 验证代替 Office 视觉验收。

## 回归

```sh
python -m unittest discover -s tests -p 'test_export_pptx.py' -v
WEBPPT_PPTX_BROWSER=1 python -m unittest discover -s tests -p 'test_export_pptx.py' -v
```

普通单测不依赖浏览器；原生 XML 测试在缺少 `python-pptx` 时明确跳过。浏览器回归须显式开启，使用现有环境，不自动安装：真实导出两页虚构复杂稿，核对原生文字/几何、内联样式、换行、内部及根 CSS scale、局部截图、非首页、隐藏内容、无备注；实际调用播放器保存并重新导出修改后的 HTML；核对远程/相对本地/绝对本地资源、任意 HTML 及整页截图降级的失败路径。
