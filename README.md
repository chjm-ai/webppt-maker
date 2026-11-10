# webppt-maker

制作离线 HTML 幻灯片的独立 Skill。内容、可替换设计规范与播放器分层；支持球形封面、关系图、截图主导页、核对流程和结论页。

## 分阶段使用

同一个Skill支持三种入口，不另装大纲技能：

- **只讨论大纲**：先输出纯文本逐页主标题、必要副标题与核心内容；主标题给结论，不提前写画面设计。
- **细化已确认大纲**：拆开上屏文案、画面意图、讲稿与证据，保留原有标题和页面分工。
- **按已确认大纲制作**：直接进入设计制作，不重新编排故事。普通新需求先确认大纲；明确要求全流程直接交付时可连续执行。

确认和内容保护细则见 `references/outline.md`。设计制作时才使用视觉转译表；程序通过不等于内容、审美和用户定稿均通过。

## 使用

本目录位于 AI_Skills 下，可通过 SKILL.md 加载；已整合原 html-ppt 的改字、演讲备注和保存版本能力，不再需要旧技能。

```bash
python3 scripts/build.py --out output/demo.html
```

打开生成的 HTML 即可离线播放。示例为虚构的“HTML 幻灯片制作流程”，没有真实公司／客户材料。

| 操作 | 按钮／快捷键 |
|---|---|
| 翻页、总览、全屏 | 方向键、O、F；手机横向滑动 |
| 改字 | “改字”／E 启用，点击文字编辑；Esc 退出 |
| 当前页演讲备注 | “备注”／N；切页自动切换，可在演讲者窗口查看 |
| 独立演讲者窗口 | “演讲者”／S；显示当前标题、讲稿与下一页标题，可控制翻页 |
| 保存新 HTML | “保存版本”／Ctrl 或 Cmd+S；保留正文和逐页备注 |

- 默认只读，避免演讲时误改。编辑时不响应文字内的翻页快捷键，暂停滑动翻页；Esc 后点页面空白再使用播放快捷键。总览自动结束改字。
- 标题、段落、列表、表格文字及文字 span 可编辑；自定义文字容器加 `data-editable`，不想被改的区域加 `data-no-edit`。图片、SVG、交互控件不进入文字编辑。纯文字编辑不保证保留被整体替换的行内强调样式；改成长文后仍需检查溢出。
- `deck.json` 每页可加字符串 `notes` 作为初始讲稿；缺省为空。备注按页面保存，作为纯文字处理。演讲者窗口需允许弹窗。
- 保存会下载新的自包含 HTML，不覆盖原文件；重开默认第一页、退出编辑／总览、收起备注。可以再次编辑、再次保存；不维护独立版本历史列表。
- 改动仅在当前浏览器内，必须确认下载完成后再关闭。下载文件包含全部备注，分享前检查是否有内部信息。不会回写源页面、deck.json 或上传服务器。

```bash
# 临时覆盖设计参数；输出文件必须尚不存在
python3 scripts/build.py --custom example/custom.example.json --out output/custom.html
# 切换完整设计入口
python3 scripts/build.py --design designs/gray-orbit/design.md --out output/alternate.html
# 构建与异常用例
python3 -m unittest discover -s tests -v
# 可选：真实浏览器验收（需要 Chromium）
uv sync --extra dev
uv run playwright install chromium
uv run python scripts/check_browser.py
# 改字、备注、演讲者、多次保存重开与手机控件回归
uv run python scripts/check_editing.py
```

浏览器验收默认检查 output/demo.html；可传 `--html /绝对路径/另一份五页.html --scratch /截图目录`。截图默认进入系统临时目录。生成输出不提交 Git。

## 目录

- `SKILL.md`：制作流程与输出契约。
- `references/outline.md`：叙事大纲、制作大纲、确认边界和结论式标题检查。
- `evals/outline-stages.json`：阶段路由与内容保护的虚构行为测试用例。
- `references/composition.md`：内容关系与整组构图检查，仅在设计制作阶段使用。
- `references/icons.md`：Lucide／Phosphor／Tabler 的选用场景、语义与误用检查。
- `assets/icons/`：两套各24个本地精选图标、固定版本来源、哈希与完整许可。
- `scripts/icons.py`：离线检索中文关键词并复制选定图标，不联网、不覆盖已有目录。
- `designs/gray-orbit/design.md`：可替换视觉规范与 JSON tokens。
- `designs/gray-orbit/layouts.css`：五种页型的布局。
- `runtime/`：通用播放器与打印样式。
- `example/`：五页虚构示例、内容清单、可定制配置、本地素材。
- `scripts/build.py`：仅依赖 Python 标准库的构建器；拒绝覆盖旧输出。
- `scripts/generate_orb.py`：本地数学投影球形生成器；已有素材时拒绝覆盖。
- `tests/`：构建、覆盖配置、重复 ID、缺图等测试。

## 设计定制

本次明确要求与 custom.json ＞ design.md ＞通用默认。小改覆盖 tokens；新品牌复制设计目录，同时维护自己的布局 CSS。只换颜色不算完整设计。

自然语言视觉与语义规则由制作者执行；构建器只解析 JSON、校验基础契约并合成文件，不会自动判断审美或事实。五页至少四种主体构图，无图页先判断步骤、分支、层级或对照关系。

## 来源与边界

- 通用构建器、播放器与球形图形独立实现，没有直接复制第三方演示模板运行时。
- 默认 Lucide，教学／生活主题可整组选 Phosphor；Tabler 为按需候选，不混库。`assets/icons/` 保存精选 SVG、固定源码版本、原件与本地 SHA-256、完整许可；每份精选 SVG 的 metadata 已含许可，内嵌时保留。旧示例素材仍在 `example/assets/icons/`。无 CDN 依赖。
- 示例：`python3 scripts/icons.py --library lucide --query 人工`；复制：`python3 scripts/icons.py --library lucide --names mail bot user-round --out /path/to/content/assets/icons`。输出目录必须尚不存在；全集没有的对象按 `references/icons.md` 从官方库补取。
- 截图页为自绘虚构工作台，不表示实际软件功能。
- 不含真实研究正文、客户截图、公司 Logo、个人绝对路径或旧验收回执。
- Chromium 验收不等于所有浏览器、实体投影或视频播放均已验证。手机保持 16:9，不是长文阅读版。
