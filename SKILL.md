---
name: x-account-monitor
description: Monitor X/Twitter accounts via RSS with HTML fallback - fetch latest tweets, track viral posts, crypto news from specified accounts. Outputs to JSON.
version: 1.1.0
author: X RSS Monitor
license: MIT
metadata:
  x:
    tags: [X, Twitter, RSS, monitor, crypto, viral]
    created: 2026-04-29
---

# X Account RSS Monitor

Monitor X/Twitter accounts to track viral posts, crypto news, and tech updates via RSS feeds with HTML scraping fallback.

## Requirements

```bash
pip install -r requirements.txt
```

Dependencies:
- `requests` - HTTP calls
- `beautifulsoup4` - HTML parsing fallback

## Use Cases

- Track viral tweets from important accounts (vitalikbuterin, sama, etc)
- Crypto news monitoring (binance, CoinDesk, etc)
- Brand monitoring / competitor tracking

## Setup

### Configure accounts

Edit `account.txt` — one username per line, `#` for comment:

```
# === Crypto / DeFi ===
vitalikbuterin
binance
CoinDesk

# === AI / Tech ===
sama
ylecun
```

## Usage

```bash
# All accounts in account.txt
python x_rss_monitor.py

# Single account
python x_rss_monitor.py --account vitalikbuterin

# Limit tweets per account
python x_rss_monitor.py --count 10

# Force update (ignore cache)
python x_rss_monitor.py --force

# Test instances only
python x_rss_monitor.py --test
```

## Output Files

| File | Description |
|------|-------------|
| `output/latest.json` | Latest tweets per account |
| `output/archive.json` | Full history of all tweets |
| `output/last_run.json` | Metadata from last run |
| `output/state/*.json` | Per-account state (cache) |

### JSON Format

```json
{
  "generated": "2026-04-29T12:15:00Z",
  "accounts": [
    {
      "username": "vitalikbuterin",
      "tweet_count": 42,
      "tweets": [
        {
          "text": " tweet content...",
          "url": "https://x.com/vitalikbuterin/status/...",
          "published": "Tue, 29 Apr 2026 12:00:00 +0000"
        }
      ]
    }
  ]
}
```

## Features

- **Dual method**: Try RSS first, fall back to HTML scraping if RSS fails
- **Instance testing**: Auto-detect working Nitter instances
- **State tracking**: Per-account cache to avoid duplicate tweets
- **Rate limiting**: 1.5s delay between requests
- **Error handling**: Graceful fallback across instances

## Nitter Instances

Script auto-fallbacks if one instance is down:

1. xcancel.com
2. nitter.poast.org
3. nitter.privacyredirect.com
4. lightbrd.com
5. nitter.space
6. nitter.net

## CRON Setup

For auto-fetch every hour:

```bash
crontab -e

# Add line:
0 * * * * cd /path/to/x-rss-monitor && python3 x_rss_monitor.py
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| No tweets fetched | Install beautifulsoup4: `pip install beautifulsoup4` |
| HTTP 429 | Rate limited — wait or reduce frequency |
| All instances fail | Check internet / try again later |

## Notes

- Some popular accounts may be rate limited
- HTML fallback requires beautifulsoup4
- No API key required