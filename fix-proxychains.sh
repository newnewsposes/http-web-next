#!/bin/bash
# Configure proxychains to exclude localhost connections

set -e

echo "🔧 Proxychains Localhost Exclusion Setup"
echo "========================================="

# Find proxychains config
PROXY_CONF="/etc/proxychains4.conf"
if [ ! -f "$PROXY_CONF" ]; then
    PROXY_CONF="/etc/proxychains.conf"
fi

if [ ! -f "$PROXY_CONF" ]; then
    echo "❌ Proxychains config not found at $PROXY_CONF"
    exit 1
fi

echo "Found config: $PROXY_CONF"

# Check if localnet exclusion exists
if grep -q "^localnet 127.0.0.0/255.0.0.0" "$PROXY_CONF"; then
    echo "✅ Localhost exclusion already configured"
    exit 0
fi

echo ""
echo "Adding localhost exclusion to proxychains config..."

# Backup original config
sudo cp "$PROXY_CONF" "${PROXY_CONF}.backup"
echo "✅ Backup created: ${PROXY_CONF}.backup"

# Add localnet exclusion before [ProxyList] section
sudo sed -i '/^\[ProxyList\]/i # Exclude localhost from proxying\nlocalnet 127.0.0.0/255.0.0.0\n' "$PROXY_CONF"

echo "✅ Localhost exclusion added to $PROXY_CONF"
echo ""
echo "Configuration added:"
echo "  localnet 127.0.0.0/255.0.0.0"
echo ""
echo "This ensures PostgreSQL and other localhost services bypass the proxy."
