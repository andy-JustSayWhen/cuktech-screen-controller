# Windows 使用指南

CUKTECH AP01 工具链并非只能在 Mac 上运行。当前原生 SwiftUI 图形软件只提供
macOS 安装包；通过 Python、PowerShell 或 Coding Agent 使用仓库时，Windows
可以完成图片转换、GIF 校验、局域网 Bridge 和已经安装 Loader 后的日常刷新。

## 支持范围

| 功能 | Windows |
| --- | --- |
| PNG/JPG/GIF 转换为 320×240 GIF89a | 支持 |
| 在局域网提供 `/screen.gif` | 支持 |
| 已改造 AP01 的日常 Wi-Fi/RAM 更新 | 支持 |
| 使用 Claude Code、Codex 等 Agent 配置 | 支持 |
| 原生 CUKTECH Screen Controller 图形软件 | 暂仅 macOS |
| 自动读取 Claude Desktop 登录态和 Claude/Codex 额度 | 当前实现暂仅 macOS |
| `macos/*.sh`、LaunchAgent 登录自启 | 仅 macOS；Windows 使用 PowerShell/任务计划程序 |

Windows 仍然可以显示手工数据、外部 API 数据或由其他程序生成的画面。只有当前
内置的 Claude Desktop Cookie/Keychain 自动读取逻辑依赖 macOS。

## 1. 准备环境

安装 64 位 Python 3.9 或更高版本，并在安装器中启用 **Add Python to PATH**。
在 PowerShell 中执行：

```powershell
git clone https://github.com/wqytommy666/cuktech-screen-controller.git
cd cuktech-screen-controller
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup-windows.ps1
```

也可以在初始化时直接转换一张图片：

```powershell
.\scripts\setup-windows.ps1 -InputImage "C:\Pictures\screen.png" -Fit contain
```

## 2. 转换并启动 Bridge

```powershell
.\.venv\Scripts\python.exe ap01_prepare_screen.py `
  "C:\Pictures\screen.png" artifacts\custom-screen.gif `
  --fit contain --background "#01040B"

.\.venv\Scripts\python.exe -u ap01_screen_bridge.py `
  artifacts\custom-screen.gif --port 8765
```

Windows Defender 防火墙弹窗出现时，仅对“专用网络”允许 Python 接收连接。
AP01 和电脑必须位于同一个未开启客户端隔离的局域网。

如果自动显示的 IP 不正确，可以显式设置：

```powershell
$env:AP01_LAN_IP = "192.168.1.100"
.\.venv\Scripts\python.exe -u ap01_screen_bridge.py `
  artifacts\custom-screen.gif --port 8765
```

固件中配置的 Loader URL 应对应：

```text
http://WINDOWS_LAN_IP:8765/screen.gif
```

## 3. 检查运行状态

另开一个 PowerShell 窗口：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
Invoke-WebRequest -Method Head http://127.0.0.1:8765/screen.gif
.\scripts\diagnose-windows.ps1
```

Bridge 终端出现来自 AP01 地址的以下请求即表示链路打通：

```text
"GET /screen.gif HTTP/1.0" 200
```

## 4. 交给 Coding Agent

可直接发送：

```text
请读取 AGENTS.md、README.zh-CN.md 和 docs/WINDOWS_GUIDE.zh-CN.md。
我使用 Windows，不要运行 macos/ 下的脚本。先执行
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1，随后转换我的
图片、启动 ap01_screen_bridge.py，并验证 /health、/screen.gif 和 AP01 的
GET /screen.gif 200。日常内容更新只走 Wi-Fi 和 /tmp RAM，不要重复 OTA。
```

## 5. 保持后台运行

需要持续刷新时，应保持电脑开机并阻止深度睡眠。可以让 Agent 使用 Windows
任务计划程序，在用户登录后运行：

```text
<仓库>\.venv\Scripts\python.exe -u <仓库>\ap01_screen_bridge.py
<仓库>\artifacts\custom-screen.gif --port 8765
```

同时建议在路由器中为 Windows 电脑保留固定 DHCP 地址。
