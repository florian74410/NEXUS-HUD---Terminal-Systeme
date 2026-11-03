# NEXUS Terminal 1.3 — Neon Context UI prototype

The source contains a real PySide6 `NeonContextBubble` widget, 150 × 50 pixels, translucent mirror gradient, beveled cyan/purple neon border, subtle glow, italic explanation.

Run `python3 preview_neon_context.py` with PySide6 installed to see it. The widget is instantiated for each QTermWidget terminal.

**Not implemented yet:** reliable 2-second per-word hover detection in QTermWidget, contextual HTTPS search, and sensitive-token suppression. These require further integration/testing and must not be advertised as complete.

Glass adjustment: semi-transparent background (~56–67% opacity), brighter top mirror reflection, opaque text and crisp neon outline.
