# Jr Instruction: JSON-LD Structured Data for VetAssist

**Task ID:** VA-JSONLD
**Kanban:** #1865
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

Add JSON-LD structured data to VetAssist pages for SEO and rich search results.

---

## Step 1: Create structured data template

Create `/ganuda/services/vetassist/templates/structured_data.html`

```text
<!-- JSON-LD Structured Data for VetAssist -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{{ org_name | default('Cherokee AI Federation') }}",
  "url": "{{ base_url | default('https://vetassist.ganuda.us') }}",
  "description": "AI-powered VA disability claims assistance for veterans"
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "{{ app_name | default('VetAssist') }}",
  "url": "{{ base_url | default('https://vetassist.ganuda.us') }}",
  "applicationCategory": "HealthApplication",
  "operatingSystem": "Web",
  "description": "AI assistant helping veterans navigate VA disability claims",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is a VA disability claim?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A VA disability claim is a formal request to the Department of Veterans Affairs for compensation for injuries or conditions that occurred or were aggravated during military service."
      }
    },
    {
      "@type": "Question",
      "name": "What is a nexus letter?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A nexus letter is a medical opinion from a qualified healthcare provider establishing a connection between your current condition and your military service. It is often critical for service connection."
      }
    },
    {
      "@type": "Question",
      "name": "How long does a VA claim take?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VA claims typically take 3-6 months for initial decisions, though complex cases or appeals can take longer. Fully Developed Claims (FDC) may be processed faster."
      }
    },
    {
      "@type": "Question",
      "name": "What is the CFR and why does it matter?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The Code of Federal Regulations (38 CFR Part 4) contains the VA's Schedule for Rating Disabilities. Each condition has specific diagnostic codes and criteria that determine your disability rating percentage."
      }
    },
    {
      "@type": "Question",
      "name": "Can I file a secondary service connection claim?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. If a service-connected condition causes or aggravates another condition, you can file a secondary service connection claim under 38 CFR 3.310. Medical evidence linking the conditions is required."
      }
    }
  ]
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "{{ base_url | default('https://vetassist.ganuda.us') }}"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "{{ page_name | default('Claims') }}",
      "item": "{{ page_url | default('https://vetassist.ganuda.us/claims') }}"
    }
  ]
}
</script>
```

---

## Verification

```text
python3 -c "
from jinja2 import Template
with open('/ganuda/services/vetassist/templates/structured_data.html') as f:
    t = Template(f.read())
print(t.render(base_url='https://vetassist.ganuda.us', app_name='VetAssist', org_name='Cherokee AI Federation')[:500])
"
```
