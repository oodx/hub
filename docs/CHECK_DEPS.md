# Dependency Change Detection & Versioning

The `bin/check-deps.sh` script monitors Cargo.toml dependencies and triggers semantic version bumps when breaking changes are detected.

## How It Works

1. **Baseline Checksum**: Stores SHA256 hash of `[dependencies]` section in `.cargo-deps-checksum`
2. **Change Detection**: Compares current hash against stored baseline
3. **Version Analysis**: Parses dependency versions to detect major version bumps
4. **Breaking Changes**: Major version increases (e.g., `1.x.x` → `2.0.0`) are considered breaking
5. **Semver Integration**: Prompts to bump hub's major version via `semv` when breaking changes detected

## Usage

### Basic Check
```bash
# Check dependencies and update baseline
bin/check-deps.sh
```

### Dry Run
```bash
# See what would happen without making changes
bin/check-deps.sh --dry-run
```

### Force Recheck
```bash
# Force check even if checksum unchanged
bin/check-deps.sh --force
```

## Workflow Integration

### Pre-Commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Check if Cargo.toml changed
if git diff --cached --name-only | grep -q "^Cargo.toml$"; then
    echo "Cargo.toml changed - checking dependencies..."
    bin/check-deps.sh --dry-run
fi
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Check dependency changes
  run: bin/check-deps.sh --dry-run
```

### Manual Workflow
```bash
# After updating dependencies
cargo update
bin/check-deps.sh

# Review breaking changes
# If prompted, confirm major version bump
```

## Breaking Change Detection

### What Triggers Breaking Changes

**Major version bumps** (considered breaking):
```toml
# Before
serde = { version = "1.0.226", ... }

# After
serde = { version = "2.0.0", ... }
```

**Not considered breaking**:
- Minor bumps: `1.0.x` → `1.1.0`
- Patch bumps: `1.0.1` → `1.0.2`
- New dependencies added
- Dependencies removed

### Example Output

```
⚠ Dependencies have changed!
✗ Breaking dependency changes detected!

Breaking changes:
  - serde: 1.0.226 → 2.0.0
  - tokio: 1.41.0 → 2.0.0

ℹ Current hub version: 0.3.0
Trigger major version bump? [y/N]
```

## Semver Integration

When breaking changes detected, the script:

1. **Creates commit** with `breaking:` label:
   ```
   breaking: update dependencies with breaking changes

   serde: 1.0.226 → 2.0.0
   tokio: 1.41.0 → 2.0.0

   Automated bump via check-deps.sh
   ```

2. **Calls semv**: `semv bump --force`
   - Reads commit label `breaking:`
   - Bumps major version: `0.3.0` → `1.0.0`
   - Creates git tag
   - Pushes to remote

3. **Updates checksum**: Stores new baseline for future checks

## Configuration

### Checksum File
- **Location**: `.cargo-deps-checksum` (git-ignored)
- **Format**: SHA256 hash of dependencies section
- **Purpose**: Detect when dependencies change

### Version Detection
The script parses both formats:
```toml
# Inline version
serde = "1.0.226"

# Table format
serde = { version = "1.0.226", features = ["derive"] }
```

## Automation Tips

### Automatic on Cargo.toml Changes
```bash
# Add to .bashrc or .zshrc
alias cargo-save='git add Cargo.toml && bin/check-deps.sh && git commit'
```

### Watch for Changes
```bash
# Using inotifywait (Linux)
while inotifywait -e modify Cargo.toml; do
    bin/check-deps.sh
done
```

### Pre-Release Checklist
```bash
# Before release
cargo update           # Update dependencies
bin/check-deps.sh      # Check for breaking changes
cargo test --all       # Verify tests pass
semv audit            # Review version state
```

## Troubleshooting

### Script doesn't detect changes
```bash
# Force recheck
bin/check-deps.sh --force

# Or delete checksum and re-baseline
rm .cargo-deps-checksum
bin/check-deps.sh
```

### False positives
The script only checks major version bumps. If you need custom logic:
1. Edit `is_breaking_change()` function
2. Adjust major version comparison logic

### semv not found
Install semv or manually bump versions:
```bash
# Manual bump
semv set rust 1.0.0  # Or edit Cargo.toml
git tag v1.0.0
git push --tags
```

## Best Practices

1. **Run before committing**: Check deps after updating Cargo.toml
2. **Review carefully**: Breaking changes affect downstream consumers
3. **Document in CHANGELOG**: Note breaking dependency updates
4. **Coordinate with team**: Major bumps may require migration guides
5. **Test thoroughly**: Breaking deps may have API changes

## Integration with Hub Strategy

Hub coordinates dependencies across the ecosystem. Breaking changes in hub affect all consumers:

```
hub 0.3.0 → 1.0.0 (breaking dep: serde 2.0)
    ↓
prontodb 0.7.0 → 1.0.0 (must update)
meteor 0.1.1 → 0.2.0 (must update)
...
```

**Recommendation**: Use `blade eco` to update entire ecosystem after hub major bump.

## See Also

- `semv --help` - Semantic version management
- `blade hub` - Hub dependency dashboard
- `FEATURE_FORWARDING.md` - Hub feature pattern
- `HUB_STRAT.md` - Centralized dependency strategy