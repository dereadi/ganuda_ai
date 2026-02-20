# Jr Instruction: Bluefin Hardware Probe — RTX 6000 Upgrade Feasibility

**Task ID:** BLUEFIN-HW-PROBE-001
**Priority:** P1
**Assigned:** Hardware/Infrastructure Jr
**Node:** bluefin (192.168.132.222)
**Date:** 2026-02-05

---

## Objective

Probe bluefin's hardware configuration to assess feasibility of upgrading from RTX 5070 to RTX 6000 (48GB). Document all relevant specs for procurement decision.

---

## Current Known State

| Node | Current GPU | Target GPU |
|------|-------------|------------|
| redfin | RTX 6000 | (reference) |
| bluefin | RTX 5070 | RTX 6000 |

---

## Investigation Tasks

### 1. Current GPU Status

```bash
# GPU model and VRAM
nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv

# Driver version
nvidia-smi --query-gpu=driver_version --format=csv

# PCIe link info
nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current --format=csv

# Full nvidia-smi dump
nvidia-smi -q
```

**Document:**
- Exact GPU model (RTX 5070 variant?)
- Current VRAM (expected 12-16GB)
- Current utilization patterns
- PCIe generation and width

### 2. Motherboard and PCIe Slots

```bash
# Motherboard info
sudo dmidecode -t baseboard

# All PCIe slots
sudo lspci -vvv | grep -A 20 "VGA\|3D\|Display"

# PCIe slot capabilities
sudo lspci -s $(lspci | grep -i nvidia | cut -d' ' -f1) -vvv | grep -i "lnkcap\|lnksta\|width\|speed"

# Check for additional PCIe x16 slots
sudo lspci | grep -i "pci bridge\|host bridge"
```

**Document:**
- Motherboard model
- Available PCIe x16 slots (RTX 6000 needs x16)
- Current slot generation (PCIe 4.0 or 5.0?)
- Physical slot availability (empty slots?)

### 3. Power Supply Assessment

```bash
# Check current power draw
nvidia-smi --query-gpu=power.draw,power.limit --format=csv

# System power info (if available)
sudo dmidecode -t 39

# Check PSU capacity from system logs
sudo dmesg | grep -i "power\|psu\|watt"
```

**Document:**
- Current GPU power draw
- RTX 6000 TDP: 300W
- RTX 5070 TDP: ~200W (estimated)
- Delta: +100W required
- PSU headroom assessment

### 4. Physical Dimensions

```bash
# Check chassis info
sudo dmidecode -t chassis

# GPU physical specs (from nvidia-smi extended)
nvidia-smi -q | grep -i "product\|serial\|board"
```

**Document:**
- RTX 6000 length: 267mm (10.5")
- RTX 6000 height: 2-slot
- Current GPU dimensions
- Chassis clearance

### 5. Cooling Assessment

```bash
# Current GPU temps
nvidia-smi --query-gpu=temperature.gpu,fan.speed --format=csv

# Run for 5 minutes under load, check temps
# (only if safe to do so)
watch -n 5 'nvidia-smi --query-gpu=temperature.gpu,fan.speed,power.draw --format=csv'
```

**Document:**
- Idle temps
- Thermal headroom
- Case airflow assessment

### 6. Memory and CPU Context

```bash
# System memory
free -h
cat /proc/meminfo | head -10

# CPU info
lscpu | head -20

# Check if system has IOMMU for GPU passthrough potential
dmesg | grep -i iommu
```

**Document:**
- RAM capacity (important for model loading)
- CPU model (PCIe lanes matter)
- IOMMU status

### 7. Current vLLM/Inference Usage (if any)

```bash
# Check for running inference services
systemctl list-units | grep -i "vllm\|ollama\|llm"

# Check GPU memory consumers
nvidia-smi pmon -s m -c 1

# Check what's using the GPU
fuser -v /dev/nvidia*
```

**Document:**
- Current GPU workloads on bluefin
- Memory usage patterns
- Services that would benefit from upgrade

### 8. Compare with Redfin (Reference)

```bash
# SSH to redfin and get RTX 6000 specs for comparison
ssh redfin "nvidia-smi -q" | head -50
```

**Document:**
- Redfin RTX 6000 configuration
- Driver version compatibility
- Any lessons from redfin setup

---

## Output Format

Create report at: `/ganuda/docs/reports/BLUEFIN-HARDWARE-ASSESSMENT-FEB05-2026.md`

### Required Sections

```markdown
# Bluefin Hardware Assessment — RTX 6000 Upgrade

## Executive Summary
[GO/NO-GO/CONDITIONAL recommendation]

## Current Configuration
- GPU: [model, VRAM, driver]
- Motherboard: [model, PCIe slots]
- PSU: [capacity, current draw, headroom]
- Cooling: [temps, airflow]

## RTX 6000 Requirements vs Bluefin Capability
| Requirement | RTX 6000 Needs | Bluefin Has | Status |
|-------------|----------------|-------------|--------|
| PCIe slot | x16 Gen4+ | [?] | [?] |
| Power | 300W + headroom | [?] | [?] |
| Length | 267mm | [?] | [?] |
| Cooling | Adequate airflow | [?] | [?] |

## Blockers (if any)
- [List any showstoppers]

## Recommendations
- [Specific actions needed for upgrade]

## Cost Estimate
- RTX 6000 Ada: ~$6,500
- Additional components: [if needed]
- Total: [estimate]
```

---

## Success Criteria

1. All hardware specs documented
2. GO/NO-GO/CONDITIONAL recommendation with reasoning
3. Blockers identified (if any)
4. Comparison with redfin RTX 6000 setup
5. Report saved to `/ganuda/docs/reports/`

---

## Security Notes

- Run commands as dereadi user (sudo where needed)
- Do not run stress tests without TPM approval
- Document but do not modify any hardware settings

---

## Thermal Memory

Archive findings with:
- `memory_type`: hardware_assessment
- `sacred_pattern`: false (unless critical finding)
- Tag: bluefin, gpu, rtx6000, upgrade

---

*Cherokee AI Federation — Hardware Assessment*
*Know your iron before you upgrade it.*
