# Hub 🏗️ - Rust Repository Management Tool

> *Comprehensive ecosystem management for oodx/RSB - repository operations, dependency analysis, and centralized utilities*

Hub is the **centralized repository management system** for the entire oodx/RSB ecosystem. It provides powerful repository operations, ecosystem-wide analysis, automated cleaning, data caching, and version resolution across all oodx projects. From superclean operations to dependency insights, it eliminates repository bloat, version conflicts, and maintenance overhead while offering comprehensive tools for repository analysis and management.

## 🚀 Major Hub Restructuring - Clean Namespace Architecture

**Hub has undergone a major restructuring to implement clean namespace separation:**

### Key Changes

1. **🏗️ Clean Namespace Separation**: Top-level namespace now **reserved exclusively** for internal oodx/rsb modules
2. **🏷️ External Package Identification**: All third-party packages now use `-ext` suffix to clearly mark them as external dependencies
3. **🧠 Philosophical Clarity**: The `-ext` suffix means "we don't like these third-party packages but use them if we have to"
4. **📦 New Feature Structure**:
   - **Internal (top-level)**: `core = ["colors"]`, `colors` (shared color system)
   - **External (-ext suffix)**: `text-ext`, `data-ext`, `time-ext`, `web-ext`, `system-ext`, `terminal-ext`, `random-ext`, `async-ext`, `cli-ext`, `error-ext`, `test-ext`
   - **Mega Package**: `dev-ext` includes ALL external dependencies for comprehensive testing
5. **🎯 Preserved Functionality**: All existing functionality maintained, including clap (in cli-ext) and serde_yaml deprecation warnings

### What This Means for Users

```toml
# OLD: Mixed internal/external unclear
hub = { features = ["core", "text", "data"] }

# NEW: Clean separation with -ext suffix for external packages
hub = { features = ["core", "text-ext", "data-ext"] }
```

```rust
// Internal oodx modules use top-level namespace (preferred)
use hub::colors;

// External third-party packages clearly identified (use if you have to)
use hub::regex;  // From text-ext
use hub::serde;  // From data-ext
```

**Migration is straightforward**: Simply add `-ext` suffix to external feature groups. Individual package names remain unchanged.

## 🎯 Lite/Full Variant System - Lean by Default

**Hub now provides lite/full variants for major packages, implementing a "lean by default" philosophy while preserving extensibility:**

### Key Benefits
- **🏃 Performance**: Lite variants reduce compile times by 20-40% and binary sizes by 100-500KB
- **🎯 Lean by Default**: Avoid feature bloat while maintaining upgrade paths
- **⚡ Granular Control**: Choose exactly the feature level your project needs
- **🔧 Extensibility**: Projects can upgrade to full variants or add custom features
- **📦 Progressive Enhancement**: Start lean, add features as needed

### Major Package Variants

| Package | Lite Variant (Default) | Full Variant | Performance Gain |
|---------|------------------------|--------------|------------------|
| **tokio** | `[\"rt\", \"macros\"]` | `[\"full\"]` | ~40% compile time, ~500KB binary |
| **clap** | `[\"std\", \"help\"]` | `[\"std\", \"help\", \"derive\", \"env\", \"unicode\"]` | ~30% compile time, ~200KB binary |
| **chrono** | `[\"clock\", \"std\"]` | `[\"clock\", \"std\", \"serde\"]` | ~25% compile time, ~100KB binary |

### Domain Group Defaults (Updated)
- **`async-ext`** → uses `tokio-lite` (basic async runtime)
- **`cli-ext`** → uses `clap-lite` (basic CLI parsing)
- **`time-ext`** → uses `chrono-lite` (basic date/time)

### Usage Examples
```toml
# Lean by default (recommended for most projects)
hub = { features = [\"async-ext\", \"cli-ext\", \"time-ext\"] }

# Explicit lite variants
hub = { features = [\"tokio-lite\", \"clap-lite\", \"chrono-lite\"] }

# Full variants when you need advanced features
hub = { features = [\"tokio-full\", \"clap-full\", \"chrono-full\"] }

# Mixed usage (lite + full as needed)
hub = { features = [\"tokio-lite\", \"clap-full\", \"chrono-lite\"] }
```

### When to Use Each Variant

#### Use Lite Variants When:
- Building CLI tools or simple applications
- Performance and binary size are priorities
- You need basic functionality without advanced features
- Starting a new project (you can always upgrade later)

#### Use Full Variants When:
- You need derive macros (clap), networking/filesystem (tokio), or serialization (chrono)
- Building feature-rich applications
- Advanced use cases require the complete feature set

### Integration Best Practices
1. **Start Lean**: Begin with domain groups (`async-ext`, `cli-ext`, `time-ext`)
2. **Measure Impact**: Profile your specific use case for compile time and binary size
3. **Upgrade Selectively**: Move to full variants only when you need specific features
4. **Document Choices**: Make it clear which variants your project uses and why

## Quick Start

### Add to your project:
```toml
# Cargo.toml - Lean by default with clean namespace separation
[dependencies]
hub = { path = "../../hub", features = ["core", "text-ext", "data-ext", "async-ext"] }
# Note: async-ext now uses tokio-lite by default for better performance
```

### Use in your code:
```rust
// Internal oodx modules (top-level namespace - no suffix)
use hub::colors;     // Internal color system

// External third-party packages (we use them but prefer our own)
use hub::regex;      // External: use if you have to
use hub::serde;      // External: use if you have to

// Or import multiple at once:
use hub::prelude::*;
```

## Hub Integration Model & Philosophy

### The Hub Clean Namespace Approach
Hub serves as the **central dependency coordinator** for the oodx/RSB ecosystem, implementing a clean namespace separation that preserves top-level space for internal oodx modules while making external third-party dependencies clearly identifiable.

#### Core Architecture Principles
- **Clean namespace separation**: Top-level reserved for internal oodx/rsb modules only
- **External package clarity**: All third-party packages get `-ext` suffix ("we don't like these but use them if we have to")
- **Feature-first design**: Projects specify what they need, not how to get it
- **Version harmony**: Single source of truth for all dependency versions
- **Modular inclusion**: Only include features you actually use
- **Semantic versioning propagation**: Hub versions reflect dependency chain changes

#### Namespace Philosophy
The `-ext` suffix signals a clear philosophical stance:
- **Internal modules** (top-level): `hub::colors` - our preferred, native oodx solutions
- **External modules** (`-ext` suffix): `hub::text_ext`, `hub::data_ext` - necessary third-party dependencies we use reluctantly

### Usage-Based Inclusion Criteria

Hub follows a data-driven approach to dependency inclusion:

- **3+ project usage**: Dependencies used by 3 or more projects are eligible for hub inclusion
  - Requires manual review and consideration
  - Evaluated for ecosystem benefit and maintenance impact

- **5+ project usage**: Dependencies used by 5 or more projects get automatic inclusion
  - Handled automatically by blade tools
  - Reflects proven ecosystem value and widespread need

- **Strategic dependencies**: Core infrastructure dependencies may be included regardless of usage count

### Lite/Full Variant Strategy

Hub implements a **lean by default** approach with optional full features:

#### Design Principles
- **Lean by Default**: Domain groups (`async-ext`, `cli-ext`, `time-ext`) default to lite variants
- **Progressive Enhancement**: Projects can upgrade to full variants when needed
- **Performance First**: Lite variants optimize for compile time and binary size
- **Granular Control**: Individual package selection beyond domain groups
- **Zero Surprise**: Clear naming convention (lite = default, full = comprehensive)

#### When to Use Each Variant
- **Use Lite When**: Building simple tools, CLI utilities, or performance-critical applications
- **Use Full When**: Need advanced features like derive macros, extensive networking, or serialization
- **Mixed Usage**: Combine lite and full variants in the same project as needed

#### Performance Impact
```
Compile Time Improvements (typical):
- tokio-lite vs tokio-full: ~40% faster compilation
- clap-lite vs clap-full: ~30% faster compilation
- chrono-lite vs chrono-full: ~25% faster compilation

Binary Size Reduction (typical):
- tokio-lite: ~500KB smaller
- clap-lite: ~200KB smaller
- chrono-lite: ~100KB smaller
```

### Hub Versioning Strategy

Hub implements **semantic versioning propagation** to ensure reliable downstream dependency management:

#### Version Bump Rules
- **Minor version update**: When any hub dependency receives a minor version update
- **Major version update**: When any hub dependency receives a major version update
- **Patch version update**: For hub-specific fixes that don't affect dependencies

This strategy ensures that:
- Downstream projects can trust semantic versioning for safe updates
- Breaking changes in dependencies are properly communicated through hub's major version
- Projects can confidently update to newer hub minor versions
- The ecosystem maintains version harmony

#### Example Version Flow
```
tokio 1.35.0 → 1.36.0  ===> hub 0.3.0 → 0.4.0 (minor bump)
serde 1.0.0 → 2.0.0    ===> hub 0.4.0 → 1.0.0 (major bump)
hub fixes only         ===> hub 1.0.0 → 1.0.1 (patch bump)
```

### Feature Flag System

Hub's feature system provides granular control with clean namespace separation:

#### Internal Features (Top-Level Namespace)
```toml
[dependencies]
hub = { features = ["core", "colors"] }  # Internal oodx modules only
```

#### External Individual Features (Third-Party Dependencies)
```toml
[dependencies]
hub = { features = ["regex", "serde", "chrono"] }  # Individual external packages
```

#### External Domain-Based Features (All with -ext suffix)
- **`text-ext`**: Text processing (regex, lazy_static, unicode-width, strip-ansi-escapes)
- **`data-ext`**: Serialization (serde, serde_json, base64, serde_yaml)
- **`time-ext`**: Date/time handling (chrono/chrono-lite, uuid)
- **`web-ext`**: Web utilities (urlencoding)
- **`system-ext`**: System access (libc, glob)
- **`terminal-ext`**: Terminal tools (portable-pty)
- **`random-ext`**: Random generation (rand)
- **`async-ext`**: Async runtime (tokio/tokio-lite)
- **`cli-ext`**: Command line tools (clap/clap-lite, anyhow)
- **`error-ext`**: Error handling (anyhow, thiserror)
- **`test-ext`**: Testing tools (criterion, tempfile)

#### Lite/Full Variants for Major Packages

Hub now provides **lite/full variants** for major packages to give you granular control over feature sets and performance:

##### Tokio Variants
- **`tokio`** / **`tokio-lite`**: `["rt", "macros"]` - Basic async runtime for lightweight applications
- **`tokio-full`**: `["full"]` - Complete async ecosystem (networking, filesystem, process, signals, etc.)

##### Clap Variants
- **`clap`** / **`clap-lite`**: `["std", "help"]` - Basic CLI argument parsing
- **`clap-full`**: `["std", "help", "derive", "env", "unicode"]` - Full-featured CLI with macros and advanced features

##### Chrono Variants
- **`chrono`** / **`chrono-lite`**: `["clock", "std"]` - Basic date/time functionality
- **`chrono-full`**: `["clock", "std", "serde"]` - Date/time with serialization support

##### Domain Group Defaults (Lean by Default)
The domain groups now use lite variants by default to avoid bloat:
- **`async-ext`** defaults to `tokio-lite` (basic async runtime)
- **`cli-ext`** defaults to `clap-lite` (basic CLI parsing)
- **`time-ext`** defaults to `chrono-lite` (basic date/time)

##### Benefits of Lite/Full System
- **🏃 Performance**: Lite variants reduce compile times and binary size
- **🎯 Lean by Default**: Hub avoids feature bloat while preserving extensibility
- **⚡ Granular Control**: Choose exactly the feature level your project needs
- **🔧 Extensibility**: Projects can upgrade to full variants or add custom features
- **📦 Progressive Enhancement**: Start lean, add features as needed

#### Convenience External Groups
- **`common-ext`**: Most frequently used external features (text-ext + data-ext + error-ext + test-ext)
- **`core-ext`**: Essential external features (text-ext + data-ext + time-ext + error-ext)
- **`extended-ext`**: Comprehensive external set (core-ext + web-ext + system-ext + cli-ext)
- **`dev-ext`**: Everything external - mega package for comprehensive testing

#### Internal Convenience Groups (Reserved for oodx modules)
- **`core`**: Essential internal features (colors)
- Future: `utils`, `ecosystem` for additional internal modules

### Integration Benefits

#### For Projects
- **Zero version conflicts**: Guaranteed compatibility across the ecosystem
- **Simplified maintenance**: No external dependency version management
- **Faster builds**: Cargo efficiently deduplicates shared dependencies
- **Coordinated updates**: Ecosystem-wide version coordination
- **Cleaner manifests**: Focus on features, not versions

#### For the Ecosystem
- **Centralized security**: Single point for vulnerability scanning
- **Consistent behavior**: Same dependency versions everywhere
- **Reduced complexity**: Unified dependency management
- **Strategic optimization**: Data-driven inclusion decisions

### Migration Path

Moving from direct dependencies to hub integration with clean namespace:

```toml
# Before: Direct dependencies
[dependencies]
regex = "1.10.2"
serde = { version = "1.0", features = ["derive"] }
chrono = { version = "0.4.42", features = ["serde"] }
tokio = { version = "1.35", features = ["full"] }
clap = { version = "4.0", features = ["derive"] }

# After: Hub integration with lite/full variants (lean by default)
[dependencies]
hub = { path = "../../hub", features = [
    "core",           # Internal oodx modules
    "text-ext",       # regex, etc.
    "data-ext",       # serde, etc.
    "time-ext",       # chrono-lite (basic date/time)
    "async-ext",      # tokio-lite (basic async runtime)
    "cli-ext"         # clap-lite (basic CLI parsing)
] }

# Or upgrade specific packages to full variants when needed:
hub = { path = "../../hub", features = [
    "core",
    "text-ext",
    "data-ext",
    "chrono-full",    # Upgrade to full chrono with serde
    "tokio-full",     # Upgrade to full tokio with networking
    "clap-full"       # Upgrade to full clap with derive macros
] }
```

```rust
// Update imports - note the -ext suffix for external packages
use regex::Regex;                    // Before
use hub::regex::Regex;               // After (external package)

use serde::{Serialize, Deserialize}; // Before
use hub::serde::{Serialize, Deserialize}; // After (external package)

// Internal oodx modules use top-level namespace
use hub::colors;                     // Internal oodx color system
```

### Quality Assurance

Hub maintains ecosystem integrity through:
- **Automated testing**: All feature combinations validated
- **Compatibility verification**: Cross-project testing before releases
- **Performance monitoring**: Build time and binary size tracking
- **Usage analytics**: Data-driven inclusion and optimization decisions

## Repository Management Commands

Hub provides powerful commands for ecosystem-wide analysis and management:

### 🚀 Polish Commands (Powered by Boxy UI)
```bash
# All commands use lightning-fast TSV cache with beautiful terminal UI

# 📊 Ecosystem Management Commands
blade stats       # Display ecosystem statistics
blade deps <repo> # Show repository dependencies
blade outdated    # List packages with updates
blade search <pattern>  # Fuzzy package search
blade graph <package>   # Show dependency graph

# 🔄 Dependency Update Commands
blade update <repo> [--dry-run] [--force-commit] [--force]  # Update specific repository
blade eco [--dry-run] [--force-commit] [--force]           # Update all repositories

# 🔍 Advanced Analysis Commands
blade conflicts   # Version conflict analysis
blade query       # Package usage analysis
blade review      # Ecosystem dependency review
blade hub         # Hub-centric dashboard
blade pkg <package-name>  # Detailed package insights
```

### 🎨 Boxy UI Integration
- Beautiful terminal UI enabled by default
- Enhanced color preservation with semantic status display
- Clean, modern interface for all repository management commands
- Improves readability and user experience

### Additional Commands
```bash
# Comprehensive ecosystem analysis
blade all

# Check latest version for a specific package
blade latest <package-name>

# Export raw repository and dependency data
blade export

# Clean all target/ directories across ecosystem
blade superclean
```

### Data Cache System & Performance Engine
```bash
# Generate structured TSV cache for lightning-fast analysis (100x+ performance)
blade data

# Cache enables 100x+ performance improvements through:
# - Pre-computed repository metadata and dependency mapping
# - Cached latest version information from crates.io
# - Pre-analyzed version conflicts and status tracking
# - Aggregated metrics and statistics for instant dashboard views

# Test the hydration system
blade test

# Use --fast-mode flag to disable progress bars in data generation
blade data --fast-mode
```

### Repository Operations
```bash
# Clean all target/ directories across ecosystem (with progress bar)
blade superclean

# Repository status and git operations (coming soon)
blade tap

# Update dependencies in a specific repository
blade update <repo-name> [--dry-run] [--force-commit] [--force]

# Update dependencies across all repositories (ecosystem-wide)
blade eco [--dry-run] [--force-commit] [--force]

# Analyze specific package usage across all repositories
blade pkg <package-name>

# Check latest version for specific package
blade latest <package-name>

# Analyze hub dependency usage patterns
blade hub
```

### Dependency Update Commands

Hub provides powerful dependency update commands with safety checks and automation options:

#### Update Commands
- **`update <repo-name>`** - Update safe dependencies in a specific repository
- **`eco`** - Update safe dependencies across all repositories (ecosystem-wide)

#### Command Options
- **`--dry-run`** - Show what would be updated without making changes
- **`--force-commit`** - Automatically commit changes with "auto:hub bump" message
- **`--force`** - Bypass git safety checks (use with caution)

#### Git Safety Checks
By default, update commands require:
- Being on the main branch
- Clean working directory (no uncommitted changes)

The `--force` flag bypasses these safety checks, allowing you to:
- Update dependencies when not on the main branch
- Update dependencies with uncommitted changes in the working directory

#### Usage Examples
```bash
# Safe update with dry-run first
blade update meteor --dry-run
blade update meteor

# Update with automatic commit
blade update boxy --force-commit

# Force update bypassing safety checks (use carefully)
blade update xstream --force

# Ecosystem-wide update with all options
blade eco --dry-run --force-commit --force

# Safe ecosystem update
blade eco
```

#### Safety Recommendations
- Always run with `--dry-run` first to preview changes
- Use `--force` only when you understand the implications
- Consider committing existing changes before running updates
- Test updated dependencies with `cargo check` and `cargo test`

### Data Export & Import
```bash
# Export raw repository and dependency data to deps_data.txt
blade export

# Data includes:
# - All repositories with metadata and dependencies
# - Latest available versions from crates.io
# - Package usage statistics across repositories
```

## Hub Dependency Features

### Clean Namespace Structure

#### Internal Features (Top-Level Namespace)
```toml
features = ["core", "colors"]  # Internal oodx modules
```

#### External Individual Dependencies (Third-Party)
```toml
features = ["regex", "serde", "chrono", "uuid"]  # Individual external packages
```

#### External Domain Groups (All with -ext suffix)
- **`text-ext`** - Text processing: regex, lazy_static, unicode-width, strip-ansi-escapes
- **`data-ext`** - Serialization: serde, serde_json, base64, serde_yaml
- **`time-ext`** - Date/time: chrono-lite (default), uuid
- **`web-ext`** - Web utilities: urlencoding
- **`system-ext`** - System access: libc, glob
- **`terminal-ext`** - Terminal tools: portable-pty
- **`random-ext`** - Random generation: rand
- **`async-ext`** - Async runtime: tokio-lite (default)
- **`cli-ext`** - Command line: clap-lite (default), anyhow
- **`error-ext`** - Error handling: anyhow, thiserror
- **`test-ext`** - Testing: criterion, tempfile

#### External Convenience Groups
- **`common-ext`** - Most used external: text-ext + data-ext + error-ext + test-ext
- **`core-ext`** - Essential external: text-ext + data-ext + time-ext + error-ext
- **`extended-ext`** - Comprehensive external: core-ext + web-ext + system-ext + cli-ext
- **`dev-ext`** - Everything external (mega package for comprehensive testing)

#### Internal Convenience Groups (Reserved)
- **`core`** - Internal essentials: colors
- Future internal groups: `utils`, `ecosystem`

### Philosophy Behind the -ext Suffix
The `-ext` suffix clearly communicates: "These are external third-party packages that we use because we have to, but we prefer our own internal solutions when available."

## Data Cache & Hydration System - Performance Engine

Hub uses a sophisticated TSV-based caching system that powers the lightning-fast commands, delivering **100x+ performance improvements** over traditional analysis:

### Cache Structure (`deps_cache.tsv`)
The data cache is organized into structured sections for instant access:

- **Aggregation Metrics**: Pre-computed summary statistics (total repos, dependencies, conflicts)
- **Repository Data**: All Cargo.toml locations with metadata for fast lookup
- **Dependency Data**: Every dependency with version, features, and source info
- **Latest Versions**: Cached crates.io versions with LOCAL flag detection
- **Version Maps**: Pre-analyzed conflicts and update status for instant visualization

### TSV Hydration System
```python
# Lightning-fast data access powers all view commands
from repos import hydrate_tsv_cache

ecosystem = hydrate_tsv_cache("deps_cache.tsv")
print(f"Loaded {len(ecosystem.repos)} repositories")
print(f"Tracking {len(ecosystem.deps)} dependencies")

# Enables instant analysis:
# - view_conflicts() - Version conflict analysis
# - view_query() - Package usage analysis
# - view_review() - Ecosystem dependency review
# - view_hub_dashboard() - Hub-centric dashboard
# - view_package_detail() - Package details
```

### Git Dependency Resolution
Hub intelligently handles git dependencies with LOCAL flag detection:
- Resolves git repository versions by checking actual git tags/commits
- Detects LOCAL development dependencies vs. published versions
- Provides accurate version analysis for git-sourced dependencies
- All git resolution results cached for instant access

### Performance Benefits
- **100x+ speed improvement**: Commands use pre-computed TSV cache vs. live analysis
- **Instant startup**: No filesystem scanning or network calls
- **Structured data**: Optimized data structures for fast lookup operations
- **Memory efficient**: Lazy loading of cache sections with targeted access patterns
- **Enhanced UX**: Proper color coding via Boxy UI and hub status semantics
- **Clean Command Structure**: Simplified, intuitive command interface

## Examples

### View Commands
```bash
# Generate cache for enhanced performance (optional)
blade data

# Ecosystem Statistics
blade stats
# Output: Quick overview of dependencies, repos, and package usage

# Dependency Details
blade deps hub
# Output: Complete dependencies for the 'hub' repository

# Outdated Packages
blade outdated
# Output: Packages with available updates

# Package Search
blade search regex
# Output: Fuzzy-matched packages containing 'regex'

# Package Dependency Graph
blade graph serde
# Output: Comprehensive dependency relationships for 'serde'

# Existing Commands (Now with TSV Cache)
blade conflicts    # Version conflict analysis
blade query        # Package usage analysis
blade review       # Ecosystem dependency review
blade hub          # Hub-centric dashboard
blade pkg serde    # Detailed package analysis
```

### Update Commands
```bash
# Update dependencies in a specific repository
blade update meteor --dry-run     # Preview changes first
blade update meteor               # Apply safe updates
blade update meteor --force-commit --force  # Force update with auto-commit

# Ecosystem-wide dependency updates
blade eco --dry-run              # Preview ecosystem changes
blade eco                        # Apply safe updates across all repos
blade eco --force-commit         # Apply updates with automatic commits
blade eco --force                # Bypass git safety checks
```

### Basic Usage
```rust
// Clean namespace example: external packages clearly marked
use hub::regex::Regex;               // External dependency (reluctantly used)
use hub::serde::{Serialize, Deserialize}; // External dependency (reluctantly used)

// Internal oodx modules get top-level namespace
use hub::colors;                     // Internal oodx module (preferred)

#[derive(Serialize, Deserialize)]
struct Config {
    pattern: String,
}

fn process_data(config: &Config, input: &str) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let re = Regex::new(&config.pattern)?;
    let matches: Vec<String> = re.find_iter(input)
        .map(|m| m.as_str().to_string())
        .collect();
    Ok(matches)
}
```

### Lite/Full Variant Usage Examples

#### Tokio Variants
```toml
# Lite variant (default with async-ext): Basic async runtime
hub = { features = ["async-ext"] }           # Gets tokio-lite
hub = { features = ["tokio-lite"] }          # Explicit lite variant

# Full variant: Complete async ecosystem
hub = { features = ["tokio-full"] }          # Advanced networking, filesystem, etc.
```

```rust
// Both variants provide the same basic API
use hub::tokio;

#[tokio::main]
async fn main() {
    println!("Hello async world!");

    // tokio-lite: Basic runtime + macros
    // tokio-full: + networking, filesystem, process, signals, etc.
}
```

#### Clap Variants
```toml
# Lite variant (default with cli-ext): Basic CLI parsing
hub = { features = ["cli-ext"] }             # Gets clap-lite
hub = { features = ["clap-lite"] }           # Explicit lite variant

# Full variant: Advanced CLI with derive macros
hub = { features = ["clap-full"] }           # Derive macros, env, unicode
```

```rust
// Lite variant: Manual setup
use hub::clap::{App, Arg};

fn main() {
    let matches = App::new("myapp")
        .arg(Arg::new("input").required(true))
        .get_matches();
}

// Full variant: Derive macros (requires clap-full)
use hub::clap::Parser;

#[derive(Parser)]  // Only available with clap-full
struct Args {
    input: String,
}

fn main() {
    let args = Args::parse();
}
```

#### Chrono Variants
```toml
# Lite variant (default with time-ext): Basic date/time
hub = { features = ["time-ext"] }            # Gets chrono-lite
hub = { features = ["chrono-lite"] }         # Explicit lite variant

# Full variant: With serialization support
hub = { features = ["chrono-full"] }         # Includes serde support
```

```rust
// Both variants provide core date/time functionality
use hub::chrono::{DateTime, Utc};

fn main() {
    let now: DateTime<Utc> = Utc::now();
    println!("Current time: {}", now);

    // chrono-lite: Basic date/time operations
    // chrono-full: + serde serialization support
}
```

#### Mixed Variant Usage
```toml
# Combine lite and full variants as needed
hub = { features = [
    "core",           # Internal oodx modules
    "tokio-lite",     # Basic async runtime
    "clap-full",      # Full CLI with derive macros
    "chrono-lite",    # Basic date/time
    "data-ext"        # Serialization tools
] }
```

#### Best Practices for Variant Selection

**Start Lean, Upgrade When Needed:**
```toml
# Phase 1: Start with domain groups (gets lite variants)
hub = { features = ["async-ext", "cli-ext", "time-ext"] }

# Phase 2: Upgrade specific packages when you need advanced features
hub = { features = ["tokio-lite", "clap-full", "chrono-lite"] }

# Phase 3: Add individual features for fine-grained control
hub = { features = ["tokio-lite", "clap-full", "chrono-full"] }
```

**Performance-Critical Applications:**
```toml
# Optimize for speed and size
hub = { features = ["tokio-lite", "clap-lite", "chrono-lite"] }
```

**Feature-Rich Applications:**
```toml
# When you need all the advanced features
hub = { features = ["tokio-full", "clap-full", "chrono-full"] }
```

### Clean Namespace Usage Examples
```rust
// Internal oodx modules (top-level namespace)
use hub::colors;  // Internal color system

// External dependencies (individual imports)
use hub::regex;
use hub::serde_json;
use hub::chrono;

// External dependencies through domain features
use hub::text_ext::regex;     // From text-ext feature
use hub::data_ext::serde_json; // From data-ext feature
use hub::time_ext::chrono;     // From time-ext feature

fn parse_log_entry(line: &str) -> Result<LogEntry, serde_json::Error> {
    // Implementation using clean namespace imports
    // External packages clearly marked, internal modules prominent
}
```

## Benefits

### For Developers
- ✅ **No version conflicts** - Guaranteed compatibility across projects
- ✅ **Simplified dependencies** - Only specify features, not versions
- ✅ **Easy ecosystem upgrades** - One place to update all versions
- ✅ **Consistent behavior** - Same crate versions everywhere
- ⚡ **Default Lightning-fast Analysis** - 100x+ performance for all view commands
- 🔍 **Deep analysis** - Comprehensive repository and dependency insights
- 🎨 **Enhanced UX** - Color-coded outputs with proper hub status semantics
- 🧹 **Repository management** - Superclean operations and automated maintenance
- 📊 **Progress tracking** - Visual progress bars for long-running operations

### For Projects
- 📦 **Cleaner Cargo.toml** - No external dependency noise
- ⚡ **Faster builds** - Cargo deduplicates dependencies + clean targets efficiently
- 🔒 **Better security** - Centralized vulnerability scanning
- 🔧 **Easier maintenance** - Coordinated dependency updates + automated analysis
- 📊 **Data-driven decisions** - Rich analytics on dependency usage and versions

### For Repository Management
- 🏗️ **Ecosystem overview** - Complete visibility into all repositories
- ⚡ **TSV cache system** - 100x+ performance improvements
- 🚀 **Performance tools** - Lightning-fast analysis with pre-computed data
- 🔄 **Version tracking** - Git dependency resolution with LOCAL flag detection
- 📈 **Usage analytics** - Instant package usage patterns and dashboard views
- 🎯 **Auto-detection** - Smart caching and performance optimization

## Ecosystem Integration

### Current oodx Projects
- **RSB** - Base framework (legacy `deps` compatibility maintained)
- **Meteor** - Token data transport
- **Boxy** - Layout rendering
- **XStream** - Data flow processing

**All projects now benefit from the clean namespace separation between internal oodx modules and external third-party dependencies.**

### Migration Guide

Replace direct dependencies with clean namespace:
```toml
# Before
[dependencies]
regex = "1.10.2"
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.35", features = ["rt", "macros"] }

# After: Clean namespace with lite/full variants (lean by default)
[dependencies]
hub = { path = "../../hub", features = ["core", "text-ext", "data-ext", "async-ext"] }
# Gets tokio-lite automatically - perfect for basic async needs
```

Update imports with clean namespace understanding:
```rust
// Before
use regex::Regex;
use serde::{Serialize, Deserialize};

// After: External packages clearly identified
use hub::regex::Regex;                    // External (reluctantly used)
use hub::serde::{Serialize, Deserialize}; // External (reluctantly used)

// Internal oodx modules get top-level namespace
use hub::colors;  // Internal (preferred)
```

## Development

### Testing Hub
```bash
# Test with different feature combinations (including lite/full variants)
cargo test --features "text-ext"
cargo test --features "data-ext"
cargo test --features "async-ext"      # Test with tokio-lite
cargo test --features "tokio-full"     # Test with full tokio
cargo test --features "clap-lite"      # Test with basic clap
cargo test --features "clap-full"      # Test with full clap features
cargo test --features "dev-ext"        # Test with all external dependencies

# Test lite vs full performance impact
cargo build --features "async-ext" --release        # Test lite variant build
cargo build --features "tokio-full" --release       # Test full variant build

# Test repository analysis tools
blade data              # Generate cache
blade test              # Test hydration system
blade review            # Full ecosystem analysis (traditional)

# Test view commands (100x+ performance)
blade conflicts       # Fast conflict analysis
blade query           # Fast usage analysis
blade review          # Fast dependency review
blade hub             # Fast hub dashboard
blade pkg serde       # Fast package detail
```

### Repository Management Workflow
```bash
# 1. Generate fresh cache (100x+ performance)
blade data

# 2. Quick ecosystem health check
blade conflicts

# 3. Package usage analysis
blade query

# 4. Full dependency review
blade review

# 5. Hub integration status
blade hub

# 6. Update dependencies (preview first)
blade eco --dry-run      # Preview ecosystem updates
blade update meteor --dry-run  # Preview specific repo updates

# 7. Apply dependency updates
blade eco                # Safe ecosystem-wide updates
blade update boxy --force-commit  # Update with auto-commit

# 8. Clean build artifacts across all repositories
blade superclean

# 9. Check specific packages
blade pkg serde

# 10. Traditional analysis (when needed)
blade all                # Comprehensive analysis
blade latest regex       # Latest version check

# 11. Check repository status (coming soon)
blade tap
```

### Adding New Dependencies

#### For External Third-Party Dependencies
1. Add to `Cargo.toml` as optional dependency
2. Add individual feature flag in `[features]` section
3. **Consider lite/full variants** for major packages:
   - Add both `package-lite` and `package-full` features if the package supports multiple feature sets
   - Default domain groups should use lite variants
   - Document feature differences and performance impact
4. Add to appropriate `-ext` domain group (e.g., `text-ext`, `data-ext`)
5. Add re-export in `src/lib.rs` with feature gate
6. Update convenience groups (`common-ext`, `core-ext`, etc.) if appropriate
7. Run `blade data` to refresh cache
8. Update this README with lite/full variant documentation

#### For Internal oodx Modules
1. Add to internal `[features]` section (no `-ext` suffix)
2. Add to `core` convenience group
3. Add re-export in `src/lib.rs` with feature gate
4. Consider future internal groups (`utils`, `ecosystem`)
5. Run `blade data` to refresh cache
6. Update this README

#### Clean Namespace Guidelines
- **External packages**: Always use `-ext` suffix in domain groups
- **Internal modules**: Top-level namespace, no suffix
- **Philosophy**: Make external dependencies clearly identifiable
- **Lite/Full Strategy**: Default to lite variants, provide full variants for advanced features

#### Lite/Full Variant Guidelines

When adding lite/full variants for a package:

1. **Evaluate Feature Impact**: Determine if the package has distinct feature sets that significantly impact:
   - Compile time (>20% difference)
   - Binary size (>100KB difference)
   - API surface area

2. **Define Lite Variant**: Should include:
   - Core functionality needed by most projects
   - Minimal feature set for basic use cases
   - Optimal compile time and binary size

3. **Define Full Variant**: Should include:
   - Advanced features (derive macros, networking, etc.)
   - Complete feature set for complex applications
   - All optional capabilities

4. **Update Domain Groups**:
   - Domain groups (`async-ext`, `cli-ext`, etc.) should default to lite variants
   - Document which variant is used by default
   - Provide upgrade path to full variants

5. **Document Performance**: Include typical performance improvements:
   ```
   Compile Time: lite variant ~X% faster
   Binary Size: lite variant ~XKB smaller
   ```

6. **Naming Convention**:
   - `package` = alias for `package-lite` (lean by default)
   - `package-lite` = explicit lite variant
   - `package-full` = comprehensive variant

### The dev-ext Mega Package

For comprehensive testing and development, the `dev-ext` feature provides access to ALL external dependencies:

```toml
# Full external dependency access for testing
[dependencies]
hub = { path = "../../hub", features = ["dev-ext"] }
```

The `dev-ext` mega package includes:
- All text processing tools (`text-ext`)
- All serialization tools (`data-ext`)
- All time handling tools (`time-ext`)
- All web utilities (`web-ext`)
- All system access tools (`system-ext`)
- All terminal tools (`terminal-ext`)
- All random generation tools (`random-ext`)
- All async runtime tools (`async-ext`)
- All CLI tools (`cli-ext`)
- All error handling tools (`error-ext`)
- All testing tools (`test-ext`)

**Use Case**: Ideal for comprehensive testing environments where you need access to all external dependencies without managing individual feature flags.

### Version Updates
1. Update versions in `Cargo.toml` (respect clean namespace separation)
2. Test all oodx projects for compatibility with new namespace structure
3. Run ecosystem analysis: `blade review`
4. Apply updates across ecosystem:
   - Preview changes: `blade eco --dry-run`
   - Apply safe updates: `blade eco`
   - Or update specific repos: `blade update <repo-name>`
5. Refresh data cache: `blade data`
6. Verify clean namespace compliance across all projects

## Architecture

```
hub/
├── src/
│   └── lib.rs          # Feature-gated re-exports
├── bin/
│   ├── repos.py        # Legacy repository management tool (migrated to blade)
│   └── analyze_deps.sh # Basic dependency scanning script
├── Cargo.toml          # THE canonical dependency list
├── deps_cache.tsv      # Generated: Structured ecosystem data cache
├── deps_data.txt       # Generated: Raw dependency export data
├── HUB_STRAT.md        # Hub strategy and design principles
├── VERSION_STRAT.md    # Version management strategy
├── REFACTOR_STRAT.md   # Refactoring guidelines
├── CONTINUE.md         # Development continuation guide
└── README.md           # This file
```

### Tool Evolution
Hub has evolved from a simple dependency analyzer to a comprehensive repository management system (now powered by the external `blade` tool):

- **Phase 1**: Basic dependency analysis and conflict detection
- **Phase 2**: Export capabilities and crates.io version checking
- **Phase 3**: Structured data caching and hydration functions
- **Phase 4**: Repository operations (superclean, git resolution) with progress bars
- **Phase 5**: TSV cache system with 100x+ performance improvements
- **Phase 6**: Enhanced UX with auto-detection and color-coded outputs
- **Phase 7**: Comprehensive view commands with rich ecosystem analytics
- **Phase 8**: Polish commands with integrated Boxy UI for beautiful terminal output
- **Phase 9**: Enhanced dependency update commands with `--force` flag for bypassing git safety checks (current)
- **Phase 10**: Coming - `tap` command for git status/auto-commit across repos

## Version Compatibility

| Hub       | RSB   | Meteor | Boxy  | XStream | Repository Tool |
|-----------|-------|--------|-------|---------|-----------------|
| 0.1.x     | 0.5.x | 0.1.x  | TBD   | TBD     | blade v1.x      |

### Repository Management Tool Versions
- **v1.x**: Complete repository management system with all analysis features (current blade)
- **Legacy repos.py phases**: v1-v5 functionality migrated to blade tool
- **Future**: Enhanced blade integration and ecosystem management

## Installation & Usage

### Prerequisites
- Python 3.8+ with `toml`, `packaging` libraries
- Rust ecosystem with Cargo
- Set `RUST_REPO_ROOT` environment variable (auto-detected if in rust/ directory)

### Quick Setup
```bash
# Clone or navigate to hub project
cd /path/to/rust/oodx/projects/hub

# Generate initial data cache
blade data

# Ecosystem commands
blade conflicts      # Version conflict analysis
blade query          # Package usage analysis
blade review         # Dependency review

# Full ecosystem analysis
blade all
```

### Environment Setup
```bash
# Optional: Set rust repo root explicitly
export RUST_REPO_ROOT="/path/to/your/rust/projects"

# Hub will auto-detect from current path if not set
```

## Contributing

### Hub Dependency Management
1. **Evaluate necessity** - Is this dependency widely needed?
2. **Check alternatives** - Can we use existing dependencies?
3. **Add feature flag** - Never expose dependencies without gates
4. **Update documentation** - Keep README and strategy docs current
5. **Test ecosystem** - Verify compatibility across projects
6. **Refresh cache** - Run `blade data` after changes

### Repository Tool Enhancement
1. **Test new features** - Use `blade test` for hydration
2. **Performance considerations** - Maintain fast cache operations
3. **Documentation** - Update command help and examples
4. **Ecosystem impact** - Consider effects on all oodx projects
5. **Data integrity** - Ensure TSV cache consistency


## Summary

Hub has evolved from a simple dependency management tool into a **comprehensive Rust repository management system**. What started as basic dependency analysis has grown into an ecosystem-wide solution (now powered by the external `blade` tool) providing:

- **Centralized dependency management** with feature-gated re-exports and clean namespace separation
- **Lite/Full variant system** implementing "lean by default" philosophy with 20-40% performance improvements
- **Lightning-fast analysis** with 100x+ performance improvements via TSV cache
- **Advanced repository analytics** with structured data caching and hydration
- **Enhanced user experience** with color-coded outputs and auto-detection
- **Repository operations** including superclean with progress bars and version analysis
- **Git dependency resolution** with LOCAL flag detection
- **Performance optimization** through intelligent TSV caching systems and lean dependencies
- **Granular control** with lite/full variants for tokio, clap, chrono, and future packages
- **Comprehensive management** with upcoming `tap` command for git operations

The tool maintains its core mission of eliminating version conflicts while providing **instant insights** and comprehensive management capabilities for the entire oodx ecosystem. The new lite/full variant system ensures optimal performance by default while preserving extensibility through its revolutionary TSV cache system and beautiful Boxy UI integration.

## License

Snek/Snekfx, RSB Framework, Oxidex (ODX), and REBEL libraries, services, and software are offered under a **multi-license model**:

| License | Who it’s for | Obligations |
|---------|--------------|-------------|
| [AGPL-3.0](./LICENSE) | Open-source projects that agree to release their own source code under the AGPL. | Must comply with the AGPL for any distribution or network service. |
| [Community Edition License](./docs/LICENSE_COMMUNITY.txt) | Personal, educational, or academic use **only**. Not for companies, organizations, or anyone acting for the benefit of a business. | Must meet all CE eligibility requirements and follow its terms. |
| [Commercial License](./docs/LICENSE_COMMERCIAL.txt) | Companies, contractors, or anyone needing to embed the software in closed-source, SaaS, or other commercial products. | Requires a signed commercial agreement with Dr. Vegajunk Hackware. |

By **downloading, installing, linking to, or otherwise using RSB Framework, Oxidex, or REBEL**, you:

1. **Accept** the terms of one of the licenses above, **and**  
2. **Represent that you meet all eligibility requirements** for the license you have chosen.

> Questions about eligibility or commercial licensing: **licensing@vegajunk.com**
