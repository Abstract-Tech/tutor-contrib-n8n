#!/bin/sh
set -e

N8N_URL="http://n8n:{{ N8N_PORT }}"

echo "Waiting for n8n to be reachable at $N8N_URL..."
for i in $(seq 1 30); do
  if wget -qO- "$N8N_URL/rest/settings" >/tmp/n8n-settings.json 2>/dev/null; then
    break
  fi
  sleep 2
done

if ! grep -q '"showSetupOnFirstLoad":true' /tmp/n8n-settings.json; then
  echo "n8n owner account already set up, skipping."
  exit 0
fi

echo "Creating n8n owner account {{ N8N_ADMIN_EMAIL }}..."
wget -qO- \
  --header="Content-Type: application/json" \
  --post-data='{"email":"{{ N8N_ADMIN_EMAIL }}","firstName":"{{ N8N_ADMIN_FIRST_NAME }}","lastName":"{{ N8N_ADMIN_LAST_NAME }}","password":"{{ N8N_ADMIN_PASSWORD }}"}' \
  "$N8N_URL/rest/owner/setup" >/dev/null

echo "n8n owner account created."
