// Error handling utilities
// Combines anyhow and thiserror for comprehensive error support

// Re-export anyhow module
#[cfg(feature = "anyhow")]
pub mod anyhow {
    pub use ::anyhow::*;
}

// Re-export thiserror module
#[cfg(feature = "thiserror")]
pub mod thiserror {
    pub use ::thiserror::*;
}

// Convenience type aliases
#[cfg(feature = "anyhow")]
pub type Result<T> = ::anyhow::Result<T>;

#[cfg(feature = "anyhow")]
pub type Error = ::anyhow::Error;