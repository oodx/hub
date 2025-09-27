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
| `serde` | 10 projects | High usage + derive feature gating |
| `serde_json` | 7 projects | High usage + type aliases (Value, Map) |
| `chrono` | 7 projects | Common types + convenience prelude |
| `regex` | 5 projects | Common patterns + Result type alias |
| `thiserror` | 5 projects | Part of combined error module |
| `tokio` | 4 projects | Lite/full variants + common utilities |
| `clap` | 4 projects | Lite/full variants + derive feature gating |
| `error` | Combined | Merges anyhow + thiserror for unified error handling |
| `colors` | Internal | Hub's own RSB color system |

### Not Yet Shaped (Future Candidates)

| Module | Usage | Consider When |
|--------|-------|---------------|
| `unicode-width` | 5 projects | Could add convenience patterns if common usage emerges |
| `criterion` | 5 projects | Testing framework - may benefit from benchmark prelude |
| `tempfile` | 5 projects | Simple utility - likely remains direct re-export |

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

### Example 4: chrono (Common Re-exports + Prelude)

**Problem**: Date/time types require verbose imports, prelude is nested.

**Solution**: Shaped module with explicit common types and convenience prelude.

```rust
// src/chrono.rs
pub use chrono::*;

// Common types (explicit for better IDE support)
pub use chrono::{DateTime, Utc, Local, Duration, NaiveDateTime, NaiveDate, NaiveTime};
pub use chrono::TimeZone;

// Prelude module for convenient imports
pub mod prelude {
    pub use chrono::prelude::*;
}
```

**Usage:**
```rust
use hub::chrono::{DateTime, Utc, Duration};  // Direct common types
use hub::chrono::prelude::*;  // Or use prelude for everything

let now: DateTime<Utc> = Utc::now();
```

### Example 5: regex (Common Patterns + Type Alias)

**Problem**: Common regex types require explicit imports, error handling verbose.

**Solution**: Shaped module with common patterns and Result alias.

```rust
// src/regex.rs
pub use regex::*;

// Common types (explicit for better IDE support)
pub use regex::{Regex, RegexBuilder, Captures, Match, Replacer};
pub use regex::{RegexSet, RegexSetBuilder};

// Result type alias
pub type Result<T> = std::result::Result<T, regex::Error>;
```

**Usage:**
```rust
use hub::regex::{Regex, Captures};
use hub::regex::Result;  // Instead of Result<T, regex::Error>

fn parse(input: &str) -> Result<Vec<String>> {
    let re = Regex::new(r"\d+")?;
    Ok(re.find_iter(input).map(|m| m.as_str().to_string()).collect())
}
```

### Example 6: tokio (Lite/Full Variants)

**Problem**: Projects need different tokio feature sets, full variant is heavy.

**Solution**: Shaped module with common utilities and feature-gated full items.

```rust
// src/tokio.rs
pub use tokio::*;

// Common runtime items (always available)
pub use tokio::{main, test, spawn};

// Full variant items (requires tokio-full feature)
#[cfg(feature = "tokio-full")]
pub use tokio::{join, select, time};
```

**Usage:**
```toml
# Lite variant (basic async runtime)
features = ["tokio-lite"]  # or use tokio directly

# Full variant (networking, filesystem, etc.)
features = ["tokio-full"]
```

```rust
use hub::tokio;

#[tokio::main]  // Works with lite
async fn main() {
    tokio::spawn(async { /* ... */ });  // Works with lite

    // Requires tokio-full:
    // tokio::net::TcpListener::bind("127.0.0.1:8080").await?;
}
```

### Example 7: clap (Lite/Full with Derive Gating)

**Problem**: Derive macros add compile time, not all projects need them.

**Solution**: Shaped module with builders (lite) and feature-gated derive (full).

```rust
// src/clap.rs
pub use clap::*;

// Common types (always available)
pub use clap::{Arg, ArgMatches, Command, ArgAction, builder};

// Derive macros (requires clap-full feature)
#[cfg(feature = "clap-full")]
pub use clap::{Parser, Args, Subcommand, ValueEnum};
```

**Usage:**
```toml
# Lite variant (builder API only)
features = ["clap-lite"]  # or use clap directly

# Full variant (derive macros)
features = ["clap-full"]
```

```rust
// Lite: Builder API
use hub::clap::{Command, Arg};

let app = Command::new("myapp")
    .arg(Arg::new("input").short('i'));

// Full: Derive API (requires clap-full)
use hub::clap::Parser;

#[derive(Parser)]
struct Cli {
    #[arg(short, long)]
    input: String,
}
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

Hub has successfully shaped all high-usage packages (5+ projects). Future candidates include:

**unicode-width shaping:**
- If common usage patterns emerge
- Could provide width calculation utilities
- Currently low complexity suggests simple re-export is sufficient

**criterion shaping:**
- Testing framework used in 5+ projects
- Could benefit from benchmark prelude module
- May add convenience macros for common patterns

**Medium-usage packages (3-4 projects):**
- Monitor usage patterns as ecosystem grows
- Consider shaping when usage reaches 5+ projects
- Examples: uuid (4), rand (4), libc (3)

### Philosophy Evolution

Hub's shaped exports have matured to cover all major use cases:

**Current State (v0.3+):**
- ✅ 7 shaped modules covering high-usage dependencies
- ✅ Feature gating for derive macros and optional functionality
- ✅ Lite/full variants for performance-critical packages
- ✅ Type aliases and convenience re-exports
- ✅ Combined modules for related functionality

**Future Evolution:**
As hub matures, shaped exports may:
- Provide more convenience preludes for complex packages
- Add hub-specific helper functions (carefully, staying close to upstream)
- Combine more related crates when usage patterns justify it
- Introduce hub-specific abstractions for common patterns
- **But always**: Stay close to upstream, maintain compatibility, avoid opinionated wrappers

## See Also

- **[FEATURE_FORWARDING.md](../FEATURE_FORWARDING.md)** - Feature forwarding pattern
- **[FEATURE_PATHS.md](FEATURE_PATHS.md)** - Module paths reference
- **[HUB_STRAT.md](HUB_STRAT.md)** - Overall hub strategy

---

*The shaping paradigm: Simple passthrough for most, curated convenience for high-value dependencies.*