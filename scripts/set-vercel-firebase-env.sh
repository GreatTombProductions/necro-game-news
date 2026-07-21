#!/usr/bin/env bash
# Set Firebase credential env vars on the necrotic-realms Vercel project.
# Run from: 0th-floor-exterior/east-mausoleum/necro-game-news/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")/frontend"
SERVICE_ACCOUNT="$HOME/.config/greattomb/firebase-service-account.json"

if [ ! -f "$SERVICE_ACCOUNT" ]; then
    echo "ERROR: Service account file not found at $SERVICE_ACCOUNT"
    exit 1
fi

echo "=== Reading Firebase credentials ==="
FIREBASE_PROJECT_ID=$(python3 -c "import json; print(json.load(open('$SERVICE_ACCOUNT'))['project_id'])")
FIREBASE_CLIENT_EMAIL=$(python3 -c "import json; print(json.load(open('$SERVICE_ACCOUNT'))['client_email'])")
FIREBASE_PRIVATE_KEY=$(python3 -c "import json; print(json.load(open('$SERVICE_ACCOUNT'))['private_key'])")

echo "  FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID"
echo "  FIREBASE_CLIENT_EMAIL=$FIREBASE_CLIENT_EMAIL"
echo "  FIREBASE_PRIVATE_KEY=*** (${#FIREBASE_PRIVATE_KEY} chars)"

cd "$PROJECT_DIR"

# Ensure project is linked
npx vercel link --project necrotic-realms --yes 2>&1 || true

echo ""
echo "=== Setting Vercel environment variables ==="

# Set each env var for all environments (production, preview, development)
for env in production preview development; do
    echo "--- $env ---"
    echo "$FIREBASE_PROJECT_ID" | npx vercel env add FIREBASE_PROJECT_ID "$env" --force 2>&1
    echo "$FIREBASE_CLIENT_EMAIL" | npx vercel env add FIREBASE_CLIENT_EMAIL "$env" --force 2>&1
    echo "$FIREBASE_PRIVATE_KEY" | npx vercel env add FIREBASE_PRIVATE_KEY "$env" --force 2>&1
done

echo ""
echo "=== Removing Discord webhook env var ==="
npx vercel env rm DISCORD_WEBHOOK_URL production --yes 2>&1 || true
npx vercel env rm DISCORD_WEBHOOK_URL preview --yes 2>&1 || true
npx vercel env rm DISCORD_WEBHOOK_URL development --yes 2>&1 || true

echo ""
echo "=== Deploying to Vercel (production) ==="
npx vercel --prod --yes 2>&1

echo ""
echo "=== Done! Testing endpoint... ==="
sleep 3
curl -s -X POST https://necroticrealms.com/api/submit \
  -H "Content-Type: application/json" \
  -d '{"gameName":"Test - Slimeko Fix Verification","steamId":"","submissionType":"addition","submitterType":"player","availability":"unknown","centrality":"d","pov":"unit","naming":"implied","vampirism":"","hemomancy":"","notes":"Testing after Firebase env var fix.","contact":"","registry":"necromancy"}' 2>&1

echo ""
echo "=== Verifying submission in Firestore ==="
cd "$(dirname "$SCRIPT_DIR")"
python3 scripts/submission_pickup.py 2>&1
