# HOWTO: Hub Integration Guide

## Overview
Hub is a centralized dependency management system for the oodx/RSB ecosystem that uses feature flags to provide modular, conflict-free dependency management with clean namespace separation between internal and external dependencies.

## Namespace Philosophy ⚠️ Major Update in v0.3.0

Hub now enforces **clean namespace separation**:
- **Top-level namespace**: Reserved exclusively for internal oodx/rsb modules
- **External dependencies**: All third-party packages get the `-ext` suffix
- **Philosophy**: The `-ext` suffix means "we don't like these third-party packages but use them if we have to"

### Internal vs External Structure
- **Internal** (top-level): `hub::colors` - our own shared infrastructure
- **External** (with modules): `hub::text_ext`, `hub::data_ext` - third-party dependencies grouped by domain

## Quick Integration

### 1. Add Hub to Your Project

#### Primary Method: GitHub Repository (Recommended)
```toml
# Cargo.toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["regex", "serde"] }
```

#### Secondary Method: Local Path (Emergency/Hot-fixes Only)
⚠️ **Use only when you have urgent local fixes that cannot wait for hub to publish**
```toml
# Cargo.toml - FOR EMERGENCY USE ONLY
hub = { path = "../../hub", features = ["regex", "serde"] }
```

### 2. Update Your Imports
```rust
// External dependencies (third-party)
use regex::Regex;                    // ❌ Before
use hub::regex::Regex;               // ✅ After (top-level re-export)
use hub::text_ext::regex::Regex;     // ✅ After (grouped module)

use serde::{Serialize, Deserialize};         // ❌ Before
use hub::serde::{Serialize, Deserialize};    // ✅ After (top-level re-export)
use hub::data_ext::serde::{Serialize, Deserialize}; // ✅ After (grouped module)

// Internal dependencies (our own infrastructure)
use hub::colors;                     // ✅ Internal oodx/rsb module

// Or use the prelude for common external features
use hub::prelude::*;
```

## Feature Selection Strategy

### Individual Features
Specify exactly what you need:
```toml
features = ["regex", "serde", "chrono", "uuid"]  # Individual external deps
```

### External Domain Groups (Third-party - Use If We Have To)
- **`text-ext`** - Text processing: regex, lazy_static, unicode-width, strip-ansi-escapes
- **`data-ext`** - Serialization: serde, serde_json, base64, serde_yaml (deprecated)
- **`time-ext`** - Date/time: chrono, uuid
- **`web-ext`** - Web utilities: urlencoding
- **`system-ext`** - System access: libc, glob
- **`terminal-ext`** - Terminal tools: portable-pty
- **`random-ext`** - Random generation: rand
- **`async-ext`** - Asynchronous programming: tokio
- **`cli-ext`** - Command line tools: clap, anyhow
- **`error-ext`** - Error handling: anyhow, thiserror
- **`test-ext`** - Testing utilities: criterion, tempfile

### External Convenience Groups
- **`common-ext`** - Most used external: text-ext + data-ext + error-ext
- **`core-ext`** - Essential external: text-ext + data-ext + time-ext + error-ext
- **`extended-ext`** - Comprehensive external: core-ext + web-ext + system-ext + cli-ext
- **`dev-ext`** - Everything external (mega package for testing/development)

### Internal oodx/rsb Groups (Top-level Namespace Reserved)
- **`core`** - Internal core: colors (shared color system)
- **`colors`** - Shared color system from jynx architecture

### The `-ext` Philosophy
The `-ext` suffix on external features embodies our approach to third-party dependencies:
- **Namespace Separation**: Clear distinction between our code and external code
- **Reluctant Usage**: "We don't like these third-party packages but use them if we have to"
- **Controlled Integration**: External dependencies are grouped and managed, not embraced
- **Future-Proofing**: Makes it easy to replace external deps with internal alternatives

### Migration from Legacy Features
Old feature names still work for backward compatibility:
```toml
# Legacy (still works)
features = ["text", "data", "core"]

# New structure (recommended)
features = ["text-ext", "data-ext", "core"]
```

## Hub Inclusion Criteria

### Usage-Based Inclusion
- **3+ projects using a dependency**: Eligible for hub inclusion (manual review)
- **5+ projects using a dependency**: Automatic inclusion by blade tools
- **Semantic versioning propagation**: Hub version updates reflect dependency changes

### Version Management Philosophy
Hub follows strict semantic versioning:
- **Minor version bump**: When any dependency has a minor version change
- **Major version bump**: When any dependency has a major version change
- This ensures downstream projects can trust semantic versioning for updates

## Integration Methods

### When to Use Each Method

#### GitHub Repository (Primary - Recommended)
✅ **Use for all standard development**
- Ensures you get the latest stable version
- Maintained and tested hub distribution
- Consistent with other projects in the ecosystem
- Proper semantic versioning

#### Local Path (Secondary - Emergency Only)
⚠️ **Use only when:**
- You have urgent hot-fixes that cannot wait for hub publishing
- You are actively developing hub features for testing
- You need immediate access to unpublished changes

⚠️ **Warnings for local path usage:**
- May introduce version inconsistencies across projects
- Requires manual coordination with hub updates
- Not suitable for production deployments
- Should be temporary - migrate to GitHub repo when fixes are published

## Integration Examples

### Basic Project Setup with Internal Features
```toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["core", "core-ext"] }
# Gets you:
# - Internal: colors (shared color system)
# - External: text-ext + data-ext + time-ext + error-ext
```

### Web Service Project
```toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["extended-ext", "random-ext"] }
# Gets you: comprehensive external capabilities + random generation
```

### Development Tools Project
```toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["dev-ext"] }
# Gets you: ALL external packages (mega package for testing/development)
```

### Testing/Development Project (Mega Package)
```toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["dev-ext"] }
# The dev-ext mega package includes ALL external dependencies:
# text-ext, data-ext, time-ext, web-ext, system-ext, terminal-ext,
# random-ext, async-ext, cli-ext, error-ext, test-ext
#
# Perfect for:
# - Integration testing across the ecosystem
# - Development environments where you need everything
# - Prototyping without worrying about specific feature selection
# - CI/CD pipelines that run comprehensive tests
```

### Production Service (Selective Features)
```toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["core", "core-ext", "async-ext"] }
# Gets you:
# - Internal: colors (shared oodx/rsb infrastructure)
# - External: essential text/data/time/error handling + async capabilities
# - Clean separation between internal infrastructure and external utilities
```

### CLI Tool Development
```toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["cli-ext", "error-ext", "terminal-ext"] }
# Focused on command-line tools:
# - clap for argument parsing
# - anyhow/thiserror for error handling
# - portable-pty for terminal interaction
```

## Benefits

### For Your Project
✅ **No version conflicts** - All projects use same dependency versions
✅ **Cleaner Cargo.toml** - No external dependency management
✅ **Faster builds** - Cargo deduplicates dependencies efficiently
✅ **Easy upgrades** - Hub manages all version updates centrally

### For the Ecosystem
✅ **Coordinated updates** - Single place to manage all dependency versions
✅ **Security scanning** - Centralized vulnerability management
✅ **Consistency** - Same behavior across all projects
✅ **Reduced bloat** - Only include features you actually need

## Migration Checklist

### For New Projects
1. **Add hub dependency** using GitHub repo with new feature naming:
   ```toml
   hub = { git = "https://github.com/oodx/hub.git", features = ["core-ext"] }
   ```
2. **Use grouped imports** for clarity:
   ```rust
   use hub::data_ext::serde::{Serialize, Deserialize};
   use hub::text_ext::regex::Regex;
   ```
3. **Access internal features** directly:
   ```rust
   use hub::colors;
   ```

### For Existing Projects
1. **Remove direct dependencies** from your Cargo.toml
2. **Update feature names** to new `-ext` format:
   ```toml
   # Old
   features = ["text", "data", "core"]
   # New (recommended)
   features = ["text-ext", "data-ext", "core"]
   ```
3. **Choose import style** - both work:
   ```rust
   // Top-level re-exports (backward compatible)
   use hub::regex::Regex;

   // Grouped modules (clearer intent)
   use hub::text_ext::regex::Regex;
   ```
4. **Test compilation** with `cargo check`
5. **Run tests** to ensure compatibility
6. **Update documentation** to reflect new structure
7. **Avoid local paths** unless you have urgent hot-fixes that cannot wait for publishing

### Breaking Changes in v0.3.0
- Legacy feature names still work but new `-ext` naming is recommended
- New module structure available (`hub::text_ext`, etc.) alongside existing re-exports
- No breaking changes to existing import patterns

## Important Notes

### YAML Deprecation Warning ⚠️
The `serde_yaml` feature is **deprecated** as of hub v0.3.0:
```rust
// This will show deprecation warnings
use hub::data_ext::serde_yaml;
```

**Migration Path:**
- **Configuration files**: Use TOML instead
- **Data exchange**: Use JSON instead
- **Rust-native serialization**: Use RON instead

This feature will be removed in a future version. Update your projects to use modern alternatives.

## Common Patterns

### Internal Features (oodx/rsb Infrastructure)
```rust
// Use internal shared infrastructure
use hub::colors;

// Access through top-level namespace (reserved for our code)
fn setup_colors() {
    // Internal oodx/rsb color system
}
```

### External Features - Top-level Re-exports
```rust
// Direct access to external dependencies
use hub::thiserror::Error;
use hub::serde::{Serialize, Deserialize};
use hub::regex::Regex;

#[derive(Error, Debug)]
pub enum MyError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}
```

### External Features - Grouped Module Access
```rust
// Access through domain-specific modules (preferred for clarity)
use hub::error_ext::thiserror::Error;
use hub::data_ext::serde::{Serialize, Deserialize};
use hub::text_ext::regex::Regex;
use hub::data_ext::serde_json;

#[derive(Serialize, Deserialize)]
struct Config {
    name: String,
    enabled: bool,
}

fn process_data() -> Result<(), MyError> {
    let config = Config {
        name: "test".to_string(),
        enabled: true
    };
    let json = serde_json::to_string(&config)?;

    let re = Regex::new(r"\d+").unwrap();
    // ... processing logic
    Ok(())
}
```

## Troubleshooting

### Feature Not Found
- Check if you're using the new `-ext` feature naming (e.g., `text-ext` not `text`)
- Verify the feature is available in hub's Cargo.toml
- Use domain groups instead of individual features when possible
- Check both top-level (`hub::regex`) and grouped (`hub::text_ext::regex`) import paths

### Compilation Errors
- Ensure you've updated all imports to use hub re-exports
- Try both import styles: `hub::serde` vs `hub::data_ext::serde`
- Check for version incompatibilities with other non-hub dependencies
- Verify feature flags match your usage

### Performance Issues
- Use specific `-ext` features instead of `dev-ext` for production
- Consider using domain groups (`text-ext`, `data-ext`) for better organization
- The `dev-ext` mega package is intended for testing/development only

### Migration Issues
- Old feature names still work for backward compatibility
- Gradually migrate to new `-ext` naming when convenient
- Both import styles work: choose based on your preference for clarity

### Path Configuration Issues
- **Always prefer GitHub repo**: Use `git = "https://github.com/oodx/hub.git"` for standard development
- **Local paths are temporary**: If using `path = "../../hub"`, plan to migrate to GitHub repo when fixes are published
- **Version conflicts**: Local paths may cause inconsistencies between projects using different hub versions

## Support

For questions or issues:
1. Check the main README.md for comprehensive documentation
2. Review hub's feature definitions in Cargo.toml
3. Use `blade` tools for ecosystem analysis
4. Follow the migration patterns used by existing oodx projects

---

## Philosophy Summary

Hub embodies a **controlled integration** approach to dependency management:

- **Internal First**: Top-level namespace reserved for oodx/rsb infrastructure
- **External Reluctance**: Third-party dependencies marked with `-ext` suffix
- **Clean Separation**: Clear boundaries between our code and external utilities
- **Ecosystem Unity**: Single source of truth for dependency versions across all projects

Hub: *One crate to rule them all, one crate to find them, one crate to bring them all, and in the ecosystem bind them - but with clear separation between internal and external.* 📦✨