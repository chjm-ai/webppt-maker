# 排障与验收

## 浏览器版本必须与 Playwright 匹配

首次安装后出现 `Executable doesn't exist`，表示当前 Playwright 对应的 Chromium 尚未安装，不是页面失败。执行 README 的 `uv run playwright install chromium`；不要通过关闭证书校验或假报通过来跳过。

本仓库将 Playwright 固定为已实际验证的 1.57.0，并提交 uv.lock。升级版本后重新安装对应 Chromium，再重新跑示例验收；机器上有其他版本的浏览器不代表当前版本能直接使用。

## 输出存在

构建器故意拒绝覆盖已有 HTML。使用新文件名；不删除历史版本来掩盖失败。页面图形和布局改变后，旧验收回执不再代表新输出。

## 独立仓库边界

此目录是 AI_Skills 下的独立 Git 仓库，不把它误加成父仓库的普通目录或无意创建 gitlink。只在本仓库提交与推送；父仓库中其他 Skill 的未提交改动不属于本项目。

运行输出、截图、缓存与真实业务资料不入库。来源与许可证必须保留，尤其是内嵌到单文件 HTML 的图标许可。
