#!/bin/bash
set -e

# Configuration
HUB_BIN_DIR="$HOME/.local/bin/odx/hub"

# Resolve repository root from bin/
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Extract version from Cargo.toml at repo root for display
VERSION=$(grep '^version' "$ROOT_DIR/Cargo.toml" | head -1 | cut -d'"' -f2 2>/dev/null || echo "unknown")

# Display deployment ceremony
echo "╔════════════════════════════════════════════════╗"
echo "║           HUB TOOLS DEPLOYMENT                 ║"
echo "╠════════════════════════════════════════════════╣"
echo "║ Package: Hub Ecosystem Analysis Tools          ║"
echo "║ Version: v$VERSION                             ║"
echo "║ Target:  $HUB_BIN_DIR/xrepos                   ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Deploy Hub xrepos tool
echo "🔧 Deploying Hub xrepos tool..."
mkdir -p "$HUB_BIN_DIR"

XREPOS_SOURCE="$ROOT_DIR/bin/repos.py"
XREPOS_TARGET="$HUB_BIN_DIR/xrepos"

if [ -f "$XREPOS_SOURCE" ]; then
    if ! cp "$XREPOS_SOURCE" "$XREPOS_TARGET"; then
        echo "❌ Failed to copy xrepos to $XREPOS_TARGET"
        exit 1
    fi

    if ! chmod +x "$XREPOS_TARGET"; then
        echo "❌ Failed to make xrepos executable"
        exit 1
    fi

    echo "✅ Hub xrepos tool deployed to $XREPOS_TARGET"

    # Test the deployment
    echo "🧪 Testing xrepos deployment..."
    if command -v xrepos >/dev/null 2>&1; then
        echo "✅ xrepos is available in PATH"
    else
        echo "⚠️  Warning: xrepos not found in PATH (may need to restart shell)"
    fi
else
    echo "❌ Error: repos.py not found at $XREPOS_SOURCE"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║          DEPLOYMENT SUCCESSFUL!                ║"
echo "╚════════════════════════════════════════════════╝"
echo "  Deployed: Hub Tools v$VERSION                  "
echo "  Location: $XREPOS_TARGET                       "
echo ""
echo "🔧 Hub ecosystem analysis commands:"
echo "   xrepos hub                  # Hub package status with safety analysis"
echo "   xrepos conflicts            # Version conflicts across ecosystem"
echo "   xrepos review               # Comprehensive dependency review"
echo "   xrepos query                # Usage analysis by priority"
echo "   xrepos outdated             # Find outdated packages"
echo ""
echo "🚀 Ready to analyze your Rust ecosystem!"