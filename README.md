# X RSS Monitor

Monitor X/Twitter accounts via RSS with HTML scraping fallback.

## Quick Start

```bash
pip install -r requirements.txt
python x_rss_monitor.py
```

## Setup

Edit `account.txt` with usernames (one per line):

```
vitalikbuterin
binance
CoinDesk
```

## Usage

```bash
# All accounts in account.txt
python x_rss_monitor.py

# Single account
python x_rss_monitor.py --account vitalikbuterin

# Limit tweets per account
python x_rss_monitor.py --count 10

# Force update
python x_rss_monitor.py --force

# Test instances
python x_rss_monitor.py --test
```

## Output

Results saved to `output/`:
- `latest.json` - Latest tweets
- `archive.json` - Full history
- `state/` - Per-account cache

## Features

- RSS with HTML scraping fallback
- Auto-fallback across Nitter instances
- State tracking per account
- Rate limit handling

## Notes

- Requires `beautifulsoup4` for HTML fallback
- No API key needed