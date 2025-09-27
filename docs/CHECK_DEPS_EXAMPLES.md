# check-deps.sh Examples

## Example Output Scenarios

### Scenario 1: Breaking Changes with Multiple Updates

**Command**: `bin/check-deps.sh`

**Console Output**:
```
ℹ Checking Cargo.toml dependencies...
⚠ Dependencies have changed!
  ⚠ Breaking: serde 1.0.226 → 2.0.0
  ⚠ Breaking: tokio 1.41.0 → 2.0.0
  ℹ Minor: regex 1.11.2 → 1.12.0
  ℹ Patch: base64 0.22.1 → 0.22.2
  ℹ New: once_cell 1.20.0
  ℹ Removed: lazy_static 1.5.0

✗ Breaking dependency changes detected!

Breaking Changes:
  - serde: 1.0.226 → 2.0.0
  - tokio: 1.41.0 → 2.0.0

Minor Updates:
  - regex: 1.11.2 → 1.12.0

Patch Updates:
  - base64: 0.22.1 → 0.22.2

New Packages:
  - once_cell: 1.20.0

Removed Packages:
  - lazy_static: 1.5.0

Automated dependency analysis via check-deps.sh

ℹ Current hub version: 0.3.0
Trigger major version bump? [y/N] y
ℹ Creating commit with detailed changes...
ℹ Running: semv bump --force
✓ Version bumped!
```

**Generated Commit**:
```
commit abc123...
Author: Developer <dev@example.com>

    breaking: update dependencies with breaking changes

    Breaking Changes:
      - serde: 1.0.226 → 2.0.0
      - tokio: 1.41.0 → 2.0.0

    Minor Updates:
      - regex: 1.11.2 → 1.12.0

    Patch Updates:
      - base64: 0.22.1 → 0.22.2

    New Packages:
      - once_cell: 1.20.0

    Removed Packages:
      - lazy_static: 1.5.0

    Automated dependency analysis via check-deps.sh
```

**Result**:
- semv reads `breaking:` label → Major bump
- Hub version: `0.3.0` → `1.0.0`
- Tag created: `v1.0.0`

---

### Scenario 2: Only Minor/Patch Updates (Safe)

**Command**: `bin/check-deps.sh`

**Console Output**:
```
ℹ Checking Cargo.toml dependencies...
⚠ Dependencies have changed!
  ℹ Minor: regex 1.11.2 → 1.12.0
  ℹ Patch: serde 1.0.226 → 1.0.228
  ℹ Patch: chrono 0.4.42 → 0.4.43

✓ No breaking changes detected
ℹ Summary of changes:

Minor Updates:
  - regex: 1.11.2 → 1.12.0

Patch Updates:
  - serde: 1.0.226 → 1.0.228
  - chrono: 0.4.42 → 0.4.43

Automated dependency analysis via check-deps.sh

✓ Checksum updated
```

**No automatic version bump** (safe changes)

**Suggested manual commit**:
```bash
git add Cargo.toml
git commit -m "update: dependency patches and minor updates

Minor Updates:
  - regex: 1.11.2 → 1.12.0

Patch Updates:
  - serde: 1.0.226 → 1.0.228
  - chrono: 0.4.42 → 0.4.43"
```

---

### Scenario 3: Adding New Packages

**Console Output**:
```
ℹ Checking Cargo.toml dependencies...
⚠ Dependencies have changed!
  ℹ New: once_cell 1.20.0
  ℹ New: tracing 0.1.40

✓ No breaking changes detected
ℹ Summary of changes:

New Packages:
  - once_cell: 1.20.0
  - tracing: 0.1.40

Automated dependency analysis via check-deps.sh
```

**Suggested commit**:
```bash
git commit -m "feat: add once_cell and tracing dependencies

New Packages:
  - once_cell: 1.20.0
  - tracing: 0.1.40"
```

---

### Scenario 4: Dry Run Mode

**Command**: `bin/check-deps.sh --dry-run`

**Console Output**:
```
ℹ Checking Cargo.toml dependencies...
⚠ Dependencies have changed!
  ⚠ Breaking: serde 1.0.226 → 2.0.0

✗ Breaking dependency changes detected!

Breaking Changes:
  - serde: 1.0.226 → 2.0.0

Automated dependency analysis via check-deps.sh

ℹ Current hub version: 0.3.0
ℹ [DRY-RUN] Would prompt for major version bump
ℹ [DRY-RUN] Commit message would be:

breaking: update dependencies with breaking changes

Breaking Changes:
  - serde: 1.0.226 → 2.0.0

Automated dependency analysis via check-deps.sh

ℹ [DRY-RUN] Would update checksum
```

**Nothing modified** - preview only

---

### Scenario 5: Pre-Commit Hook Trigger

**Workflow**:
```bash
# Edit Cargo.toml
vim Cargo.toml  # Change serde = "2.0.0"

# Stage changes
git add Cargo.toml

# Commit
git commit -m "update: upgrade serde"
```

**Hook Output**:
```
⚡ Cargo.toml changed - checking dependencies...
ℹ Checking Cargo.toml dependencies...
⚠ Dependencies have changed!
  ⚠ Breaking: serde 1.0.226 → 2.0.0

✗ Breaking dependency changes detected!

Breaking Changes:
  - serde: 1.0.226 → 2.0.0

Automated dependency analysis via check-deps.sh

ℹ [DRY-RUN] Would prompt for major version bump
✓ Dependency check passed
[main abc123] update: upgrade serde
 1 file changed, 1 insertion(+), 1 deletion(-)
```

**After commit**:
```bash
# Review and trigger version bump
bin/check-deps.sh
# Prompts for major version bump
```

---

### Scenario 6: Removing Deprecated Dependencies

**Console Output**:
```
ℹ Checking Cargo.toml dependencies...
⚠ Dependencies have changed!
  ℹ Removed: lazy_static 1.5.0
  ℹ New: once_cell 1.20.0

✓ No breaking changes detected
ℹ Summary of changes:

New Packages:
  - once_cell: 1.20.0

Removed Packages:
  - lazy_static: 1.5.0

Automated dependency analysis via check-deps.sh
```

**Suggested commit**:
```bash
git commit -m "refactor: replace lazy_static with once_cell

New Packages:
  - once_cell: 1.20.0

Removed Packages:
  - lazy_static: 1.5.0"
```

---

## Commit Message Format

The script automatically generates structured commit messages:

### With Breaking Changes
```
breaking: update dependencies with breaking changes

Breaking Changes:
  - package1: old → new
  - package2: old → new

[Minor Updates:]
  - package3: old → new

[Patch Updates:]
  - package4: old → new

[New Packages:]
  - package5: version

[Removed Packages:]
  - package6: version

Automated dependency analysis via check-deps.sh
```

### Without Breaking Changes
```
update: dependency updates

Minor Updates:
  - package1: old → new

Patch Updates:
  - package2: old → new

Automated dependency analysis via check-deps.sh
```

## Integration with semv

The script uses semv commit labels:

- `breaking:` → Major bump (`0.3.0` → `1.0.0`)
- `feat:` → Minor bump (`0.3.0` → `0.4.0`)
- `fix:` → Patch bump (`0.3.0` → `0.3.1`)

**Automatic labeling**:
- Breaking changes → `breaking:` label
- Other changes → Manual commit with appropriate label

## Best Practices

### Always Review Breaking Changes
```bash
# Don't blindly accept
bin/check-deps.sh
# Read the changes carefully
# Check migration guides for affected packages
# Test thoroughly before confirming
```

### Use Dry Run First
```bash
bin/check-deps.sh --dry-run  # Preview
bin/check-deps.sh            # Execute
```

### Document Major Bumps
```bash
# After major bump, create migration guide
cat > MIGRATION_1.0.md << 'EOF'
# Migrating to Hub 1.0.0

## Breaking Changes
- serde 2.0: [link to serde migration guide]
- tokio 2.0: [link to tokio migration guide]

## Action Required
All projects using hub must update...
EOF
```