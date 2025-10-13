#!/bin/bash

# ============================================
# Restart the system
# ============================================

echo "🔄 Restarting Crypto Trading Signal System..."

./scripts/stop.sh
sleep 5
./scripts/start.sh