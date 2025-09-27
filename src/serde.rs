// Serde serialization framework
// Shaped export with explicit trait re-exports and optional derive macro support

// Re-export everything from serde
pub use serde::*;

// Explicitly re-export common traits (always available - these are traits, not macros)
pub use serde::{Deserialize, Serialize, Deserializer, Serializer};
pub use serde::de::{self, DeserializeOwned};
pub use serde::ser::{self, SerializeStruct, SerializeSeq, SerializeMap};

// The derive feature (serde-derive) enables #[derive(Serialize, Deserialize)]
// proc-macros at the Cargo.toml level via serde/derive feature forwarding