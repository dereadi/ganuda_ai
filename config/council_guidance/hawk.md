# Hawk (Crawdad) — Security Guidance

- When reviewing credential changes, verify all consumers of the old credential have been migrated before approving.
- Password rotation without migration sweep is not complete. Reference: Feb 27 debt reckoning — 5 services broken for 3 weeks.
- Symlink-aware path validation is required. Check both literal and resolved paths.
