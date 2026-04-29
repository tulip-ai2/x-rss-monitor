#!/usr/bin/env python3
"""
X/Twitter Account Monitor
=====================
Fetch tweets via RSS with HTML scraping fallback.
Track viral posts, crypto news, and tech updates.
Outputs to JSON for further processing.

Usage:
    python x_rss_monitor.py                    # all accounts in account.txt
    python x_rss_monitor.py --account user    # single account
    python x_rss_monitor.py --count 10        # limit tweets per account
    python x_rss_monitor.py --force            # force update (ignore cache)
    python x_rss_monitor.py --test             # test instances only
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Optional

# Try to import BeautifulSoup, fallback to simple parsing
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# ─── Config ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
ACCOUNT_FILE = SCRIPT_DIR / "account.txt"
OUTPUT_DIR = SCRIPT_DIR / "output"
STATE_DIR = OUTPUT_DIR / "state"
ARCHIVE_FILE = OUTPUT_DIR / "archive.json"
LATEST_FILE = OUTPUT_DIR / "latest.json"
STATE_FILE = OUTPUT_DIR / "last_run.json"

# Updated Nitter instances (working as of 2026)
NITTER_INSTANCES = [
    "https://xcancel.com",
    "https://nitter.poast.org",
    "https://nitter.privacyredirect.com",
    "https://lightbrd.com",
    "https://nitter.space",
    "https://nitter.tiekoetter.com",
    "https://nuku.trabun.org",
    "https://nitter.catsarch.com",
    "https://nitter.net",
    "https://nitter.kavin.rocks",
]

REQUEST_TIMEOUT = 15
MAX_TWEETS_DEFAULT = 5
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ─── Helpers ──────────────────────────────────────────────

def load_accounts(path: Path) -> list[str]:
    """Parse account.txt, return list of usernames."""
    accounts = []
    if not path.exists():
        print(f"[WARN] {path} not found")
        return accounts
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        username = line.lstrip("@").lower()
        if username:
            accounts.append(username)
    return accounts


def load_state(username: str) -> dict:
    """Load per-account state from state file."""
    state_file = STATE_DIR / f"{username}.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except Exception:
            pass
    return {
        "last_hash": None,
        "last_update": None,
        "last_count": 0,
        "failures": 0,
        "instance_used": None,
        "last_successful_instance": None,
    }


def save_state(username: str, state: dict):
    """Save per-account state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"{username}.json"
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def calculate_hash(tweets: list) -> str:
    """Calculate hash of tweets for change detection."""
    if not tweets:
        return "no_tweets"
    content = "".join([t[:200] for t in tweets[:3]])
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def fetch_rss(username: str, max_tweets: int = MAX_TWEETS_DEFAULT) -> list[dict]:
    """Fetch tweets via RSS feed."""
    tweets = []
    state = load_state(username)
    
    # Try last successful instance first
    instances_order = list(NITTER_INSTANCES)
    last_success = state.get("last_successful_instance")
    if last_success and last_success in instances_order:
        instances_order.remove(last_success)
        instances_order.insert(0, last_success)

    for instance in instances_order:
        try:
            url = f"{instance}/{username}/rss"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml"},
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                xml_text = resp.read().decode("utf-8", errors="replace")

            root = ET.fromstring(xml_text)
            channel = root.find("channel")
            if channel is None:
                continue

            items = channel.findall("item")[:max_tweets]
            for item in items:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                description = (item.findtext("description") or "").strip()
                
                # Nitter: full tweet in description, or title with "username: " prefix
                tweet_text = description or title
                tweet_text = tweet_text.replace(f"{username}: ", "", 1)

                tweets.append({
                    "username": username,
                    "text": tweet_text[:500],
                    "url": link,
                    "published": pub_date,
                    "instance": instance,
                })

            if tweets:
                # Update state
                state["last_successful_instance"] = instance
                state["failures"] = 0
                save_state(username, state)
                print(f"[RSS] {username:20s} — {len(tweets)} tweets from {instance.replace('https://', '')}")
                return tweets

        except Exception as e:
            state["failures"] = state.get("failures", 0) + 1
            print(f"[RSS-FAIL] {username} via {instance.replace('https://', '')}: {str(e)[:30]}")
            continue

    save_state(username, state)
    return []


def fetch_html(username: str, max_tweets: int = MAX_TWEETS_DEFAULT) -> list[dict]:
    """Fallback: fetch tweets via HTML scraping."""
    if not HAS_BS4:
        return []

    tweets = []
    state = load_state(username)
    
    instances_order = list(NITTER_INSTANCES)
    last_success = state.get("last_successful_instance")
    if last_success and last_success in instances_order:
        instances_order.remove(last_success)
        instances_order.insert(0, last_success)

    # HTML selectors for tweets (try in order)
    selectors = [
        ".tweet-content",
        ".tweet-body", 
        ".timeline-item",
        ".tweet",
        ".tweet-text",
        "[data-testid='tweet']",
    ]

    for instance in instances_order:
        try:
            url = f"{instance}/{username}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            soup = BeautifulSoup(html, "html.parser")
            
            # Try each selector
            for selector in selectors:
                found = soup.select(selector)
                if found:
                    for elem in found[:max_tweets]:
                        text = elem.get_text(strip=True)
                        if text and len(text) > 10:
                            # Try to find link
                            link_elem = elem.find("a", href=True)
                            link = ""
                            if link_elem and "/status/" in link_elem.get("href", ""):
                                link = instance + link_elem.get("href")
                            
                            tweets.append({
                                "username": username,
                                "text": text[:500],
                                "url": link,
                                "published": "",
                                "instance": instance,
                            })
                    if tweets:
                        break
            
            if tweets:
                state["last_successful_instance"] = instance
                state["failures"] = state.get("failures", 0) + 1
                save_state(username, state)
                print(f"[HTML] {username:20s} — {len(tweets)} tweets from {instance.replace('https://', '')}")
                return tweets

        except Exception as e:
            print(f"[HTML-FAIL] {username} via {instance.replace('https://', '')}: {str(e)[:30]}")
            continue

    state["failures"] = state.get("failures", 0) + 1
    save_state(username, state)
    return []


def fetch_tweets(username: str, max_tweets: int, force: bool = False) -> list[dict]:
    """Fetch tweets: try RSS first, then HTML fallback."""
    # Get existing state
    state = load_state(username)
    
    # Try RSS first
    tweets = fetch_rss(username, max_tweets)
    
    # If RSS fails, try HTML
    if not tweets:
        print(f"[FALLBACK] {username}: trying HTML scraping...")
        tweets = fetch_html(username, max_tweets)
    
    # If still no tweets, return empty
    return tweets


def test_instances() -> bool:
    """Test which Nitter instances are working."""
    print("=== Testing Nitter Instances ===")
    working = []
    
    for instance in NITTER_INSTANCES:
        try:
            url = f"{instance}/nitter"
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    working.append(instance)
                    print(f"[OK] {instance}")
        except Exception as e:
            print(f"[FAIL] {instance}: {str(e)[:30]}")
    
    print(f"\n=== Result: {len(working)}/{len(NITTER_INSTANCES)} working ===")
    if working:
        print(f"Working: {working}")
    return len(working) > 0


def load_archive() -> dict:
    """Load existing archive."""
    if ARCHIVE_FILE.exists():
        try:
            return json.loads(ARCHIVE_FILE.read_text())
        except Exception:
            pass
    return {"accounts": {}}


def save_archive(archive: dict):
    """Write archive.json."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_FILE.write_text(json.dumps(archive, indent=2, ensure_ascii=False))


def merge_tweets(archive: dict, results: list[dict]) -> dict:
    """Merge new tweets into archive, deduplicate by URL."""
    seen = set()
    for acc in archive.get("accounts", {}).values():
        for tweet in acc.get("tweets", []):
            seen.add((tweet.get("username"), tweet.get("url")))

    # Collect tweets by user
    by_user: dict[str, list] = {}
    for acc_data in archive.get("accounts", {}).values():
        by_user[acc_data["username"]] = list(acc_data.get("tweets", []))

    for tweet in results:
        username = tweet["username"]
        if username not in by_user:
            by_user[username] = []
        if not any(t["url"] == tweet["url"] for t in by_user[username]):
            by_user[username].insert(0, tweet)

    new_archive = {
        "updated": datetime.utcnow().isoformat() + "Z",
        "accounts": {}
    }
    for username, twts in by_user.items():
        new_archive["accounts"][username] = {
            "username": username,
            "tweet_count": len(twts),
            "tweets": twts,
        }
    
    return new_archive


def build_latest(archive: dict, limit: int = 3) -> dict:
    """Build latest.json - newest N tweets per account."""
    latest = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "accounts": [],
    }
    for username, acc in archive.get("accounts", {}).items():
        tweets = acc.get("tweets", [])[:limit]
        latest["accounts"].append({
            "username": username,
            "tweet_count": acc.get("tweet_count", 0),
            "tweets": tweets,
        })
    return latest


# ─── CLI ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="X Account RSS/HTML Monitor")
    parser.add_argument("--account", help="Monitor single account")
    parser.add_argument("--count", type=int, default=MAX_TWEETS_DEFAULT, help="Tweets per account")
    parser.add_argument("--force", action="store_true", help="Force update (ignore cache)")
    parser.add_argument("--test", action="store_true", help="Test instances only")
    parser.add_argument("--html-only", action="store_true", help="Use HTML only (no RSS)")
    args = parser.parse_args()

    print(f"=== X RSS Monitor ===")
    print(f"BeautifulSoup: {'Available' if HAS_BS4 else 'Not installed'}")
    
    if args.test:
        test_instances()
        return

    accounts = [args.account] if args.account else load_accounts(ACCOUNT_FILE)
    if not accounts:
        print("No accounts. Add usernames to account.txt")
        sys.exit(0)

    print(f"Accounts to monitor: {len(accounts)}")
    print(f"Use HTML fallback: {'Yes' if HAS_BS4 else 'No (install beautifulsoup4)'}")
    print("")

    all_results = []
    for idx, username in enumerate(accounts, 1):
        print(f"[{idx}/{len(accounts)}] {username}")
        tweets = fetch_tweets(username, args.count, force=args.force)
        all_results.extend(tweets)
        time.sleep(1.5)  # Rate limit delay

    # Save outputs
    archive = load_archive()
    archive = merge_tweets(archive, all_results)
    save_archive(archive)
    
    latest = build_latest(archive)
    LATEST_FILE.write_text(json.dumps(latest, indent=2, ensure_ascii=False))
    
    STATE_FILE.write_text(json.dumps({
        "run_at": datetime.utcnow().isoformat() + "Z",
        "accounts_fetched": len(accounts),
        "tweets_fetched": len(all_results),
    }, indent=2))

    print(f"\n=== Done ===")
    print(f"Accounts: {len(accounts)}")
    print(f"Tweets: {len(all_results)}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()