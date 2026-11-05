# HTML PPT Design Pack

制作离线 HTML 幻灯片的独立 Skill。内容、可替换设计规范与播放器分层；支持球形封面、关系图、截图主导页、核对流程和结论页。

## 使用

本目录位于 AI_Skills 下，可通过 SKILL.md 加载；旧 html-ppt 技能保持独立。

```bash
python3 scripts/build.py --out output/demo.html
```

打开生成的 HTML 即可离线播放；方向键翻页，O 总览，F 全屏。示例为虚构的“HTML 幻灯片制作流程”，没有真实公司／客户材料。

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
```

浏览器验收默认检查 output/demo.html；可传 `--html /绝对路径/另一份五页.html --scratch /截图目录`。截图默认进入系统临时目录。生成输出不提交 Git。

## 目录

- `SKILL.md`：制作流程与输出契约。
- `references/composition.md`：内容关系与整组构图检查。
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
- 图标为 Lucide 本地 SVG；真实下载 URL、SHA-256 与完整许可随 `example/assets/icons/` 保存。编译 HTML 包含许可，无 CDN 依赖。
- 截图页为自绘虚构工作台，不表示实际软件功能。
- 不含真实研究正文、客户截图、公司 Logo、个人绝对路径或旧验收回执。
- Chromium 验收不等于所有浏览器、实体投影或视频播放均已验证。手机保持 16:9，不是长文阅读版。
