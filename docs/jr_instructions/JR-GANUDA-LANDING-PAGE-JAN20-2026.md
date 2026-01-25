# Jr Instruction: Ganuda.us Landing Page Enhancement
## Cherokee AI Federation
### January 20, 2026

---

## Priority: MEDIUM

## Context

We need ganuda.us to be a professional company landing page that showcases our products and builds trust with potential users. Currently it's a minimal placeholder.

---

## Requirements

### 1. Replace Landing Page Content

**File:** `/ganuda/www/ganuda.us/index.html`

Create a professional landing page with:

#### Header Section
- Ganuda logo (text-based for now)
- Tagline: "Cherokee AI Federation"
- Navigation: Products | About | Contact

#### Hero Section
- Main headline: "AI Solutions Built on Trust"
- Subheadline: "Secure, ethical AI products designed for seven generations"
- CTA button linking to VetAssist

#### Products Section

**VetAssist**
- AI-powered VA claims assistant
- Free for veterans
- 24/7 availability
- CFR-compliant rating calculator
- Link: https://vetassist.ganuda.us

**Tribal Vision**
- Intelligent video & audio processing
- On-premise deployment available
- Privacy-first design
- Coming Soon / Contact for demo

#### Trust & Security Section
- "Your Data, Protected"
- Bullet points:
  - All data encrypted at rest and in transit
  - No data sold to third parties
  - On-premise deployment options
  - Open about our practices

#### About Section
- "Built by the Cherokee AI Federation"
- Brief mission statement about ethical AI
- "For Seven Generations" philosophy explanation

#### Footer
- Copyright 2026 Ganuda
- Links: Privacy | Terms | Contact
- Contact email: hello@ganuda.ai

### 2. Styling Requirements

- Clean, professional design
- Dark blue/slate color scheme (matches current)
- Mobile responsive
- Fast loading (no heavy frameworks)
- CSS-only (no JS required for basic page)

### 3. File Structure

```
/ganuda/www/ganuda.us/
├── index.html      # Main page
├── css/
│   └── style.css   # Optional: external stylesheet
└── images/         # Optional: any images
```

---

## Design Reference

Current placeholder uses these colors (keep them):
- Background: `linear-gradient(135deg, #1a365d 0%, #2d3748 100%)`
- Text: white
- Cards: `rgba(255,255,255,0.1)` with backdrop blur

---

## Content Requirements

### Value Proposition (use this text)

> Ganuda builds AI solutions with trust at their core. Our products are designed with security, privacy, and long-term impact in mind. We believe AI should serve people for generations, not just quarterly earnings.

### VetAssist Description

> VetAssist is a free AI-powered tool that helps veterans prepare VA disability claims. Calculate your potential rating, identify required evidence, and navigate VA forms step-by-step. Available 24/7, completely free.

### Tribal Vision Description

> Tribal Vision brings intelligent video and audio analysis to your organization. Process surveillance footage, meeting recordings, or media archives with AI that respects privacy. Deploy on-premise for complete data control.

---

## Acceptance Criteria

1. [ ] Professional landing page at `/ganuda/www/ganuda.us/index.html`
2. [ ] Products section with VetAssist and Tribal Vision
3. [ ] Trust/security messaging included
4. [ ] Mobile responsive
5. [ ] All links work (VetAssist link, email contact)
6. [ ] Page loads quickly (< 2 seconds)

---

## Testing

After deployment, verify:
```bash
curl -s https://ganuda.us | grep -q "VetAssist" && echo "VetAssist section present"
curl -s https://ganuda.us | grep -q "Tribal Vision" && echo "Tribal Vision section present"
curl -s https://ganuda.us | grep -q "security" && echo "Security section present"
```

---

*Cherokee AI Federation - For Seven Generations*
