// Asynchronous runtime via tokio
// Shaped module with common re-exports

// Re-export everything from tokio
pub use tokio::*;

// Common runtime items (explicit for better IDE support)
pub use tokio::{main, test, spawn};

// Common async utilities
#[cfg(feature = "tokio-full")]
pub use tokio::{join, select, time};