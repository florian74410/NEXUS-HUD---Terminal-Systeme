N3XV5 TERMINAL HUD V1.3.8 — LAN PAIRING DEVELOPMENT

SSH ▾ → Appareils du réseau / Appairage :
- UDP LAN discovery when enabled in Settings; TCP pairing on port 43872 while pairing dialog open.
- Pairing request with Ed25519 public key and random nonce; both PCs show a matching comparison code.
- Explicit approval on BOTH PCs before updating ~/.ssh/authorized_keys.
- No private keys transferred. No SSH daemon installed or enabled automatically.
- Pairing dialog must be open on both PCs. Host keys must still be verified at first SSH connection.
- Firewall must allow UDP 43871 and TCP 43872 on trusted LAN only.
- This is an unauthenticated public-key exchange protected by an out-of-band code comparison;
  never approve if codes differ. LAN discovery announcements are untrusted.
- No actual two-PC SSH connection tested. Validate before release.
