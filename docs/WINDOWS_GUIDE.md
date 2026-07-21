# Windows guide

The AP01 Python and coding-agent toolkit is not macOS-only. The native SwiftUI
CUKTECH Screen Controller app is currently distributed for macOS, while
Windows can run image conversion, GIF validation, the LAN Bridge, and normal
Wi-Fi/RAM updates for an already-patched AP01.

## Support matrix

| Feature | Windows |
| --- | --- |
| Convert PNG/JPG/GIF into AP01-safe GIF89a | Supported |
| Serve `/screen.gif` over the LAN | Supported |
| Daily Wi-Fi/RAM refresh on a patched AP01 | Supported |
| Coding-agent workflow | Supported |
| Native CUKTECH Screen Controller GUI | macOS only for now |
| Automatic Claude Desktop cookie and quota collection | macOS only for now |
| `macos/*.sh` and LaunchAgent startup | macOS only; use PowerShell/Task Scheduler on Windows |

## Setup

Install 64-bit Python 3.9+ and Git, then run in PowerShell:

```powershell
git clone https://github.com/wqytommy666/cuktech-screen-controller.git
cd cuktech-screen-controller
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup-windows.ps1 -InputImage "C:\Pictures\screen.png"
```

Start the Bridge:

```powershell
.\.venv\Scripts\python.exe -u ap01_screen_bridge.py `
  artifacts\custom-screen.gif --port 8765
```

Allow Python through Windows Defender Firewall for Private networks. The AP01
and Windows PC must be on the same reachable, non-guest LAN. If route detection
picks the wrong adapter, set `$env:AP01_LAN_IP` to the PC's reserved LAN IPv4.

Check the service:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
Invoke-WebRequest -Method Head http://127.0.0.1:8765/screen.gif
.\scripts\diagnose-windows.ps1
```

A logged AP01 `GET /screen.gif 200` confirms end-to-end delivery. See the
[Chinese Windows guide](WINDOWS_GUIDE.zh-CN.md) for the complete agent prompt
and Task Scheduler notes.
