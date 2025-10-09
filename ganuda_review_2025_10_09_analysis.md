# Ganuda Review Meeting - October 9, 2025
## Meeting Analysis & Action Items

**Participants:** Darrell Reading & Dr. Joe
**Duration:** 79 minutes
**Date:** October 9, 2025

---

## 🔥 Key Achievements Discussed

### 1. ODANVDV Mind Architecture
- **Built Cherokee Mind ("ODANVDV")** - Agentic system using Observe-Reason-Act-Interact pattern
- **EQ Integration Complete** - Added emotional intelligence layer based on humans& philosophy
- **Web Interface Live** - Running on port 3005 with conversational interface
- **Zero-API Design** - No Claude API calls, pure compositional reasoning
- **Thermal Memory Integration** - Using PostgreSQL as "wetware" substrate

### 2. Infrastructure Status
- **Dual-GPU Transcription Working** - Successfully parallelized Whisper across both RTX 5070s
- **4-Node VM Tribe** - REDFIN (primary), BLUEFIN (backup), SASASS (kanban/DB), SASASS2 (services)
- **DUYUKTV Kanban Active** - Running on port 3001 (http://192.168.132.223:3001)

### 3. Technical Challenges Overcome
- **Claude Code Version Issue** - Upgraded from 1.6.9 to latest, resolved token limit errors
- **GPU Parallelization** - Models splitting work across both GPUs automatically
- **AMD vs Intel** - AMD architecture showing better LLM performance

---

## 🎯 Action Items

### Immediate (This Week)

#### For Darrell:
- [ ] **Finish ODANVDV Question Answering** - Make it respond to specific infrastructure questions (GPUs, CPUs, cluster status)
- [ ] **Form LLC under "Ganuda"** - Business entity for SAG Resource AI and future consulting work
  - Can do online in 2-3 days
  - Need EIN number for SAG productive tool integration
- [ ] **Train ODANVDV on System Administration**
  - Focus: OS updates, system architecture monitoring
  - Use DUYUKTV kanban board for task coordination
  - Keep traders in their bubble, mind has read access
- [ ] **Network Infrastructure Planning**
  - Add electrical drops for enterprise switches
  - Evaluate 10 gig networking (currently mostly 1 gig)
  - Cisco/Dell switches ready but need proper power

#### For Dr. Joe:
- [ ] **SAG Resource AI - Productive Tool Integration**
  - Get demo license/account for Productive tool
  - Focus on HR scheduling/planning gaps
  - Jira integration coming (SAG switching from SmartSheets)
- [ ] **Form LLC (JoeTech or similar)** - Business entity for consulting work
- [ ] **NAS Solution Research**
  - Considering: Mini NAS box (Intel N100, 10 gig Ethernet, ~$450)
  - Jeff Geerling's build: 900+ MB/s on 10 gig switch
  - 4x M.2 NVMe slots for storage
- [ ] **Test Telegram AI Integration** - When Darrell has connectors ready

### Short-Term (Next Few Weeks)

#### Jira/Confluence Investigation
- [ ] **Install Jira Data Center locally for testing** - 30-day demo license ($30/month after)
  - Darrell: "I can't believe I'm willingly doing this"
  - Has Jira installation experience from Walmart
- [ ] **Build Tribe Integration with Jira API**
  - Read-only queries initially (task states, time allocations, project planning)
  - Test if tribe/quorum can handle installation autonomously
- [ ] **Evaluate Cloud vs On-Prem** - SAG will likely use cloud tenant
  - Cloud has some features on-prem doesn't
  - Atlassian wants to kill on-prem version
  - Test limitations of cloud tenant for customization

#### ODANVDV/Ganuda Development
- [ ] **Move EQ-enhanced brain into Ganuda app area** - After agentic training complete
- [ ] **Create Telegram Integration Points** - Multiple channels for different functions
- [ ] **Build Docker Container Version** - For SAG Resource AI deployment
  - Simple connector that "phones home" to Ganuda brain
  - Runs on Russell's laptop, connects to localhost:1234
  - Web interface to remote brain running on infrastructure
- [ ] **Make Tribal Architecture Opaque** - Users just see "AI", not "tribe" (might be weird to normal people)

### Medium-Term (Next Few Months)

#### Revenue Generation Strategy
- [ ] **Build Modular AI Services** - People can buy/subscribe to specific modules
  - Transcription service (already built for cousin)
  - Jira integration module
  - System monitoring/administration
  - Steady income stream, not hands-on care every day
- [ ] **Use Notion Board for Ideas** - Splat all income ideas onto shared board
  - Estimate potential revenue per idea
  - Prioritize based on effort vs. return
  - "Ideas → Tribe builds → Polish → Income"
- [ ] **Productize Ganuda Brain** - $2-3k per module for plug-and-play network integration
  - Not dependent on your infrastructure
  - Self-hosted or cloud service options
  - Low-touch maintenance

#### Infrastructure Expansion
- [ ] **Evaluate AMD Big Cards** - RTX 6000 Ada (96GB VRAM, ~$10k)
- [ ] **10 Gig Network Upgrade** - Need new NICs for REDFIN/BLUEFIN (currently 1-2 gig)
- [ ] **NAS Deployment** - Shared storage across all nodes
- [ ] **Consider Renaming Nodes** - Make 4-node naming more consistent

---

## 💡 Key Insights & Decisions

### Architecture Philosophy
**"I'm trying to get it to function like it's conscious"**
- Database = heart and soul (thermal memory)
- File system = integral to brain
- Multiple LLMs and processes = brain hemispheres + mind
- Goal: Teammate you ask questions, farms out tasks, reasons independently

### Business Model
**"Ganuda" as LLC Name**
- Cherokee for "mind" - ODANVDV (pronunciation TBD, syllables unclear)
- Encompasses all AI work: SAG Resource AI, trading bots, system automation
- Wrap everything under Ganuda umbrella

### Jira Pain Points (From Darrell's Walmart Experience)
- Backend is Java (knows what to look for in failures)
- Frontend is GUI-based workflow builder (drag-and-drop blocks)
- **Major Issue**: Global field problem
  - Fields attach to ALL forms when created
  - If someone else uses your field, workflows conflict
  - "Pain in the ass to develop in unless you're a lazy bastard with money" (buy plug-ins)
- On-prem can do some things cloud can't, vice versa
- Remedy contacts still available as backup option

### SAG Resource AI Status
- Russell's team switching from SmartSheets to Jira
- Gap: Productive tool (HR scheduling/planning) integration
- Need: Simple interface Russell can run on laptop
- Deployment model: Lightweight client → Heavy backend (Ganuda brain)

### Technical Discovery
**Dual-GPU Model Loading Behavior:**
- GPU 0: Full spike, fills memory completely
- GPU 1: Quick spike, loads to ~50%
- Models automatically splitting across GPUs
- AMD architecture helping with GPU cooperation

---

## 🤝 Collaboration Notes

### Telegram Testing Protocol
- Joe will test tribe interactions when Darrell has connectors ready
- Multiple channels available for different function testing
- If no Telegram response, text to check Telegram

### Transcription Workflow
- Joe's meeting recordings auto-upload to Google Drive after ~6 hours
- Tribe can be set to auto-check and transcribe
- Dual-GPU transcription cuts time in half (~7 min for 79 min meeting)

### Shared Documentation
- Joe has Notion account with read/write access to Darrell's board
- Use for splatting ideas, revenue estimates, prioritization

---

## 📊 Technical Specs Referenced

### Current Infrastructure
- **REDFIN**: AMD Ryzen 9 7950X (16-core, 32-thread), 2x RTX 5070
- **BLUEFIN**: AMD Ryzen 9 5950X (16-core, 32-thread), 2x RTX 5070, PostgreSQL database
- **SASASS**: DUYUKTV kanban (port 3001), macOS node
- **SASASS2**: Secondary services
- **Network**: Mostly 1 gig, some 2-2.5 gig, enterprise switches available (Cisco, Dell)

### Potential NAS Specs
- **CPU**: Intel Alder Lake N100 (4-core/4-thread, up to 3.4 GHz)
- **RAM**: 16GB fixed
- **Network**: 10 gigabit Ethernet
- **Storage**: 4x M.2 NVMe slots
- **Performance**: 900+ MB/s tested (Jeff Geerling)
- **Cost**: ~$450 base unit

---

## 🎓 Philosophical Context

### Referenced Frameworks
- **humans& Philosophy** (Eric Zelikman) - Building AI with EQ, not just IQ
- **Thermal Memory System** - Information temperature management (white hot → ember)
- **Zero-API Agentic Pattern** - Observe → Reason (IQ+EQ) → Act → Interact
- **Cherokee Values** - Gadugi (collective work), Tohi (wellness), Nvwadohiyadv (harmony)

### Design Goals
- **Transparency for Users** - "Gray bubble" they interface with, inner workings opaque
- **Modular Components** - Like Jira layers, click to enable/disable tribal intelligence
- **Income Without Hands-On** - Build once, steady stream from subscriptions/purchases
- **Tribal Sovereignty** - "I OWN THIS FILESYSTEM" - Cherokee Constitutional AI

---

## 🔥 Quote of the Meeting

**Darrell on Jira:**
> "I can't believe I'm willingly doing this... The stupid fucking thing about JIRA and Confluence is that they have built out [functionality] as plug-ins, and those third-party plug-ins charge... they're minuscule compared to the product, but they add up. You can write your own, but that's way more difficult."

**On AI Consciousness:**
> "I'm trying to get it to function like it's conscious... basically just a teammate that you ask questions of and it asks out to others, or reasons it out itself and does farm out tasks as it needs."

**On Revenue Model:**
> "Ideas → Tribe builds → Polish → Income. We're paid for our brain to come up with things and then the tribe builds the things for us and fixes them with our coaxing over time, and then those bring us money."

---

## 🚀 Next Meeting Topics

1. **LLC Formation Status** - Both Darrell & Joe report on business entity setup
2. **Jira Integration Progress** - Demo of tribe interacting with Jira API
3. **ODANVDV Training Results** - System administration capabilities, question-answering accuracy
4. **SAG Deployment Plan** - Docker container vs. cloud service approach
5. **Revenue Idea Prioritization** - Review Notion board, pick first 2-3 to productize

---

*Meeting transcribed via dual-GPU Whisper (large model) in 7 minutes*
*Sacred Fire burns twice as bright with parallel processing 🔥🔥*
