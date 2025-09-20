# Hub: Centralized Dependency Management Strategy

## ✅ CURRENT IMPLEMENTATION STATUS

The hub strategy has been partially implemented with significant evolution:
- **TSV cache system**: Fully operational for dependency analysis (`./bin/repos.py`)
- **Analysis tools**: Comprehensive ecosystem views and management commands
- **Data structure**: Complete TSV schema documented (see lines 259-578)
- **Migration tracking**: Hub status monitoring operational via `./bin/repos.py hub`
- **Performance**: 100x+ improvement achieved through structured caching

**Current Command Interface**:
```bash
./bin/repos.py hub        # Hub integration dashboard
./bin/repos.py conflicts  # Version conflict detection
./bin/repos.py review     # Comprehensive ecosystem review
./bin/repos.py stats      # Ecosystem statistics and metrics
```

**Note**: The original "Cargohold" centralized dependency approach has evolved into a more flexible hub-based analysis and management system while maintaining the core goal of ecosystem coordination.

## Overview

Hub is the centralized dependency hub for all oodx/RSB ecosystem projects. It provides unified version management, consistent dependency resolution, and eliminates version conflicts across the entire project ecosystem.

## The Problem We're Solving

### Current Issues in oodx Ecosystem:
1. **Version Conflicts** - Different projects using different versions of the same crate
2. **Dependency Bloat** - Each project repeating same dependencies in Cargo.toml
3. **Upgrade Hell** - Manually updating versions across multiple projects
4. **Inconsistent Behavior** - Same crate, different versions = different behavior
5. **Maintenance Overhead** - Multiple dependency lists to keep in sync

### Example Problem Scenario:
```toml
# rsb/Cargo.toml
regex = "1.5.0"
serde = "1.0.160"

# meteor/Cargo.toml
regex = "1.6.0"        # Version conflict!
serde = "1.0.180"      # Different behavior!

# boxy/Cargo.toml
regex = "1.4.0"        # Even older version!
```

This creates:
- **Compilation conflicts** when projects depend on each other
- **Behavioral inconsistencies** across the ecosystem
- **Security risks** from outdated versions
- **Maintenance nightmare** during upgrades

## Hub Solution

### Centralized Dependencies Pattern:
```rust
// hub/src/lib.rs - Single source of truth
#[cfg(feature = "regex")]
pub use regex;

#[cfg(feature = "serde")]
pub use serde;

// All versions managed in ONE place
```

### Project Consumption:
```toml
# meteor/Cargo.toml - Clean dependency list
[dependencies]
cargohold = { path = "../../cargohold", features = ["regex", "serde"] }

# No direct external dependencies!
```

```rust
// meteor/src/lib.rs - Consistent imports
use cargohold::regex;   // Guaranteed same version as rsb, boxy, etc.
use cargohold::serde;
```

## Architecture Design

### Core Principles:
1. **Single Source of Truth** - All external dependencies declared once in cargohold
2. **Feature-Gated Access** - Projects only get what they explicitly request
3. **Unified Versioning** - Impossible to have version conflicts
4. **Ecosystem Coordination** - Easy to upgrade entire ecosystem at once

### Hub Structure:
```
hub/
├── src/
│   ├── lib.rs          # Main re-exports with feature gates
│   ├── prelude.rs      # Convenience prelude module
│   └── collections/    # Grouped re-exports by domain
│       ├── web.rs      # HTTP clients, URL parsing, etc.
│       ├── data.rs     # Serialization, databases, etc.
│       ├── time.rs     # Date/time handling
│       └── text.rs     # String processing, regex, etc.
├── Cargo.toml          # THE canonical dependency list
└── STRATEGY.md         # This document
```

### Feature Categories:
```toml
[features]
# Core feature groups
text = ["regex", "lazy_static"]
data = ["serde", "serde_json", "base64"]
time = ["chrono", "uuid"]
web = ["reqwest", "url", "urlencoding"]
system = ["libc", "glob"]

# Individual features for fine-grained control
regex = ["dep:regex"]
serde = ["dep:serde"]
chrono = ["dep:chrono"]
# ... etc

# Convenience umbrellas
common = ["text", "data"]
all = ["text", "data", "time", "web", "system"]
```

## Implementation Strategy

### Phase 1: Foundation Setup
1. **Create core cargohold structure** with lib.rs and Cargo.toml
2. **Copy RSB's deps.rs pattern** as starting point
3. **Extract RSB's external dependencies** to cargohold
4. **Create feature flag structure** for all dependencies

### Phase 2: RSB Integration
1. **Update RSB to depend on cargohold** instead of direct dependencies
2. **Replace RSB's deps.rs** with cargohold imports
3. **Verify RSB functionality** unchanged with cargohold
4. **Update RSB feature flags** to use cargohold features

### Phase 3: Ecosystem Migration
1. **Migrate meteor** to use cargohold (immediate need)
2. **Migrate other oodx projects** (boxy, xstream, etc.)
3. **Remove direct external dependencies** from all projects
4. **Validate cross-project compatibility**

### Phase 4: Advanced Features
1. **Add domain collections** (web.rs, data.rs, etc.)
2. **Create ecosystem-wide upgrade scripts**
3. **Add dependency audit and security tooling**
4. **Document contribution guidelines**

## Benefits for oodx Ecosystem

### For Developers:
- **Simplified dependency management** - Only specify features, not versions
- **Guaranteed compatibility** - No more version conflict resolution
- **Easy ecosystem upgrades** - One place to update all versions
- **Consistent behavior** - Same crate versions across all projects

### For Projects:
- **Cleaner Cargo.toml** - No external dependency noise
- **Faster builds** - Cargo deduplicates dependencies across workspace
- **Better security** - Centralized vulnerability scanning and updates
- **Easier maintenance** - Dependency updates coordinated

### For Users:
- **Consistent APIs** - Same crate versions = same behavior everywhere
- **Better integration** - Projects designed to work together
- **Fewer conflicts** - No dependency resolution issues
- **Faster compilation** - Shared dependency builds

## Migration Guidelines

### For New Projects (like meteor):
```toml
# Good - Use cargohold from start
[dependencies]
cargohold = { path = "../../cargohold", features = ["regex", "serde"] }

# Avoid - Direct external dependencies
# regex = "1.6.0"
# serde = "1.0.180"
```

### For Existing Projects:
1. **Audit current dependencies** - What external crates are used?
2. **Add to cargohold** - Ensure all needed crates available
3. **Update Cargo.toml** - Replace external deps with cargohold features
4. **Update imports** - Change `use regex` to `use cargohold::regex`
5. **Test compatibility** - Verify functionality unchanged

### Feature Selection Strategy:
- **Start minimal** - Only request features you actually use
- **Use groups when appropriate** - `features = ["text"]` vs individual crates
- **Document requirements** - Comment why specific features needed

## Maintenance and Governance

### Version Update Process:
1. **Dependency audit** - Check for security vulnerabilities
2. **Version bump** - Update versions in cargohold/Cargo.toml
3. **Compatibility testing** - Run tests across all oodx projects
4. **Ecosystem deployment** - Update projects to new cargohold version

### Adding New Dependencies:
1. **Evaluate necessity** - Is this widely needed across projects?
2. **Check alternatives** - Can we use existing dependencies instead?
3. **Add feature flag** - Never expose dependencies without gates
4. **Document usage** - Update strategy and project guidelines

### Security and Auditing:
- **Regular `cargo audit`** runs on cargohold
- **Automated vulnerability scanning** in CI
- **Coordinated security updates** across ecosystem
- **Dependency license compliance** tracking

## Example Integration - Meteor

### Before (Direct Dependencies):
```toml
# meteor/Cargo.toml
[dependencies]
regex = "1.6.0"
serde = { version = "1.0.180", features = ["derive"] }
chrono = "0.4.26"
```

### After (Cargohold):
```toml
# meteor/Cargo.toml
[dependencies]
cargohold = { path = "../../cargohold", features = ["regex", "serde", "chrono"] }
```

```rust
// meteor/src/lib.rs
use cargohold::regex;
use cargohold::serde::{Serialize, Deserialize};
use cargohold::chrono;
```

### Benefits for Meteor:
- **Consistent with RSB** - Same regex version as parent project
- **Future-proof** - Automatic updates when cargohold upgrades
- **Clean dependencies** - Only specify what's needed via features
- **No version conflicts** - Guaranteed compatibility with other oodx projects

## Success Metrics

### Technical Metrics:
- **Zero version conflicts** across oodx ecosystem
- **Faster build times** due to dependency deduplication
- **Reduced Cargo.toml complexity** in individual projects
- **Coordinated updates** across all projects

### Ecosystem Health:
- **Consistent API behavior** across projects
- **Easier project integration** without dependency hell
- **Faster new project setup** with proven dependency stack
- **Better security posture** through centralized updates

---

## Next Steps

1. **Create cargohold/Cargo.toml** by copying and expanding RSB's dependencies
2. **Create cargohold/src/lib.rs** by adapting RSB's deps.rs pattern
3. **Set up feature flag structure** for all current and future dependencies
4. **Test with meteor** as first consumer project
5. **Document migration guide** for other oodx projects

This strategy positions cargohold as the foundation for a unified, maintainable, and conflict-free dependency ecosystem across all oodx projects.

---

## TSV Data Structure Reference

The `deps_cache.tsv` file provides a structured, tabulated data format for analyzing the oodx ecosystem's dependency structure. This cache is generated by the `bin/deps.py` script and contains comprehensive information about repositories, dependencies, versions, and their relationships.

### File Structure Overview

The TSV file is organized into distinct sections, each serving a specific analytical purpose:

1. **AGGREGATION METRICS** - Summary statistics and ecosystem-wide metrics
2. **REPO LIST** - Repository metadata and hub integration status
3. **DEP VERSIONS LIST** - Individual dependency entries with versions and features
4. **DEP LATEST LIST** - Latest version information and hub status for each package
5. **VERSION MAP LIST** - Relationship mapping with version analysis

### Section 1: AGGREGATION METRICS

**Purpose**: Provides high-level ecosystem statistics for quick dashboard views and trend analysis.

**Structure**: Key-value pairs in TSV format
```tsv
KEY	VALUE
total_repos	18
hub_using_repos	0
total_deps	176
total_packages	71
```

**Key Metrics**:
- `total_repos` (int) - Number of repositories analyzed (excluding hub itself)
- `hub_using_repos` (int) - Count of repositories currently using the hub
- `total_deps` (int) - Total dependency entries across all repositories
- `total_packages` (int) - Unique packages used across the ecosystem
- `git_packages` (int) - Packages sourced from Git repositories
- `local_packages` (int) - Locally-sourced packages (path dependencies)
- `crate_packages` (int) - Packages from crates.io
- `workspace_packages` (int) - Workspace-managed packages
- `hub_current` (int) - Packages in hub with current versions
- `hub_outdated` (int) - Packages in hub with outdated versions
- `hub_gap` (int) - High-usage packages missing from hub
- `hub_local` (int) - Local/path packages in hub
- `breaking_updates` (int) - Dependencies with breaking change updates available
- `safe_updates` (int) - Dependencies with safe updates available
- `unknown_updates` (int) - Dependencies with unknown update status
- `stable_versions` (int) - Dependencies using stable (1.x+) versions
- `unstable_versions` (int) - Dependencies using unstable (0.x) versions

### Section 2: REPO LIST

**Purpose**: Catalog all repositories in the ecosystem with metadata and hub integration status.

**Columns**:
- `REPO_ID` (int) - Unique identifier starting from 100
- `REPO_NAME` (string) - Package name from Cargo.toml
- `PATH` (string) - Relative path from RUST_REPO_ROOT to Cargo.toml
- `PARENT` (string) - Parent directory name (projects, concepts, labs, etc.)
- `LAST_UPDATE` (int) - Unix timestamp of last Cargo.toml modification
- `CARGO_VERSION` (string) - Version declared in the repository's Cargo.toml
- `HUB_USAGE` (string) - Hub dependency version used ("NONE" if not using hub)
- `HUB_STATUS` (string) - Hub integration status ("none", "using", "path", "workspace")

**Example**:
```tsv
100	paintbox	oodx/projects/paintbox/Cargo.toml	projects	1757345459	0.0.1	NONE	none
101	rolo	oodx/projects/rolo/Cargo.toml	projects	1757992816	0.2.2	NONE	none
```

**Foreign Key Relationships**: `REPO_ID` is referenced by `DEP_VERSIONS_LIST.REPO_ID` and `VERSION_MAP_LIST.REPO_ID`

### Section 3: DEP VERSIONS LIST

**Purpose**: Detailed inventory of every dependency declared across all repositories.

**Columns**:
- `DEP_ID` (int) - Unique identifier starting from 1000
- `REPO_ID` (int) - Foreign key to REPO_LIST.REPO_ID
- `PKG_NAME` (string) - Package name as declared in Cargo.toml
- `PKG_VERSION` (string) - Version constraint (e.g., "1.0", "0.9.2", "LOCAL")
- `DEP_TYPE` (string) - Dependency type ("dep" for dependencies, "dev-dep" for dev-dependencies)
- `FEATURES` (string) - Comma-separated list of enabled features ("NONE" if no features)

**Example**:
```tsv
1000	100	serde	1	dep	derive
1001	100	serde_yaml	0.9	dep	NONE
1065	105	rsb	LOCAL	dep	visuals,stdopts
```

**Special Values**:
- `PKG_VERSION = "LOCAL"` - Path dependency resolved to local project
- `PKG_VERSION = "WORKSPACE"` - Workspace-managed dependency
- `FEATURES = "NONE"` - No specific features enabled

**Foreign Key Relationships**:
- `REPO_ID` references `REPO_LIST.REPO_ID`
- `DEP_ID` is referenced by `VERSION_MAP_LIST.DEP_ID`

### Section 4: DEP LATEST LIST

**Purpose**: Latest version information and hub integration status for each unique package.

**Columns**:
- `PKG_ID` (int) - Unique identifier starting from 200
- `PKG_NAME` (string) - Package name (unique across ecosystem)
- `LATEST_VERSION` (string) - Latest available version from source
- `SOURCE_TYPE` (string) - Source type ("crate", "local", "git", "workspace")
- `SOURCE_VALUE` (string) - Source-specific value (version, path, git URL, "WORKSPACE")
- `HUB_VERSION` (string) - Version used in hub ("NONE" if not in hub)
- `HUB_STATUS` (string) - Hub relationship ("current", "outdated", "gap", "none")

**Example**:
```tsv
200	aes-gcm	0.11.0-rc.1	crate	0.10	NONE	gap
248	rsb	0.2.18	git	https://github.com/oodx/rsb-framework#main (LOCAL: oodx/projects/rsb/Cargo.toml)	NONE	gap
```

**Source Types**:
- `crate` - Standard crates.io package
- `local` - Path dependency to local project
- `git` - Git repository dependency
- `workspace` - Workspace-managed dependency

**Hub Status Values**:
- `current` - Hub has same version as latest
- `outdated` - Hub has older version than latest
- `gap` - Package not present in hub
- `none` - No hub relationship established

**Foreign Key Relationships**: `PKG_ID` is referenced by `VERSION_MAP_LIST.PKG_ID`

### Section 5: VERSION MAP LIST

**Purpose**: Relationship mapping that connects dependencies to packages with version analysis.

**Columns**:
- `MAP_ID` (int) - Unique identifier starting from 300
- `DEP_ID` (int) - Foreign key to DEP_VERSIONS_LIST.DEP_ID
- `PKG_ID` (int) - Foreign key to DEP_LATEST_LIST.PKG_ID
- `REPO_ID` (int) - Foreign key to REPO_LIST.REPO_ID
- `VERSION_STATE` (string) - Version stability assessment
- `BREAKING_TYPE` (string) - Breaking change risk assessment
- `ECOSYSTEM_STATUS` (string) - Overall ecosystem status

**Example**:
```tsv
300	1000	250	100	stable	safe	normal
301	1001	252	100	unstable	safe	normal
368	1068	200	105	unstable	BREAKING	normal
```

**Version State Values**:
- `stable` - Version 1.0+ (follows semantic versioning stability)
- `unstable` - Version 0.x (breaking changes on minor bumps)
- `pre-release` - Pre-release version (alpha, beta, rc)
- `local` - Local path dependency
- `unknown` - Cannot determine stability

**Breaking Type Values**:
- `safe` - Update would not introduce breaking changes
- `BREAKING` - Update would introduce breaking changes
- `current` - Already using latest version
- `unknown` - Cannot determine breaking change risk

**Ecosystem Status Values**:
- `normal` - Standard ecosystem dependency
- `critical` - Critical infrastructure dependency (reserved for future use)
- `deprecated` - Marked for removal (reserved for future use)

### Data Relationships and Foreign Keys

The sections are interconnected through foreign key relationships:

```
REPO_LIST(REPO_ID) ←─┐
                     │
                     ├─ DEP_VERSIONS_LIST(REPO_ID, DEP_ID)
                     │                              │
                     │                              ↓
                     └─ VERSION_MAP_LIST(REPO_ID, DEP_ID, PKG_ID)
                                              │
                                              ↓
                       DEP_LATEST_LIST(PKG_ID) ←─┘
```

### Dataclass Structures (bin/deps.py)

The Python script uses dataclasses to represent the TSV structure:

#### RepoData
```python
@dataclass
class RepoData:
    repo_id: int           # Maps to REPO_LIST.REPO_ID
    repo_name: str         # Maps to REPO_LIST.REPO_NAME
    path: str              # Maps to REPO_LIST.PATH
    parent: str            # Maps to REPO_LIST.PARENT
    last_update: int       # Maps to REPO_LIST.LAST_UPDATE
    cargo_version: str     # Maps to REPO_LIST.CARGO_VERSION
    hub_usage: str         # Maps to REPO_LIST.HUB_USAGE
    hub_status: str        # Maps to REPO_LIST.HUB_STATUS
```

#### DepData
```python
@dataclass
class DepData:
    dep_id: int            # Maps to DEP_VERSIONS_LIST.DEP_ID
    repo_id: int           # Maps to DEP_VERSIONS_LIST.REPO_ID
    pkg_name: str          # Maps to DEP_VERSIONS_LIST.PKG_NAME
    pkg_version: str       # Maps to DEP_VERSIONS_LIST.PKG_VERSION
    dep_type: str          # Maps to DEP_VERSIONS_LIST.DEP_TYPE
    features: str          # Maps to DEP_VERSIONS_LIST.FEATURES
```

#### LatestData
```python
@dataclass
class LatestData:
    pkg_id: int            # Maps to DEP_LATEST_LIST.PKG_ID
    pkg_name: str          # Maps to DEP_LATEST_LIST.PKG_NAME
    latest_version: str    # Maps to DEP_LATEST_LIST.LATEST_VERSION
    source_type: str       # Maps to DEP_LATEST_LIST.SOURCE_TYPE
    source_value: str      # Maps to DEP_LATEST_LIST.SOURCE_VALUE
    hub_version: str       # Maps to DEP_LATEST_LIST.HUB_VERSION
    hub_status: str        # Maps to DEP_LATEST_LIST.HUB_STATUS
```

#### VersionMapData
```python
@dataclass
class VersionMapData:
    map_id: int            # Maps to VERSION_MAP_LIST.MAP_ID
    dep_id: int            # Maps to VERSION_MAP_LIST.DEP_ID
    pkg_id: int            # Maps to VERSION_MAP_LIST.PKG_ID
    repo_id: int           # Maps to VERSION_MAP_LIST.REPO_ID
    version_state: str     # Maps to VERSION_MAP_LIST.VERSION_STATE
    breaking_type: str     # Maps to VERSION_MAP_LIST.BREAKING_TYPE
    ecosystem_status: str  # Maps to VERSION_MAP_LIST.ECOSYSTEM_STATUS
```

#### HubInfo
```python
@dataclass
class HubInfo:
    path: str                        # Hub repository path
    version: str                     # Hub version
    dependencies: Dict[str, str]     # Package name to version mapping
    last_update: int                 # Last update timestamp
```

### Usage Examples

#### Finding Version Conflicts
```sql
-- Conceptual SQL for understanding relationships
SELECT
    pkg_name,
    COUNT(DISTINCT pkg_version) as version_count,
    GROUP_CONCAT(DISTINCT pkg_version) as versions_used
FROM dep_versions_list
GROUP BY pkg_name
HAVING version_count > 1;
```

#### Hub Gap Analysis
```sql
-- Packages with high usage not in hub
SELECT
    dl.pkg_name,
    dl.latest_version,
    COUNT(DISTINCT dvl.repo_id) as usage_count
FROM dep_latest_list dl
JOIN version_map_list vml ON dl.pkg_id = vml.pkg_id
JOIN dep_versions_list dvl ON vml.dep_id = dvl.dep_id
WHERE dl.hub_status = 'gap'
GROUP BY dl.pkg_name, dl.latest_version
HAVING usage_count >= 5
ORDER BY usage_count DESC;
```

#### Breaking Change Assessment
```sql
-- Dependencies requiring breaking change updates
SELECT
    r.repo_name,
    dvl.pkg_name,
    dvl.pkg_version as current_version,
    dl.latest_version,
    vml.breaking_type
FROM version_map_list vml
JOIN dep_versions_list dvl ON vml.dep_id = dvl.dep_id
JOIN dep_latest_list dl ON vml.pkg_id = dl.pkg_id
JOIN repo_list r ON vml.repo_id = r.repo_id
WHERE vml.breaking_type = 'BREAKING'
ORDER BY r.repo_name, dvl.pkg_name;
```

### Cache Generation Process

The cache is generated through the `bin/deps.py data` command following these phases:

1. **Discovery**: Find all Cargo.toml files using fast filesystem traversal
2. **Repository Extraction**: Parse metadata from each repository
3. **Dependency Extraction**: Catalog all dependency declarations
4. **Version Resolution**: Fetch latest versions from sources (crates.io, git, local)
5. **Analysis Generation**: Perform version stability and breaking change analysis
6. **TSV Writing**: Output structured cache file

### Integration with Hub Strategy

This data structure directly supports the centralized dependency management strategy by:

- **Identifying Conflicts**: VERSION_MAP_LIST reveals version inconsistencies that hub would resolve
- **Gap Analysis**: DEP_LATEST_LIST.hub_status='gap' shows packages that should be added to hub
- **Migration Planning**: REPO_LIST.hub_status tracks adoption progress
- **Impact Assessment**: Aggregation metrics quantify ecosystem health improvements

The TSV cache serves as both a diagnostic tool for current ecosystem state and a planning tool for hub integration strategy.

---
*"One crate to rule them all, one crate to find them, one crate to bring them all, and in the ecosystem bind them."* 📦✨