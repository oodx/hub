// Command-line argument parsing via clap
// Shaped module with common re-exports and derive support

// Re-export everything from clap
pub use clap::*;

// Common types (explicit for better IDE support)
pub use clap::{Arg, ArgMatches, Command};

// Derive macros when enabled
#[cfg(feature = "clap-full")]
pub use clap::{Parser, Args, Subcommand, ValueEnum};

// Common builders
pub use clap::{ArgAction, builder};