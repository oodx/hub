# Hub Feature Paths & Configuration Reference

This document shows the correct paths and feature configurations for hub's shaped export pattern.

## Feature Naming Convention

Hub uses **kebab-case** for feature names and **snake_case** for module/crate names:

```toml
# Feature name (kebab-case)
serde-json = ["serde", "dep:serde_json"]

# Crate name (snake_case)
serde_json = { version = "1.0.145", optional = true }
```

## Serde Configuration

### Cargo.toml Features

```toml
[features]
# Base serde traits
serde = ["dep:serde"]

# Add derive macros (Serialize, Deserialize)
serde-derive = ["serde", "serde/derive"]

# JSON support (includes base serde)
serde-json = ["serde", "dep:serde_json"]

# Convenience: derive + json
json = ["serde-derive", "serde-json"]

# Domain group includes derive by default
data-ext = ["serde-derive", "serde-json", "base64", "serde_yaml"]

[dependencies]
serde = { version = "1.0.226", optional = true, default-features = false }
serde_json = { version = "1.0.145", optional = true }
```

### Module Paths

```rust
// lib.rs - Top level
#[cfg(feature = "serde")]
pub mod serde;  // Shaped module

#[cfg(feature = "serde-json")]
pub use serde_json;  // Direct crate re-export

// lib.rs - data_ext module
pub mod data_ext {
    #[cfg(feature = "serde")]
    pub use crate::serde;  // Use crate:: for shaped module

    #[cfg(feature = "serde-json")]
    pub use super::serde_json;  // Use super:: for crate re-export
}
```

### Shaped Module (src/serde.rs)

```rust
// Re-export entire crate
pub use serde::*;

// Conditionally re-export derive macros
#[cfg(feature = "serde-derive")]
pub use serde::{Deserialize, Serialize};
```

## Usage Paths

### Direct Access

```rust
// With serde-derive or json feature
use hub::serde::{Serialize, Deserialize};

// With serde-json or json feature
use hub::serde_json;

#[derive(Serialize, Deserialize)]
struct Config { name: String }

let json = serde_json::to_string(&config)?;
```

### Via Domain Module

```rust
// With data-ext feature
use hub::data_ext::{serde, serde_json};

#[derive(serde::Serialize, serde::Deserialize)]
struct Config { name: String }

let json = serde_json::to_string(&config)?;
```

### Via Prelude

```rust
// Prelude includes commonly used items
use hub::prelude::*;

// Now hub::serde and hub::serde_json are available
use hub::serde::{Serialize, Deserialize};
```

## Feature Testing

### Test Feature Gates

```rust
// Test that serde-derive provides macros
#[cfg(feature = "serde-derive")]
#[test]
fn test_derive_available() {
    use hub::serde::{Deserialize, Serialize};
    // ...
}

// Test that json convenience works
#[cfg(feature = "json")]
#[test]
fn test_json_bundle() {
    use hub::serde::{Deserialize, Serialize};
    use hub::serde_json;
    // ...
}

// Test data-ext bundle
#[cfg(feature = "data-ext")]
#[test]
fn test_data_ext() {
    use hub::data_ext::{serde, serde_json};
    // ...
}
```

## Common Patterns

### Pattern 1: JSON with Derive (Most Common)

```toml
[dependencies]
hub = { path = "../../hub", features = ["json"] }
```

```rust
use hub::serde::{Serialize, Deserialize};
use hub::serde_json;

#[derive(Serialize, Deserialize)]
struct MyData { /* ... */ }

let json = serde_json::to_string(&data)?;
```

### Pattern 2: Just Derive (No JSON)

```toml
[dependencies]
hub = { path = "../../hub", features = ["serde-derive"] }
```

```rust
use hub::serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize)]
struct MyData { /* ... */ }
```

### Pattern 3: JSON Parsing Only (No Derive)

```toml
[dependencies]
hub = { path = "../../hub", features = ["serde-json"] }
```

```rust
use hub::serde_json;

let value: serde_json::Value = serde_json::from_str(json)?;
```

### Pattern 4: Full Data Stack

```toml
[dependencies]
hub = { path = "../../hub", features = ["data-ext"] }
```

```rust
use hub::data_ext::{serde, serde_json, base64};

#[derive(serde::Serialize, serde::Deserialize)]
struct MyData { /* ... */ }

let json = serde_json::to_string(&data)?;
let encoded = base64::encode(&json);
```

## Key Points

1. **Feature names use kebab-case**: `serde-json`, `serde-derive`
2. **Module/crate names use snake_case**: `serde_json`, `serde`
3. **Shaped modules use `crate::`**: `pub use crate::serde`
4. **Crate re-exports use `super::`**: `pub use super::serde_json`
5. **Feature gates must match feature names**: `#[cfg(feature = "serde-json")]`
6. **Convenience bundles make common patterns easy**: `json = ["serde-derive", "serde-json"]`