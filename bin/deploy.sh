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
echo "║ Target:  $HUB_BIN_DIR/                         ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Deploy Hub tools
echo "🔧 Deploying Hub tools..."
mkdir -p "$HUB_BIN_DIR"

REPOS_SOURCE="$ROOT_DIR/bin/repos.py"
XREPOS_TARGET="$HUB_BIN_DIR/xrepos"
BLADE_TARGET="$HUB_BIN_DIR/blade"

if [ -f "$REPOS_SOURCE" ]; then
    # Deploy as xrepos (legacy hub integration)
    if ! cp "$REPOS_SOURCE" "$XREPOS_TARGET"; then
        echo "❌ Failed to copy xrepos to $XREPOS_TARGET"
        exit 1
    fi

    if ! chmod +x "$XREPOS_TARGET"; then
        echo "❌ Failed to make xrepos executable"
        exit 1
    fi

    echo "✅ Hub xrepos tool deployed to $XREPOS_TARGET"

    # Deploy as blade (standalone tool)
    if ! cp "$REPOS_SOURCE" "$BLADE_TARGET"; then
        echo "❌ Failed to copy blade to $BLADE_TARGET"
        exit 1
    fi

    if ! chmod +x "$BLADE_TARGET"; then
        echo "❌ Failed to make blade executable"
        exit 1
    fi

    echo "✅ Blade tool deployed to $BLADE_TARGET"

    # Test the deployments
    echo "🧪 Testing deployments..."
    if command -v xrepos >/dev/null 2>&1; then
        echo "✅ xrepos is available in PATH"
    else
        echo "⚠️  Warning: xrepos not found in PATH (may need to restart shell)"
    fi

    if command -v blade >/dev/null 2>&1; then
        echo "✅ blade is available in PATH"
    else
        echo "⚠️  Warning: blade not found in PATH (may need to restart shell)"
    fi
else
    echo "❌ Error: repos.py not found at $REPOS_SOURCE"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║          DEPLOYMENT SUCCESSFUL!                ║"
echo "╚════════════════════════════════════════════════╝"
echo "  Deployed: Hub Tools v$VERSION                  "
echo "  xrepos:   $XREPOS_TARGET                       "
echo "  blade:    $BLADE_TARGET                        "
echo ""
echo "🔧 Hub ecosystem analysis commands (xrepos):"
echo "   xrepos hub                  # Hub package status with safety analysis"
echo "   xrepos conflicts            # Version conflicts across ecosystem"
echo "   xrepos review               # Comprehensive dependency review"
echo "   xrepos query                # Usage analysis by priority"
echo "   xrepos outdated             # Find outdated packages"
echo ""
echo "⚔️  Blade dependency management commands:"
echo "   blade update <repo>         # Update specific repository dependencies"
echo "   blade eco                   # Update entire ecosystem"
echo "   blade conflicts             # Analyze dependency conflicts"
echo "   blade --help                # Full command reference"
echo ""
echo "🚀 Ready to analyze your Rust ecosystem!"