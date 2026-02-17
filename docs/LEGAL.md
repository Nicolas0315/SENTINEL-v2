# Legal Guidelines for Data Collection

## Overview

SENTINEL collects publicly available data from multiple sources. This document establishes the legal and ethical guidelines all contributors and operators must follow.

## Core Principles

1. **Respect `robots.txt`** — Always check and obey robots.txt directives before scraping any website.
2. **Review Terms of Service** — Read and comply with each data source's ToS before integration.
3. **Use Official APIs First** — Always prefer official APIs over scraping when available.
4. **Rate Limiting** — Implement reasonable rate limits; never overload target servers.
5. **No Personal Data Collection** — SENTINEL monitors public market signals only. Never collect, store, or process personal information.
6. **Copyright Compliance** — Extract facts and data points, not copyrighted content. Do not reproduce full articles or proprietary analysis.
7. **No Unauthorized Access** — Never circumvent authentication, CAPTCHAs, or access controls.

## Jurisdiction-Specific Notes

### Japan (不正アクセス禁止法)
Japan's Unauthorized Computer Access Law (不正アクセス行為の禁止等に関する法律) prohibits:
- Accessing systems without authorization
- Using credentials belonging to others
- Circumventing access controls

**SENTINEL must only access publicly available endpoints and authorized APIs.**

### United States (CFAA)
The Computer Fraud and Abuse Act applies to unauthorized access to computer systems. Key considerations:
- Public data on public websites is generally accessible
- Violating ToS may constitute unauthorized access in some circuits
- Respect rate limits and do not cause service degradation

### EU (GDPR)
- SENTINEL does not target or collect personal data of EU residents
- Public figure monitoring is limited to public statements on public platforms
- No profiling of private individuals

## API-Specific Compliance

| Source | Method | Notes |
|--------|--------|-------|
| Yahoo Finance | `yfinance` library | Personal/research use; review Yahoo ToS for commercial use |
| FRED API | Official API with key | Free for public use; attribution required |
| CoinGecko | Official API | Free tier with rate limits; respect usage limits |
| Bitflyer | Official API with key | Authorized use with API credentials |
| X (Twitter) | Official API | Comply with X Developer Agreement; no bulk scraping |
| Google News | RSS Feed | Public RSS; respect robots.txt |
| SEC EDGAR | Official EDGAR system | Public data; include User-Agent header per SEC guidelines |
| Alpaca | Official API with key | Paper trading under Alpaca's terms |
| World ID | Official API | Follow Worldcoin developer terms |

## Implementation Requirements

### For All Data Sources
```python
# Example: Rate limiting implementation
import time
from functools import wraps

def rate_limit(calls_per_second=1):
    min_interval = 1.0 / calls_per_second
    last_call = [0]
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_call[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Checklist Before Adding a New Data Source
- [ ] Check `robots.txt`
- [ ] Read Terms of Service
- [ ] Confirm official API availability
- [ ] Implement rate limiting
- [ ] Verify no personal data is collected
- [ ] Document the data source in this file
- [ ] Test with minimal requests first

## Reporting Concerns

If you identify a potential legal or ethical issue with SENTINEL's data collection, please open a GitHub issue with the `legal` label immediately.
