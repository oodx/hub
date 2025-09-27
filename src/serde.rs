// Serde serialization framework
// Simple passthrough with feature-gated derive support

// Re-export everything from serde
pub use serde::*;

// Explicitly re-export derive macros when derive feature is enabled
#[cfg(feature = "serde-derive")]
pub use serde::{Deserialize, Serialize};