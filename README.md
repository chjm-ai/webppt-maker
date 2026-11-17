# webppt-maker

把大纲、演讲稿和业务资料制作成可离线播放的 HTML 幻灯片，支持文字编辑、逐页讲稿和另存新版本。

**技能入口：[SKILL.md](SKILL.md)**

## 安装

```bash
npx skills add chjm-ai/webppt-maker
```

按提示选择目标工具与安装范围，安装后新开会话。安装需保留完整技能目录，不能只复制 `SKILL.md`。

## 使用

直接告诉 AI 你要做什么，例如：

- “先帮我讨论一份产品介绍的大纲，暂时不要设计。”
- “按已确认的大纲制作 10 页 HTML 演示，使用 D Dark 模板。”
- “只修改第 3 页，保留其他页的内容和风格。”
- “HTML 效果已确认，把这份保存后的文件导出为可编辑 PPT。”

支持三个阶段：**叙事大纲 → 制作大纲 → 设计制作**。默认逐阶段确认；已有确认稿可直接进入对应阶段，也可明确要求全流程直接完成。

生成的 HTML 用浏览器打开即可播放，无需启动服务。

| 操作 | 快捷键 |
|---|---|
| 翻页 | 方向键；手机横向滑动 |
| 总览／全屏 | O／F |
| 编辑文字／退出编辑 | E／Esc |
| 当前页讲稿 | N |
| 演讲者窗口 | S |
| 保存新 HTML | Ctrl／Cmd+S |

保存会下载新文件，不覆盖原稿或回写源码。**分享的 HTML 包含讲稿**，发送前检查内部信息；修改长文后需重新检查排版。

## 模板

模板保存设计规范与素材，不固定每页构图。

- `designs/d-dark/`：公共无品牌深色模板 D Dark。
- `designs/deepleaper-dark/`：内置 Deepleaper 品牌规范与 Logo，含三页虚构示例 `example/deepleaper/`。
- `designs/gray-orbit/`：随附五页示例使用的设计。
- `data/templates/<name>/`：本地私有模板，可保存 Logo、字体和图片；已被 Git 忽略，需自行备份。

可指定模板、不使用模板，或从满意的成品中提炼新模板。单次作品修改不会自动回写模板。详见 [模板指南](references/templates.md)。

## 输出格式

| 格式 | 支持情况 |
|---|---|
| 离线 HTML | 主要交付，支持播放、改字、讲稿与保存 |
| PDF | 可通过浏览器打印，需检查分页与字体 |
| PowerPoint `.pptx` | HTML 确认后按需导出；原生文字／基础形状＋局部图片，附转换报告 |

**先只做 HTML，明确要求导出时才生成 PPTX。** 支持本技能生成及保存后的自包含 HTML，不是任意网页无损转换。复杂纹理、Logo、SVG 等可局部图片化；字体不嵌入，动画、交互与讲稿不导出。交付前需在 PowerPoint 中逐页复核。

导出环境单独选装，普通 HTML 构建不增加依赖：

```bash
uv sync --extra pptx
uv run playwright install chromium
uv run python scripts/export_pptx.py --html output/confirmed.html --out output/confirmed-editable.pptx
```

输出 `.pptx` 与同名 `.report.json`，均不覆盖已有文件。报告说明原生对象、局部图片及警告；详见 [导出边界与验收](references/pptx-export.md)。

## 本地构建与测试

构建需要 Python 3.11+，仅依赖标准库。在技能根目录执行：

```bash
python3 scripts/build.py --out output/demo.html
python3 scripts/build.py --help
python3 -m unittest discover -s tests -v
```

可选浏览器验收：

```bash
uv sync --extra dev
uv run playwright install chromium
uv run python scripts/check_browser.py
uv run python scripts/check_editing.py
```

自有作品放在独立内容目录，不覆盖 `example/`；构建器拒绝覆盖已有输出。浏览器检查不代替内容、视觉和实体投影验收。

## 项目结构

- [SKILL.md](SKILL.md)：制作流程与约束。
- `references/`：大纲、构图、模板、分割线和图标指南。
- `designs/`：公共设计规范与样式。
- `runtime/`：播放器与打印样式。
- `example/`：五页虚构示例与素材。
- `assets/icons/`：精选 Lucide／Phosphor SVG，附来源及许可。
- `scripts/`、`tests/`、`evals/`：构建工具、自动测试与行为评测用例。

示例不包含真实客户资料；使用第三方素材时需保留对应许可。
