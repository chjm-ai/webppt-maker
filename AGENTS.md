# AGENTS.md

独立 HTML 幻灯片 Skill；入口 SKILL.md，安装与命令见 README.md。

## 结构

- runtime/：通用播放层，不写品牌布局。
- designs/<name>/：design.md 配置与独立布局 CSS。
- example/：四页虚构示例；页面用 data-template-only 标记支持多套模板。
- scripts/：标准库构建器、模板校验（check_templates.py）、图标检索、浏览器验收。
- tests/：构建与异常用例。

## 命令

- Python 3.11+；构建：python3 scripts/build.py --out output/demo.html。
- 测试：python3 -m unittest discover -s tests -v。
- 浏览器验收：uv sync --extra dev；uv run playwright install chromium；uv run python scripts/check_browser.py。

## 本项目约定

- 页面 ID、data-layout 与 deck.json 保持一致。
- design.md 自然语言由制作者执行；构建器只读取 JSON，不声称自动审美评分。
- 页面图片只能引用内容目录内的文件，离线输出全部内嵌。
- 图标按 references/icons.md 选库；assets/icons/ 附带 Lucide／Phosphor 精选 SVG，scripts/icons.py 离线检索与复制。逐件来源与哈希随库保存；内嵌须保留 metadata 中的完整许可，不混库。旧示例仍用 example/assets/icons/。
- 五页至少四种主体构图；无图页先识别内容关系再绘图。
- 真实资料、客户截图、个人路径、生成输出不提交到本仓库；示例明确标注为虚构。
- 修改在工作分支／worktree 完成，验证后合并 main；不自动公开发布演示。
