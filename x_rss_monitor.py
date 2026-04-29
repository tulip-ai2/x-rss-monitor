#!/usr/bin/env python3
"""
X / Twitter Account RSS Monitor
================================
Reads account list from account.txt
Fetches latest tweets via Nitter RSS
Saves results to JSON for GitHub sync or further processing.

Usage:
    python x_rss_monitor.py                    # fetch all accounts
    python x_rss_monitor.py --account elonmusk  # fetch single account
    python x_rss_monitor.py --count 10         # limit tweets per account
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

# ─── Config ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
ACCOUNT_FILE = SCRIPT_DIR / "account.txt"
OUTPUT_DIR = SCRIPT_DIR / "output"
ARCHIVE_FILE = OUTPUT_DIR / "archive.json"
STATE_FILE = OUTPUT_DIR / "last_run.json"
FEED_FILE = OUTPUT_DIR / "latest.json"

# Nitter instances (fallback chain — rotate if one fails)
NITTER_INSTANCES = [
    "nitter.net",
    "nitter.privacydev.net",
    "nitter.poast.org",
    "nitter.kavin.rocks",
    "nitter.1d4.us",
    "nitter.mw1w.com",
]

REQUEST_TIMEOUT = 15  # seconds
MAX_TWEETS_DEFAULT = 5
USER_AGENT = (
    "Mozilla/5.0 (compatible; X-RSS-Monitor/1.0; "
    "+https://github.com/tulip-ai2/x-rss-monitor)"
)


# ─── Helpers ──────────────────────────────────────────────

def load_accounts(path: Path) -> list[str]:
    """Parse account.txt, return list of usernames (stripped, no @)."""
    accounts = []
    if not path.exists():
        print(f"[WARN] {path} not found, no accounts to monitor.")
        return accounts
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Remove @ prefix if user accidentally included it
        username = line.lstrip("@")
        if username:
            accounts.append(username.lower())
    return accounts


def fetch_rss(username: str, max_tweets: int = MAX_TWEETS_DEFAULT) -> list[dict]:
    """Fetch RSS feed for a username from a Nitter instance. Returns list of tweet dicts."""
    tweets = []
    errors = []

    for instance in NITTER_INSTANCES:
        url = f"https://{instance}/{username}/rss"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml"},
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                xml_text = resp.read().decode("utf-8", errors="replace")

            root = ET.fromstring(xml_text)
            channel = root.find("channel")
            if channel is None:
                raise ValueError("No <channel> element in RSS")

            items = channel.findall("item")[:max_tweets]
            for item in items:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                description = (item.findtext("description") or "").strip()
                # Nitter puts full tweet text in <description>
                tweet_text = description or title
                # Remove "username: " prefix from title if present
                tweet_text = tweet_text.replace(f"{username}: ", "", 1)

                tweets.append({
                    "username": username,
                    "text": tweet_text[:500],  # cap for sanity
                    "url": link,
                    "published": pub_date,
                    "instance": instance,
                })

            print(f"[OK]   {username:25s} — {len(tweets)} tweets from {instance}")
            return tweets

        except Exception as e:
            errors.append(f"{instance}: {e}")
            print(f"[RETRY] {username} via {instance} failed: {e}")
            continue

    print(f"[FAIL] {username:25s} — all {len(NITTER_INSTANCES)} instances failed")
    return []


def load_archive() -> dict:
    """Load existing archive.json or return empty dict."""
    if ARCHIVE_FILE.exists():
        try:
            return json.loads(ARCHIVE_FILE.read_text())
        except Exception:
            pass
    return {"accounts": {}}


def save_archive(archive: dict):
    """Write archive.json, creating output dir if needed."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_FILE.write_text(json.dumps(archive, indent=2, ensure_ascii=False))


def merge_tweets(archive: dict, results: list[dict]) -> dict:
    """Merge new tweets into archive, avoid duplicates by (username, url)."""
    seen = set()
    for acc_data in archive["accounts"].values():
        for tweet in acc_data.get("tweets", []):
            seen.add((tweet.get("username"), tweet.get("url")))

    new_count = 0
    for tweet in results:
        key = (tweet["username"], tweet["url"])
        if key not in seen:
            seen.add(key)
            new_count += 1

    # Rebuild archive
    new_archive = {"updated": datetime.utcnow().isoformat() + "Z", "accounts": {}}

    # Carry over existing + add new (newest first per account)
    all_tweets_by_user: dict[str, list] = {}
    for acc_data in archive["accounts"].values():
        all_tweets_by_user[acc_data["username"]] = list(acc_data.get("tweets", []))

    for tweet in reversed(results):  # oldest first → reverse for newest first
        username = tweet["username"]
        if username not in all_tweets_by_user:
            all_tweets_by_user[username] = []
        # Avoid duplicate
        if not any(t["url"] == tweet["url"] for t in all_tweets_by_user[username]):
            all_tweets_by_user[username].insert(0, tweet)

    for username, tweets in all_tweets_by_user.items():
        new_archive["accounts"][username] = {
            "username": username,
            "tweet_count": len(tweets),
            "tweets": tweets,
        }

    return new_archive


def build_latest(archive: dict, limit_per_account: int = 3) -> dict:
    """Build latest.json — newest N tweets per account."""
    latest = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "accounts": [],
    }
    for username, acc_data in archive.get("accounts", {}).items():
        tweets = acc_data.get("tweets", [])[:limit_per_account]
        latest["accounts"].append({
            "username": username,
            "tweet_count": acc_data.get("tweet_count", 0),
            "tweets": tweets,
        })
    return latest


# ─── CLI ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="X Account RSS Monitor")
    parser.add_argument("--account", help="Monitor single account (bypass account.txt)")
    parser.add_argument("--count", type=int, default=MAX_TWEETS_DEFAULT, help="Tweets per account")
    parser.add_argument("--no-save", action="store_true", help="Skip saving archive/feeds")
    args = parser.parse_args()

    accounts = [args.account] if args.account else load_accounts(ACCOUNT_FILE)

    if not accounts:
        print("No accounts to monitor. Add usernames to account.txt")
        sys.exit(0)

    print(f"=== X RSS Monitor ({len(accounts)} accounts) ===\n")

    all_results = []
    for username in accounts:
        tweets = fetch_rss(username, max_tweets=args.count)
        all_results.extend(tweets)
        time.sleep(1.5)  # Be polite to Nitter instances

    # Load existing archive
    archive = load_archive()

    # Merge new tweets
    archive = merge_tweets(archive, all_results)

    # Save outputs
    if not args.no_save:
        save_archive(archive)
        latest = build_latest(archive)
        FEED_FILE.write_text(json.dumps(latest, indent=2, ensure_ascii=False))
        STATE_FILE.write_text(json.dumps({
            "run_at": datetime.utcnow().isoformat() + "Z",
            "accounts_fetched": len(accounts),
            "tweets_fetched": len(all_results),
        }, indent=2))
        print(f"\n=== Done ===")
        print(f"  Accounts fetched : {len(accounts)}")
        print(f"  Tweets fetched   : {len(all_results)}")
        print(f"  Archive          : {ARCHIVE_FILE}")
        print(f"  Latest feed      : {FEED_FILE}")
    else:
        print(f"\nFetched {len(all_results)} tweets (no files saved)")


if __name__ == "__main__":
    main()