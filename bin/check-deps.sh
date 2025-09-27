#!/usr/bin/env bash
# check-deps.sh - Monitor Cargo.toml dependencies and trigger semver bumps
#
# This script:
# 1. Maintains a checksum of Cargo.toml dependencies
# 2. Detects when dependency versions change
# 3. Analyzes if changes are breaking (major version bumps)
# 4. Triggers semv major bump if breaking changes detected
#
# Usage:
#   bin/check-deps.sh         # Check and update if needed
#   bin/check-deps.sh --force # Force recheck
#   bin/check-deps.sh --dry-run # Show what would happen

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CARGO_TOML="$PROJECT_ROOT/Cargo.toml"
CHECKSUM_FILE="$PROJECT_ROOT/.cargo-deps-checksum"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

DRY_RUN=false
FORCE=false

# Parse args
for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --force) FORCE=true ;;
        -h|--help)
            echo "Usage: $0 [--dry-run] [--force]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would happen without making changes"
            echo "  --force      Force recheck even if checksum hasn't changed"
            exit 0
            ;;
    esac
done

log_info() {
    echo -e "${BLUE}ℹ ${NC}$*"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*"
}

log_error() {
    echo -e "${RED}✗${NC} $*" >&2
}

# Extract dependencies section from Cargo.toml (just the [dependencies] block)
extract_deps() {
    awk '/^\[dependencies\]/,/^\[/' "$CARGO_TOML" | grep -E "^[a-z].*=" || true
}

# Calculate checksum of dependencies
calc_checksum() {
    extract_deps | sha256sum | cut -d' ' -f1
}

# Parse version from dependency line
parse_version() {
    local dep_line="$1"
    # Handle: serde = { version = "1.0.226", ... }
    # or:     serde = "1.0.226"
    echo "$dep_line" | grep -oP 'version\s*=\s*"\K[^"]+' || \
    echo "$dep_line" | grep -oP '=\s*"\K[^"]+' || echo ""
}

# Get major version number
major_version() {
    local ver="$1"
    echo "$ver" | cut -d. -f1
}

# Compare two dependency versions
is_breaking_change() {
    local old_ver="$1"
    local new_ver="$2"

    # Extract major version
    local old_major=$(major_version "$old_ver")
    local new_major=$(major_version "$new_ver")

    # If major version increased, it's breaking
    if [[ "$new_major" -gt "$old_major" ]]; then
        return 0  # true
    fi

    return 1  # false
}

# Main logic
main() {
    cd "$PROJECT_ROOT"

    log_info "Checking Cargo.toml dependencies..."

    # Calculate current checksum
    current_checksum=$(calc_checksum)

    # Read previous checksum if exists
    if [[ -f "$CHECKSUM_FILE" ]]; then
        previous_checksum=$(cat "$CHECKSUM_FILE")
    else
        previous_checksum=""
        log_warning "No previous checksum found - initializing"
    fi

    # Check if changed
    if [[ "$current_checksum" == "$previous_checksum" ]] && [[ "$FORCE" != "true" ]]; then
        log_success "Dependencies unchanged"
        exit 0
    fi

    if [[ -z "$previous_checksum" ]]; then
        log_info "First run - storing baseline checksum"
        if [[ "$DRY_RUN" != "true" ]]; then
            echo "$current_checksum" > "$CHECKSUM_FILE"
            log_success "Baseline stored"
        else
            log_info "[DRY-RUN] Would store baseline checksum"
        fi
        exit 0
    fi

    log_warning "Dependencies have changed!"

    # Extract old and new deps
    old_deps=$(git show "HEAD:Cargo.toml" 2>/dev/null | awk '/^\[dependencies\]/,/^\[/' | grep -E "^[a-z].*=" || true)
    new_deps=$(extract_deps)

    breaking_changes=()
    minor_changes=()
    patch_changes=()
    new_packages=()
    removed_packages=()

    # Compare versions
    while IFS= read -r new_line; do
        [[ -z "$new_line" ]] && continue
        pkg_name=$(echo "$new_line" | cut -d= -f1 | tr -d ' ')
        new_ver=$(parse_version "$new_line")

        # Find matching old line
        old_line=$(echo "$old_deps" | grep "^$pkg_name\s*=" || true)

        if [[ -n "$old_line" ]] && [[ -n "$new_ver" ]]; then
            old_ver=$(parse_version "$old_line")

            if [[ -n "$old_ver" ]] && [[ "$old_ver" != "$new_ver" ]]; then
                if is_breaking_change "$old_ver" "$new_ver"; then
                    log_warning "  Breaking: $pkg_name $old_ver → $new_ver"
                    breaking_changes+=("$pkg_name: $old_ver → $new_ver")
                else
                    # Check if minor or patch
                    old_minor=$(echo "$old_ver" | cut -d. -f2)
                    new_minor=$(echo "$new_ver" | cut -d. -f2)
                    if [[ "$new_minor" -gt "$old_minor" ]] 2>/dev/null; then
                        log_info "  Minor: $pkg_name $old_ver → $new_ver"
                        minor_changes+=("$pkg_name: $old_ver → $new_ver")
                    else
                        log_info "  Patch: $pkg_name $old_ver → $new_ver"
                        patch_changes+=("$pkg_name: $old_ver → $new_ver")
                    fi
                fi
            fi
        elif [[ -n "$new_ver" ]]; then
            log_info "  New: $pkg_name $new_ver"
            new_packages+=("$pkg_name: $new_ver")
        fi
    done <<< "$new_deps"

    # Check for removed packages
    while IFS= read -r old_line; do
        [[ -z "$old_line" ]] && continue
        pkg_name=$(echo "$old_line" | cut -d= -f1 | tr -d ' ')
        old_ver=$(parse_version "$old_line")

        # Check if still exists
        if ! echo "$new_deps" | grep -q "^$pkg_name\s*="; then
            log_info "  Removed: $pkg_name $old_ver"
            removed_packages+=("$pkg_name: $old_ver")
        fi
    done <<< "$old_deps"

    # Build commit message with all changes
    total_changes=$((${#breaking_changes[@]} + ${#minor_changes[@]} + ${#patch_changes[@]} + ${#new_packages[@]} + ${#removed_packages[@]}))

    if [[ $total_changes -eq 0 ]]; then
        log_success "No changes detected"
        if [[ "$DRY_RUN" != "true" ]]; then
            echo "$current_checksum" > "$CHECKSUM_FILE"
        fi
        exit 0
    fi

    # Build commit message body
    commit_body=""

    if [[ ${#breaking_changes[@]} -gt 0 ]]; then
        commit_body+="Breaking Changes:\n"
        for change in "${breaking_changes[@]}"; do
            commit_body+="  - $change\n"
        done
        commit_body+="\n"
    fi

    if [[ ${#minor_changes[@]} -gt 0 ]]; then
        commit_body+="Minor Updates:\n"
        for change in "${minor_changes[@]}"; do
            commit_body+="  - $change\n"
        done
        commit_body+="\n"
    fi

    if [[ ${#patch_changes[@]} -gt 0 ]]; then
        commit_body+="Patch Updates:\n"
        for change in "${patch_changes[@]}"; do
            commit_body+="  - $change\n"
        done
        commit_body+="\n"
    fi

    if [[ ${#new_packages[@]} -gt 0 ]]; then
        commit_body+="New Packages:\n"
        for change in "${new_packages[@]}"; do
            commit_body+="  - $change\n"
        done
        commit_body+="\n"
    fi

    if [[ ${#removed_packages[@]} -gt 0 ]]; then
        commit_body+="Removed Packages:\n"
        for change in "${removed_packages[@]}"; do
            commit_body+="  - $change\n"
        done
        commit_body+="\n"
    fi

    commit_body+="Automated dependency analysis via check-deps.sh"

    # If breaking changes detected, trigger major bump
    if [[ ${#breaking_changes[@]} -gt 0 ]]; then
        log_error "Breaking dependency changes detected!"
        echo ""
        echo -e "$commit_body"

        if command -v semv &> /dev/null; then
            current_version=$(semv version 2>/dev/null || echo "unknown")
            log_info "Current hub version: $current_version"

            if [[ "$DRY_RUN" != "true" ]]; then
                echo ""
                read -p "Trigger major version bump? [y/N] " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    log_info "Creating commit with detailed changes..."
                    git add Cargo.toml
                    git commit -m "breaking: update dependencies with breaking changes

$(echo -e "$commit_body")" || true

                    log_info "Running: semv bump --force"
                    semv bump --force
                    log_success "Version bumped!"
                else
                    log_info "Skipping version bump"
                fi
            else
                log_info "[DRY-RUN] Would prompt for major version bump"
                log_info "[DRY-RUN] Commit message would be:"
                echo ""
                echo "breaking: update dependencies with breaking changes"
                echo ""
                echo -e "$commit_body"
            fi
        else
            log_warning "semv not found - cannot auto-bump version"
            log_info "Install semv or manually bump version"
            log_info "Suggested commit message:"
            echo ""
            echo "breaking: update dependencies with breaking changes"
            echo ""
            echo -e "$commit_body"
        fi
    else
        log_success "No breaking changes detected"
        log_info "Summary of changes:"
        echo ""
        echo -e "$commit_body"
    fi

    # Update checksum
    if [[ "$DRY_RUN" != "true" ]]; then
        echo "$current_checksum" > "$CHECKSUM_FILE"
        log_success "Checksum updated"
    else
        log_info "[DRY-RUN] Would update checksum"
    fi
}

main "$@"