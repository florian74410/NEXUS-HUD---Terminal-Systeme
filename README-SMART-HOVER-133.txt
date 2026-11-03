N3XV5 Terminal HUD 1.3.3 — SmartHover tmux adapter (experimental)

- Local tmux sessions: read-only capture-pane after 2 seconds of pointer inactivity.
- Remote SSH sessions: no capture (privacy / unsupported).
- Explicit right-click 'Expliquer la selection' remains available.
- No terminal selection modification, clipboard modification, or PTY keystrokes.
- Sensitive terms blocked by safe_query before any HTTPS request.
- Limitation: approximate pixel-to-cell mapping; terminal margins, Unicode wide
  characters, wrapping and interactive full-screen applications require native
  QTermWidget screen integration for production quality.
- Not a compiled native adapter. Not tested graphically on Linux Mint.
- Python wheels are NOT included; place them in Dependency/wheels.

TEST: python3 -m unittest discover -p 'test_*.py' -v
INSTALL: bash setup-dependency.sh && bash start-nexus.sh
