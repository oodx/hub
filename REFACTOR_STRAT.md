# Dependency Analysis Refactor Strategy

## Overview

Move from on-the-fly calculation to structured data cache for faster analysis views and better separation of concerns.

## Current Problem
- Views calculate everything during rendering (slow)
- Mixed data gathering and presentation logic
- Repeated network calls and file parsing
- Hard to add new analysis features

## Solution: Structured Data Cache

Generate TSV file with section delimiters containing all analysis data, then fast view rendering from cache.

## Data Structure

### Section 1: REPO LIST
```
REPO_ID | REPO_NAME | PATH | PARENT | LAST_UPDATE | CARGO_VERSION
```
- `REPO_ID`: 100 (incrementing)
- `REPO_NAME`: name from Cargo.toml (not folder name)
- `PATH`: relative path from $RUST_REPO_ROOT
- `PARENT`: parent repo name from project folder
- `LAST_UPDATE`: epoch timestamp (git stat)
- `CARGO_VERSION`: version from Cargo.toml

### Section 2: DEPS VERSIONS LIST
```
DEP_ID | REPO_ID | PKG_NAME | PKG_VERSION | DEP_TYPE | FEATURES
```
- `DEP_ID`: unique per (repo + package + version) combination
- `REPO_ID`: reference to repo
- `PKG_NAME`: package name
- `PKG_VERSION`: version used by repo
- `DEP_TYPE`: dep/dev-dep/build-dep
- `FEATURES`: features used by repo, or NONE

### Section 3: LATEST LIST
```
PKG_ID | PKG_NAME | LATEST_VERSION
```
- `PKG_ID`: 100 (incrementing)
- `PKG_NAME`: canonical package name
- `LATEST_VERSION`: latest version from source

### Section 4: VERSION MAP LIST
```
MAP_ID | DEP_ID | PKG_ID | REPO_ID | VERSION_STATE | BREAKING_TYPE | ECOSYSTEM_STATUS
```
- `MAP_ID`: unique identifier
- `DEP_ID`: reference to dependency usage
- `PKG_ID`: reference to package
- `REPO_ID`: reference to repo
- `VERSION_STATE`: unstable/pre-release/stable
- `BREAKING_TYPE`: safe/minor-breaking/major-breaking
- `ECOSYSTEM_STATUS`: conflict/outdated/current

## Helper Functions Architecture

### Phase 1: Discovery
```python
def find_all_cargo_files() -> List[Path]:
    """Use find/grep for speed, return all Cargo.toml paths"""

def extract_repo_metadata(cargo_paths: List[Path]) -> List[RepoData]:
    """Extract name, version, parent from each Cargo.toml"""

def get_git_timestamps(repo_paths: List[Path]) -> Dict[Path, int]:
    """Batch git command for last update times"""
```

### Phase 2: Dependency Extraction
```python
def extract_all_dependencies(cargo_paths: List[Path]) -> List[DepData]:
    """Extract ALL dependencies from all Cargo.toml files"""

def collect_unique_packages(dependencies: List[DepData]) -> Set[str]:
    """Get unique package names needing latest version lookup"""
```

### Phase 3: External Data (Batch Operations)
```python
def batch_fetch_latest_versions(package_names: Set[str]) -> Dict[str, str]:
    """Batch fetch all crates.io versions at once"""

def resolve_path_dependencies(path_deps: List[DepData]) -> Dict[str, str]:
    """Read local Cargo.toml files for path dependencies"""

def resolve_git_dependencies(git_deps: List[DepData]) -> Dict[str, str]:
    """Use gh command to query git dependencies"""
```

### Phase 4: Status Analysis (Pure Functions)
```python
def is_breaking_update(current_ver: str, latest_ver: str) -> str:
    """Returns: 'safe', 'minor-breaking', 'major-breaking'"""

def get_version_stability(version: str) -> str:
    """Returns: 'stable', 'unstable', 'pre-release'"""

def is_using_hub(repo_name: str, pkg_name: str, hub_deps: Dict) -> bool:
    """Check if repo uses hub for this package"""

def get_hub_status(pkg_name: str, ecosystem_ver: str, hub_ver: str) -> str:
    """Returns: 'hub-current', 'hub-outdated', 'hub-gap'"""

def get_conflict_status(pkg_name: str, all_versions: List[str]) -> str:
    """Returns: 'no-conflict', 'version-conflict', 'critical-conflict'"""

def calculate_ecosystem_impact(pkg_name: str, usage_count: int) -> str:
    """Returns: 'high-impact', 'medium-impact', 'low-impact'"""

def determine_overall_status(dep_data, hub_data, latest_data) -> StatusData:
    """Combine all status checks into final determination"""
```

### Phase 5: Output Generation
```python
def generate_tsv_sections(...) -> str:
    """Generate final TSV with section delimiters"""
```

## Dependency Source Handling

### Different Sources:
1. **crates.io** - `serde = "1.0"` → batch API calls
2. **path** - `my-lib = { path = "../my-lib" }` → read local Cargo.toml
3. **github** - `some-crate = { git = "https://..." }` → use `gh` command
4. **workspace** - `serde = { workspace = true }` → resolve workspace root

### Workspace Handling:
- Detect workspace structure via `[workspace]` sections
- Mark workspace members with flags
- Resolve `{ workspace = true }` references to actual versions
- Handle nested Cargo.toml files without double-counting

## View Rendering Refactor

### Current State:
- Mixed data gathering and formatting
- String coloring scattered throughout logic
- Repeated calculations per view

### Future State:
```python
def render_eco_view(cache_data: CacheData) -> None:
    """Fast rendering from pre-calculated cache"""

def format_with_colors(text: str, status: str) -> str:
    """Centralized color formatting based on status"""

def get_display_columns(view_type: str) -> List[ColumnDef]:
    """Define columns per view type"""
```

## Implementation Priority

1. **Phase 1**: Implement basic data cache generation (`data` command)
2. **Phase 2**: Add helper functions for status analysis
3. **Phase 3**: Enhance with path/git dependency resolution
4. **Phase 4**: Add workspace detection and handling
5. **Phase 5**: Refactor existing views to use cache
6. **Phase 6**: Centralize color formatting and view logic

## Benefits

- **Performance**: Pre-calculated data, no repeated parsing
- **Maintainability**: Single-purpose functions, clear separation
- **Extensibility**: Easy to add new analysis features
- **Testability**: Pure functions with clear inputs/outputs
- **Consistency**: Centralized status determination logic

## Files Structure

- `bin/deps.py` - Main CLI with view commands
- `REFACTOR_STRAT.md` - This strategy document
- Generated: `deps_cache.tsv` - Structured data cache
- Existing: `deps_data.txt` - Legacy export format (keep for compatibility)