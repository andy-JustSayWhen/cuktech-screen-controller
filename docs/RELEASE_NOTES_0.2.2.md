# CUKTECH Screen Controller 0.2.2

## 中文

- 在 README、零基础教程与软件新手引导中加入明确的安装前准备说明；
- 区分本地图片、Claude/Codex 额度和原厂屏首次加载器三种联网需求；
- 明确日常画面通过 Wi-Fi/LAN 传输，不需要 USB 或底座触点；
- 补充米家在线状态、稳定供电、访客网络/AP 隔离、TCP 8765、VPN/防火墙、
  DHCP 地址保留和 Mac 睡眠行为；
- 软件现在同时检查 `en0` 与 `en1`，Mac 使用 Wi-Fi 或有线局域网都能显示正确地址；
- 新增中英文独立安装前检查清单。

安装包继续支持 Apple Silicon Mac 与 macOS 14 或更高版本，包括 2024、2025、
2026 款 Mac。日常图片与额度刷新仍然只写 AP01 的 `/tmp` RAM 槽位。

## English

- Adds explicit preparation guidance to the README, beginner guide, and in-app onboarding;
- distinguishes LAN-only artwork, internet-backed quotas, and first-loader connectivity;
- clarifies that normal screen content uses Wi-Fi/LAN rather than USB or base contacts;
- documents Mi Home online state, stable power, guest/AP isolation, TCP 8765,
  VPN/firewall behavior, DHCP reservation, and Mac sleep behavior;
- checks both `en0` and `en1` so Wi-Fi and Ethernet Macs expose the correct LAN URL;
- adds standalone Chinese and English preparation checklists.

