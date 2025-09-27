// Regular expression processing via regex
// Shaped module with common re-exports

// Re-export everything from regex
pub use regex::*;

// Common types and functions (explicit for better IDE support)
pub use regex::{Regex, RegexBuilder, Captures, Match, Replacer};

// Common regex set types
pub use regex::{RegexSet, RegexSetBuilder};

// Commonly used result type
pub type Result<T> = std::result::Result<T, regex::Error>;