# NEXUS Smart Hover — V1.3 integration preview

Integrated `SmartHover` into `Terminal(QTermWidget)` in `nexus_workspace.py`.

Implemented:
- 2-second hover timer, click to open 150x50 NeonGlass bubble.
- Local filter for IP, port numbers, password/passphrase/token keywords, explicit IDs, known local username, username@host patterns.
- HTTPS-only JSON explanation endpoint in a QThread, timeout 6 seconds.
- Sends only a short generic selected keyword; never the complete terminal line.
- Context-menu fallback on selected text.

Configuration: `NEXUS_CONTEXT_ENDPOINT=https://your-trusted-service.example/api/explain` must return JSON `{ "summary": "short explanation" }` for GET `?q=...&lang=fr`. No service is bundled, so without configuration the popup says the service is not configured.

**Not yet fully functional:** `pyside6_qtermwidget` has not been installed or tested in this build environment. Hover lookup currently requires an optional `getText(row, column, length)` binding; when absent, it is disabled safely. The active word is indicated by pointer cursor, not underlined: a robust underline overlay still requires a tested terminal-cell coordinate API. Selection fallback depends on the binding exposing `selectedText()`. IDs/pseudonyms not known to the identity registry cannot be reliably classified. Do not treat the filter as a guarantee that every secret is recognized.

Tests: `test_nexus_smart_context.py` (6 tests passing), Python compileall passing. No graphical runtime test performed.
