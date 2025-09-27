# Hub Automation & Tooling

Hub includes automation scripts and git hooks to maintain dependency integrity and version consistency.

## Quick Start

```bash
# Install git hooks
bin/install-hooks.sh

# Check dependencies manually
bin/check-deps.sh

# Run with options
bin/check-deps.sh --dry-run   # Preview without changes
bin/check-deps.sh --force     # Force recheck
```

## Automated Dependency Checking

### Overview

Hub automatically detects when dependency versions change and triggers semantic version bumps when breaking changes occur.

**Components:**
1. **`bin/check-deps.sh`** - Dependency analysis script
2. **`.git/hooks/pre-commit`** - Git hook for automatic checks
3. **`.cargo-deps-checksum`** - Baseline checksum file (git-ignored)

### How It Works

```
Cargo.toml modified
    ↓
git add Cargo.toml
    ↓
git commit  ← Pre-commit hook triggers
    ↓
bin/check-deps.sh --dry-run runs
    ↓
Detects major version bumps (e.g., serde 1.x → 2.0)
    ↓
Shows warning, passes commit
    ↓
Manually run: bin/check-deps.sh
    ↓
Prompts to bump hub's major version
    ↓
Creates commit with breaking: label
    ↓
Runs: semv bump --force
    ↓
Hub version bumped (0.3.0 → 1.0.0)
```

### Workflow Example

```bash
# 1. Update dependencies
vim Cargo.toml  # Update serde = "2.0.0"

# 2. Stage changes
git add Cargo.toml

# 3. Commit (pre-commit hook runs)
git commit -m "update: upgrade serde to 2.0"
# Output:
# ⚡ Cargo.toml changed - checking dependencies...
# ⚠ Breaking dependency changes detected!
# ✓ Dependency check passed

# 4. Review and trigger version bump
bin/check-deps.sh
# Output:
# ✗ Breaking dependency changes detected!
# Breaking changes:
#   - serde: 1.0.226 → 2.0.0
# Trigger major version bump? [y/N] y

# 5. Hub version automatically bumped and tagged
# 0.3.0 → 1.0.0
```

## Git Hooks

### Installation

```bash
# One-time setup
bin/install-hooks.sh
```

### Installed Hooks

#### Pre-Commit Hook
- **Trigger**: When `Cargo.toml` is staged
- **Action**: Runs `bin/check-deps.sh --dry-run`
- **Purpose**: Early warning about breaking changes
- **Bypass**: `git commit --no-verify` (not recommended)

### Hook Output

**Normal commit (no Cargo.toml changes):**
```bash
git commit -m "fix: typo in docs"
# (no dependency check)
```

**Cargo.toml changed, no breaking changes:**
```bash
git commit -m "update: patch version bumps"
# ⚡ Cargo.toml changed - checking dependencies...
# ℹ Checking Cargo.toml dependencies...
# ✓ No breaking changes detected
# ✓ Dependency check passed
```

**Cargo.toml changed, breaking changes detected:**
```bash
git commit -m "update: major dependency updates"
# ⚡ Cargo.toml changed - checking dependencies...
# ⚠ Dependencies have changed!
# ⚠ Breaking: serde 1.0.226 → 2.0.0
# ✓ Dependency check passed
# [Commit proceeds, manual review needed]
```

## Dependency Check Script

### Commands

```bash
# Basic check
bin/check-deps.sh

# Dry run (no changes)
bin/check-deps.sh --dry-run

# Force recheck
bin/check-deps.sh --force
```

### Detection Logic

**Breaking Changes** (trigger major bump):
```toml
# Major version increase
serde = "1.0.226" → "2.0.0"  ✗ BREAKING
tokio = "1.41.0" → "2.0.0"   ✗ BREAKING
```

**Safe Changes** (no major bump):
```toml
# Minor/patch bumps
serde = "1.0.226" → "1.0.228"  ✓ Safe
tokio = "1.41.0" → "1.42.0"    ✓ Safe

# New dependencies
uuid = "1.18.1"                ✓ Safe

# Removed dependencies
old-dep removed                ✓ Safe
```

### Integration with Semver

When breaking changes detected:

1. **Creates commit** with special label:
   ```
   breaking: update dependencies with breaking changes

   serde: 1.0.226 → 2.0.0

   Automated bump via check-deps.sh
   ```

2. **Triggers semv**:
   ```bash
   semv bump --force
   # Reads "breaking:" label → Major bump
   # 0.3.0 → 1.0.0
   ```

3. **Updates ecosystem**:
   ```bash
   # After hub major bump, update consumers
   blade eco --dry-run
   blade eco --force-commit
   ```

## Automation Best Practices

### 1. Regular Checks
```bash
# Weekly dependency review
cargo update
bin/check-deps.sh
cargo test --all
```

### 2. Pre-Release Workflow
```bash
# Before releasing hub version
bin/check-deps.sh            # Check deps
cargo clippy --all           # Lint
cargo test --all             # Test
bin/validate-docs.sh         # Validate docs
semv audit                   # Review version
```

### 3. CI/CD Integration
```yaml
# .github/workflows/deps.yml
name: Dependency Check
on:
  pull_request:
    paths:
      - 'Cargo.toml'

jobs:
  check-deps:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check dependencies
        run: bin/check-deps.sh --dry-run
```

### 4. Team Coordination
```bash
# When hub major version bumps
# 1. Notify team
echo "Hub 1.0.0 released with breaking changes"

# 2. Update all consumers
blade eco --dry-run
blade eco --force-commit

# 3. Document migration
cat > MIGRATION_1.0.md << 'EOF'
# Migrating to Hub 1.0.0

Breaking changes:
- serde 2.0 (see serde migration guide)
- ...
EOF
```

## Disabling Automation

### Temporary Disable

```bash
# Skip pre-commit hook once
git commit --no-verify

# Skip dependency check
git add Cargo.toml
git commit -m "wip: testing" --no-verify
```

### Permanent Disable

```bash
# Remove pre-commit hook
rm .git/hooks/pre-commit

# Or keep hook but disable check
# Edit .git/hooks/pre-commit:
# Comment out: bin/check-deps.sh --dry-run
```

## Troubleshooting

### Hook not running
```bash
# Reinstall hooks
bin/install-hooks.sh

# Verify hook is executable
ls -l .git/hooks/pre-commit
```

### False positives
```bash
# Clear checksum and re-baseline
rm .cargo-deps-checksum
bin/check-deps.sh
```

### semv not found
```bash
# Install semv
# (see semv installation docs)

# Or manually bump versions
vim Cargo.toml  # Update version
git tag v1.0.0
git push --tags
```

## See Also

- **`CHECK_DEPS.md`** - Detailed dependency check documentation
- **`FEATURE_FORWARDING.md`** - Hub feature patterns
- **`HUB_STRAT.md`** - Centralized dependency strategy
- **`semv --help`** - Semantic version management