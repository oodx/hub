# Hub Feature Forwarding Pattern

Hub provides granular feature flags that forward to underlying crate features, giving projects precise control over what they include.

## Serde Example

### Available Features

```toml
# Base serde (traits only, no derive macros)
serde = ["dep:serde"]

# Add derive macro support
serde-derive = ["serde", "serde/derive"]

# JSON support (includes base serde)
serde-json = ["serde", "dep:serde_json"]

# Convenience: derive + json together
json = ["serde-derive", "serde-json"]
```

### Usage Examples

```toml
# Just need serde traits (rare)
hub = { features = ["serde"] }

# Need derive macros but no JSON
hub = { features = ["serde-derive"] }

# Need derive + JSON (most common)
hub = { features = ["json"] }

# OR explicitly
hub = { features = ["serde-derive", "serde-json"] }

# Just JSON parsing (no derive on your types)
hub = { features = ["serde-json"] }
```

### Code Usage

```rust
// With serde-derive or json feature
use hub::serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize)]
struct Config {
    name: String,
}

// With serde-json or json feature
use hub::serde_json;

let json = serde_json::to_string(&config)?;
let parsed: Config = serde_json::from_str(&json)?;
```

## Benefits

1. **Granular Control**: Projects only pay for what they use
2. **Clear Intent**: Feature names express what's needed
3. **Flexibility**: Hub can reorganize internals without breaking consumers
4. **Convenience**: Common patterns bundled (e.g., `json`)

## Pattern for Other Crates

This pattern can be extended to other hub-managed crates:

```toml
# Example: tokio with granular features
tokio = ["tokio-rt"]                    # Just runtime
tokio-rt = ["dep:tokio", "tokio/rt"]
tokio-macros = ["tokio", "tokio/macros"]
tokio-full = ["tokio-rt", "tokio-macros", "tokio/full"]

# Example: clap with granular features
clap = ["clap-derive"]                  # Default with derive
clap-base = ["dep:clap"]
clap-derive = ["clap-base", "clap/derive"]
cli = ["clap-derive", "anyhow"]         # Convenience bundle
```

## Implementation

Shaped export modules (like `src/serde.rs`) conditionally re-export items based on hub's feature flags:

```rust
// src/serde.rs
pub use serde::*;

#[cfg(feature = "serde-derive")]
pub use serde::{Deserialize, Serialize};
```

This keeps the implementation simple while providing maximum flexibility.