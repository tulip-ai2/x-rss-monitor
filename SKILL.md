---
name: x-account-monitor
description: Monitor X/Twitter accounts via RSS using Nitter instances - fetch latest tweets, track viral posts, crypto news from specified accounts. Outputs to JSON for processing.
version: 1.0.0
author: X RSS Monitor
license: MIT
metadata:
  x:
    tags: [X, Twitter, RSS, monitor, crypto, viral]
    created: 2026-04-29
---

# X Account RSS Monitor

Monitor X/Twitter accounts to track viral posts, crypto news, and tech updates via RSS feeds from Nitter instances.

## Use Cases

- Track viral tweets from important accounts (vitalikbuterin, sama, etc)
- Crypto news monitoring (binance, CoinDesk, etc)
- Brand monitoring / competitor tracking

## Setup

### 1. Install dependencies

```bash
pip install requests
```

### 2. Configure accounts

Edit `account.txt` — one username per line, `#` for comment:

```
# === Crypto / DeFi ===
vitalikbuterin
binance
CoinDesk

# === AI / Tech ===
sama
ylecun

# === Indonesian ===
detikcom
```

## Usage

```bash
python x_rss_monitor.py                    # all accounts in account.txt
python x_rss_monitor.py --account vitalikbuterin  # single account
python x_rss_monitor.py --count 10         # limit tweets per account
```

## Output Files

| File | Description |
|------|-------------|
| `output/latest.json` | Latest tweets per account (3 per account default) |
| `output/archive.json` | Full history of all tweets |
| `output/last_run.json` | Metadata from last run |

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

## CRON Setup (optional)

For auto-fetch every hour:

```bash
crontab -e

# Add line:
0 * * * * cd /path/to/x-rss-monitor && python3 x_rss_monitor.py
```

## Nitter Instances

Script auto-fallbacks to another instance if one is down. Default chain:
1. nitter.net (primary)
2. nitter.privacydev.net
3. nitter.poast.org
4. nitter.kavin.rocks
5. nitter.1d4.us
6. nitter.mw1w.com

## Troubleshooting

| Error | Solution |
|-------|----------|
| `HTTP 429` | Rate limited — wait a bit or reduce frequency |
| `HTTP 404` | Account not found / private |
| `Connection refused` | Nitter instance down — try another |
| All instances fail | Check internet / try again later |

## Limitations & Known Issues

- **No following/followers support**: Nitter RSS only provides tweets, NOT following or followers lists. Attempting to fetch `/username/following` returns empty/blocked.
- **Rate limiting common**: Popular accounts like `elonmusk`, `cryptoethereum` frequently get HTTP 429 from Nitter.
- Some Nitter instances unreliable: `nitter.1d4.us`, `nitter.mw1w.com` often fail.

## Notes

- No API key required — uses RSS feeds only