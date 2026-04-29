# X RSS Monitor

Monitor X/Twitter accounts via RSS — track viral posts, crypto news, dan tech updates.

## Quick Start

```bash
# Install
pip install requests

# Configure accounts (edit account.txt)
vim account.txt

# Run
python x_rss_monitor.py
```

## Features

- ✅ Fetch tweets via Nitter RSS (no API key needed)
- ✅ Auto-fallback to multiple Nitter instances  
- ✅ Track crypto, AI, dan Indonesian accounts
- ✅ JSON output for archive/display
- ✅ Rate limit handling

## Configuration

Edit `account.txt` — satu username per baris:

```
# === Crypto ===
vitalikbuterin
binance
CoinDesk

# === AI ===
sama
ylecun
```

## Output

Results saved to `data/`:
- `latest.json` — newest tweets per account
- `archive.json` — full history

## Deployment

### Railway (auto-update)

1. Fork this repo
2. Connect to Railway
3. Add cron job: `python x_rss_monitor.py`
4. Optional: GitHub Actions untuk auto-commit

### GitHub Actions

```yaml
# .github/workflows/rss.yml
name: RSS Monitor
on:
  schedule:
    - cron: '0 * * * *'  # setiap jam
jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install requests
      - run: python x_rss_monitor.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "data: RSS update"
          file_pattern: "data/*.json"
```

## Notes

- Beberapa akun popular (elonmusk) sering di-rate limit
- Nitter instances bisa down — script auto-fallback
- Tanpa API key, hanya RSS feeds

## License

MIT