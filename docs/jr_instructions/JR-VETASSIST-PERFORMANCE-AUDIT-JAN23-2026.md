# JR Instruction: VetAssist Performance Audit

**Task ID:** VETASSIST-PERF-001
**Priority:** P1
**Date:** January 23, 2026

## Objective

Audit and optimize performance of https://vetassist.ganuda.us/

Initial WebFetch analysis identified:
- Heavy JavaScript bundle fragmentation
- Multiple chunk files requiring HTTP requests
- Substantial serialized Next.js data payload
- Possible runtime overhead from AuthProvider and layout components

## Investigation Steps

### Step 1: Lighthouse Audit

Run Lighthouse performance audit from bluefin:

```bash
# Install lighthouse if needed
npm install -g lighthouse

# Run audit
lighthouse https://vetassist.ganuda.us/ \
  --output=json \
  --output-path=/ganuda/reports/vetassist-lighthouse-$(date +%Y%m%d).json \
  --chrome-flags="--headless --no-sandbox"

# Generate HTML report too
lighthouse https://vetassist.ganuda.us/ \
  --output=html \
  --output-path=/ganuda/reports/vetassist-lighthouse-$(date +%Y%m%d).html \
  --chrome-flags="--headless --no-sandbox"
```

### Step 2: Bundle Analysis

Check the Next.js build output:

```bash
cd /ganuda/vetassist/frontend

# Analyze bundle size
npx @next/bundle-analyzer

# Or check build output
npm run build 2>&1 | tee /tmp/vetassist-build.log

# Look for large chunks
ls -lhS .next/static/chunks/*.js | head -20
```

### Step 3: Network Waterfall

Use curl to measure time-to-first-byte and total load:

```bash
# TTFB measurement
curl -o /dev/null -s -w "TTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" https://vetassist.ganuda.us/

# Check response headers for caching
curl -I https://vetassist.ganuda.us/ 2>/dev/null | grep -i cache
```

### Step 4: Check Server-Side Issues

On bluefin where VetAssist runs:

```bash
# Check process memory/CPU
ps aux | grep -E 'next|node' | head -10

# Check for slow API responses
journalctl -u vetassist-frontend --since "1 hour ago" | grep -i slow

# Database query times (if applicable)
# Check backend logs for slow queries
```

### Step 5: Core Web Vitals Focus

Key metrics to optimize:
- **LCP (Largest Contentful Paint)**: Target < 2.5s
- **FID (First Input Delay)**: Target < 100ms
- **CLS (Cumulative Layout Shift)**: Target < 0.1

Common fixes:
1. Preload critical fonts
2. Optimize images (next/image with priority)
3. Reduce JavaScript bundle size
4. Add proper loading states to prevent CLS

## Potential Quick Wins

1. **Enable gzip/brotli compression** in Caddy config
2. **Add Cache-Control headers** for static assets
3. **Lazy load non-critical components**
4. **Reduce AuthProvider initialization overhead**

## Deliverables

1. Lighthouse report saved to `/ganuda/reports/`
2. List of top 5 performance bottlenecks
3. Recommended fixes with estimated impact
4. Bundle size breakdown

## Success Criteria

- [ ] Lighthouse Performance score > 80
- [ ] LCP < 2.5 seconds
- [ ] TTFB < 500ms
- [ ] Bundle analysis completed
