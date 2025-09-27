// JSON serialization via serde_json
// Simple passthrough with convenience re-exports

// Re-export everything
pub use serde_json::*;

// Common type aliases for convenience
pub type Map<K = String, V = Value> = serde_json::Map<K, V>;

// Commonly used functions (explicit for better IDE support)
pub use serde_json::{from_str, to_string, from_value, to_value, Value};