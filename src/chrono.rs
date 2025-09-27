// Date and time handling via chrono
// Shaped module with common re-exports and convenience prelude

// Re-export everything from chrono
pub use chrono::*;

// Common types (explicit for better IDE support)
pub use chrono::{DateTime, Utc, Local, Duration, NaiveDateTime, NaiveDate, NaiveTime};

// TimeZone traits
pub use chrono::TimeZone;

// Prelude module for convenient imports
pub mod prelude {
    pub use chrono::prelude::*;
}