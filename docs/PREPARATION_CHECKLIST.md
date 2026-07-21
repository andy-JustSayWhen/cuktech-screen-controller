# CUKTECH Screen Controller preparation and connectivity checklist

Before installing, separate the three workflows: normal artwork updates,
internet-backed quota refreshes, and the one-time loader installation for a
stock AP01.

## 1. Identify the display state

| Display state | Correct action |
| --- | --- |
| It has shown computer-supplied artwork, GIFs, or a quota dashboard | The real-time loader exists. Install the app and **do not OTA again** |
| Completely stock; it has never shown computer-supplied content | Verify the exact model and firmware, then use the coding-agent loader workflow once |
| Unknown | Run read-only diagnostics and look for `GET /screen.gif 200`; do not guess or flash it |

## 2. Hardware

- A CUKTECH 10 charging station and its detachable AP01 display;
- stable AP01 power, especially during a first loader installation;
- model `njcuk.enstor.ap01` on firmware `1.0.2_0031` for the published loader;
- an Apple Silicon Mac running macOS 14 or later. The current package is
  `arm64`; Intel Macs are not supported;
- no USB data cable is required. Normal content delivery uses Wi-Fi/LAN rather
  than USB or the charging-base contacts.

## 3. LAN preparation

Pair the AP01/charging station in Mi Home and make sure it is online. Put the
Mac and AP01 on the same reachable LAN, not a guest network. Disable AP/client
isolation, allow incoming connections when macOS asks, and allow TCP port
`8765` through VPN/firewall software. Ethernet on the Mac is fine if it can
reach the AP01 across the same LAN/VLAN.

Reserve the Mac's LAN address with DHCP. The AP01 must be able to request:

```text
http://<MAC_LAN_IP>:8765/screen.gif
```

The end-to-end success signal is a logged request such as:

```text
AP01_IP "GET /screen.gif HTTP/1.0" 200
```

## 4. Internet requirements

| Workflow | Mac internet | AP01 internet | Local LAN |
| --- | --- | --- | --- |
| Local artwork on an already-patched display | Only for initial download | No | Required |
| Claude/Codex live quotas | Required for quota refreshes | No, but it must reach the Mac | Required |
| First loader installation on a stock display | Required | Required and online in Mi Home | Required |

If the WAN fails but the LAN remains available, local artwork can still work.
Quota mode retains its last successful values until internet access returns.

## 5. Accounts

For quota mode, install and sign in to the official Claude Desktop and
Codex/ChatGPT app, or a signed-in Codex CLI. Approve Claude Safe Storage access
when macOS asks. Never paste cookies, passwords, or Keychain data into a chat.

For a first loader installation, have the target AP01 owner's Mi Home account
available and use the same device region. An account without an FDS-capable
gateway may require the app's OTA ticket-handoff workflow. Keep Xiaomi
credentials, DIDs, signed URLs, firmware binaries, and generated artifacts out
of GitHub.

## 6. Continuous operation

The installer creates a per-user login service. Keep the Mac awake and the user
logged in for live updates. The AP01 retains the last successful screen while
the Mac sleeps or is offline, but it cannot refresh. Its normal poll interval
is about five minutes, so a pushed image may not appear immediately.

## 7. Final checklist

- [ ] Apple Silicon Mac with macOS 14+
- [ ] AP01 on stable power and online in Mi Home
- [ ] Same non-guest, non-isolated LAN
- [ ] Local TCP 8765 allowed by macOS/VPN/firewall
- [ ] Mac DHCP reservation configured if possible
- [ ] Official Claude/Codex clients signed in for quota mode
- [ ] Stock loader work verified as `njcuk.enstor.ap01` / `1.0.2_0031`
- [ ] User understands daily updates use `/tmp` RAM and do not reinstall firmware

Continue with the [beginner guide](BEGINNER_GUIDE.md) after these checks pass.

