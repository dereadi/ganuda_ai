# JR Instruction: S6000 Backplane Shopping List

**JR ID:** JR-NETWORK-001
**Priority:** P2 (Planning)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** Internet Research Jr.
**Effort:** Small

## Objective

Compile a shopping list with direct purchase links for the 10GbE backplane network connecting redfin and bluefin via Dell S6000 switch.

## Required Items

### 1. For redfin (PCIe SFP+ NIC)

| Item | Specs | Target Price |
|------|-------|--------------|
| Mellanox ConnectX-3 EN | MCX311A-XCAT, Single SFP+, PCIe x4 | $20-30 |
| SFP+ DAC Cable | 2-3 meter, passive copper | $10-15 |

**Search terms:**
- eBay: "Mellanox MCX311A-XCAT"
- eBay: "SFP+ DAC 2m passive"

### 2. For bluefin (USB-C 10GbE Adapter)

| Item | Specs | Target Price |
|------|-------|--------------|
| USB-C to 10GbE Adapter | USB 3.2 Gen 2, RJ45, 10GBase-T | $100-120 |
| SFP+ to RJ45 Transceiver | 10GBase-T, for S6000 switch side | $25-35 |
| CAT6a Cable | 3 meter, shielded preferred | $8-12 |

**Search terms:**
- Amazon: "TRENDnet TUC-ET10G" or "USB-C 10GbE adapter"
- eBay: "SFP+ 10GBase-T RJ45 transceiver"
- Amazon: "CAT6a cable 3m shielded"

### 3. For Dell S6000 Switch

| Item | Specs | Target Price |
|------|-------|--------------|
| QSFP+ to 4xSFP+ Breakout Cable | 3 meter, Dell compatible | $30-40 |

**Search terms:**
- eBay: "Dell QSFP+ 4x SFP+ breakout" or "MRN9N" or "P4YPY"

## Deliverable

Create a markdown file with:

1. **Direct links** to specific listings (eBay item numbers, Amazon ASINs)
2. **Current prices** as of search date
3. **Seller ratings** (prefer 98%+ positive)
4. **Shipping costs** and estimated delivery
5. **Total cost** summary

### Output File

CREATE: `/ganuda/docs/procurement/S6000-BACKPLANE-SHOPPING-LIST-JAN2026.md`

```markdown
# S6000 Backplane Shopping List
**Generated:** [DATE]
**Total Budget:** ~$250

## redfin Components
| Item | Link | Price | Shipping | Seller Rating |
|------|------|-------|----------|---------------|
| Mellanox MCX311A-XCAT | [eBay #xxxxx](url) | $XX | $X | XX% |
| SFP+ DAC 2m | [eBay #xxxxx](url) | $XX | $X | XX% |

## bluefin Components
| Item | Link | Price | Shipping | Seller Rating |
|------|------|-------|----------|---------------|
| TRENDnet TUC-ET10G | [Amazon](url) | $XX | Prime | N/A |
| SFP+ 10GBase-T Transceiver | [eBay #xxxxx](url) | $XX | $X | XX% |
| CAT6a 3m | [Amazon](url) | $XX | Prime | N/A |

## S6000 Components
| Item | Link | Price | Shipping | Seller Rating |
|------|------|-------|----------|---------------|
| Dell QSFP+ Breakout 3m | [eBay #xxxxx](url) | $XX | $X | XX% |

## Summary
| Category | Cost |
|----------|------|
| redfin | $XX |
| bluefin | $XX |
| S6000 | $XX |
| **Total** | **$XXX** |
```

## Verification

- [ ] All links are valid and items in stock
- [ ] Prices are current (within last 24 hours)
- [ ] Sellers have good ratings
- [ ] Shipping to US confirmed
- [ ] Total within $250 budget

## Notes

- Prefer US-based sellers for faster shipping
- Dell-branded cables preferred for S6000 compatibility
- Check "Buy It Now" listings, not auctions
- If 2-pack Mellanox cards available with cable included, note as alternative

---

FOR SEVEN GENERATIONS
