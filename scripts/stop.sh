#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "⏹ Stopping VeriNews containers..."
docker compose down

echo "✔ VeriNews containers stopped."
