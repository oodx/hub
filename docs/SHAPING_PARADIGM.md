# Hub Shaping Paradigm

Hub uses a **shaped export pattern** to provide curated, convenient APIs for high-usage dependencies. This document explains the philosophy, implementation, and guidelines for shaped exports.

## Philosophy

### Traditional Re-exports (Simple)

```rust
// lib.rs
#[cfg(feature = "serde")]
pub use serde;
```

**Pros:**
- Simple to implement
- Minimal code
- Direct passthrough

**Cons:**
- No customization layer
- Can't add convenience items
- Limited IDE discoverability
- No type aliases or helpers

### Shaped Exports (Hub's Approach)

```rust
// lib.rs
#[cfg(feature = "serde")]
pub mod serde;

// src/serde.rs
pub use serde::*;

#[cfg(feature = "serde-derive")]
pub use serde::{Serialize, Deserialize};
```

**Pros:**
- ✅ Explicit re-exports improve IDE autocomplete
- ✅ Can add type aliases and helpers
- ✅ Documentation layer for hub-specific patterns
- ✅ Feature-gated items (derive macros, etc.)
- ✅ Still provides full crate access

**Cons:**
- More files to maintain
- Slightly more complex

## When to Shape

Not every dependency needs shaping. Use this decision tree:

### ✅ Good Candidates for Shaping

1. **High usage** (5+ projects in ecosystem)
2. **Complex features** (lite/full variants, derive macros)
3. **Common patterns** (type aliases, prelude modules)
4. **Combined functionality** (error handling: anyhow + thiserror)

### ❌ Keep Simple Re-exports

1. **Low usage** (1-2 projects)
2. **Simple passthrough** (no features to gate)
3. **No convenience needed** (no common patterns)

### Current Shaped Modules

| Module | Usage | Why Shaped |
|--------|-------|------------|
| `serde` | 11 projects | High usage + derive feature gating |
| `serde_json` | 8 projects | High usage + type aliases (Value, Map) |
| `error` | Combined | Merges anyhow (5) + thiserror (6) |
| `colors` | Internal | Hub's own RSB color system |

### Not Yet Shaped (Future Candidates)

| Module | Usage | Consider When |
|--------|-------|---------------|
| `chrono` | 7 projects | Already has lite/full, could add convenience |
| `regex` | 6 projects | Could add common patterns |
| `tokio` | 5 projects | Already has lite/full, could add prelude |

## Implementation Pattern

### 1. Create Shaped Module

```rust
// src/package_name.rs
// Brief description of what this provides

// Re-export entire crate
pub use package_name::*;

// Feature-gated explicit re-exports (for IDE support)
#[cfg(feature = "package-derive")]
pub use package_name::{Derive, Macro};

// Convenience type aliases
pub type CommonType<T> = package_name::LongType<T>;

// Common re-exports for discoverability
pub use package_name::{common_fn, CommonStruct};
```

### 2. Update lib.rs

```rust
// lib.rs

/// Package description
#[cfg(feature = "package")]
pub mod package_name;
```

### 3. Update Cargo.toml

```toml
[features]
package = ["dep:package_name"]
package-derive = ["package", "package_name/derive"]
package-full = ["package-derive", "package_name/full"]
```

### 4. Add to Domain Module

```rust
// lib.rs - domain modules
pub mod domain_ext {
    #[cfg(feature = "package")]
    pub use crate::package_name;
}
```

## Real Examples

### Example 1: serde (Feature Gating)

**Problem**: Projects need derive macros but hub was forcing them always.

**Solution**: Shaped module with feature-gated re-exports.

```rust
// src/serde.rs
pub use serde::*;

// Only available with serde-derive feature
#[cfg(feature = "serde-derive")]
pub use serde::{Deserialize, Serialize};
```

**Usage:**
```toml
# Just traits
hub = { features = ["serde"] }

# With derive macros
hub = { features = ["serde-derive"] }
```

### Example 2: serde_json (Type Aliases)

**Problem**: Common types like `Map` and `Value` require verbose imports.

**Solution**: Shaped module with convenience aliases.

```rust
// src/serde_json.rs
pub use serde_json::*;

// Convenience type alias
pub type Map<K = String, V = Value> = serde_json::Map<K, V>;

// Explicit re-exports for IDE
pub use serde_json::{from_str, to_string, from_value, to_value, Value};
```

**Usage:**
```rust
use hub::serde_json::{Value, Map};  // Shorter, clearer

// Instead of:
use hub::serde_json;
type Map = serde_json::Map<String, serde_json::Value>;
```

### Example 3: error (Combined Module)

**Problem**: Projects use both anyhow and thiserror, always together.

**Solution**: Shaped module that combines both.

```rust
// src/error.rs
#[cfg(feature = "anyhow")]
pub mod anyhow {
    pub use ::anyhow::*;
}

#[cfg(feature = "thiserror")]
pub mod thiserror {
    pub use ::thiserror::*;
}

// Convenience type aliases
#[cfg(feature = "anyhow")]
pub type Result<T> = ::anyhow::Result<T>;

#[cfg(feature = "anyhow")]
pub type Error = ::anyhow::Error;
```

**Usage:**
```rust
use hub::error::{Result, anyhow, thiserror};

// Instead of:
use hub::anyhow;
use hub::thiserror;
type Result<T> = anyhow::Result<T>;
```

## Guidelines

### Naming Conventions

1. **Module files**: `src/package_name.rs` (snake_case)
2. **Feature names**: `package-name-variant` (kebab-case)
3. **Type aliases**: `PascalCase` or `snake_case` (match ecosystem)

### What to Include

#### ✅ Always Include

- Full crate re-export: `pub use package::*;`
- Brief module comment explaining purpose

#### ✅ Include When Relevant

- Feature-gated items (derive macros, optional features)
- Common type aliases (`Result<T>`, `Map<K,V>`)
- Frequently used function re-exports
- Combined modules (anyhow + thiserror)

#### ❌ Don't Include

- Custom implementations (stay close to upstream)
- Opinionated wrappers (let projects decide)
- Experimental APIs (wait for stability)

### Documentation

Each shaped module should have:

```rust
// src/package.rs
// Package Name - Brief description
//
// Provides shaped exports with [list key conveniences].
//
// ## Features
// - `package`: Base package
// - `package-derive`: Add derive macros
// - `package-full`: Full feature set
//
// ## Common Usage
// ```rust
// use hub::package::{CommonType, common_fn};
// ```

pub use package::*;
// ... rest of implementation
```

## Testing Shaped Modules

### Basic Compilation Test

```rust
// tests/shaped_exports.rs
#[cfg(feature = "package-derive")]
#[test]
fn test_package_provides_derive() {
    use hub::package::{Derive, Macro};

    // Type check ensures items exist
    fn _check<T: Derive>() {}
}
```

### Path Tests

```rust
// tests/feature_paths.rs
#[cfg(feature = "package")]
#[test]
fn test_package_paths() {
    // Direct access
    use hub::package::CommonType;

    // Via domain module
    use hub::domain_ext::package;

    // Both should work
    let _: CommonType = package::CommonType::new();
}
```

## Migration Strategy

### Adding New Shaped Module

1. **Assess need** using decision tree
2. **Create module file** following pattern
3. **Update lib.rs** and Cargo.toml
4. **Add tests** for key paths
5. **Document** in appropriate guides
6. **Minor version bump** (new features added)

### Converting Simple to Shaped

1. **Create shaped module** file
2. **Keep backward compatibility**:
   ```rust
   // lib.rs - old direct re-export still works
   #[cfg(feature = "package")]
   pub use package_name;

   // New shaped module
   #[cfg(feature = "package")]
   pub mod package_name;
   ```
3. **Document migration** in CHANGELOG
4. **Minor version bump** (non-breaking addition)

### Deprecating Shaped Module

1. Add deprecation warning:
   ```rust
   #[deprecated(since = "0.x.0", note = "Use direct access instead")]
   pub mod old_module;
   ```
2. Document in CHANGELOG
3. Wait 2-3 versions
4. Remove in major version bump

## Maintenance

### Review Schedule

- **Quarterly**: Review usage stats with `blade hub`
- **On major updates**: Re-assess shaping decisions
- **When adding features**: Consider if shaping helps

### Usage Analysis

```bash
# Check high-usage packages
blade usage --fast-mode | head -20

# Top candidates (5+ uses):
# - serde (11) ✅ Shaped
# - serde_json (8) ✅ Shaped
# - chrono (7) 🔄 Consider shaping
# - regex (6) 🔄 Consider shaping
```

### Quality Criteria

Shaped modules should:
- ✅ Compile with all feature combinations
- ✅ Have basic tests
- ✅ Follow naming conventions
- ✅ Provide clear value over simple re-export
- ✅ Be documented

## Future Directions

### Potential Additions

**chrono shaping:**
```rust
// src/chrono.rs
pub use chrono::*;

// Common re-exports
pub use chrono::{DateTime, Utc, Local, Duration, TimeZone};

// Convenience prelude
pub mod prelude {
    pub use chrono::prelude::*;
}
```

**regex shaping:**
```rust
// src/regex.rs
pub use regex::*;

// Common re-exports
pub use regex::{Regex, RegexBuilder, Captures, Match};

// Type alias
pub type Result<T> = Result<T, regex::Error>;
```

### Philosophy Evolution

As hub matures, shaped exports may:
- Provide more convenience preludes
- Add hub-specific helper functions
- Combine related crates (like error module)
- **But always**: Stay close to upstream, maintain compatibility

## See Also

- **[FEATURE_FORWARDING.md](../FEATURE_FORWARDING.md)** - Feature forwarding pattern
- **[FEATURE_PATHS.md](FEATURE_PATHS.md)** - Module paths reference
- **[HUB_STRAT.md](HUB_STRAT.md)** - Overall hub strategy

---

*The shaping paradigm: Simple passthrough for most, curated convenience for high-value dependencies.*