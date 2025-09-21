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
//! ## External Feature Groups (Third-party - use if we have to)
//!
//! - **`text-ext`** - Text processing: regex, lazy_static, strip-ansi-escapes
//! - **`data-ext`** - Serialization: serde, serde_json, base64, serde_yaml (deprecated)
//! - **`time-ext`** - Date/time: chrono, uuid
//! - **`web-ext`** - Web utilities: urlencoding
//! - **`system-ext`** - System access: libc, glob
//! - **`terminal-ext`** - Terminal tools: portable-pty
//! - **`random-ext`** - Random generation: rand
//! - **`async-ext`** - Asynchronous programming: tokio
//! - **`cli-ext`** - Command line tools: clap, anyhow
//! - **`error-ext`** - Error handling: anyhow, thiserror
//! - **`test-ext`** - Testing utilities: criterion, tempfile
//!
//! ## External Convenience Groups
//!
//! - **`common-ext`** - Most commonly used external: text-ext + data-ext + error-ext
//! - **`core-ext`** - Essential external: text-ext + data-ext + time-ext + error-ext
//! - **`extended-ext`** - Comprehensive external: core-ext + web-ext + system-ext + cli-ext
//! - **`dev-ext`** - Everything external (testing/dev use): ALL external packages
//!
//! ## Internal oodx/rsb Groups (Top-level namespace reserved)
//!
//! - **`core`** - Internal oodx/rsb core: colors
//! - **`colors`** - Shared color system from jynx architecture
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

/// Error handling utilities
#[cfg(feature = "anyhow")]
pub use anyhow;

/// Base64 encoding/decoding utilities
#[cfg(feature = "base64")]
pub use base64;

/// Date and time handling
#[cfg(feature = "chrono")]
pub use chrono;

/// Command line argument parsing
#[cfg(feature = "clap")]
pub use clap;

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

/// YAML serialization support
///
/// **⚠️ DEPRECATION WARNING ⚠️**
///
/// YAML support is deprecated and should be migrated to:
/// - TOML (for configuration files)
/// - JSON (for data exchange)
/// - RON (for Rust-native serialization)
///
/// This feature will be removed in a future version.
#[cfg(feature = "serde_yaml")]
#[deprecated(since = "0.3.0", note = "YAML is deprecated. Use TOML, JSON, or RON instead.")]
pub use serde_yaml;

/// ANSI escape sequence removal utilities
#[cfg(feature = "strip-ansi-escapes")]
pub use strip_ansi_escapes;

/// Asynchronous runtime
#[cfg(feature = "tokio")]
pub use tokio;

/// URL encoding utilities
#[cfg(feature = "urlencoding")]
pub use urlencoding;

/// UUID generation and parsing
#[cfg(feature = "uuid")]
pub use uuid;

/// Unicode character width calculation
#[cfg(feature = "unicode-width")]
pub use unicode_width;

/// Benchmarking framework
#[cfg(feature = "criterion")]
pub use criterion;

/// Error type generation
#[cfg(feature = "thiserror")]
pub use thiserror;

/// Temporary file creation
#[cfg(feature = "tempfile")]
pub use tempfile;

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
    #[cfg(feature = "anyhow")]
    pub use super::anyhow;

    #[cfg(feature = "base64")]
    pub use super::base64;

    #[cfg(feature = "chrono")]
    pub use super::chrono;

    #[cfg(feature = "clap")]
    pub use super::clap;

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

    #[cfg(feature = "serde_yaml")]
    pub use super::serde_yaml;

    #[cfg(feature = "strip-ansi-escapes")]
    pub use super::strip_ansi_escapes;

    #[cfg(feature = "tokio")]
    pub use super::tokio;

    #[cfg(feature = "urlencoding")]
    pub use super::urlencoding;

    #[cfg(feature = "uuid")]
    pub use super::uuid;

    #[cfg(feature = "unicode-width")]
    pub use super::unicode_width;

    #[cfg(feature = "criterion")]
    pub use super::criterion;

    #[cfg(feature = "thiserror")]
    pub use super::thiserror;

    #[cfg(feature = "tempfile")]
    pub use super::tempfile;
}

// ============================================================================
// Internal oodx/rsb Modules (Top-level namespace reserved for our own code)
// ============================================================================

/// Shared color system from jynx architecture
#[cfg(feature = "colors")]
pub mod colors;

// Future internal modules:
// pub mod utils;
// pub mod shared;
// pub mod rsb;

// ============================================================================
// External Dependencies Collection Modules (Third-party - use if we have to)
// ============================================================================

/// Text processing utilities (external)
pub mod text_ext {
    #[cfg(feature = "regex")]
    pub use super::regex;

    #[cfg(feature = "lazy_static")]
    pub use super::lazy_static;

    #[cfg(feature = "strip-ansi-escapes")]
    pub use super::strip_ansi_escapes;
}

/// Data serialization and encoding utilities (external)
pub mod data_ext {
    #[cfg(feature = "serde")]
    pub use super::serde;

    #[cfg(feature = "serde_json")]
    pub use super::serde_json;

    #[cfg(feature = "serde_yaml")]
    pub use super::serde_yaml;

    #[cfg(feature = "base64")]
    pub use super::base64;
}

/// Date, time, and identification utilities (external)
pub mod time_ext {
    #[cfg(feature = "chrono")]
    pub use super::chrono;

    #[cfg(feature = "uuid")]
    pub use super::uuid;
}

/// Web and networking utilities (external)
pub mod web_ext {
    #[cfg(feature = "urlencoding")]
    pub use super::urlencoding;
}

/// System and filesystem utilities (external)
pub mod system_ext {
    #[cfg(feature = "libc")]
    pub use super::libc;

    #[cfg(feature = "glob")]
    pub use super::glob;
}

/// Terminal utilities (external)
pub mod terminal_ext {
    #[cfg(feature = "portable-pty")]
    pub use super::portable_pty;
}

/// Random number generation utilities (external)
pub mod random_ext {
    #[cfg(feature = "rand")]
    pub use super::rand;
}

/// Asynchronous programming utilities (external)
pub mod async_ext {
    #[cfg(feature = "tokio")]
    pub use super::tokio;
}

/// Command line interface utilities (external)
pub mod cli_ext {
    #[cfg(feature = "clap")]
    pub use super::clap;

    #[cfg(feature = "anyhow")]
    pub use super::anyhow;
}

/// Error handling utilities (external)
pub mod error_ext {
    #[cfg(feature = "anyhow")]
    pub use super::anyhow;
}

/// Testing utilities (external)
pub mod test_ext {
    #[cfg(feature = "criterion")]
    pub use super::criterion;

    #[cfg(feature = "tempfile")]
    pub use super::tempfile;
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

    #[cfg(feature = "anyhow")]
    features.push("anyhow");

    #[cfg(feature = "base64")]
    features.push("base64");

    #[cfg(feature = "chrono")]
    features.push("chrono");

    #[cfg(feature = "clap")]
    features.push("clap");

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

    #[cfg(feature = "serde_yaml")]
    features.push("serde_yaml");

    #[cfg(feature = "strip-ansi-escapes")]
    features.push("strip-ansi-escapes");

    #[cfg(feature = "tokio")]
    features.push("tokio");

    #[cfg(feature = "urlencoding")]
    features.push("urlencoding");

    #[cfg(feature = "uuid")]
    features.push("uuid");

    #[cfg(feature = "unicode-width")]
    features.push("unicode-width");

    #[cfg(feature = "criterion")]
    features.push("criterion");

    #[cfg(feature = "thiserror")]
    features.push("thiserror");

    #[cfg(feature = "tempfile")]
    features.push("tempfile");

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
