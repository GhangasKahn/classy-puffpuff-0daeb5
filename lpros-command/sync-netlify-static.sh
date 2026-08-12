#!/usr/bin/env bash
# Sync desk UI copies for Netlify (root of lpros-command/) from public/
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd)"
cp "$root/public/index.html" "$root/index.html"
cp "$root/public/app.js" "$root/app.js"
cp "$root/public/styles.css" "$root/styles.css"
cp "$root/public/playground-ui.js" "$root/playground-ui.js"
echo "Synced public/ → lpros-command/ for Netlify static hosting"
