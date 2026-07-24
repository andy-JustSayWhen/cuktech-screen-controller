
## 项目权威文档指引

开始任何安装、配置、设备操作或代码修改前，依次读取并遵守以下根目录文件：

1. `Goal.md`：只记录当前目标、范围、执行顺序、验收标准与安全停止条件。目标发生变化时先更新此文件。
2. `Depends.md`：只记录实现目标所需的软件、硬件、环境、网络、账号登录、工具和用户输入依赖，以及当前满足状态。
3. `.env`：只保存密码、长期令牌、账号标识、凭据文件路径等敏感信息。此文件必须加入 `.gitignore`、权限保持为仅当前用户可读写，禁止提交、打印或复制到普通文档和日志。

`Goal.md` 与 `Depends.md` 是可提交的项目依据；`.env` 只存在于当前电脑。不得在 `Goal.md` 或 `Depends.md` 中写入任何敏感值。若三者与聊天中的临时描述冲突，先请用户确认并更新对应权威文件，再继续执行。

## 固件操作安全指南

为防止 AP01 设备变砖，
进行任何固件制作、修改、上传、下载校验、安装、回滚或恢复前，必须先读取并遵守
`agent-docs/firmware-safety.md`。该文档中的确认门和停止条件不可跳过。

对 AP01 实时加载器进行操作时，再读取
`skills/cuktech-ap01-screen-kit/references/realtime-firmware.md`。

## 硬性检查项

- Never guess firmware offsets or reuse the patch on another build.
- Never OTA an already real-time-patched image through `ap01_custom_ota.py`.
- Never run OTA merely to update artwork or quota values.
- Never commit cookies, Xiaomi credentials, device IDs, signed OTA URLs,
  firmware binaries, or generated `artifacts/`.
- Require the user's explicit confirmation immediately before a one-time
  firmware installation.
- A successful handoff includes `/health`, a valid GIF89a, and a logged AP01
  `GET /screen.gif 200` request.
