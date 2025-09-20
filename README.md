# Hub 🏗️ - Rust Repository Management Tool

> *Comprehensive ecosystem management for oodx/RSB - repository operations, dependency analysis, and centralized utilities*

Hub is the **centralized repository management system** for the entire oodx/RSB ecosystem. It provides powerful repository operations, ecosystem-wide analysis, automated cleaning, data caching, and version resolution across all oodx projects. From superclean operations to dependency insights, it eliminates repository bloat, version conflicts, and maintenance overhead while offering comprehensive tools for repository analysis and management.

## Quick Start

### Add to your project:
```toml
# Cargo.toml
[dependencies]
hub = { path = "../../hub", features = ["regex", "serde"] }
```

### Use in your code:
```rust
use hub::regex;      // Instead of: use regex;
use hub::serde;      // Instead of: use serde;

// Or import multiple at once:
use hub::prelude::*;
```

## Repository Management Commands

Hub provides powerful commands for ecosystem-wide analysis and management:

### 🚀 Polish Commands (Powered by Boxy UI)
```bash
# All commands use lightning-fast TSV cache with beautiful terminal UI

# 📊 Ecosystem Management Commands
./bin/repos.py stats       # Display ecosystem statistics
./bin/repos.py deps <repo> # Show repository dependencies
./bin/repos.py outdated    # List packages with updates
./bin/repos.py search <pattern>  # Fuzzy package search
./bin/repos.py graph <package>   # Show dependency graph

# 🔍 Advanced Analysis Commands
./bin/repos.py conflicts   # Version conflict analysis
./bin/repos.py query       # Package usage analysis
./bin/repos.py review      # Ecosystem dependency review
./bin/repos.py hub         # Hub-centric dashboard
./bin/repos.py pkg <package-name>  # Detailed package insights
```

### 🎨 Boxy UI Integration
- Beautiful terminal UI enabled by default
- Enhanced color preservation with semantic status display
- Clean, modern interface for all repository management commands
- Improves readability and user experience

### Additional Commands
```bash
# Comprehensive ecosystem analysis
./bin/repos.py all

# Check latest version for a specific package
./bin/repos.py latest <package-name>

# Export raw repository and dependency data
./bin/repos.py export
```

### Data Cache System & Performance Engine
```bash
# Generate structured TSV cache for lightning-fast analysis (100x+ performance)
./bin/repos.py data

# Cache enables 100x+ performance improvements through:
# - Pre-computed repository metadata and dependency mapping
# - Cached latest version information from crates.io
# - Pre-analyzed version conflicts and status tracking
# - Aggregated metrics and statistics for instant dashboard views

# Test the hydration system
./bin/repos.py test

# Use --fast-mode flag to disable progress bars in data generation
./bin/repos.py data --fast-mode
```

### Repository Operations
```bash
# Clean all target/ directories across ecosystem (with progress bar)
./bin/repos.py superclean

# Repository status and git operations (coming soon)
./bin/repos.py tap

# Analyze specific package usage across all repositories
./bin/repos.py pkg <package-name>

# Check latest version for specific package
./bin/repos.py latest <package-name>

# Analyze hub dependency usage patterns
./bin/repos.py hub
```

### Data Export & Import
```bash
# Export raw repository and dependency data to deps_data.txt
./bin/repos.py export

# Data includes:
# - All repositories with metadata and dependencies
# - Latest available versions from crates.io
# - Package usage statistics across repositories
```

## Hub Dependency Features

### Individual Dependencies
```toml
features = ["regex", "serde", "chrono", "uuid"]
```

### Domain Groups
- **`text`** - Text processing: regex, lazy_static
- **`data`** - Serialization: serde, serde_json, base64
- **`time`** - Date/time: chrono, uuid
- **`web`** - Web utilities: urlencoding
- **`system`** - System access: libc, glob
- **`random`** - Random generation: rand
- **`dev`** - Development tools: portable-pty

### Convenience Groups
- **`common`** - Most used: text + data
- **`core`** - Essential: text + data + time
- **`extended`** - Comprehensive: core + web + system
- **`all`** - Everything

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
./bin/repos.py data

# Ecosystem Statistics
./bin/repos.py stats
# Output: Quick overview of dependencies, repos, and package usage

# Dependency Details
./bin/repos.py deps hub
# Output: Complete dependencies for the 'hub' repository

# Outdated Packages
./bin/repos.py outdated
# Output: Packages with available updates

# Package Search
./bin/repos.py search regex
# Output: Fuzzy-matched packages containing 'regex'

# Package Dependency Graph
./bin/repos.py graph serde
# Output: Comprehensive dependency relationships for 'serde'

# Existing Commands (Now with TSV Cache)
./bin/repos.py conflicts    # Version conflict analysis
./bin/repos.py query        # Package usage analysis
./bin/repos.py review       # Ecosystem dependency review
./bin/repos.py hub          # Hub-centric dashboard
./bin/repos.py pkg serde    # Detailed package analysis
```

### Basic Usage
```rust
use hub::regex::Regex;
use hub::serde::{Serialize, Deserialize};

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

### Domain-Specific Imports
```rust
use hub::text::regex;
use hub::data::serde_json;
use hub::time::chrono;

fn parse_log_entry(line: &str) -> Result<LogEntry, serde_json::Error> {
    // Implementation using domain-specific imports
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

### Migration Guide

Replace direct dependencies:
```toml
# Before
[dependencies]
regex = "1.10.2"
serde = { version = "1.0", features = ["derive"] }

# After
[dependencies]
hub = { path = "../../hub", features = ["regex", "serde"] }
```

Update imports:
```rust
// Before
use regex::Regex;
use serde::{Serialize, Deserialize};

// After
use hub::regex::Regex;
use hub::serde::{Serialize, Deserialize};
```

## Development

### Testing Hub
```bash
# Test with different feature combinations
cargo test --features "text"
cargo test --features "data"
cargo test --features "all"

# Test repository analysis tools
./bin/repos.py data              # Generate cache
./bin/repos.py test              # Test hydration system
./bin/repos.py review            # Full ecosystem analysis (traditional)

# Test view commands (100x+ performance)
./bin/repos.py --conflicts       # Fast conflict analysis
./bin/repos.py --query           # Fast usage analysis
./bin/repos.py --review          # Fast dependency review
./bin/repos.py --hub-dashboard   # Fast hub dashboard
./bin/repos.py --pkg-detail serde # Fast package detail
```

### Repository Management Workflow
```bash
# 1. Generate fresh cache (100x+ performance)
./bin/repos.py data

# 2. Quick ecosystem health check
./bin/repos.py conflicts

# 3. Package usage analysis
./bin/repos.py query

# 4. Full dependency review
./bin/repos.py review

# 5. Hub integration status
./bin/repos.py hub

# 6. Clean build artifacts across all repositories
./bin/repos.py superclean

# 7. Check specific packages
./bin/repos.py pkg serde

# 8. Traditional analysis (when needed)
./bin/repos.py all                # Comprehensive analysis
./bin/repos.py latest regex       # Latest version check

# 9. Check repository status (coming soon)
./bin/repos.py tap
```

### Adding New Dependencies
1. Add to `Cargo.toml` as optional dependency
2. Add feature flag in `[features]` section
3. Add re-export in `src/lib.rs` with feature gate
4. Update domain collections if appropriate
5. Run `./bin/repos.py data` to refresh cache
6. Update this README

### Version Updates
1. Update versions in `Cargo.toml`
2. Test all oodx projects for compatibility
3. Run ecosystem analysis: `./bin/repos.py review`
4. Update projects to new hub version
5. Refresh data cache: `./bin/repos.py data`

## Architecture

```
hub/
├── src/
│   └── lib.rs          # Feature-gated re-exports
├── bin/
│   ├── repos.py        # Comprehensive repository management tool
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
Hub has evolved from a simple dependency analyzer to a comprehensive repository management tool (`repos.py`):

- **Phase 1**: Basic dependency analysis and conflict detection
- **Phase 2**: Export capabilities and crates.io version checking
- **Phase 3**: Structured data caching and hydration functions
- **Phase 4**: Repository operations (superclean, git resolution) with progress bars
- **Phase 5**: TSV cache system with 100x+ performance improvements
- **Phase 6**: Enhanced UX with auto-detection and color-coded outputs
- **Phase 7**: Comprehensive view commands with rich ecosystem analytics
- **Phase 8**: Polish commands with integrated Boxy UI for beautiful terminal output (current)
- **Phase 9**: Coming - `tap` command for git status/auto-commit across repos

## Version Compatibility

| Hub       | RSB   | Meteor | Boxy  | XStream | Repository Tool |
|-----------|-------|--------|-------|---------|-----------------|
| 0.1.x     | 0.5.x | 0.1.x  | TBD   | TBD     | repos.py v3.x   |

### Repository Management Tool Versions
- **v1.x**: Basic dependency analysis
- **v2.x**: Export functionality and latest version checking
- **v3.x**: Data caching, hydration, repository operations with progress bars
- **v4.x**: Polish commands with TSV cache (100x+ performance) and Boxy UI (current)
- **v5.x**: Planned - `tap` command and automated git operations

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
./bin/repos.py data

# Ecosystem commands
./bin/repos.py conflicts      # Version conflict analysis
./bin/repos.py query          # Package usage analysis
./bin/repos.py review         # Dependency review

# Full ecosystem analysis
./bin/repos.py all
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
6. **Refresh cache** - Run `./bin/repos.py data` after changes

### Repository Tool Enhancement
1. **Test new features** - Use `./bin/repos.py test` for hydration
2. **Performance considerations** - Maintain fast cache operations
3. **Documentation** - Update command help and examples
4. **Ecosystem impact** - Consider effects on all oodx projects
5. **Data integrity** - Ensure TSV cache consistency

## License

AGPL-3.0 - Same as the oodx ecosystem

---

## Summary

Hub has evolved from a simple dependency management tool into a **comprehensive Rust repository management system**. What started as basic dependency analysis has grown into an ecosystem-wide solution (`repos.py`) providing:

- **Centralized dependency management** with feature-gated re-exports
- **Lightning-fast analysis** with 100x+ performance improvements via TSV cache
- **Advanced repository analytics** with structured data caching and hydration
- **Enhanced user experience** with color-coded outputs and auto-detection
- **Repository operations** including superclean with progress bars and version analysis
- **Git dependency resolution** with LOCAL flag detection
- **Performance optimization** through intelligent TSV caching systems
- **Comprehensive management** with upcoming `tap` command for git operations

The tool maintains its core mission of eliminating version conflicts while providing **instant insights** and comprehensive management capabilities for the entire oodx ecosystem through its revolutionary TSV cache system and beautiful Boxy UI integration.

---

*One crate to rule them all, one crate to find them, one crate to bring them all, and in the ecosystem bind them.* 📦✨