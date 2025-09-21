# HOWTO: Hub Integration Guide

## Overview
Hub is a centralized dependency management system for the oodx/RSB ecosystem that uses feature flags to provide modular, conflict-free dependency management.

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
// Replace direct imports
use regex::Regex;           // ❌ Before
use hub::regex::Regex;      // ✅ After

use serde::{Serialize, Deserialize};    // ❌ Before
use hub::serde::{Serialize, Deserialize}; // ✅ After

// Or use the prelude for common features
use hub::prelude::*;
```

## Feature Selection Strategy

### Individual Features
Specify exactly what you need:
```toml
features = ["regex", "serde", "chrono", "uuid"]
```

### Domain Groups (Recommended)
- **`text`** - Text processing: regex, lazy_static, unicode-width
- **`data`** - Serialization: serde, serde_json, base64
- **`time`** - Date/time: chrono, uuid
- **`web`** - Web utilities: urlencoding
- **`system`** - System access: libc, glob
- **`random`** - Random generation: rand
- **`dev`** - Development tools: portable-pty

### Convenience Groups
- **`common`** - Most used: text + data + dev tools
- **`core`** - Essential: text + data + time
- **`extended`** - Comprehensive: core + web + system
- **`all`** - Everything (use sparingly)

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

### Basic Project Setup
```toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["core"] }
# Gets you: regex, lazy_static, unicode-width, serde, serde_json, base64, chrono, uuid
```

### Web Service Project
```toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["extended", "random"] }
# Gets you: core + web + system + random capabilities
```

### Development Tools Project
```toml
[dependencies]
hub = { git = "https://github.com/oodx/hub.git", features = ["common", "dev"] }
# Gets you: common features + portable-pty for terminal tools
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

1. **Remove direct dependencies** from your Cargo.toml
2. **Add hub dependency** using GitHub repo with appropriate features:
   ```toml
   hub = { git = "https://github.com/oodx/hub.git", features = ["your-features"] }
   ```
3. **Update imports** to use hub re-exports
4. **Test compilation** with `cargo check`
5. **Run tests** to ensure compatibility
6. **Update documentation** if needed
7. **Avoid local paths** unless you have urgent hot-fixes that cannot wait for publishing

## Common Patterns

### Error Handling
```rust
use hub::thiserror::Error;

#[derive(Error, Debug)]
pub enum MyError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}
```

### Serialization
```rust
use hub::serde::{Serialize, Deserialize};
use hub::serde_json;

#[derive(Serialize, Deserialize)]
struct Config {
    name: String,
    enabled: bool,
}

let config = Config { name: "test".to_string(), enabled: true };
let json = serde_json::to_string(&config)?;
```

### Regular Expressions
```rust
use hub::regex::Regex;

fn extract_numbers(text: &str) -> Vec<String> {
    let re = Regex::new(r"\d+").unwrap();
    re.find_iter(text)
        .map(|m| m.as_str().to_string())
        .collect()
}
```

## Troubleshooting

### Feature Not Found
- Check if the feature is available in hub's Cargo.toml
- Use domain groups instead of individual features when possible
- Verify you're using the correct import path

### Compilation Errors
- Ensure you've updated all imports to use hub re-exports
- Check for version incompatibilities with other non-hub dependencies
- Verify feature flags match your usage

### Performance Issues
- Use specific features instead of "all" to reduce compilation time
- Consider using domain groups for better organization

### Path Configuration Issues
- **Always prefer GitHub repo**: Use `git = "https://github.com/oodx/hub.git"` for standard development
- **Local paths are temporary**: If using `path = "../../hub"`, plan to migrate to GitHub repo when fixes are published
- **Version conflicts**: Local paths may cause inconsistencies between projects using different hub versions

## Support

For questions or issues:
1. Check the main README.md for comprehensive documentation
2. Review hub's feature definitions in Cargo.toml
3. Use `./bin/repos.py` tools for ecosystem analysis
4. Follow the migration patterns used by existing oodx projects

---

Hub: *One crate to rule them all, one crate to find them, one crate to bring them all, and in the ecosystem bind them.* 📦✨