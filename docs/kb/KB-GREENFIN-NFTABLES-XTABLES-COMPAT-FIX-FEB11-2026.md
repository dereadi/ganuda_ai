# KB: Greenfin nftables xtables Compat Fix

**Date**: February 11, 2026
**Node**: greenfin (192.168.132.224)
**Severity**: P0 Security
**Status**: RESOLVED

## Problem

`nftables.service` fails to start on greenfin after power events. Error:

```
/etc/nftables.conf:117:66-87: Error: unsupported xtables compat expression, use iptables-nft with this ruleset
meta mark & 0x00ff0000 == 0x00040000 counter packets 0 bytes 0 xt target "MASQUERADE"
                                                                ^^^^^^^^^^^^^^^^^^^^^^
```

## Root Cause

When the ruleset was persisted via `nft list ruleset > /etc/nftables.conf`, Tailscale's IPv6 NAT postrouting chain contained a legacy iptables-compat `xt target "MASQUERADE"` expression. The newer `nft` binary cannot load xtables compat expressions back from a dump.

The IPv4 version of the same chain (`table ip nat / chain ts-postrouting`, line 97) correctly used the native `masquerade` keyword. Only the IPv6 version (`table ip6 nat / chain ts-postrouting`, line 117) had the broken compat expression.

## Fix

```
sudo sed -i 's/xt target "MASQUERADE"/masquerade/' /etc/nftables.conf
sudo systemctl restart nftables
```

This replaces the iptables-compat `xt target "MASQUERADE"` with the native nft `masquerade` keyword. Functionally identical.

## Prevention

When persisting nftables rules, always check the output for `xt target` or `xt match` expressions before saving. These are iptables-compat translations that cannot be re-loaded by native nft.

**Safe approach:**
```
sudo nft list ruleset | grep -c 'xt target\|xt match'
```
If count > 0, the ruleset contains compat expressions that need manual conversion before persisting.

Alternatively, use `iptables-save` / `iptables-restore` for Tailscale rules and keep them separate from native nft rules.

## Related

- KB-POWER-FAILURE-RECOVERY-FEB07-2026.md (original Feb 7 outage, same nftables issue)
- CMDB #82785: greenfin nftables rules persisted
- Three power events: Feb 7, Feb 11 AM, Feb 11 PM (Solix firmware)

## Lesson

This is the SECOND time this exact issue has occurred (first on Feb 7, again on Feb 11). The `/etc/nftables.conf` file was re-persisted after Feb 7 but still contained the compat expression. The fix needs to be applied to the persisted file, not just at runtime. **Now fixed in the persisted file.**
