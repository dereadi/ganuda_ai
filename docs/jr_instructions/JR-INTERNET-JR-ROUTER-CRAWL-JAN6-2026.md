# Jr Task: Internet Jr - Crawl and Document TP-Link Switch

**Date**: January 6, 2026
**Priority**: MEDIUM
**Target**: TP-Link TL-SG1428PE Documentation
**Tool**: Web4UI Crawler on redfin
**TPM**: Flying Squirrel (dereadi)

## Background

We need to create comprehensive documentation of the TP-Link TL-SG1428PE switch capabilities for the Cherokee AI Federation. This uses the Web4UI crawler system at `/ganuda/pathfinder/pathfinder_web4ui_crawler.js` on redfin.

## Switch Documentation Already Gathered

### From Manual Crawl (https://www.manualslib.com/manual/3206987/Tp-Link-Tl-Sg1428pe.html)

#### VLAN Support
| Mode | Description |
|------|-------------|
| MTU VLAN | Uplink port management |
| Port-Based VLAN | Isolated broadcast domains |
| 802.1Q VLAN | Standards-based tagging with PVID |

**Note**: Only one mode active at a time - enabling another disables previous config.

#### QoS (Quality of Service)
- Port-Based: 4 priority queues (1=lowest, 4=highest)
- 802.1P-Based: Priority from frame tags
- DSCP/802.1P Hybrid mode
- Bandwidth control (ingress/egress)
- Storm control (broadcast/multicast/unknown unicast)

#### PoE Features
- IEEE-compliant powered devices
- System power limit: 150W default
- Per-port PoE enable/disable
- Auto-recovery with ping-based monitoring

#### Port Configuration
- Individual port status control
- Speed/duplex with auto-negotiation
- Flow control

#### Monitoring & Diagnostics
- Port Statistics (packet counts)
- Port Mirroring (traffic duplication)
- Cable Testing (fault detection)
- Loop Prevention (auto-blocking)

#### Advanced Switching
- IGMP Snooping (multicast optimization)
- LAG (Link Aggregation) for bandwidth
- Web management interface

---

## Task 1: Run Web4UI Crawler for Extended Documentation

SSH to redfin and run:

```bash
cd /ganuda/pathfinder
node pathfinder_web4ui_crawler.js
```

Or create a custom crawl for switch documentation:

```javascript
// Custom research plan for switch documentation
const crawler = new Web4UICrawlerSystem();
const plan = await crawler.createResearchPlan(
  'TP-Link TL-SG1428PE VLAN QoS PoE configuration best practices',
  ['eagle_eye', 'spider']  // Technical + knowledge specialists
);
await crawler.executeCrawlPlan(plan.id);
const report = crawler.generateCrawlReport(plan.id);
```

## Task 2: Document Additional Resources

### Official TP-Link Resources
- Manual: https://www.manualslib.com/manual/3206987/Tp-Link-Tl-Sg1428pe.html
- Downloads: https://www.tp-link.com/us/support/download/tl-sg1428pe/
- VLAN Guide: https://www.tp-link.com/us/support/faq/788/

### Key Configuration Pages
- Page 49: VLAN Configuration
- Page 55: 802.1Q VLAN Details
- Page 30: PoE Management

## Task 3: Create KB Article

After crawling, create a KB article at:
`/Users/Shared/ganuda/docs/kb/TPLINK_TL-SG1428PE_COMPLETE_GUIDE.md`

Include:
1. All features and capabilities
2. Cherokee AI Federation specific configuration
3. VLAN setup for goldfin/silverfin
4. Security hardening checklist
5. Monitoring setup recommendations

## Task 4: Update Thermal Memory

Store the documentation in thermal memory:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash,
    original_content,
    temperature_score,
    tags,
    source_triad,
    source_node,
    memory_type
) VALUES (
    md5('tplink_switch_documentation_jan6_2026'),
    '... full documentation ...',
    90.0,
    ARRAY['switch', 'tp-link', 'documentation', 'vlan', 'network'],
    'internet_jr',
    'redfin',
    'reference'
);
```

---

## Web4UI Crawler Location

```
redfin:/ganuda/pathfinder/
├── pathfinder_web4ui_crawler.js    # Main crawler
├── web4ui_research_data.json       # Saved research data
├── pathfinder_web_research_crawler.js
└── fixed_quantum_crawler.py
```

## Creating an Internet Jr

If we want a dedicated Internet Jr for web research, we should:

1. Create Jr entry in jr_status table
2. Deploy as a service on redfin or greenfin
3. Expose API for research requests
4. Integrate with thermal memory for knowledge storage

```sql
INSERT INTO jr_status (
    jr_name, jr_mountain, jr_gender, jr_model, jr_role,
    endpoint, is_online, specialties
) VALUES (
    'Internet Jr.',
    'Web Research',
    'Neutral',
    'Web4UI Crawler',
    'Web Research and Documentation',
    'http://192.168.132.223:8020',
    true,
    ARRAY['web crawling', 'documentation', 'research', 'knowledge gathering']
);
```

---

## For Seven Generations
