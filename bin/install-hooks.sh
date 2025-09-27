#!/usr/bin/env bash
# install-hooks.sh - Install git hooks for hub
#
# Installs pre-commit hook that checks dependencies when Cargo.toml changes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}✓${NC} $*"
}

log_info() {
    echo -e "${YELLOW}➜${NC} $*"
}

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOFHOOK'
#!/usr/bin/env bash
# Hub pre-commit hook - Check dependencies when Cargo.toml changes

# Check if Cargo.toml is staged
if git diff --cached --name-only | grep -q "^Cargo.toml$"; then
    echo "⚡ Cargo.toml changed - checking dependencies..."

    # Run dependency check
    if ! bin/check-deps.sh --dry-run; then
        echo ""
        echo "❌ Dependency check failed!"
        echo "Run 'bin/check-deps.sh' manually to review changes"
        exit 1
    fi

    echo "✓ Dependency check passed"
fi

exit 0
EOFHOOK

chmod +x "$HOOKS_DIR/pre-commit"

log_success "Installed pre-commit hook"
log_info "Hook will run 'bin/check-deps.sh --dry-run' when Cargo.toml changes"
log_info "To bypass: git commit --no-verify"

echo ""
echo "Installed hooks:"
echo "  • pre-commit: Dependency change detection"