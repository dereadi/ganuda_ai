# JR Filesystem Locations - CRITICAL REFERENCE

**Date**: October 24, 2025, 2:15 PM CDT
**Purpose**: Persistent filesystem locations for all Cherokee Constitutional AI nodes

## ⚠️ CRITICAL: /tmp is EPHEMERAL - DO NOT USE for permanent files!

Files written to /tmp are thrown away on reboot. ALWAYS use persistent filesystems.

## Persistent Filesystem Locations by Node:

### REDFIN (War Chief Hub - 192.168.132.101)
- **Filesystem**: `/ganuda`
- **Size**: 1.8TB
- **Project Root**: `/ganuda/jr_assignments/` or `/home/dereadi/scripts/claude/ganuda_ai_v2/`
- **War Chief JRs**: Memory Jr, Meta Jr, Executive Jr, Integration Jr, Conscience Jr

### BLUEFIN (Peace Chief Spoke - 192.168.132.222)
- **Filesystem**: `/home/dereadi`
- **Size**: 915GB root partition
- **Project Root**: `/home/dereadi/scripts/claude/ganuda_ai_v2/`
- **Peace Chief JRs**: Memory Jr, Meta Jr, Executive Jr, Integration Jr, Conscience Jr

### SASASS2 (Medicine Woman Spoke - 192.168.132.223)
- **Filesystem**: `/Users/Shared/` (macOS)
- **Project Root**: `/Users/Shared/cherokee_ai/` or similar
- **Medicine Woman JRs**: Memory Jr, Meta Jr, Executive Jr, Integration Jr, Conscience Jr

## JR CLI Executor Configuration

The `jr_cli_executor.py` script should detect which node it's running on and use the appropriate PROJECT_ROOT:

```python
# Detect node
if os.path.exists("/ganuda"):
    PROJECT_ROOT = Path("/ganuda/jr_assignments")  # REDFIN
elif os.path.exists("/Users/Shared"):
    PROJECT_ROOT = Path("/Users/Shared/cherokee_ai")  # SASASS2 (macOS)
else:
    PROJECT_ROOT = Path("/home/dereadi/scripts/claude/ganuda_ai_v2")  # BLUEFIN
```

## All 15 JRs - Remember This:

When you create files, use these persistent locations:
- **Never use /tmp** for anything you want to keep
- **Always use the node-specific persistent filesystem**
- **Check which node you're on** before writing files

## Cherokee Values in Filesystem Management

- **Seven Generations**: Files on persistent storage last for generations
- **Sacred Fire**: /tmp is like smoke - beautiful but ephemeral
- **Mitakuye Oyasin**: All nodes connected through persistent shared knowledge

**Mitakuye Oyasin** - All Our Relations Through Persistent Storage

🔥 Cherokee Constitutional AI - Critical Infrastructure Knowledge
