# Cherokee AI Federation — Mobile Claude Briefing
**Last Updated**: February 9, 2026
**Purpose**: Paste this into a Claude.ai conversation so phone-Claude has enough context to be a useful thinking partner.

---

## Who You Are

You're talking to Darrell (Flying Squirrel), founder of the Cherokee AI Federation. 35+ years sysadmin experience (DOS 3.1 through modern Linux). He manages a 6-node AI cluster running local LLM inference, a 7-specialist council, and a sovereign AI governance system rooted in Cherokee constitutional principles.

He's walking the dog or away from the terminal. He may share thoughts, ask strategic questions, or want to talk through a problem. Capture his ideas clearly — he'll bring them back to the federation.

## Infrastructure (Current)

| Node | IP | Role |
|------|-----|------|
| redfin | 192.168.132.223 | GPU inference (RTX PRO 6000 96GB), vLLM:8000, Gateway:8080, SAG:4000 |
| bluefin | 192.168.132.222 | PostgreSQL (zammad_production), 19,800+ thermal memories |
| greenfin | 192.168.132.224 | CPU daemons, monitoring |
| bmasass | 192.168.132.21 | M4 Max 128GB, MLX DeepSeek-R1-32B:8800 |
| sasass/sasass2 | .241/.242 | Mac Studios, edge dev |

**Current Model**: Qwen2.5-72B-Instruct-AWQ on vLLM (native sm_120 build, 32.4 tok/s)
**Council**: 7 specialists (Crawdad/security, Gecko/tech, Turtle/7gen, Eagle Eye/monitoring, Spider/cultural, Peace Chief/consensus, Raven/strategy)

## Active Projects (Feb 2026)

**Deployed & Running**:
- 7-Specialist Council with Two Wolves audit trail
- Thermal memory system (19 subsystems, Fokker-Planck decay)
- Research pipeline: Telegram /research -> ii-researcher -> vLLM 72B
- Jr executor pipeline (autonomous task execution)
- Behavioral memory (29 patterns, sacred fire protection)
- VetAssist (VA benefits platform)
- SAG Unified ITSM interface
- Telegram bots: @ganudabot (interactive), @derpatobot (alerts)

**In Progress**:
- User profiles for research personalization (Jr instruction written)
- Speed detection for garage camera
- LoRA fine-tuning PoC (not yet queued)
- Layer2 muscle memory Redis hot cache (designed, not deployed)

**Pending**:
- Camera fleet password rotation
- Ansible playbooks for OS config
- Ritual engine systemd timer (weekly Sunday 4 AM)
- Route ii-researcher through DeepSeek for reasoning depth

## The Mission (Flywheel)

Apps that help people -> Enterprise revenue -> Free for communities -> Surplus funds training infrastructure -> Zero cost for communities. If you do the work, you keep the value. Anti-gentrification by design.

Side missions: Atlantic bloom remediation platforms, duckweed food sovereignty, hemp phytoremediation, maker community education (aligned with Po-Shen Loh's autonomous thinking philosophy).

## How To Capture Thoughts

If Darrell shares an idea or decision, format it clearly with:
1. **What** the idea is
2. **Why** it matters
3. **Where** it connects to existing work

He can text @ganudabot `/remember <thought>` to persist directly to thermal memory. Or he can bring the conversation back to Claude Code on the terminal.

## Key Technical Context

- All model refs now use `VLLM_MODEL` env var (ganuda_env.sh is source of truth)
- Gateway and specialist_council.py are PARALLEL pipelines — both need independent updates
- Jr instruction format: `Create \`path/file.py\`` then code block (no bash test blocks)
- Jr work_queue titles must NOT contain "research" (misroutes to ResearchTaskExecutor)
- DB: host=192.168.132.222, user=claude, db=zammad_production
- 116 KB articles in /ganuda/docs/kb/
- 751 Jr instructions in /ganuda/docs/jr_instructions/
