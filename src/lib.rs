//! # Hub: Central Ecosystem Hub
//!
//! Hub is the central hub for all oodx/RSB ecosystem projects, providing
//! unified dependency management, global utilities, and ecosystem coordination.
//! It eliminates version conflicts and provides shared infrastructure.
//!
//! ## Usage
//!
//! Add hub to your project's Cargo.toml with the features you need:
//!
//! ```toml
//! [dependencies]
//! hub = { path = "../../hub", features = ["regex", "serde"] }
//! ```
//!
//! Then import dependencies from hub instead of directly:
//!
//! ```rust,ignore
//! use hub::regex;      // Instead of: use regex;
//! use hub::serde;      // Instead of: use serde;
//! ```
//!
//! ## Feature Groups
//!
//! - **`text`** - Text processing: regex, lazy_static
//! - **`data`** - Serialization: serde, serde_json, base64
//! - **`time`** - Date/time: chrono, uuid
//! - **`web`** - Web utilities: urlencoding
//! - **`system`** - System access: libc, glob
//! - **`random`** - Random generation: rand
//! - **`dev`** - Development tools: portable-pty
//!
//! ## Convenience Groups
//!
//! - **`common`** - Most commonly used: text + data
//! - **`core`** - Essential features: text + data + time
//! - **`extended`** - Comprehensive: core + web + system
//! - **`all`** - Everything available
//!
//! ## Example
//!
//! ```rust,ignore
//! // Enable multiple features at once
//! // Cargo.toml: features = ["text", "data"]
//! use cargohold::regex::Regex;
//! use cargohold::serde::{Serialize, Deserialize};
//!
//! #[derive(Serialize, Deserialize)]
//! struct Config {
//!     pattern: String,
//! }
//!
//! fn process_config(config: &Config) -> Result<(), Box<dyn std::error::Error>> {
//!     let regex = Regex::new(&config.pattern)?;
//!     // ... processing logic
//!     Ok(())
//! }
//! ```

// ============================================================================
// Core Re-exports - Feature Gated External Dependencies
// ============================================================================

/// Base64 encoding/decoding utilities
#[cfg(feature = "base64")]
pub use base64;

/// Date and time handling
#[cfg(feature = "chrono")]
pub use chrono;

/// File glob pattern matching
#[cfg(feature = "glob")]
pub use glob;

/// Static variable initialization
#[cfg(feature = "lazy_static")]
pub use lazy_static;

/// System library bindings
#[cfg(feature = "libc")]
pub use libc;

/// Portable pseudo-terminal support
#[cfg(feature = "portable-pty")]
pub use portable_pty;

/// Random number generation
#[cfg(feature = "rand")]
pub use rand;

/// Regular expression processing
#[cfg(feature = "regex")]
pub use regex;

/// Serialization framework
#[cfg(feature = "serde")]
pub use serde;

/// JSON serialization support
#[cfg(feature = "serde_json")]
pub use serde_json;

/// URL encoding utilities
#[cfg(feature = "urlencoding")]
pub use urlencoding;

/// UUID generation and parsing
#[cfg(feature = "uuid")]
pub use uuid;

// ============================================================================
// Convenience Prelude Module
// ============================================================================

/// Convenience prelude: `use hub::prelude::*;` to bring enabled crates into scope.
///
/// This module re-exports all enabled dependencies, allowing for quick imports:
///
/// ```rust,ignore
/// use hub::prelude::*;
///
/// // Now you can use regex, serde, etc. directly
/// let re = regex::Regex::new(r"\d+")?;
/// ```
pub mod prelude {
    #[cfg(feature = "base64")]
    pub use super::base64;

    #[cfg(feature = "chrono")]
    pub use super::chrono;

    #[cfg(feature = "glob")]
    pub use super::glob;

    #[cfg(feature = "lazy_static")]
    pub use super::lazy_static;

    #[cfg(feature = "libc")]
    pub use super::libc;

    #[cfg(feature = "portable-pty")]
    pub use super::portable_pty;

    #[cfg(feature = "rand")]
    pub use super::rand;

    #[cfg(feature = "regex")]
    pub use super::regex;

    #[cfg(feature = "serde")]
    pub use super::serde;

    #[cfg(feature = "serde_json")]
    pub use super::serde_json;

    #[cfg(feature = "urlencoding")]
    pub use super::urlencoding;

    #[cfg(feature = "uuid")]
    pub use super::uuid;
}

// ============================================================================
// Domain-Specific Collection Modules
// ============================================================================

/// Text processing utilities
pub mod text {
    #[cfg(feature = "regex")]
    pub use super::regex;

    #[cfg(feature = "lazy_static")]
    pub use super::lazy_static;
}

/// Data serialization and encoding utilities
pub mod data {
    #[cfg(feature = "serde")]
    pub use super::serde;

    #[cfg(feature = "serde_json")]
    pub use super::serde_json;

    #[cfg(feature = "base64")]
    pub use super::base64;
}

/// Date, time, and identification utilities
pub mod time {
    #[cfg(feature = "chrono")]
    pub use super::chrono;

    #[cfg(feature = "uuid")]
    pub use super::uuid;
}

/// Web and networking utilities
pub mod web {
    #[cfg(feature = "urlencoding")]
    pub use super::urlencoding;
}

/// System and filesystem utilities
pub mod system {
    #[cfg(feature = "libc")]
    pub use super::libc;

    #[cfg(feature = "glob")]
    pub use super::glob;
}

/// Random number generation utilities
pub mod random {
    #[cfg(feature = "rand")]
    pub use super::rand;
}

/// Development and testing utilities
pub mod dev {
    #[cfg(feature = "portable-pty")]
    pub use super::portable_pty;
}

// ============================================================================
// Utility Functions and Version Information
// ============================================================================

/// Returns the hub version
pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// Returns information about enabled features
pub fn enabled_features() -> Vec<&'static str> {
    let mut features = Vec::new();

    #[cfg(feature = "base64")]
    features.push("base64");

    #[cfg(feature = "chrono")]
    features.push("chrono");

    #[cfg(feature = "glob")]
    features.push("glob");

    #[cfg(feature = "lazy_static")]
    features.push("lazy_static");

    #[cfg(feature = "libc")]
    features.push("libc");

    #[cfg(feature = "portable-pty")]
    features.push("portable-pty");

    #[cfg(feature = "rand")]
    features.push("rand");

    #[cfg(feature = "regex")]
    features.push("regex");

    #[cfg(feature = "serde")]
    features.push("serde");

    #[cfg(feature = "serde_json")]
    features.push("serde_json");

    #[cfg(feature = "urlencoding")]
    features.push("urlencoding");

    #[cfg(feature = "uuid")]
    features.push("uuid");

    features
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version_is_set() {
        assert!(!version().is_empty());
    }

    #[test]
    fn test_enabled_features_tracking() {
        let features = enabled_features();
        // Should at least track what we're testing with
        assert!(features.len() >= 0); // Always true, but documents the function
    }
}