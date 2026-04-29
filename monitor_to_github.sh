#!/usr/bin/env bash
# =========================================
# monitor_to_github.sh
# Fetch RSS + commit results to GitHub repo
# =========================================
# Usage:
#   ./monitor_to_github.sh                      # normal run
#   GITHUB_TOKEN=ghp_xxx ./monitor_to_github.sh # with token env var
# =========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${SCRIPT_DIR}/.git_worktree"   # clone target

# ── Config (override dengan env var) ──────────────────────
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_REPO="${GITHUB_REPO:-tulip-ai2/x-rss-monitor}"   # ganti sesuai repo
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"
COMMIT_MSG="${COMMIT_MSG:-"chore: auto-update RSS feed $(date -u +'%Y-%m-%dT%H:%MZ')"}"

# ── Detect Python venv ─────────────────────────────────────
if [[ -f "${SCRIPT_DIR}/.venv/bin/python" ]]; then
    PYTHON="${SCRIPT_DIR}/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    PYTHON="python"
fi

echo "=== X RSS Monitor → GitHub Sync ==="
echo "Repo : https://github.com/${GITHUB_REPO}"
echo "Branch: ${GITHUB_BRANCH}"
echo ""

# ── Run RSS monitor ─────────────────────────────────────────
echo "[1/4] Fetching RSS feeds..."
cd "${SCRIPT_DIR}"
"${PYTHON}" x_rss_monitor.py

# ── Clone/pull repo ─────────────────────────────────────────
echo ""
echo "[2/4] Syncing to GitHub..."

if [[ -z "${GITHUB_TOKEN}" ]]; then
    echo "[WARN] GITHUB_TOKEN not set — dry-run mode (no commit)"
    echo "       Set: export GITHUB_TOKEN=ghp_xxxx"
    DRY_RUN=true
else
    DRY_RUN=false
    REMOTE="https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"

    if [[ -d "${REPO_DIR}/.git" ]]; then
        echo "  Pulling latest from ${GITHUB_REPO}..."
        cd "${REPO_DIR}"
        git pull origin "${GITHUB_BRANCH}" --quiet
    else
        echo "  Cloning ${GITHUB_REPO}..."
        rm -rf "${REPO_DIR}"
        git clone --depth=1 --branch "${GITHUB_BRANCH}" "${REMOTE}" "${REPO_DIR}"
        cd "${REPO_DIR}"
    fi
fi

# ── Copy output files to repo dir ───────────────────────────
if [[ -d "${SCRIPT_DIR}/output" ]]; then
    mkdir -p "${REPO_DIR}/data"
    cp "${SCRIPT_DIR}/output/"*.json "${REPO_DIR}/data/" 2>/dev/null || true
    echo "  Copied feeds → ${REPO_DIR}/data/"
fi

# ── Commit & push ───────────────────────────────────────────
if [[ "${DRY_RUN}" == false ]]; then
    echo ""
    echo "[3/4] Committing changes..."

    cd "${REPO_DIR}"
    git config user.email "bot@hermes.local" 2>/dev/null || true
    git config user.name "Hermes RSS Bot"    2>/dev/null || true

    if git diff --quiet; then
        echo "  No changes — skipping commit."
    else
        git add -A
        git commit -m "${COMMIT_MSG}"
        echo "  Committed!"
        echo ""
        echo "[4/4] Pushing to GitHub..."
        git push origin "${GITHUB_BRANCH}"
        echo "  ✅ Done! → https://github.com/${GITHUB_REPO}"
    fi
else
    echo "  Skipped (dry-run)"
fi

echo ""
echo "=== Sync complete ==="