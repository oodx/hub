# Hub 🏗️

> *Central hub for the oodx/RSB ecosystem - dependency management and global utilities*

Hub eliminates version conflicts, dependency bloat, and upgrade hell across all oodx projects by providing a single source of truth for external dependencies and shared ecosystem infrastructure.

## Quick Start

### Add to your project:
```toml
# Cargo.toml
[dependencies]
hub = { path = "../../hub", features = ["regex", "serde"] }
```

### Use in your code:
```rust
use hub::regex;      // Instead of: use regex;
use hub::serde;      // Instead of: use serde;

// Or import multiple at once:
use hub::prelude::*;
```

## Features

### Individual Dependencies
```toml
features = ["regex", "serde", "chrono", "uuid"]
```

### Domain Groups
- **`text`** - Text processing: regex, lazy_static
- **`data`** - Serialization: serde, serde_json, base64
- **`time`** - Date/time: chrono, uuid
- **`web`** - Web utilities: urlencoding
- **`system`** - System access: libc, glob
- **`random`** - Random generation: rand
- **`dev`** - Development tools: portable-pty

### Convenience Groups
- **`common`** - Most used: text + data
- **`core`** - Essential: text + data + time
- **`extended`** - Comprehensive: core + web + system
- **`all`** - Everything

## Examples

### Basic Usage
```rust
use hub::regex::Regex;
use hub::serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize)]
struct Config {
    pattern: String,
}

fn process_data(config: &Config, input: &str) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let re = Regex::new(&config.pattern)?;
    let matches: Vec<String> = re.find_iter(input)
        .map(|m| m.as_str().to_string())
        .collect();
    Ok(matches)
}
```

### Domain-Specific Imports
```rust
use cargohold::text::regex;
use cargohold::data::serde_json;
use cargohold::time::chrono;

fn parse_log_entry(line: &str) -> Result<LogEntry, serde_json::Error> {
    // Implementation using domain-specific imports
}
```

## Benefits

### For Developers
- ✅ **No version conflicts** - Guaranteed compatibility across projects
- ✅ **Simplified dependencies** - Only specify features, not versions
- ✅ **Easy ecosystem upgrades** - One place to update all versions
- ✅ **Consistent behavior** - Same crate versions everywhere

### For Projects
- 📦 **Cleaner Cargo.toml** - No external dependency noise
- ⚡ **Faster builds** - Cargo deduplicates dependencies
- 🔒 **Better security** - Centralized vulnerability scanning
- 🔧 **Easier maintenance** - Coordinated dependency updates

## Ecosystem Integration

### Current oodx Projects
- **RSB** - Base framework (legacy `deps` compatibility maintained)
- **Meteor** - Token data transport
- **Boxy** - Layout rendering
- **XStream** - Data flow processing

### Migration Guide

Replace direct dependencies:
```toml
# Before
[dependencies]
regex = "1.10.2"
serde = { version = "1.0", features = ["derive"] }

# After
[dependencies]
cargohold = { path = "../../cargohold", features = ["regex", "serde"] }
```

Update imports:
```rust
// Before
use regex::Regex;
use serde::{Serialize, Deserialize};

// After
use cargohold::regex::Regex;
use cargohold::serde::{Serialize, Deserialize};
```

## Development

### Testing Cargohold
```bash
# Test with different feature combinations
cargo test --features "text"
cargo test --features "data"
cargo test --features "all"
```

### Adding New Dependencies
1. Add to `Cargo.toml` as optional dependency
2. Add feature flag in `[features]` section
3. Add re-export in `src/lib.rs` with feature gate
4. Update domain collections if appropriate
5. Update this README

### Version Updates
1. Update versions in `Cargo.toml`
2. Test all oodx projects for compatibility
3. Update projects to new cargohold version

## Architecture

```
cargohold/
├── src/
│   └── lib.rs          # Feature-gated re-exports
├── Cargo.toml          # THE canonical dependency list
├── STRATEGY.md         # Design principles and migration guide
└── README.md           # This file
```

## Version Compatibility

| Cargohold | RSB   | Meteor | Boxy  | XStream |
|-----------|-------|--------|-------|---------|
| 0.1.x     | 0.5.x | 0.1.x  | TBD   | TBD     |

## Contributing

1. **Evaluate necessity** - Is this dependency widely needed?
2. **Check alternatives** - Can we use existing dependencies?
3. **Add feature flag** - Never expose dependencies without gates
4. **Update documentation** - Keep README and STRATEGY.md current
5. **Test ecosystem** - Verify compatibility across projects

## License

AGPL-3.0 - Same as the oodx ecosystem

---

*One crate to rule them all, one crate to find them, one crate to bring them all, and in the ecosystem bind them.* 📦✨