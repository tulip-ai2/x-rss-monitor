---
name: x-account-monitor
description: Monitor X/Twitter accounts via RSS using Nitter instances - fetch latest tweets, track viral posts, crypto news from specified accounts. Outputs to JSON for further processing or GitHub sync.
version: 1.0.0
author: X RSS Monitor
license: MIT
metadata:
  x:
    tags: [X, Twitter, RSS, monitor, crypto, viral]
    related_skills: [xitter, github-auth]
    created: 2026-04-29
---

# X Account RSS Monitor

Monitor X/Twitter accounts to track viral posts, crypto news, dan tech updates via RSS feeds dari Nitter instances.

## Use Cases

- Track viral tweets dari akun penting (vitalikbuterin, sama, etc)
- Crypto news monitoring (binance, CoinDesk, etc)  
- Auto-fetch ke GitHub untuk archive atau Railway bot
- Brand monitoring / competitor tracking

## Setup

### 1. Install dependencies

```bash
pip install requests
```

### 2. Configure accounts

Edit `account.txt` — satu username per baris, `#` untuk comment:

```
# === Crypto / DeFi ===
vitalikbuterin
CryptoEthereum
binance

# === AI / Tech ===
sama
ylecun

# === Indonesian ===
detikcom
```

## Usage

### Standalone (fetch only)

```bash
python x_rss_monitor.py                    # semua akun di account.txt
python x_rss_monitor.py --account vitalikbuterin  # satu akun
python x_rss_monitor.py --count 10         # limit tweet per akun
```

### With GitHub sync (manual)

```python
# Fetch dan simpan ke JSON
python x_rss_monitor.py

# Commit manual ke GitHub (bisa automation)
cd .git_worktree  # atau clone repo
git add data/*.json
git commit -m "data: RSS update $(date -u +'%Y-%m-%d')"
git push origin main
```

## Output Files

| File | Description |
|------|-------------|
| `output/latest.json` | Tweet terbaru per akun (3 per account default) |
| `output/archive.json` | Full history semua tweet |
| `output/last_run.json` | Metadata run terakhir |

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

Buat auto-fetch setiap jam:

```bash
# Edit crontab
crontab -e

# Tambah line:
0 * * * * cd /path/to/x-rss-monitor && python3 x_rss_monitor.py
```

## Nitter Instances

Script auto-fallback ke instance lain kalau satu down. Default chain:
1. nitter.net (utama)
2. nitter.privacydev.net
3. nitter.poast.org
4. nitter.kavin.rocks
5. nitter.1d4.us
6. nitter.mw1w.com

## Troubleshooting

| Error | Solution |
|-------|----------|
| `HTTP 429` | Rate limited — tunggu sebentar atau kurangi freq |
| `HTTP 404` | Akun tidak ditemukan / private |
| `Connection refused` | Nitter instance down — coba instance lain |
| All instances fail | Cek internet / coba nanti |

## Notes

- Beberapa akun popular (elonmusk) sering di-rate limit
- Delay 1.5s antar request untuk avoid rate limit
- Hasil bisa langsung di-push ke GitHub untuk archive publik