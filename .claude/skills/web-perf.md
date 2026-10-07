---
name: web-perf
description: Analyzes web performance using Chrome DevTools MCP. Measures Core Web Vitals (FCP, LCP, TBT, CLS, Speed Index), identifies render-blocking resources, network dependency chains, layout shifts, caching issues, and accessibility gaps. Use when asked to audit, profile, debug, or optimize page load performance, Lighthouse scores, or site speed.
---

# Web Performance Audit

Audit web page performance focusing on Core Web Vitals, network optimization, and accessibility.

## Key Guidelines

- **Be assertive**: Verify claims by checking network requests, DOM, or codebase—then state findings definitively.
- **Quantify impact**: Use estimated savings from insights. Don't prioritize changes with 0ms impact.
- **Be specific**: Say "compress hero.png (450KB) to WebP" not "optimize images".
- **Prioritize ruthlessly**: A site with 200ms LCP and 0 CLS is already excellent—say so.

## Core Web Vitals Thresholds

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| TTFB | < 800ms | < 1.8s | > 1.8s |
| FCP | < 1.8s | < 3s | > 3s |
| LCP | < 2.5s | < 4s | > 4s |
| INP | < 200ms | < 500ms | > 500ms |
| TBT | < 200ms | < 600ms | > 600ms |
| CLS | < 0.1 | < 0.25 | > 0.25 |
| Speed Index | < 3.4s | < 5.8s | > 5.8s |

## Audit Checklist

```
- [ ] Phase 1: Performance trace (navigate + record)
- [ ] Phase 2: Core Web Vitals analysis (LCP, CLS, FCP)
- [ ] Phase 3: Network analysis (blocking resources, chains)
- [ ] Phase 4: Accessibility snapshot
- [ ] Phase 5: Codebase analysis (if available)
```

## Common Issues to Look For

### Render-Blocking Resources
- JS/CSS in `<head>` without `async`/`defer`/`media` attributes
- Large CSS files blocking first paint

### Network Chains
- Resources discovered late due to dependencies
- CSS imports, JS-loaded fonts
- Missing preloads for critical resources

### Caching Issues
- Missing `Cache-Control` headers
- No `ETag` or `Last-Modified`
- Short cache TTLs for static assets

### Large Payloads
- Uncompressed JS/CSS bundles
- Unoptimized images (use WebP/AVIF)
- Source maps in production

## Framework Detection

| Tool | Config Files |
|------|--------------|
| Next.js | `next.config.js`, `next.config.mjs` |
| Vite | `vite.config.js`, `vite.config.ts` |
| Webpack | `webpack.config.js` |
| Nuxt | `nuxt.config.js` |

## Quick Wins

1. **Add `loading="lazy"`** to below-fold images
2. **Preload LCP image**: `<link rel="preload" as="image" href="...">`
3. **Defer non-critical JS**: `<script defer src="...">`
4. **Add dimensions to images**: Prevents CLS
5. **Use `font-display: swap`**: Prevents FOIT

## Output Format

Present findings as:

1. **Core Web Vitals Summary** - Table with metric, value, rating
2. **Top Issues** - Prioritized by impact (high/medium/low)
3. **Recommendations** - Specific fixes with code snippets
4. **Codebase Findings** - Framework detected, optimization opportunities
