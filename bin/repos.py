#!/usr/bin/env python3
"""
Rust dependency analyzer - Enhanced with commands for export, review, and package analysis
Commands:
  python deps.py                    # Default analysis view
  python deps.py export             # Export raw data to deps_data.txt
  python deps.py review             # Detailed review with latest versions
  python deps.py pkg <package>      # Analyze specific package usage
  python deps.py latest <package>   # Check latest version from crates.io
"""

import os
import sys
try:
    import tomllib
    def load_toml(file_or_string, is_string=False):
        if is_string:
            return tomllib.loads(file_or_string)
        else:
            with open(file_or_string, 'rb') as f:
                return tomllib.load(f)
except ImportError:
    import toml
    def load_toml(file_or_string, is_string=False):
        if is_string:
            return toml.loads(file_or_string)
        else:
            return toml.load(file_or_string)
import json
import argparse
import time
import threading
import signal
import termios
import tty
import io
from pathlib import Path
from collections import defaultdict
from packaging import version
import subprocess
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple

# Get RUST_REPO_ROOT environment variable or auto-detect
RUST_REPO_ROOT = os.environ.get('RUST_REPO_ROOT')
if not RUST_REPO_ROOT:
    # Auto-detect by finding 'rust' directory in the current path
    current_path = Path.cwd()
    for parent in [current_path] + list(current_path.parents):
        if parent.name == 'rust' or (parent / 'rust').exists():
            if parent.name == 'rust':
                RUST_REPO_ROOT = str(parent)
            else:
                RUST_REPO_ROOT = str(parent / 'rust')
            break

    if not RUST_REPO_ROOT:
        # Fallback: try to find rust directory from common patterns
        possible_paths = [
            Path.home() / 'repos' / 'code' / 'rust',
            Path('/home/xnull/repos/code/rust'),
            Path.cwd().parent.parent.parent  # Assume we're in rust/oodx/projects/hub
        ]
        for path in possible_paths:
            if path.exists() and path.name == 'rust':
                RUST_REPO_ROOT = str(path)
                break

# Legacy color palette from colors.rs
class Colors:
    # Core legacy colors (v0.5.0)
    RED = '\x1B[38;5;9m'      # red - bright red
    GREEN = '\x1B[38;5;10m'   # green - bright green
    YELLOW = '\x1B[33m'       # yellow - standard yellow
    BLUE = '\x1B[36m'         # blue - cyan-ish blue
    PURPLE = '\x1B[38;5;141m' # purple2 - light purple
    CYAN = '\x1B[38;5;14m'    # cyan - bright cyan
    WHITE = '\x1B[38;5;247m'  # white - light gray
    GRAY = '\x1B[38;5;242m'   # grey - medium gray

    # Extended colors for semantic meaning
    ORANGE = '\x1B[38;5;214m' # orange - warnings/attention
    AMBER = '\x1B[38;5;220m'  # amber - golden orange
    EMERALD = '\x1B[38;5;34m' # emerald - pure green for success
    CRIMSON = '\x1B[38;5;196m' # crimson - pure red for critical errors

    # Style modifiers
    BOLD = '\x1B[1m'
    DIM = '\x1B[2m'
    END = '\x1B[0m'
    RESET = '\x1B[0m'

class ProgressSpinner:
    """Progress bar with spinner for showing detailed progress"""
    def __init__(self, message="Working", total=100):
        self.message = message
        self.total = total
        self.current = 0
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.idx = 0
        self.stop_spinner = False
        self.spinner_thread = None
        self.max_line_length = 0
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful exit"""
        signal.signal(signal.SIGINT, self._signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, self._signal_handler)  # Termination
        # Note: SIGTSTP (Ctrl+Z) is handled by the shell and suspends the process

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        self.stop_spinner = True
        if self.spinner_thread and self.spinner_thread.is_alive():
            # Clean up display
            clear_line = ' ' * (self.max_line_length + 20)
            sys.stdout.write('\r')  # Move to start of current line
            sys.stdout.write('\033[1A')  # Move up one line
            sys.stdout.write(f'\r{clear_line}\n{clear_line}')  # Clear both lines
            sys.stdout.write('\r')  # Move cursor to start
            sys.stdout.write('\033[1A')  # Move up one line
            sys.stdout.flush()

        print(f"\n{Colors.YELLOW}⚠️  Operation interrupted by user{Colors.END}")
        sys.exit(0)

    def _draw_progress_bar(self, width=40):
        """Draw a progress bar"""
        if self.total == 0:
            return "[" + "?" * width + "]"

        filled = int(width * self.current / self.total)
        bar = "█" * filled + "▒" * (width - filled)
        return f"[{bar}]"

    def _get_percentage(self):
        """Get percentage as string"""
        if self.total == 0:
            return "?%"
        return f"{int(100 * self.current / self.total)}%"

    def spin(self):
        first_iteration = True
        while not self.stop_spinner:
            char = self.spinner_chars[self.idx % len(self.spinner_chars)]

            # Progress bar line
            progress_bar = self._draw_progress_bar()
            percentage = self._get_percentage()
            progress_line = f"{Colors.BLUE}{progress_bar}{Colors.END} {Colors.WHITE}{percentage}{Colors.END} ({self.current}/{self.total})"

            # Spinner line
            spinner_line = f"{Colors.CYAN}{char}{Colors.END} {self.message}"

            # Track max length for clearing
            current_length = max(len(progress_line), len(spinner_line))
            self.max_line_length = max(self.max_line_length, current_length)

            if first_iteration:
                # First time, just write the lines
                sys.stdout.write(f'{progress_line}\n\r{spinner_line}')
                first_iteration = False
            else:
                # Move to start of line, clear both lines, then rewrite
                sys.stdout.write('\033[1A')  # Move up to progress line
                sys.stdout.write('\r')  # Move to start of line
                sys.stdout.write('\033[K')  # Clear entire line
                sys.stdout.write(f'{progress_line}\n\r')
                sys.stdout.write('\033[K')  # Clear entire line
                sys.stdout.write(f'{spinner_line}')

            sys.stdout.flush()

            self.idx += 1
            time.sleep(0.1)

    def start(self):
        self.stop_spinner = False
        # Save terminal settings and disable canonical mode (but keep signal handling)
        try:
            self.old_terminal_settings = termios.tcgetattr(sys.stdin)
            # Get current settings
            new_settings = termios.tcgetattr(sys.stdin)
            # Disable canonical mode and echo (but keep signal handling)
            new_settings[3] &= ~(termios.ICANON | termios.ECHO)
            termios.tcsetattr(sys.stdin, termios.TCSANOW, new_settings)
        except (termios.error, io.UnsupportedOperation):
            self.old_terminal_settings = None

        # Hide cursor during animation
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.start()

    def update(self, current, message=None):
        """Update progress"""
        self.current = current
        if message:
            self.message = message

    def stop(self, final_message=None):
        self.stop_spinner = True
        if self.spinner_thread:
            self.spinner_thread.join()

        # Move up to progress line and clear both lines
        sys.stdout.write('\033[1A')  # Move up to progress line
        sys.stdout.write('\r')  # Move to start of line
        clear_line = ' ' * (self.max_line_length + 20)
        sys.stdout.write(f'{clear_line}\n{clear_line}')  # Clear both lines
        sys.stdout.write('\033[1A')  # Move back up to where progress line was
        sys.stdout.write('\r')  # Move to start of line

        # Restore terminal settings
        if hasattr(self, 'old_terminal_settings') and self.old_terminal_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_terminal_settings)
            except (termios.error, io.UnsupportedOperation):
                pass

        # Show cursor again
        sys.stdout.write('\033[?25h')

        if final_message:
            print(final_message)
        sys.stdout.flush()

def parse_version(ver_str):
    """Parse version string, handling workspace and path dependencies"""
    if not ver_str or ver_str == 'path' or 'workspace' in ver_str:
        return None
    # Clean up version string
    ver_str = ver_str.strip('"').split()[0]
    if ver_str.startswith('='):
        ver_str = ver_str[1:]
    try:
        return version.parse(ver_str)
    except:
        return None

def is_breaking_change(from_version, to_version):
    """Check if version change represents a breaking change according to Rust SemVer"""
    if not from_version or not to_version:
        return False

    from_ver = parse_version(from_version) if isinstance(from_version, str) else from_version
    to_ver = parse_version(to_version) if isinstance(to_version, str) else to_version

    if not from_ver or not to_ver:
        return False

    # Major version bump is always breaking
    if to_ver.major > from_ver.major:
        return True

    # For 0.x versions, minor bump is potentially breaking
    if from_ver.major == 0 and to_ver.minor > from_ver.minor:
        return True

    return False

def get_version_risk(ver):
    """Get risk level for a version"""
    parsed = parse_version(ver) if isinstance(ver, str) else ver
    if not parsed:
        return "unknown", Colors.GRAY

    # Pre-release versions
    if parsed.is_prerelease:
        return "pre-release", Colors.YELLOW

    # 0.x versions are inherently unstable
    if parsed.major == 0:
        return "unstable", Colors.ORANGE

    return "stable", Colors.GREEN

def get_latest_version(package_name):
    """Get latest version from crates.io"""
    try:
        url = f"https://crates.io/api/v1/crates/{package_name}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data['crate']['max_version']
    except KeyboardInterrupt:
        # Re-raise to let the main handler deal with it
        raise
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError):
        return None

def get_parent_repo(cargo_path):
    """Get parent.repo format - parent folder + project name using relative paths"""
    # Use relative path from RUST_REPO_ROOT
    rel_path = get_relative_path(cargo_path)
    rel_cargo_path = Path(rel_path)

    project_name = rel_cargo_path.parent.name
    parent_name = rel_cargo_path.parent.parent.name

    # Handle edge cases
    if parent_name == '.':
        parent_name = 'root'

    return f"{parent_name}.{project_name}"

def find_cargo_files(root_dir):
    """Find all Cargo.toml files, excluding target, ref, _arch, archive, and howto directories"""
    cargo_files = []
    for root, dirs, files in os.walk(root_dir):
        # Get relative path from root_dir for checking
        rel_path = Path(root).relative_to(root_dir) if str(root).startswith(str(root_dir)) else Path(root)
        rel_parts = rel_path.parts if rel_path != Path('.') else []

        # Skip if in ref, howto, or contains _arch/archive
        if rel_parts and (rel_parts[0] == 'ref' or
                         rel_parts[0] == 'howto' or
                         any('_arch' in part or 'archive' in part for part in rel_parts)):
            dirs[:] = []  # Don't descend into subdirectories
            continue

        # Skip target directories
        dirs[:] = [d for d in dirs if d != 'target' and d != 'ref' and d != 'howto'
                   and '_arch' not in d and 'archive' not in d]

        if 'Cargo.toml' in files:
            cargo_path = Path(root) / 'Cargo.toml'
            cargo_files.append(cargo_path)

    return cargo_files

def get_relative_path(file_path):
    """Convert absolute path to relative path from RUST_REPO_ROOT"""
    if not RUST_REPO_ROOT:
        return str(file_path)

    try:
        abs_path = Path(file_path).resolve()
        rust_root = Path(RUST_REPO_ROOT).resolve()

        # Check if file is under RUST_REPO_ROOT
        if str(abs_path).startswith(str(rust_root)):
            rel_path = abs_path.relative_to(rust_root)
            return str(rel_path)
        else:
            # File is outside RUST_REPO_ROOT, return full path
            return str(file_path)
    except (ValueError, OSError):
        # Fallback to original path if there's any issue
        return str(file_path)

def analyze_dependencies():
    """Main analysis function"""
    if not RUST_REPO_ROOT:
        print(f"{Colors.RED}❌ Could not determine RUST_REPO_ROOT. Please set the environment variable or run from within a rust project directory.{Colors.END}")
        return {}

    rust_dir = Path(RUST_REPO_ROOT)
    if not rust_dir.exists():
        print(f"{Colors.RED}❌ RUST_REPO_ROOT directory does not exist: {rust_dir}{Colors.END}")
        return {}

    print(f"{Colors.BLUE}🔍 Using RUST_REPO_ROOT: {Colors.BOLD}{rust_dir}{Colors.END}")
    cargo_files = find_cargo_files(rust_dir)

    # Data structure: dep_name -> [(parent.repo, version, dep_type, cargo_path), ...]
    dependencies = defaultdict(list)

    print(f"{Colors.CYAN}{Colors.BOLD}🔍 Analyzing {len(cargo_files)} Rust projects...{Colors.END}\n")

    for cargo_path in cargo_files:
        try:
            cargo_data = load_toml(cargo_path)

            parent_repo = get_parent_repo(cargo_path)

            # Parse regular dependencies
            if 'dependencies' in cargo_data:
                for dep_name, dep_info in cargo_data['dependencies'].items():
                    if isinstance(dep_info, str):
                        # Simple version: dep = "1.0"
                        dependencies[dep_name].append((parent_repo, dep_info, 'dep', cargo_path))
                    elif isinstance(dep_info, dict):
                        # Complex dependency: dep = { version = "1.0", features = [...] }
                        if 'version' in dep_info:
                            dependencies[dep_name].append((parent_repo, dep_info['version'], 'dep', cargo_path))
                        elif 'path' in dep_info:
                            dependencies[dep_name].append((parent_repo, 'path', 'dep', cargo_path))
                        elif 'workspace' in dep_info and dep_info['workspace']:
                            dependencies[dep_name].append((parent_repo, 'workspace', 'dep', cargo_path))

            # Parse dev-dependencies
            if 'dev-dependencies' in cargo_data:
                for dep_name, dep_info in cargo_data['dev-dependencies'].items():
                    if isinstance(dep_info, str):
                        dependencies[dep_name].append((parent_repo, dep_info, 'dev', cargo_path))
                    elif isinstance(dep_info, dict) and 'version' in dep_info:
                        dependencies[dep_name].append((parent_repo, dep_info['version'], 'dev', cargo_path))

        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Warning: Could not parse {cargo_path}: {e}{Colors.END}")

    return dependencies

def format_version_analysis(dependencies):
    """Format the dependency analysis with colors and columns"""

    # Filter out dependencies with only path/workspace references
    filtered_deps = {}
    for dep_name, usages in dependencies.items():
        version_usages = [(parent_repo, ver, typ, path) for parent_repo, ver, typ, path in usages
                         if ver not in ['path', 'workspace']]
        if version_usages:
            filtered_deps[dep_name] = version_usages

    # Sort by dependency name
    sorted_deps = sorted(filtered_deps.items())

    print(f"{Colors.BLUE}{Colors.BOLD}📊 DEPENDENCY VERSION ANALYSIS{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")

    conflicts_found = 0

    # Load latest versions from data file if it exists
    latest_cache = {}
    data_file = Path("deps_data.txt")
    if data_file.exists():
        print(f"{Colors.GRAY}Loading latest versions from deps_data.txt cache...{Colors.END}\n")
        with open(data_file, 'r') as f:
            for line in f:
                if line.startswith("DEPENDENCY:"):
                    parts = line.strip().split(", LATEST: ")
                    if len(parts) == 2:
                        dep_name = parts[0].replace("DEPENDENCY: ", "")
                        latest_version = parts[1]
                        latest_cache[dep_name] = latest_version
    else:
        print(f"{Colors.GRAY}No cache found - fetching latest versions from crates.io...{Colors.END}")

    for dep_name, usages in sorted_deps:
        # Get unique versions
        versions = set()
        version_map = {}  # version -> [(parent_repo, type), ...]

        for parent_repo, ver_str, dep_type, cargo_path in usages:
            parsed_ver = parse_version(ver_str)
            if parsed_ver:
                versions.add(parsed_ver)
                if parsed_ver not in version_map:
                    version_map[parsed_ver] = []
                version_map[parsed_ver].append((parent_repo, dep_type))

        if not versions:
            continue

        # Get latest version from cache (no API call)
        latest_version = latest_cache.get(dep_name)

        # Check for conflicts (multiple versions)
        has_conflict = len(versions) > 1
        if has_conflict:
            conflicts_found += 1

        # Sort versions
        sorted_versions = sorted(versions)
        min_version = min(sorted_versions) if sorted_versions else None
        max_version = max(sorted_versions) if sorted_versions else None

        # Check for breaking changes in this dependency
        has_breaking = False
        if latest_version and len(versions) > 1:
            has_breaking = is_breaking_change(str(min_version), latest_version)
        elif latest_version and len(versions) == 1:
            has_breaking = is_breaking_change(str(max_version), latest_version)

        # Header with breaking change indicators
        if has_conflict and has_breaking:
            conflict_indicator = f"{Colors.CRIMSON}⚠️ BREAKING CONFLICT"
        elif has_conflict:
            conflict_indicator = f"{Colors.RED}⚠️ CONFLICT"
        elif latest_version and has_breaking:
            conflict_indicator = f"{Colors.ORANGE}⚠️ BREAKING UPDATE"
        else:
            conflict_indicator = f"{Colors.GREEN}✅"

        latest_str = f" (latest: {Colors.CYAN}{latest_version}{Colors.END})" if latest_version else ""
        version_info = f" ({len(versions)} versions)" if has_conflict else ""
        print(f"{conflict_indicator} {Colors.BOLD}{dep_name}{Colors.END}{latest_str}{version_info}")

        # Show versions in columns
        for ver in sorted_versions:
            # Color coding with version risk assessment
            risk_level, risk_color = get_version_risk(ver)

            if len(sorted_versions) > 1:
                if ver == min_version:
                    ver_color = Colors.RED  # Oldest version
                elif ver == max_version:
                    ver_color = Colors.GREEN  # Newest version
                else:
                    ver_color = Colors.YELLOW  # Middle version
            else:
                ver_color = risk_color  # Single version - show risk level

            projects_with_version = version_map[ver]
            projects_str = ', '.join([f"{proj}({typ})" if typ == 'dev' else proj
                                    for proj, typ in projects_with_version])

            # Add risk indicator for unstable/pre-release versions
            risk_level, _ = get_version_risk(ver)
            risk_indicator = ""
            if risk_level == "unstable":
                risk_indicator = f" {Colors.YELLOW}◐{Colors.END}"  # 0.x indicator
            elif risk_level == "pre-release":
                risk_indicator = f" {Colors.YELLOW}◑{Colors.END}"  # pre-release indicator

            print(f"  {ver_color}{str(ver):<12}{Colors.END}{risk_indicator} → {projects_str}")

        print()

    # Summary
    print(f"{Colors.PURPLE}{Colors.BOLD}📈 SUMMARY{Colors.END}")
    print(f"{Colors.PURPLE}{'='*40}{Colors.END}")
    print(f"Total dependencies analyzed: {Colors.BOLD}{len(sorted_deps)}{Colors.END}")
    print(f"Dependencies with version conflicts: {Colors.RED}{Colors.BOLD}{conflicts_found}{Colors.END}")
    print(f"Clean dependencies (single version): {Colors.GREEN}{Colors.BOLD}{len(sorted_deps) - conflicts_found}{Colors.END}")

    # Count breaking change issues
    breaking_conflicts = 0
    breaking_updates = 0
    for dep_name, usages in sorted_deps:
        versions = set()
        for parent_repo, ver_str, dep_type, cargo_path in usages:
            parsed_ver = parse_version(ver_str)
            if parsed_ver:
                versions.add(parsed_ver)

        if versions:
            min_version = min(versions)
            max_version = max(versions)
            latest_version = latest_cache.get(dep_name)

            if len(versions) > 1 and latest_version:
                if is_breaking_change(str(min_version), latest_version):
                    breaking_conflicts += 1
            elif len(versions) == 1 and latest_version:
                if is_breaking_change(str(max_version), latest_version):
                    breaking_updates += 1

    if conflicts_found > 0 or breaking_conflicts > 0 or breaking_updates > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 Hub integration will resolve {conflicts_found} conflicts!{Colors.END}")
        if breaking_conflicts > 0:
            print(f"{Colors.CRIMSON}{Colors.BOLD}⚠️  {breaking_conflicts} dependencies have BREAKING CHANGE conflicts{Colors.END}")
        if breaking_updates > 0:
            print(f"{Colors.ORANGE}{Colors.BOLD}⚠️  {breaking_updates} dependencies have breaking updates available{Colors.END}")
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✨ No version conflicts detected - ecosystem is clean!{Colors.END}")

def export_raw_data(dependencies):
    """Export raw dependency data to text file"""
    output_file = "deps_data.txt"

    # Filter dependencies with actual versions
    filtered_deps = {}
    for dep_name, usages in dependencies.items():
        version_usages = [(parent_repo, ver, typ, path) for parent_repo, ver, typ, path in usages
                         if ver not in ['path', 'workspace']]
        if version_usages:
            filtered_deps[dep_name] = version_usages

    total_deps = len(filtered_deps)

    # Start progress spinner
    progress = ProgressSpinner("Initializing export...", total_deps)
    progress.start()

    # Cache for latest versions
    latest_cache = {}
    processed = 0

    try:
        with open(output_file, 'w') as f:
            f.write("Raw Dependency Data Export\n")
            f.write("=" * 50 + "\n\n")

            for dep_name, usages in sorted(filtered_deps.items()):
                processed += 1

                # Update progress with current dependency
                progress.update(processed, f"Fetching latest version for {dep_name}...")

                # Get latest version from crates.io
                if dep_name not in latest_cache:
                    latest_version = get_latest_version(dep_name)
                    latest_cache[dep_name] = latest_version
                else:
                    latest_version = latest_cache[dep_name]

                # Update progress message for writing
                progress.update(processed, f"Writing {dep_name} to file...")

                latest_str = f", LATEST: {latest_version}" if latest_version else ""
                f.write(f"DEPENDENCY: {dep_name}{latest_str}\n")
                for parent_repo, ver_str, dep_type, cargo_path in usages:
                    rel_path = get_relative_path(cargo_path)
                    f.write(f"  {parent_repo:<25} {ver_str:<12} {dep_type:<4} {rel_path}\n")
                f.write("\n")

        # Stop progress and show success
        progress.stop(f"{Colors.GREEN}✅ Raw data exported to {Colors.BOLD}{output_file}{Colors.END} ({total_deps} dependencies)")

    except Exception as e:
        progress.stop(f"{Colors.RED}❌ Export failed: {e}{Colors.END}")
        raise

def detailed_review(dependencies):
    """Show detailed review with latest versions across entire ecosystem"""
    print(f"{Colors.WHITE}{Colors.BOLD}📋 ECOSYSTEM DEPENDENCY REVIEW{Colors.END}")
    print(f"{Colors.GRAY}Status of each dependency across all Rust projects (ignoring hub){Colors.END}")
    print(f"{Colors.GRAY}{'='*80}{Colors.END}\n")

    # Load latest versions from data file if it exists
    latest_cache = {}
    data_file = Path("deps_data.txt")
    if data_file.exists():
        print(f"{Colors.GRAY}Loading latest versions from deps_data.txt cache (run 'export' to refresh)...{Colors.END}\n")
        with open(data_file, 'r') as f:
            for line in f:
                if line.startswith("DEPENDENCY:"):
                    parts = line.strip().split(", LATEST: ")
                    if len(parts) == 2:
                        dep_name = parts[0].replace("DEPENDENCY: ", "")
                        latest_version = parts[1]
                        latest_cache[dep_name] = latest_version
    else:
        print(f"{Colors.YELLOW}⚠️  No deps_data.txt found. Run 'deps.py export' first to cache latest versions.{Colors.END}\n")

    # Filter and sort dependencies
    filtered_deps = {}
    for dep_name, usages in dependencies.items():
        version_usages = [(parent_repo, ver, typ, path) for parent_repo, ver, typ, path in usages
                         if ver not in ['path', 'workspace']]
        if version_usages:
            filtered_deps[dep_name] = version_usages

    # Sort by usage count (descending), then alphabetically by package name
    def sort_key(item):
        dep_name, usages = item
        # Count unique repos using this dependency
        repo_count = len(set(parent_repo for parent_repo, _, _, _ in usages))
        return (-repo_count, dep_name)  # Negative for descending order

    sorted_deps = sorted(filtered_deps.items(), key=sort_key)

    # Header
    print(f"{Colors.WHITE}{Colors.BOLD}{'Package':<20} {'#U':<4} {'Ecosystem':<14} {'Latest':<20} {'Breaking'}{Colors.END}")
    print(f"{Colors.GRAY}{'-' * 105}{Colors.END}")

    for dep_name, usages in sorted_deps:
        # Get versions used in ecosystem
        versions = set()
        for parent_repo, ver_str, dep_type, cargo_path in usages:
            parsed_ver = parse_version(ver_str)
            if parsed_ver:
                versions.add(parsed_ver)

        if not versions:
            continue

        sorted_versions = sorted(versions)
        min_version = min(sorted_versions)
        max_version = max(sorted_versions)
        ecosystem_version = str(max_version)

        # Get latest version from cache or fetch if not available
        if dep_name not in latest_cache:
            latest_version = get_latest_version(dep_name)
            latest_cache[dep_name] = latest_version
        else:
            latest_version = latest_cache[dep_name]

        # Status and smart coloring logic
        has_conflict = len(versions) > 1
        latest_str = latest_version if latest_version else "unknown"

        # Check for breaking changes
        has_breaking = False
        if latest_version and has_conflict:
            # Check if update from min to latest would be breaking
            has_breaking = is_breaking_change(str(min_version), latest_version)

        # Get version risk for ecosystem version
        risk_level, risk_color = get_version_risk(max_version)

        # Determine block color for ecosystem version (simplified - breaking info in separate column)
        if has_conflict:
            status_block = f"{Colors.RED}■{Colors.END}"  # Conflict
        elif latest_version and parse_version(latest_version) and parse_version(latest_version) > max_version:
            status_block = f"{Colors.ORANGE}■{Colors.END}"  # Update available
        elif risk_level == "unstable":
            status_block = f"{Colors.YELLOW}◐{Colors.END}"  # 0.x version
        elif risk_level == "pre-release":
            status_block = f"{Colors.YELLOW}◑{Colors.END}"  # Pre-release
        else:
            status_block = f"{Colors.GRAY}■{Colors.END}"  # Stable and current

        # Count repos using this dependency
        repo_count = len(set(parent_repo for parent_repo, _, _, _ in usages))

        # Check for breaking changes
        breaking_status = ""
        if latest_version and latest_str != "unknown":
            if has_conflict:
                # Check if update from min to latest would be breaking
                if is_breaking_change(str(min_version), latest_version):
                    breaking_status = f"{Colors.CRIMSON}BREAKING{Colors.END}"
                else:
                    breaking_status = f"{Colors.GREEN}safe{Colors.END}"
            else:
                # Single version - check if update would be breaking
                if is_breaking_change(str(max_version), latest_version):
                    if parse_version(latest_version) > max_version:
                        breaking_status = f"{Colors.ORANGE}BREAKING{Colors.END}"
                    else:
                        breaking_status = f"{Colors.GRAY}current{Colors.END}"
                else:
                    if parse_version(latest_version) > max_version:
                        breaking_status = f"{Colors.GREEN}safe{Colors.END}"
                    else:
                        breaking_status = f"{Colors.GRAY}current{Colors.END}"
        else:
            breaking_status = f"{Colors.GRAY}unknown{Colors.END}"

        # Smart version coloring - only highlight differences
        # Compare parsed versions to handle "0.9" vs "0.9.0" properly
        ecosystem_parsed = parse_version(ecosystem_version)
        latest_parsed = parse_version(latest_str) if latest_str != "unknown" else None
        versions_match = (ecosystem_parsed and latest_parsed and ecosystem_parsed == latest_parsed)

        if versions_match:
            # Versions match - keep latest gray, but eco still gets block
            eco_with_block = f"{status_block} {Colors.GRAY}{ecosystem_version:<12}{Colors.END}"
            latest_colored = f"{Colors.GRAY}{latest_str:<18}{Colors.END}"
        else:
            # Versions differ - color ecosystem by status, latest in blue
            if has_conflict:
                eco_with_block = f"{status_block} {Colors.RED}{ecosystem_version:<12}{Colors.END}"
            elif latest_version and parse_version(latest_version) and parse_version(latest_version) > max_version:
                eco_with_block = f"{status_block} {Colors.ORANGE}{ecosystem_version:<12}{Colors.END}"
            else:
                eco_with_block = f"{status_block} {Colors.GRAY}{ecosystem_version:<12}{Colors.END}"

            latest_colored = f"{Colors.CYAN}{latest_str:<18}{Colors.END}"

        # Print gray row with block in front of ecosystem version and breaking status
        print(f"{Colors.GRAY}{dep_name:<20} "
              f"{repo_count:<4} "
              f"{Colors.END}{eco_with_block} "
              f"{latest_colored} "
              f"{breaking_status}")

    print(f"\n{Colors.PURPLE}{Colors.BOLD}Legend:{Colors.END}")
    print(f"{Colors.GRAY}■{Colors.END} UPDATED   - Using latest version, no conflicts")
    print(f"{Colors.ORANGE}■{Colors.END} OUTDATED  - Newer version available (safe update)")
    print(f"{Colors.ORANGE}⚠{Colors.END} BREAKING  - Breaking change update available")
    print(f"{Colors.RED}■{Colors.END} CONFLICT  - Multiple versions in ecosystem")
    print(f"{Colors.CRIMSON}⚠{Colors.END} CRITICAL  - Breaking change conflicts")
    print(f"{Colors.YELLOW}◐{Colors.END} UNSTABLE  - 0.x version (minor bumps can break)")
    print(f"{Colors.YELLOW}◑{Colors.END} PREREL    - Pre-release version")
    print(f"\nBreaking: {Colors.CRIMSON}BREAKING{Colors.END} (conflicts), {Colors.ORANGE}BREAKING{Colors.END} (updates), {Colors.GREEN}safe{Colors.END}, {Colors.GRAY}current{Colors.END}")
    print(f"Versions: Only colored when {Colors.ORANGE}ecosystem{Colors.END} ≠ {Colors.CYAN}latest{Colors.END}")

def analyze_package(dependencies, package_name):
    """Analyze specific package usage across ecosystem"""
    if package_name not in dependencies:
        print(f"{Colors.RED}❌ Package '{package_name}' not found in ecosystem{Colors.END}")
        return

    usages = dependencies[package_name]
    version_usages = [(parent_repo, ver, typ, path) for parent_repo, ver, typ, path in usages
                     if ver not in ['path', 'workspace']]

    if not version_usages:
        print(f"{Colors.YELLOW}⚠️  Package '{package_name}' only has path/workspace dependencies{Colors.END}")
        return

    print(f"{Colors.CYAN}{Colors.BOLD}📦 PACKAGE ANALYSIS: {package_name}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

    # Get latest version
    latest_version = get_latest_version(package_name)
    if latest_version:
        print(f"{Colors.CYAN}Latest on crates.io: {Colors.BOLD}{latest_version}{Colors.END}\n")

    # Collect versions
    versions = set()
    version_map = {}

    for parent_repo, ver_str, dep_type, cargo_path in version_usages:
        parsed_ver = parse_version(ver_str)
        if parsed_ver:
            versions.add(parsed_ver)
            if parsed_ver not in version_map:
                version_map[parsed_ver] = []
            version_map[parsed_ver].append((parent_repo, dep_type))

    sorted_versions = sorted(versions)
    min_version = min(sorted_versions) if sorted_versions else None
    max_version = max(sorted_versions) if sorted_versions else None

    # Header
    print(f"{Colors.WHITE}{Colors.BOLD}{'Version':<12} {'Type':<6} {'Parent.Repo':<25} {'Status'}{Colors.END}")
    print(f"{Colors.GRAY}{'-' * 60}{Colors.END}")

    for ver in sorted_versions:
        # Color for version (min=red, max=green, middle=yellow)
        if len(sorted_versions) > 1:
            if ver == min_version:
                ver_color = Colors.RED
                status = "OLDEST"
            elif ver == max_version:
                ver_color = Colors.GREEN
                status = "NEWEST"
            else:
                ver_color = Colors.YELLOW
                status = "MIDDLE"
        else:
            ver_color = Colors.WHITE
            status = "ONLY"

        repos_with_version = version_map[ver]
        for parent_repo, dep_type in repos_with_version:
            type_color = Colors.GRAY if dep_type == 'dev' else Colors.WHITE
            print(f"{ver_color}{str(ver):<12}{Colors.END} "
                  f"{type_color}{dep_type:<6}{Colors.END} "
                  f"{Colors.WHITE}{parent_repo:<25}{Colors.END} "
                  f"{ver_color}{status}{Colors.END}")

    # Summary
    print(f"\n{Colors.PURPLE}{Colors.BOLD}Summary for {package_name}:{Colors.END}")
    print(f"Versions in ecosystem: {Colors.BOLD}{len(versions)}{Colors.END}")
    print(f"Total usage count: {Colors.BOLD}{len(version_usages)}{Colors.END}")
    print(f"Repositories using: {Colors.BOLD}{len(set(repo for repo, _, _ in [(r, t, p) for r, v, t, p in version_usages]))}{Colors.END}")

    if len(versions) > 1:
        print(f"{Colors.RED}⚠️  Version conflict detected - Hub will resolve to {max_version}{Colors.END}")
    else:
        print(f"{Colors.GREEN}✅ No version conflicts{Colors.END}")

def analyze_hub_status(dependencies):
    """Analyze hub's current package status"""
    print(f"{Colors.PURPLE}{Colors.BOLD}🎯 HUB PACKAGE STATUS{Colors.END}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.END}\n")

    # Get hub dependencies
    hub_deps = get_hub_dependencies()

    if not hub_deps:
        print(f"{Colors.RED}❌ No hub dependencies found or could not read hub's Cargo.toml{Colors.END}")
        return

    # Load latest versions from cache
    latest_cache = {}
    data_file = Path("deps_data.txt")
    if data_file.exists():
        with open(data_file, 'r') as f:
            for line in f:
                if line.startswith("DEPENDENCY:"):
                    parts = line.strip().split(", LATEST: ")
                    if len(parts) == 2:
                        dep_name = parts[0].replace("DEPENDENCY: ", "")
                        latest_version = parts[1]
                        latest_cache[dep_name] = latest_version

    # Count usage for all packages in ecosystem
    package_usage = {}
    for dep_name, usages in dependencies.items():
        version_usages = [(parent_repo, ver, typ, path) for parent_repo, ver, typ, path in usages
                         if ver not in ['path', 'workspace']]
        if version_usages:
            unique_repos = set(parent_repo.split('.')[1] for parent_repo, _, _, _ in version_usages)
            package_usage[dep_name] = len(unique_repos)

    # Analyze hub packages
    hub_current = []
    hub_outdated = []

    for dep_name, hub_version_str in hub_deps.items():
        hub_version = parse_version(hub_version_str)
        latest_version = parse_version(latest_cache.get(dep_name, ""))
        usage_count = package_usage.get(dep_name, 0)

        if latest_version and hub_version and hub_version < latest_version:
            hub_outdated.append((dep_name, hub_version_str, latest_cache.get(dep_name, "unknown"), usage_count))
        else:
            hub_current.append((dep_name, hub_version_str, latest_cache.get(dep_name, hub_version_str), usage_count))

    # Sort by usage count
    hub_current.sort(key=lambda x: x[3], reverse=True)
    hub_outdated.sort(key=lambda x: x[3], reverse=True)

    # Print current packages in columns
    if hub_current:
        print(f"{Colors.PURPLE}{Colors.BOLD}CURRENT PACKAGES:{Colors.END}")
        print(f"{Colors.WHITE}{'Package':<20} {'Hub Version':<15} {'Latest':<15} {'Usage':<10}{Colors.END}")
        print(f"{Colors.GRAY}{'-' * 60}{Colors.END}")

        for dep_name, hub_ver, latest_ver, usage in hub_current:
            usage_color = Colors.GREEN if usage >= 5 else Colors.WHITE if usage >= 3 else Colors.GRAY
            print(f"  {Colors.WHITE}{dep_name:<20}{Colors.END} "
                  f"{Colors.WHITE}{hub_ver:<15}{Colors.END} "
                  f"{Colors.CYAN}{latest_ver:<15}{Colors.END} "
                  f"{usage_color}({usage} projects){Colors.END}")
        print()

    # Print outdated packages
    if hub_outdated:
        print(f"{Colors.PURPLE}{Colors.BOLD}OUTDATED PACKAGES:{Colors.END}")
        print(f"{Colors.WHITE}{'Package':<20} {'Hub Version':<15} {'Latest':<15} {'Usage':<10}{Colors.END}")
        print(f"{Colors.GRAY}{'-' * 60}{Colors.END}")

        for dep_name, hub_ver, latest_ver, usage in hub_outdated:
            usage_color = Colors.GREEN if usage >= 5 else Colors.WHITE if usage >= 3 else Colors.GRAY
            print(f"  {Colors.WHITE}{dep_name:<20}{Colors.END} "
                  f"{Colors.YELLOW}{hub_ver:<15}{Colors.END} "
                  f"{Colors.CYAN}{latest_ver:<15}{Colors.END} "
                  f"{usage_color}({usage} projects){Colors.END}")
        print()

    # Find opportunities (5+ usage packages not in hub)
    opportunities = []
    for dep_name, usage_count in package_usage.items():
        if usage_count >= 5 and dep_name not in hub_deps:
            latest_ver = latest_cache.get(dep_name, "unknown")
            opportunities.append((dep_name, usage_count, latest_ver))

    opportunities.sort(key=lambda x: x[1], reverse=True)

    # Print opportunities in columns
    if opportunities:
        print(f"{Colors.PURPLE}{Colors.BOLD}PACKAGE OPPORTUNITIES (5+ usage, not in hub):{Colors.END}")
        print(f"{Colors.GRAY}{'-' * 80}{Colors.END}")
        col_width = 30
        cols = 3

        for i in range(0, len(opportunities), cols):
            row = "  "
            for j in range(cols):
                if i + j < len(opportunities):
                    dep_name, usage, latest_ver = opportunities[i + j]
                    text = f"{dep_name}({usage})"
                    colored = f"{Colors.GREEN}{text}{Colors.END}"  # Changed to green to match Gap color
                    # Pad based on actual text length, not colored string
                    padding = " " * max(0, col_width - len(text))
                    row += colored + padding
            print(row.rstrip())
        print()

    # Summary using hub-only mode (no High/Med/Low categories)
    # Convert package_usage to the format expected by calculate_hub_status
    package_consumers_format = {dep_name: (count, []) for dep_name, count in package_usage.items()}
    hub_status = calculate_hub_status(package_consumers_format, hub_deps, latest_cache)

    print_summary_table(hub_status=hub_status, hub_only=True)

def check_latest(package_name):
    """Check latest version of a specific package"""
    print(f"{Colors.CYAN}{Colors.BOLD}🔍 CHECKING LATEST VERSION: {package_name}{Colors.END}")
    print(f"{Colors.CYAN}{'='*50}{Colors.END}\n")

    latest_version = get_latest_version(package_name)

    if latest_version:
        print(f"{Colors.CYAN}Latest version on crates.io: {Colors.BOLD}{latest_version}{Colors.END}")
        print(f"{Colors.GRAY}URL: https://crates.io/crates/{package_name}{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Could not fetch latest version for '{package_name}'")
        print(f"{Colors.GRAY}Package may not exist on crates.io or network error{Colors.END}")

def calculate_hub_status(package_consumers, hub_deps, latest_cache):
    """Calculate hub status metrics"""
    hub_current = []  # In hub and up-to-date
    hub_outdated = []  # In hub but outdated
    hub_unused = []   # In hub but not used anywhere
    hub_gap_high = []  # High usage packages not in hub
    hub_unique = []  # All packages not in hub

    # First, check what's actually used in the ecosystem
    for dep_name, (count, _) in package_consumers.items():
        if dep_name in hub_deps:
            hub_version = parse_version(hub_deps[dep_name])
            latest_version = parse_version(latest_cache.get(dep_name, ""))
            if latest_version and hub_version and hub_version < latest_version:
                hub_outdated.append(dep_name)
            else:
                hub_current.append(dep_name)
        else:
            hub_unique.append(dep_name)
            if count >= 5:
                hub_gap_high.append(dep_name)

    # Check for hub packages that aren't used anywhere
    used_packages = set(package_consumers.keys())
    for dep_name in hub_deps:
        if dep_name not in used_packages:
            hub_unused.append(dep_name)

    return hub_current, hub_outdated, hub_unused, hub_gap_high, hub_unique

def print_summary_table(high_usage=None, medium_usage=None, low_usage=None, package_consumers=None, hub_status=None, hub_only=False):
    """Print summary table with package counts and optional hub status"""
    col_width = 12

    # Only show package counts if not hub_only mode
    if not hub_only and high_usage is not None:
        print(f"{Colors.PURPLE}{Colors.BOLD}SUMMARY:{Colors.END}")
        # Package counts
        labels = ["High", "Med", "Low", "Total"]
        values = [len(high_usage), len(medium_usage), len(low_usage), len(package_consumers)]
        colors = [Colors.WHITE, Colors.WHITE, Colors.GRAY, Colors.BOLD]

        row = "  "
        for label in labels:
            row += f"{label:<{col_width}}"
        print(row)

        row = "  "
        for i, (value, color) in enumerate(zip(values, colors)):
            text = str(value)
            colored = f"{color}{text}{Colors.END}"
            padding = " " * (col_width - len(text))
            row += colored + padding
        print(row)

        print()

    # Hub status (if provided)
    if hub_status:
        hub_current, hub_outdated, hub_unused, hub_gap_high, hub_unique = hub_status

        # Use different title if hub_only mode
        title = "HUB STATUS:" if not hub_only else "HUB PACKAGES:"
        print(f"{Colors.PURPLE}{Colors.BOLD}{title}{Colors.END}")

        hub_labels = ["Current", "Outdated", "Gap", "Unused", "Unique"]
        hub_values = [len(hub_current), len(hub_outdated), len(hub_gap_high), len(hub_unused), len(hub_unique)]
        hub_colors = [Colors.BLUE, Colors.ORANGE, Colors.GREEN, Colors.RED, Colors.GRAY]

        row = "  "
        for label in hub_labels:
            row += f"{label:<{col_width}}"
        print(row)

        row = "  "
        for i, (value, color) in enumerate(zip(hub_values, hub_colors)):
            text = str(value)
            colored = f"{color}■{Colors.END} {color}{text}{Colors.END}"
            # Calculate padding based on visible text (■ + space + number)
            visible_len = 1 + 1 + len(text)  # block + space + number
            padding = " " * (col_width - visible_len)
            row += colored + padding
        print(row)

        print()

# Data structures for structured cache
@dataclass
class RepoData:
    repo_id: int
    repo_name: str
    path: str
    parent: str
    last_update: int
    cargo_version: str
    hub_usage: str  # "1.0.0" or "path" or "NONE"
    hub_status: str  # "using", "path", "none"

@dataclass
class DepData:
    dep_id: int
    repo_id: int
    pkg_name: str
    pkg_version: str
    dep_type: str
    features: str

@dataclass
class LatestData:
    pkg_id: int
    pkg_name: str
    latest_version: str
    source_type: str  # "crate", "local", "git", "workspace"
    source_value: str  # crates.io version, local path, git repo, or "WORKSPACE"
    hub_version: str  # Hub's version or "NONE"
    hub_status: str   # "current", "outdated", "gap", "none"

@dataclass
class VersionMapData:
    map_id: int
    dep_id: int
    pkg_id: int
    repo_id: int
    version_state: str
    breaking_type: str
    ecosystem_status: str

@dataclass
class HubInfo:
    """Hub repository information container"""
    path: str
    version: str
    dependencies: Dict[str, str]  # pkg_name -> version
    last_update: int

# Helper functions for data cache generation
def find_all_cargo_files_fast() -> List[Path]:
    """Fast discovery of all Cargo.toml files using find command"""
    if not RUST_REPO_ROOT:
        return []

    try:
        # Use find command for speed, exclude target directories
        cmd = [
            'find', RUST_REPO_ROOT,
            '-name', 'Cargo.toml',
            '-not', '-path', '*/target/*',
            '-not', '-path', '*/ref/*',
            '-not', '-path', '*/howto/*',
            '-not', '-path', '*/_arch/*',
            '-not', '-path', '*/archive/*'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            paths = [Path(line.strip()) for line in result.stdout.strip().split('\n') if line.strip()]
            return paths
        else:
            print(f"{Colors.YELLOW}⚠️  find command failed, falling back to Python search{Colors.END}")
            return find_cargo_files(RUST_REPO_ROOT)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"{Colors.YELLOW}⚠️  find command not available, using Python search{Colors.END}")
        return find_cargo_files(RUST_REPO_ROOT)

def get_repo_info(cargo_path: Path) -> Optional[Dict]:
    """Get repository information from Cargo.toml file"""
    try:
        cargo_data = load_toml(cargo_path)

        # Get basic package info
        package_info = cargo_data.get('package', {})
        repo_name = package_info.get('name', cargo_path.parent.name)
        version = package_info.get('version', '0.0.0')

        # Extract dependencies
        dependencies = {}
        deps_section = cargo_data.get('dependencies', {})
        for dep_name, dep_info in deps_section.items():
            if isinstance(dep_info, str):
                dependencies[dep_name] = dep_info
            elif isinstance(dep_info, dict) and 'version' in dep_info:
                dependencies[dep_name] = dep_info['version']

        # Get last update time
        last_update = int(cargo_path.stat().st_mtime)

        # Get relative path
        rel_path = get_relative_path(cargo_path)

        return {
            'cargo_path': cargo_path,
            'repo_name': repo_name,
            'version': version,
            'dependencies': dependencies,
            'last_update': last_update,
            'rel_path': rel_path
        }
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Could not load repo info from {cargo_path}: {e}{Colors.END}")
        return None

def get_hub_info() -> Optional[HubInfo]:
    """Get hub repository information using the general repo helper"""
    if not RUST_REPO_ROOT:
        return None

    # Look for hub directory in common locations
    hub_paths = [
        Path(RUST_REPO_ROOT) / "oodx" / "projects" / "hub",
        Path(RUST_REPO_ROOT) / "oodx" / "hub",
        Path(RUST_REPO_ROOT) / "hub"
    ]

    for hub_path in hub_paths:
        cargo_path = hub_path / "Cargo.toml"
        if cargo_path.exists():
            repo_info = get_repo_info(cargo_path)
            if repo_info:
                return HubInfo(
                    path=repo_info['rel_path'],
                    version=repo_info['version'],
                    dependencies=repo_info['dependencies'],
                    last_update=repo_info['last_update']
                )

    return None

def detect_hub_usage(cargo_path: Path, hub_info: Optional[HubInfo]) -> Tuple[str, str]:
    """Detect if a repo uses hub and return (usage, status)"""
    if not hub_info:
        return "NONE", "none"

    try:
        cargo_data = load_toml(cargo_path)

        deps_section = cargo_data.get('dependencies', {})

        # Check for hub dependency
        if 'hub' in deps_section:
            hub_dep = deps_section['hub']
            if isinstance(hub_dep, str):
                return hub_dep, "using"
            elif isinstance(hub_dep, dict):
                if 'path' in hub_dep:
                    return "path", "path"
                elif 'version' in hub_dep:
                    return hub_dep['version'], "using"
                elif 'workspace' in hub_dep and hub_dep['workspace']:
                    return "workspace", "workspace"

        return "NONE", "none"
    except Exception:
        return "NONE", "none"

def extract_repo_metadata_batch(cargo_files: List[Path], hub_info: Optional[HubInfo]) -> List[RepoData]:
    """Extract repository metadata from all Cargo.toml files, excluding hub itself"""
    repos = []
    repo_id = 100

    for cargo_path in cargo_files:
        repo_info = get_repo_info(cargo_path)
        if not repo_info:
            continue

        # Include hub in analysis (hub is part of the ecosystem)

        # Get parent repo info
        parent_repo = get_parent_repo(cargo_path)

        # Detect hub usage
        hub_usage, hub_status = detect_hub_usage(cargo_path, hub_info)

        repos.append(RepoData(
            repo_id=repo_id,
            repo_name=repo_info['repo_name'],
            path=repo_info['rel_path'],
            parent=parent_repo.split('.')[0],  # Just parent part
            last_update=repo_info['last_update'],
            cargo_version=repo_info['version'],
            hub_usage=hub_usage,
            hub_status=hub_status
        ))
        repo_id += 1

    return repos

def extract_dependencies_batch(cargo_files: List[Path]) -> List[DepData]:
    """Extract all dependencies from all Cargo.toml files"""
    deps = []
    dep_id = 1000

    # Create repo_id lookup - only for valid repos (apply same filtering as extract_repo_metadata_batch)
    repo_lookup = {}
    repo_id = 100

    for cargo_path in cargo_files:
        repo_info = get_repo_info(cargo_path)
        if not repo_info:
            continue

        # Include hub in dependency analysis (consistent with repo metadata)

        repo_lookup[str(cargo_path)] = repo_id
        repo_id += 1

    for cargo_path in cargo_files:
        try:
            # Skip if this cargo file was filtered out during repo_lookup creation
            if str(cargo_path) not in repo_lookup:
                continue

            cargo_data = load_toml(cargo_path)
            current_repo_id = repo_lookup[str(cargo_path)]

            # Process regular dependencies
            if 'dependencies' in cargo_data:
                for dep_name, dep_info in cargo_data['dependencies'].items():
                    dep_version, features, source_type, source_value = parse_dependency_info(dep_info, cargo_path)
                    if dep_version:  # Include all deps, even path/workspace
                        deps.append(DepData(
                            dep_id=dep_id,
                            repo_id=current_repo_id,
                            pkg_name=dep_name,
                            pkg_version=dep_version,
                            dep_type='dep',
                            features=features
                        ))
                        dep_id += 1

            # Process dev-dependencies
            if 'dev-dependencies' in cargo_data:
                for dep_name, dep_info in cargo_data['dev-dependencies'].items():
                    dep_version, features, source_type, source_value = parse_dependency_info(dep_info, cargo_path)
                    if dep_version:
                        deps.append(DepData(
                            dep_id=dep_id,
                            repo_id=current_repo_id,
                            pkg_name=dep_name,
                            pkg_version=dep_version,
                            dep_type='dev-dep',
                            features=features
                        ))
                        dep_id += 1

        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Warning: Could not parse dependencies in {cargo_path}: {e}{Colors.END}")

    return deps

def parse_dependency_info(dep_info, cargo_path: Path) -> Tuple[Optional[str], str, str, str]:
    """Parse dependency info and return (version, features, source_type, source_value)"""
    if isinstance(dep_info, str):
        # Simple version string: serde = "1.0"
        return dep_info, "NONE", "crate", dep_info
    elif isinstance(dep_info, dict):
        features = ','.join(dep_info.get('features', [])) or "NONE"

        if 'version' in dep_info:
            # Standard crate: serde = { version = "1.0", features = [...] }
            return dep_info['version'], features, "crate", dep_info['version']
        elif 'path' in dep_info:
            # Local path dependency: my-lib = { path = "../my-lib" }
            path_value = dep_info['path']
            local_version = resolve_local_version(cargo_path, path_value)
            return local_version, features, "local", path_value
        elif 'workspace' in dep_info and dep_info['workspace']:
            # Workspace dependency: serde = { workspace = true }
            workspace_version = resolve_workspace_version(cargo_path, dep_info)
            return workspace_version, features, "workspace", "WORKSPACE"
        elif 'git' in dep_info:
            # Git dependency: some-crate = { git = "https://..." }
            git_repo = dep_info['git']
            git_ref = dep_info.get('rev', dep_info.get('branch', dep_info.get('tag', 'HEAD')))
            git_version = resolve_git_version(git_repo, git_ref)
            return git_version, features, "git", f"{git_repo}#{git_ref}"
    return None, "NONE", "unknown", "NONE"

def resolve_local_version(cargo_path: Path, relative_path: str) -> str:
    """Resolve version from local path dependency using get_repo_info"""
    try:
        # Resolve relative path from current Cargo.toml location
        local_cargo_path = (cargo_path.parent / relative_path / "Cargo.toml").resolve()
        if local_cargo_path.exists():
            repo_info = get_repo_info(local_cargo_path)
            if repo_info:
                return repo_info['version']
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Could not resolve local version for {relative_path}: {e}{Colors.END}")
    return "LOCAL"

def resolve_workspace_version(cargo_path: Path, dep_info: dict) -> str:
    """Resolve version from workspace dependency (placeholder for now)"""
    # TODO: Implement workspace version resolution
    # Would need to find workspace root and resolve the actual version
    return "WORKSPACE"

def resolve_git_version(git_repo: str, git_ref: str) -> str:
    """Resolve version from git dependency using gh command"""
    try:
        # Extract owner/repo from git URL
        if "github.com/" in git_repo:
            # Handle both SSH and HTTPS URLs
            if git_repo.startswith("git@github.com:"):
                repo_path = git_repo.replace("git@github.com:", "").replace(".git", "")
            elif git_repo.startswith("https://github.com/"):
                repo_path = git_repo.replace("https://github.com/", "").replace(".git", "")
            else:
                return f"GIT#{git_ref[:8]}"

            # Try to get version from Cargo.toml in the repository
            import subprocess
            import json
            import base64

            try:
                # Get Cargo.toml content from specific branch/commit
                result = subprocess.run([
                    "gh", "api", f"repos/{repo_path}/contents/Cargo.toml",
                    "--jq", ".content"
                ], capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    # Decode base64 content and parse TOML
                    content = base64.b64decode(result.stdout.strip()).decode('utf-8')
                    cargo_data = load_toml(content, is_string=True)

                    if 'package' in cargo_data and 'version' in cargo_data['package']:
                        version = cargo_data['package']['version']
                        # Return just the semantic version, not git hash
                        return version

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
                pass

            # Fallback: if we can't get Cargo.toml, assume a reasonable default
            # This handles cases where the repo exists but Cargo.toml is missing/inaccessible
            return "0.0.0"

        # Ultimate fallback for non-GitHub repos
        return "0.0.0"

    except Exception as e:
        return "0.0.0"

def collect_unique_packages_with_sources(cargo_files: List[Path]) -> Dict[str, Tuple[str, str]]:
    """Collect unique package names with their source info (source_type, source_value)"""
    packages = {}  # pkg_name -> (source_type, source_value)

    for cargo_path in cargo_files:
        try:
            cargo_data = load_toml(cargo_path)

            # Process regular dependencies
            if 'dependencies' in cargo_data:
                for dep_name, dep_info in cargo_data['dependencies'].items():
                    dep_version, features, source_type, source_value = parse_dependency_info(dep_info, cargo_path)
                    if dep_version and dep_name not in packages:
                        packages[dep_name] = (source_type, source_value)

            # Process dev-dependencies
            if 'dev-dependencies' in cargo_data:
                for dep_name, dep_info in cargo_data['dev-dependencies'].items():
                    dep_version, features, source_type, source_value = parse_dependency_info(dep_info, cargo_path)
                    if dep_version and dep_name not in packages:
                        packages[dep_name] = (source_type, source_value)

        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Warning: Could not parse dependencies in {cargo_path}: {e}{Colors.END}")

    return packages

def collect_unique_packages(deps: List[DepData]) -> Set[str]:
    """Collect unique package names (legacy function for compatibility)"""
    packages = set()
    for dep in deps:
        packages.add(dep.pkg_name)
    return packages

def create_local_repo_lookup(repos: List[RepoData]) -> Dict[str, str]:
    """Create a lookup map from package names to local paths"""
    local_lookup = {}
    for repo in repos:
        # Map repo name to its path for LOCAL flag detection
        local_lookup[repo.repo_name] = repo.path
    return local_lookup

def batch_fetch_latest_versions(packages_with_sources: Dict[str, Tuple[str, str]], hub_info: Optional[HubInfo] = None, repos: Optional[List[RepoData]] = None) -> Dict[str, LatestData]:
    """Batch fetch latest versions for all packages with source information"""
    latest_data = {}
    pkg_id = 200

    # Create local repo lookup for LOCAL flag detection
    local_lookup = create_local_repo_lookup(repos) if repos else {}

    total = len(packages_with_sources)
    progress = ProgressSpinner(f"Fetching latest versions...", total)
    progress.start()

    try:
        processed = 0
        for pkg_name, (source_type, source_value) in sorted(packages_with_sources.items()):
            processed += 1
            progress.update(processed, f"Fetching {pkg_name}...")

            # Fetch version based on source type
            if source_type == "crate":
                latest_version = get_latest_version(pkg_name)
            elif source_type == "git":
                # For git dependencies, extract the repo URL and resolve the version
                if "#" in source_value:
                    repo_url, git_ref = source_value.split("#", 1)
                else:
                    repo_url, git_ref = source_value, "main"
                latest_version = resolve_git_version(repo_url, git_ref)
            elif source_type == "local":
                # For local dependencies, we'll need to resolve from the local path
                latest_version = "LOCAL"
            elif source_type == "workspace":
                latest_version = "WORKSPACE"
            else:
                latest_version = "UNKNOWN"

            if latest_version or source_type != "crate":
                # Check if git repos are also available locally
                final_source_value = source_value
                if source_type == "git" and pkg_name in local_lookup:
                    # Git repo is also available locally - add LOCAL flag
                    final_source_value = f"{source_value} (LOCAL: {local_lookup[pkg_name]})"

                # Check if package is in hub
                if hub_info and pkg_name in hub_info.dependencies:
                    hub_version = hub_info.dependencies[pkg_name]
                    # Determine hub status (only compare for crate dependencies)
                    if source_type == "crate" and latest_version != "N/A":
                        hub_ver = parse_version(hub_version)
                        latest_ver = parse_version(latest_version)
                        if hub_ver and latest_ver:
                            if hub_ver == latest_ver:
                                hub_status = "current"
                            elif hub_ver < latest_ver:
                                hub_status = "outdated"
                            else:
                                hub_status = "ahead"
                        else:
                            hub_status = "unknown"
                    else:
                        hub_status = "local"  # Local/git deps in hub
                else:
                    hub_version = "NONE"
                    hub_status = "gap"

                latest_data[pkg_name] = LatestData(
                    pkg_id=pkg_id,
                    pkg_name=pkg_name,
                    latest_version=latest_version,
                    source_type=source_type,
                    source_value=final_source_value,
                    hub_version=hub_version,
                    hub_status=hub_status
                )
                pkg_id += 1

        progress.stop(f"{Colors.GREEN}✅ Fetched {len(latest_data)} latest versions{Colors.END}")

    except Exception as e:
        progress.stop(f"{Colors.RED}❌ Failed to fetch versions: {e}{Colors.END}")

    return latest_data

def generate_version_analysis(deps: List[DepData], repos: List[RepoData], latest_versions: Dict[str, LatestData]) -> List[VersionMapData]:
    """Generate version analysis mapping"""
    version_maps = []
    map_id = 300

    for dep in deps:
        # Find corresponding repo and latest version data
        repo = next((r for r in repos if r.repo_id == dep.repo_id), None)
        latest = latest_versions.get(dep.pkg_name)

        if repo and latest:
            # Determine version state
            version_state = get_version_stability(dep.pkg_version)

            # Determine breaking type
            breaking_type = "unknown"
            if not dep.pkg_version.startswith(('path:', 'git:', 'workspace:')):
                breaking_type = determine_breaking_type(dep.pkg_version, latest.latest_version)

            # Determine ecosystem status (simplified for now)
            ecosystem_status = "normal"

            version_maps.append(VersionMapData(
                map_id=map_id,
                dep_id=dep.dep_id,
                pkg_id=latest.pkg_id,
                repo_id=dep.repo_id,
                version_state=version_state,
                breaking_type=breaking_type,
                ecosystem_status=ecosystem_status
            ))
            map_id += 1

    return version_maps

def determine_breaking_type(current_version: str, latest_version: str) -> str:
    """Determine if update would be breaking"""
    if is_breaking_change(current_version, latest_version):
        return "BREAKING"
    elif parse_version(latest_version) and parse_version(current_version):
        if parse_version(latest_version) > parse_version(current_version):
            return "safe"
        else:
            return "current"
    return "unknown"

def get_version_stability(version_str: str) -> str:
    """Get version stability status"""
    if version_str.startswith(('path:', 'git:', 'workspace:')):
        return "local"

    parsed = parse_version(version_str)
    if not parsed:
        return "unknown"

    if parsed.is_prerelease:
        return "pre-release"
    elif parsed.major == 0:
        return "unstable"
    else:
        return "stable"

def write_tsv_cache(repos: List[RepoData], deps: List[DepData], latest_versions: Dict[str, LatestData], version_maps: List[VersionMapData], output_file: str):
    """Write structured TSV cache file"""
    with open(output_file, 'w') as f:
        # Section 0: AGGREGATION METRICS
        f.write("#------ SECTION : AGGREGATION METRICS --------#\n")
        f.write("KEY\tVALUE\n")

        # Repository metrics
        f.write(f"total_repos\t{len(repos)}\n")
        hub_using_repos = len([r for r in repos if r.hub_status in ['using', 'path']])
        f.write(f"hub_using_repos\t{hub_using_repos}\n")

        # Dependency metrics
        f.write(f"total_deps\t{len(deps)}\n")
        f.write(f"total_packages\t{len(latest_versions)}\n")

        # Package source breakdown
        git_packages = len([p for p in latest_versions.values() if p.source_type == 'git'])
        local_packages = len([p for p in latest_versions.values() if p.source_type == 'local'])
        crate_packages = len([p for p in latest_versions.values() if p.source_type == 'crate'])
        workspace_packages = len([p for p in latest_versions.values() if p.source_type == 'workspace'])
        f.write(f"git_packages\t{git_packages}\n")
        f.write(f"local_packages\t{local_packages}\n")
        f.write(f"crate_packages\t{crate_packages}\n")
        f.write(f"workspace_packages\t{workspace_packages}\n")

        # Hub status breakdown
        current_packages = len([p for p in latest_versions.values() if p.hub_status == 'current'])
        outdated_packages = len([p for p in latest_versions.values() if p.hub_status == 'outdated'])
        gap_packages = len([p for p in latest_versions.values() if p.hub_status == 'gap'])
        local_hub_packages = len([p for p in latest_versions.values() if p.hub_status == 'local'])
        f.write(f"hub_current\t{current_packages}\n")
        f.write(f"hub_outdated\t{outdated_packages}\n")
        f.write(f"hub_gap\t{gap_packages}\n")
        f.write(f"hub_local\t{local_hub_packages}\n")

        # Breaking change analysis
        breaking_deps = len([v for v in version_maps if v.breaking_type == 'BREAKING'])
        safe_deps = len([v for v in version_maps if v.breaking_type == 'safe'])
        unknown_deps = len([v for v in version_maps if v.breaking_type == 'unknown'])
        f.write(f"breaking_updates\t{breaking_deps}\n")
        f.write(f"safe_updates\t{safe_deps}\n")
        f.write(f"unknown_updates\t{unknown_deps}\n")

        # Version state analysis
        stable_deps = len([v for v in version_maps if v.version_state == 'stable'])
        unstable_deps = len([v for v in version_maps if v.version_state == 'unstable'])
        f.write(f"stable_versions\t{stable_deps}\n")
        f.write(f"unstable_versions\t{unstable_deps}\n")

        f.write("\n")

    with open(output_file, 'a') as f:
        # Section 1: REPO LIST
        f.write("#------ SECTION : REPO LIST --------#\n")
        f.write("REPO_ID\tREPO_NAME\tPATH\tPARENT\tLAST_UPDATE\tCARGO_VERSION\tHUB_USAGE\tHUB_STATUS\n")
        for repo in repos:
            f.write(f"{repo.repo_id}\t{repo.repo_name}\t{repo.path}\t{repo.parent}\t{repo.last_update}\t{repo.cargo_version}\t{repo.hub_usage}\t{repo.hub_status}\n")
        f.write("\n")

        # Section 2: DEPS VERSIONS LIST
        f.write("#------ SECTION : DEP VERSIONS LIST --------#\n")
        f.write("DEP_ID\tREPO_ID\tPKG_NAME\tPKG_VERSION\tDEP_TYPE\tFEATURES\n")
        for dep in deps:
            f.write(f"{dep.dep_id}\t{dep.repo_id}\t{dep.pkg_name}\t{dep.pkg_version}\t{dep.dep_type}\t{dep.features}\n")
        f.write("\n")

        # Section 3: LATEST LIST
        f.write("#------ SECTION : DEP LATEST LIST --------#\n")
        f.write("PKG_ID\tPKG_NAME\tLATEST_VERSION\tSOURCE_TYPE\tSOURCE_VALUE\tHUB_VERSION\tHUB_STATUS\n")
        for latest in latest_versions.values():
            f.write(f"{latest.pkg_id}\t{latest.pkg_name}\t{latest.latest_version}\t{latest.source_type}\t{latest.source_value}\t{latest.hub_version}\t{latest.hub_status}\n")
        f.write("\n")

        # Section 4: VERSION MAP LIST
        f.write("#------ SECTION : VERSION MAP LIST --------#\n")
        f.write("MAP_ID\tDEP_ID\tPKG_ID\tREPO_ID\tVERSION_STATE\tBREAKING_TYPE\tECOSYSTEM_STATUS\n")
        for vm in version_maps:
            f.write(f"{vm.map_id}\t{vm.dep_id}\t{vm.pkg_id}\t{vm.repo_id}\t{vm.version_state}\t{vm.breaking_type}\t{vm.ecosystem_status}\n")

# === TSV HYDRATION FUNCTIONS ===

@dataclass
class EcosystemData:
    """Hydrated ecosystem data from TSV cache"""
    aggregation: Dict[str, str]
    repos: Dict[int, RepoData]
    deps: Dict[int, DepData]
    latest: Dict[str, LatestData]  # keyed by pkg_name
    version_maps: Dict[int, VersionMapData]

def hydrate_tsv_cache(cache_file: str = "deps_cache.tsv") -> EcosystemData:
    """Load and parse structured TSV cache into organized data structures"""
    if not Path(cache_file).exists():
        raise FileNotFoundError(f"Cache file {cache_file} not found. Run './bin/deps.py data' to generate it.")

    aggregation = {}
    repos = {}
    deps = {}
    latest = {}
    version_maps = {}

    current_section = None

    with open(cache_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Section headers
            if line.startswith("#------ SECTION :"):
                if "AGGREGATION METRICS" in line:
                    current_section = "aggregation"
                elif "REPO LIST" in line:
                    current_section = "repos"
                elif "DEP VERSIONS LIST" in line:
                    current_section = "deps"
                elif "DEP LATEST LIST" in line:
                    current_section = "latest"
                elif "VERSION MAP LIST" in line:
                    current_section = "version_maps"
                continue

            # Skip header rows
            if "\t" in line and (line.startswith("KEY\t") or line.startswith("REPO_ID\t") or
                                line.startswith("DEP_ID\t") or line.startswith("PKG_ID\t") or
                                line.startswith("MAP_ID\t")):
                continue

            # Parse data rows
            parts = line.split("\t")

            try:
                if current_section == "aggregation" and len(parts) >= 2:
                    key, value = parts[0], parts[1]
                    aggregation[key] = value

                elif current_section == "repos" and len(parts) >= 8:
                    repo = RepoData(
                        repo_id=int(parts[0]),
                        repo_name=parts[1],
                        path=parts[2],
                        parent=parts[3],
                        last_update=int(parts[4]),
                        cargo_version=parts[5],
                        hub_usage=parts[6],
                        hub_status=parts[7]
                    )
                    repos[repo.repo_id] = repo

                elif current_section == "deps" and len(parts) >= 6:
                    dep = DepData(
                        dep_id=int(parts[0]),
                        repo_id=int(parts[1]),
                        pkg_name=parts[2],
                        pkg_version=parts[3],
                        dep_type=parts[4],
                        features=parts[5]
                    )
                    deps[dep.dep_id] = dep

                elif current_section == "latest" and len(parts) >= 7:
                    latest_data = LatestData(
                        pkg_id=int(parts[0]),
                        pkg_name=parts[1],
                        latest_version=parts[2],
                        source_type=parts[3],
                        source_value=parts[4],
                        hub_version=parts[5],
                        hub_status=parts[6]
                    )
                    latest[latest_data.pkg_name] = latest_data

                elif current_section == "version_maps" and len(parts) >= 7:
                    vm = VersionMapData(
                        map_id=int(parts[0]),
                        dep_id=int(parts[1]),
                        pkg_id=int(parts[2]),
                        repo_id=int(parts[3]),
                        version_state=parts[4],
                        breaking_type=parts[5],
                        ecosystem_status=parts[6]
                    )
                    version_maps[vm.map_id] = vm

            except (ValueError, IndexError) as e:
                print(f"{Colors.YELLOW}⚠️  Skipping malformed line {line_num}: {line[:50]}... ({e}){Colors.END}")
                continue

    return EcosystemData(
        aggregation=aggregation,
        repos=repos,
        deps=deps,
        latest=latest,
        version_maps=version_maps
    )

# === VIEW HELPER FUNCTIONS ===

def get_package_usage_count(ecosystem: EcosystemData, pkg_name: str) -> int:
    """Get count of repositories using a specific package"""
    return len([dep for dep in ecosystem.deps.values() if dep.pkg_name == pkg_name])

def get_packages_by_usage(ecosystem: EcosystemData) -> List[Tuple[str, int]]:
    """Get packages sorted by usage count (descending)"""
    usage_counts = {}
    for dep in ecosystem.deps.values():
        usage_counts[dep.pkg_name] = usage_counts.get(dep.pkg_name, 0) + 1

    return sorted(usage_counts.items(), key=lambda x: (-x[1], x[0]))

def get_version_conflicts(ecosystem: EcosystemData) -> Dict[str, List[str]]:
    """Get packages with version conflicts (multiple versions in ecosystem)"""
    package_versions = {}
    for dep in ecosystem.deps.values():
        if dep.pkg_name not in package_versions:
            package_versions[dep.pkg_name] = set()
        package_versions[dep.pkg_name].add(dep.pkg_version)

    return {pkg: sorted(list(versions)) for pkg, versions in package_versions.items() if len(versions) > 1}

def get_breaking_updates(ecosystem: EcosystemData) -> List[Tuple[str, str, str]]:
    """Get packages with breaking updates available. Returns [(pkg_name, current_version, latest_version)]"""
    breaking = []
    for latest in ecosystem.latest.values():
        if latest.source_type == "crate":  # Only check crates.io packages
            pkg_versions = [dep.pkg_version for dep in ecosystem.deps.values() if dep.pkg_name == latest.pkg_name]
            if pkg_versions:
                current_version = max(pkg_versions, key=parse_version)
                if is_breaking_change(current_version, latest.latest_version):
                    breaking.append((latest.pkg_name, current_version, latest.latest_version))

    return breaking

def get_hub_gaps(ecosystem: EcosystemData) -> List[str]:
    """Get packages used in ecosystem but missing from hub"""
    return [latest.pkg_name for latest in ecosystem.latest.values() if latest.hub_status == "gap"]

def get_repos_using_package(ecosystem: EcosystemData, pkg_name: str) -> List[RepoData]:
    """Get repositories that use a specific package"""
    repo_ids = set()
    for dep in ecosystem.deps.values():
        if dep.pkg_name == pkg_name:
            repo_ids.add(dep.repo_id)

    return [ecosystem.repos[repo_id] for repo_id in repo_ids if repo_id in ecosystem.repos]

def format_aggregation_summary(ecosystem: EcosystemData) -> str:
    """Format aggregation metrics into a readable summary"""
    agg = ecosystem.aggregation
    lines = []
    lines.append(f"📊 **Ecosystem Overview**")
    lines.append(f"   Repositories: {agg.get('total_repos', '?')}")
    lines.append(f"   Dependencies: {agg.get('total_deps', '?')}")
    lines.append(f"   Unique Packages: {agg.get('total_packages', '?')}")
    lines.append(f"")
    lines.append(f"🔗 **Package Sources**")
    lines.append(f"   Crates.io: {agg.get('crate_packages', '?')}")
    lines.append(f"   Git: {agg.get('git_packages', '?')}")
    lines.append(f"   Local: {agg.get('local_packages', '?')}")
    lines.append(f"   Workspace: {agg.get('workspace_packages', '?')}")
    lines.append(f"")
    lines.append(f"🎯 **Hub Integration**")
    lines.append(f"   Using Hub: {agg.get('hub_using_repos', '?')} repos")
    lines.append(f"   Current: {agg.get('hub_current', '?')} packages")
    lines.append(f"   Outdated: {agg.get('hub_outdated', '?')} packages")
    lines.append(f"   Gaps: {agg.get('hub_gap', '?')} packages")
    lines.append(f"")
    lines.append(f"⚠️ **Breaking Changes**")
    lines.append(f"   Breaking Updates: {agg.get('breaking_updates', '?')}")
    lines.append(f"   Safe Updates: {agg.get('safe_updates', '?')}")

    return "\n".join(lines)

def get_hub_dependencies():
    """Get dependencies from hub's Cargo.toml"""
    hub_deps = {}
    hub_cargo_path = Path(RUST_REPO_ROOT) / "oodx" / "projects" / "hub" / "Cargo.toml"

    if hub_cargo_path.exists():
        try:
            cargo_data = load_toml(hub_cargo_path)

            # Parse regular dependencies
            if 'dependencies' in cargo_data:
                for dep_name, dep_info in cargo_data['dependencies'].items():
                    if isinstance(dep_info, dict) and 'version' in dep_info:
                        hub_deps[dep_name] = dep_info['version']
                    elif isinstance(dep_info, str):
                        hub_deps[dep_name] = dep_info

            # Parse dev-dependencies
            if 'dev-dependencies' in cargo_data:
                for dep_name, dep_info in cargo_data['dev-dependencies'].items():
                    if isinstance(dep_info, dict) and 'version' in dep_info:
                        hub_deps[dep_name] = dep_info['version']
                    elif isinstance(dep_info, str):
                        hub_deps[dep_name] = dep_info
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Could not read hub's Cargo.toml: {e}{Colors.END}")

    return hub_deps

def analyze_package_usage(dependencies):
    """Analyze package usage across the ecosystem"""
    print(f"{Colors.PURPLE}{Colors.BOLD}📊 PACKAGE USAGE ANALYSIS{Colors.END}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.END}\n")

    # Get hub dependencies
    hub_deps = get_hub_dependencies()

    # Load latest versions from cache
    latest_cache = {}
    data_file = Path("deps_data.txt")
    if data_file.exists():
        with open(data_file, 'r') as f:
            for line in f:
                if line.startswith("DEPENDENCY:"):
                    parts = line.strip().split(", LATEST: ")
                    if len(parts) == 2:
                        dep_name = parts[0].replace("DEPENDENCY: ", "")
                        latest_version = parts[1]
                        latest_cache[dep_name] = latest_version

    # Count consumers for each package
    package_consumers = {}
    for dep_name, usages in dependencies.items():
        # Filter out path/workspace dependencies
        version_usages = [(parent_repo, ver, typ, path) for parent_repo, ver, typ, path in usages
                         if ver not in ['path', 'workspace']]
        if version_usages:
            # Get unique parent repos
            unique_repos = set(parent_repo.split('.')[1] for parent_repo, _, _, _ in version_usages)
            package_consumers[dep_name] = (len(unique_repos), version_usages)

    # Categorize packages
    high_usage = []  # 5+ consumers
    medium_usage = []  # 3-4 consumers
    low_usage = []  # 1-2 consumers

    for dep_name, (consumer_count, usages) in package_consumers.items():
        if consumer_count >= 5:
            high_usage.append((dep_name, consumer_count, usages))
        elif consumer_count >= 3:
            medium_usage.append((dep_name, consumer_count, usages))
        else:
            low_usage.append((dep_name, consumer_count, usages))

    # Sort each category: hub packages first, then by usage count
    def sort_key(item):
        dep_name, count, _ = item
        in_hub = dep_name in hub_deps
        # Return tuple: (0 if in hub else 1, -count) for sorting
        # This puts hub packages first, then sorts by count descending
        return (0 if in_hub else 1, -count)

    high_usage.sort(key=sort_key)
    medium_usage.sort(key=sort_key)
    low_usage.sort(key=sort_key)

    # Print summary at the top (package counts only for query view)
    print_summary_table(high_usage, medium_usage, low_usage, package_consumers)

    # Print high usage packages (5+) in columns
    if high_usage:
        print(f"{Colors.PURPLE}{Colors.BOLD}HIGH USAGE (5+ projects):{Colors.END}")
        print(f"{Colors.GRAY}{'-' * 80}{Colors.END}")
        col_width = 25
        cols = 3
        for i in range(0, len(high_usage), cols):
            row = "  "
            for j in range(cols):
                if i + j < len(high_usage):
                    dep_name, count, _ = high_usage[i + j]
                    in_hub = dep_name in hub_deps
                    if in_hub:
                        hub_version = parse_version(hub_deps[dep_name])
                        latest_version = parse_version(latest_cache.get(dep_name, ""))
                        star = "*" if latest_version and hub_version and hub_version < latest_version else ""
                        text = f"{dep_name}({count}){star}"
                        colored = f"{Colors.BLUE}{text}{Colors.END}"
                    else:
                        text = f"{dep_name}({count})"
                        colored = f"{Colors.GREEN}{text}{Colors.END}"
                    # Pad based on actual text length, not colored string
                    padding = " " * max(0, col_width - len(text))
                    row += colored + padding
            print(row.rstrip())
        print()

    # Print medium usage packages (3-4) in columns
    if medium_usage:
        print(f"{Colors.PURPLE}{Colors.BOLD}MEDIUM USAGE (3-4 projects):{Colors.END}")
        print(f"{Colors.GRAY}{'-' * 80}{Colors.END}")
        col_width = 25
        cols = 3
        for i in range(0, len(medium_usage), cols):
            row = "  "
            for j in range(cols):
                if i + j < len(medium_usage):
                    dep_name, count, _ = medium_usage[i + j]
                    in_hub = dep_name in hub_deps
                    if in_hub:
                        hub_version = parse_version(hub_deps[dep_name])
                        latest_version = parse_version(latest_cache.get(dep_name, ""))
                        star = "*" if latest_version and hub_version and hub_version < latest_version else ""
                        text = f"{dep_name}({count}){star}"
                        colored = f"{Colors.BLUE}{text}{Colors.END}"
                    else:
                        text = f"{dep_name}({count})"
                        colored = f"{Colors.WHITE}{text}{Colors.END}"
                    # Pad based on actual text length, not colored string
                    padding = " " * max(0, col_width - len(text))
                    row += colored + padding
            print(row.rstrip())
        print()

    # Print low usage packages (1-2) in 3 columns
    if low_usage:
        print(f"{Colors.PURPLE}{Colors.BOLD}LOW USAGE (1-2 projects):{Colors.END}")
        print(f"{Colors.GRAY}{'-' * 80}{Colors.END}")
        col_width = 25
        cols = 3
        for i in range(0, len(low_usage), cols):
            row = "  "
            for j in range(cols):
                if i + j < len(low_usage):
                    dep_name, count, _ = low_usage[i + j]
                    in_hub = dep_name in hub_deps
                    if in_hub:
                        hub_version = parse_version(hub_deps[dep_name])
                        latest_version = parse_version(latest_cache.get(dep_name, ""))
                        star = "*" if latest_version and hub_version and hub_version < latest_version else ""
                        text = f"{dep_name}({count}){star}"
                        colored = f"{Colors.BLUE}{text}{Colors.END}"
                    else:
                        text = f"{dep_name}({count})"
                        colored = f"{Colors.GRAY}{text}{Colors.END}"
                    # Pad based on actual text length, not colored string
                    padding = " " * max(0, col_width - len(text))
                    row += colored + padding
            print(row.rstrip())
        print()

    # Calculate and show hub status at the bottom
    hub_status = calculate_hub_status(package_consumers, hub_deps, latest_cache)
    hub_current, hub_outdated, hub_unused, hub_gap_high, hub_unique = hub_status

    print(f"{Colors.PURPLE}{Colors.BOLD}HUB STATUS:{Colors.END}")
    col_width = 12

    hub_labels = ["Current", "Outdated", "Gap", "Unused", "Unique"]
    hub_values = [len(hub_current), len(hub_outdated), len(hub_gap_high), len(hub_unused), len(hub_unique)]
    hub_colors = [Colors.BLUE, Colors.ORANGE, Colors.GREEN, Colors.RED, Colors.GRAY]

    row = "  "
    for label in hub_labels:
        row += f"{label:<{col_width}}"
    print(row)

    row = "  "
    for i, (value, color) in enumerate(zip(hub_values, hub_colors)):
        text = str(value)
        colored = f"{color}■{Colors.END} {color}{text}{Colors.END}"
        # Calculate padding based on visible text (■ + space + number)
        visible_len = 1 + 1 + len(text)  # block + space + number
        padding = " " * (col_width - visible_len)
        row += colored + padding
    print(row)

def generate_data_cache(dependencies):
    """Generate structured TSV data cache for fast view rendering"""
    print(f"{Colors.PURPLE}{Colors.BOLD}📊 GENERATING STRUCTURED DATA CACHE{Colors.END}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.END}\n")

    # Phase 0: Get hub information first (separate container)
    print(f"{Colors.CYAN}Phase 0: Loading hub information...{Colors.END}")
    hub_info = get_hub_info()
    if hub_info:
        print(f"Found hub at {hub_info.path} (v{hub_info.version}) with {len(hub_info.dependencies)} dependencies")
    else:
        print("No hub found in standard locations")

    # Phase 1: Discovery
    print(f"{Colors.CYAN}Phase 1: Discovering Cargo.toml files...{Colors.END}")
    cargo_files = find_all_cargo_files_fast()
    print(f"Found {len(cargo_files)} Cargo.toml files")

    # Phase 2: Extract repo metadata (excluding hub)
    print(f"{Colors.CYAN}Phase 2: Extracting repository metadata...{Colors.END}")
    repos = extract_repo_metadata_batch(cargo_files, hub_info)
    print(f"Processed {len(repos)} repositories (hub excluded)")

    # Phase 3: Extract dependencies
    print(f"{Colors.CYAN}Phase 3: Extracting dependencies...{Colors.END}")
    deps = extract_dependencies_batch(cargo_files)
    packages_with_sources = collect_unique_packages_with_sources(cargo_files)
    hub_using_repos = len([r for r in repos if r.hub_status in ['using', 'path', 'workspace']])
    print(f"Found {len(deps)} dependency entries, {len(packages_with_sources)} unique packages, {hub_using_repos} repos using hub")

    # Phase 4: Batch fetch latest versions with source info
    print(f"{Colors.CYAN}Phase 4: Fetching latest versions...{Colors.END}")
    latest_versions = batch_fetch_latest_versions(packages_with_sources, hub_info, repos)
    print(f"Fetched latest versions for {len(latest_versions)} packages")

    # Phase 5: Generate analysis data
    print(f"{Colors.CYAN}Phase 5: Analyzing version status...{Colors.END}")
    version_maps = generate_version_analysis(deps, repos, latest_versions)
    print(f"Generated {len(version_maps)} version analysis entries")

    # Phase 6: Write TSV cache
    output_file = "deps_cache.tsv"
    print(f"{Colors.CYAN}Phase 6: Writing cache to {output_file}...{Colors.END}")
    write_tsv_cache(repos, deps, latest_versions, version_maps, output_file)

    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Data cache generated: {output_file}{Colors.END}")

# ============================================================================
# OPTIMIZED VIEW FUNCTIONS - Using hydrated TSV data for lightning-fast analysis
# ============================================================================

def view_conflicts(ecosystem: EcosystemData) -> None:
    """Lightning-fast version conflict analysis using hydrated data

    Replaces format_version_analysis() with ~100x performance improvement
    """
    print(f"{Colors.CYAN}{Colors.BOLD}🔍 VERSION CONFLICT ANALYSIS{Colors.END}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}")

    conflicts = {}

    # Group deps by package name using pre-indexed data (instant lookup)
    for dep_id, dep in ecosystem.deps.items():
        if dep.pkg_name not in conflicts:
            conflicts[dep.pkg_name] = []

        repo = ecosystem.repos[dep.repo_id]
        conflicts[dep.pkg_name].append({
            'repo': repo.repo_name,
            'version': dep.pkg_version,
            'type': dep.dep_type,
            'repo_parent': repo.parent
        })

    # Filter to only packages with conflicts (>1 version)
    conflict_packages = {k: v for k, v in conflicts.items()
                        if len(set(item['version'] for item in v)) > 1}

    if not conflict_packages:
        print(f"\n{Colors.GREEN}✅ No version conflicts found in ecosystem!{Colors.END}")
        return

    print(f"\n{Colors.RED}📊 Found {len(conflict_packages)} packages with version conflicts:{Colors.END}")

    # Sort by package name for consistent output
    for pkg_name in sorted(conflict_packages.keys()):
        usages = conflict_packages[pkg_name]
        versions = set(item['version'] for item in usages)
        latest_info = ecosystem.latest.get(pkg_name)
        latest_version = latest_info.latest_version if latest_info else "unknown"

        print(f"\n{Colors.YELLOW}{Colors.BOLD}📦 {pkg_name}{Colors.END} (latest: {Colors.GREEN}{latest_version}{Colors.END})")
        print(f"{Colors.GRAY}   {'Version':<15} Repositories{Colors.END}")
        print(f"{Colors.GRAY}   {'-'*50}{Colors.END}")

        # Group by version for structured display
        by_version = {}
        for usage in usages:
            ver = usage['version']
            if ver not in by_version:
                by_version[ver] = []
            by_version[ver].append(usage)

        # Sort versions (handle different version formats)
        try:
            sorted_versions = sorted(by_version.keys(), key=lambda x: [int(i) if i.isdigit() else i for i in x.split('.')])
        except:
            sorted_versions = sorted(by_version.keys())

        for version in sorted_versions:
            repos_using = by_version[version]
            repo_names = sorted([f"{item['repo']}" for item in repos_using])
            dep_types = sorted(set(item['type'] for item in repos_using))

            # Color code version based on currency
            version_color = Colors.GREEN if version == latest_version else Colors.YELLOW if 'LOCAL' not in version else Colors.BLUE

            version_str = f"{version_color}{version:<15}{Colors.END}"
            repo_str = f"{Colors.WHITE}{', '.join(repo_names)}{Colors.END}"
            type_str = f"{Colors.GRAY}({', '.join(dep_types)}){Colors.END}"

            print(f"   {version_str} {repo_str} {type_str}")

    # Summary statistics
    total_conflicts = sum(len(set(item['version'] for item in usages)) for usages in conflict_packages.values())
    print(f"\n{Colors.PURPLE}{Colors.BOLD}Conflict Summary:{Colors.END}")
    print(f"  Packages with conflicts: {Colors.BOLD}{len(conflict_packages)}{Colors.END}")
    print(f"  Total version variants: {Colors.BOLD}{total_conflicts}{Colors.END}")
    print(f"  Ecosystem health: {Colors.YELLOW}⚠️  Requires attention{Colors.END}")

def view_package_detail(ecosystem: EcosystemData, pkg_name: str) -> None:
    """Lightning-fast package analysis using hydrated data

    Replaces analyze_package() with instant lookup performance
    """
    print(f"{Colors.CYAN}{Colors.BOLD}📦 PACKAGE ANALYSIS: {pkg_name}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")

    if pkg_name not in ecosystem.latest:
        print(f"{Colors.RED}❌ Package '{pkg_name}' not found in ecosystem{Colors.END}")
        return

    latest_info = ecosystem.latest[pkg_name]

    # Get all usages using indexed data (instant lookup)
    usages = [dep for dep in ecosystem.deps.values() if dep.pkg_name == pkg_name]

    if not usages:
        print(f"{Colors.YELLOW}⚠️  Package found in latest versions but not used in any repos{Colors.END}")
        return

    print(f"\n{Colors.CYAN}Latest on crates.io: {Colors.BOLD}{latest_info.latest_version}{Colors.END}")

    # Table header matching legacy format
    print(f"\n{Colors.WHITE}{Colors.BOLD}Version      Type   Parent.Repo               Status{Colors.END}")
    print(f"{Colors.GRAY}------------------------------------------------------------{Colors.END}")

    # Group by repository and format like legacy
    by_repo = {}
    for dep in usages:
        repo_id = dep.repo_id
        if repo_id not in by_repo:
            by_repo[repo_id] = []
        by_repo[repo_id].append(dep)

    # Build table rows
    for repo_id, repo_deps in sorted(by_repo.items()):
        repo = ecosystem.repos[repo_id]

        for dep in repo_deps:
            # Format version (left-aligned, 12 chars)
            version_str = f"{dep.pkg_version:<12}"

            # Format dependency type (left-aligned, 6 chars)
            dep_type_str = f"{dep.dep_type:<6}"

            # Format repo name with proper prefix like legacy (left-aligned, 25 chars)
            repo_full_name = f"projects.{repo.repo_name}" if repo.repo_name != "hub" else f"projects.{repo.repo_name}"
            repo_name_str = f"{repo_full_name:<25}"

            # Status - simplified to ONLY for now (matches legacy output)
            status_str = "ONLY"

            print(f"{Colors.WHITE}{version_str} {dep_type_str} {repo_name_str} {status_str}{Colors.END}")

    # Summary section matching legacy format
    versions_in_use = set(dep.pkg_version for dep in usages)
    repos_using = len(set(dep.repo_id for dep in usages))

    print(f"\n{Colors.PURPLE}{Colors.BOLD}Summary for {pkg_name}:{Colors.END}")
    print(f"Versions in ecosystem: {Colors.BOLD}{len(versions_in_use)}{Colors.END}")
    print(f"Total usage count: {Colors.BOLD}{len(usages)}{Colors.END}")
    print(f"Repositories using: {Colors.BOLD}{repos_using}{Colors.END}")

    # Check for version conflicts
    if len(versions_in_use) == 1:
        print(f"{Colors.GREEN}✅ No version conflicts{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️  Version conflicts detected{Colors.END}")

def view_hub_dashboard(ecosystem: EcosystemData) -> None:
    """Lightning-fast hub-centric analysis using hydrated data

    Replaces analyze_hub_status() with pre-computed hub metrics
    """
    print(f"{Colors.PURPLE}{Colors.BOLD}🎯 HUB PACKAGE STATUS{Colors.END}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.END}")

    # Get hub packages (packages with hub status)
    hub_packages = {name: info for name, info in ecosystem.latest.items()
                   if info.hub_status != 'NONE'}

    if not hub_packages:
        print(f"{Colors.YELLOW}⚠️  No hub packages found in ecosystem{Colors.END}")
        return

    # Separate packages by status
    current_packages = []
    outdated_packages = []
    gap_packages = []

    for pkg_name, pkg_info in hub_packages.items():
        # Get usage count
        usage_count = len([dep for dep in ecosystem.deps.values() if dep.pkg_name == pkg_name])

        package_data = {
            'name': pkg_name,
            'hub_version': pkg_info.hub_version or "unknown",
            'latest_version': pkg_info.latest_version,
            'usage_count': usage_count,
            'status': pkg_info.hub_status
        }

        if pkg_info.hub_status == 'current':
            current_packages.append(package_data)
        elif pkg_info.hub_status == 'outdated':
            outdated_packages.append(package_data)
        else:
            gap_packages.append(package_data)

    # Current packages section
    if current_packages:
        print(f"\n{Colors.PURPLE}{Colors.BOLD}CURRENT PACKAGES:{Colors.END}")
        print(f"{Colors.WHITE}Package              Hub Version     Latest          Usage     {Colors.END}")
        print(f"{Colors.GRAY}------------------------------------------------------------{Colors.END}")

        for pkg in sorted(current_packages, key=lambda x: x['name']):
            pkg_name = f"{pkg['name']:<20}"
            hub_ver = f"{pkg['hub_version']:<15}"
            latest_ver = f"{Colors.CYAN}{pkg['latest_version']:<15}{Colors.END}"
            usage = f"{Colors.WHITE}({pkg['usage_count']} projects){Colors.END}"

            print(f"  {Colors.WHITE}{pkg_name} {hub_ver} {latest_ver} {usage}")

    # Outdated packages section
    if outdated_packages:
        print(f"\n{Colors.PURPLE}{Colors.BOLD}OUTDATED PACKAGES:{Colors.END}")
        print(f"{Colors.WHITE}Package              Hub Version     Latest          Usage     {Colors.END}")
        print(f"{Colors.GRAY}------------------------------------------------------------{Colors.END}")

        for pkg in sorted(outdated_packages, key=lambda x: -x['usage_count']):
            pkg_name = f"{pkg['name']:<20}"
            hub_ver = f"{Colors.YELLOW}{pkg['hub_version']:<15}{Colors.END}"
            latest_ver = f"{Colors.CYAN}{pkg['latest_version']:<15}{Colors.END}"

            # Color code usage based on project count
            usage_color = Colors.GREEN if pkg['usage_count'] >= 8 else Colors.WHITE if pkg['usage_count'] >= 5 else Colors.GRAY
            usage = f"{usage_color}({pkg['usage_count']} projects){Colors.END}"

            print(f"  {Colors.WHITE}{pkg_name} {hub_ver} {latest_ver} {usage}")

    # Find packages with high usage but not in hub (opportunities)
    all_packages = {}
    for dep in ecosystem.deps.values():
        pkg_name = dep.pkg_name
        if pkg_name not in all_packages:
            all_packages[pkg_name] = 0
        all_packages[pkg_name] += 1

    opportunities = []
    for pkg_name, usage_count in all_packages.items():
        if usage_count >= 5 and pkg_name not in hub_packages:
            opportunities.append((pkg_name, usage_count))

    if opportunities:
        print(f"\n{Colors.PURPLE}{Colors.BOLD}PACKAGE OPPORTUNITIES (5+ usage, not in hub):{Colors.END}")
        print(f"{Colors.GRAY}{'-'*80}{Colors.END}")

        # Show opportunities in legacy format
        opp_text = "  "
        for i, (pkg_name, count) in enumerate(sorted(opportunities, key=lambda x: -x[1])):
            opp_text += f"{Colors.GREEN}{pkg_name}({count}){Colors.END}"
            if i < len(opportunities) - 1 and i % 2 == 0:
                opp_text += "                  "
            elif i < len(opportunities) - 1:
                opp_text += "\n  "
        print(opp_text)

    # Visual summary bar matching legacy
    current_count = len(current_packages)
    outdated_count = len(outdated_packages)
    gap_count = len(gap_packages)
    unused_count = 0  # Not tracking unused packages in fast view
    unique_count = len(ecosystem.latest) - len(hub_packages)  # Packages not in hub

    print(f"\n{Colors.PURPLE}{Colors.BOLD}HUB PACKAGES:{Colors.END}")
    summary_line = (f"  Current     Outdated    Gap         Unused      Unique      \n"
                   f"  {Colors.BLUE}■{Colors.END} {Colors.BLUE}{current_count}{Colors.END}         "
                   f"{Colors.ORANGE}■{Colors.END} {Colors.ORANGE}{outdated_count}{Colors.END}        "
                   f"{Colors.GREEN}■{Colors.END} {Colors.GREEN}{gap_count}{Colors.END}         "
                   f"{Colors.RED}■{Colors.END} {Colors.RED}{unused_count}{Colors.END}         "
                   f"{Colors.GRAY}■{Colors.END} {Colors.GRAY}{unique_count}{Colors.END}")
    print(summary_line)

def discover_repositories(force_live=False):
    """Discover repository paths using cache or live discovery

    Args:
        force_live: If True, force live discovery even if cache exists

    Returns:
        List[Path]: List of repository paths
    """
    if not force_live:
        try:
            ecosystem = hydrate_tsv_cache()
            # repo.path includes Cargo.toml, so get parent directory
            repo_paths = [(Path(RUST_REPO_ROOT) / repo.path).parent for repo in ecosystem.repos.values()]
            print(f"{Colors.GREEN}📋 Found {len(repo_paths)} repositories from cache{Colors.END}")
            return repo_paths
        except FileNotFoundError:
            print(f"{Colors.YELLOW}⚠️  Cache not found, discovering repositories...{Colors.END}")

    # Live discovery
    print(f"{Colors.CYAN}🔍 Live discovery: scanning filesystem...{Colors.END}")
    cargo_files = find_all_cargo_files_fast()
    repo_paths = [path.parent for path in cargo_files]
    print(f"{Colors.GREEN}📋 Found {len(repo_paths)} repositories via live discovery{Colors.END}")
    return repo_paths

def list_repositories(force_live=False):
    """List all repository names"""
    print(f"{Colors.CYAN}{Colors.BOLD}📂 Repository List{Colors.END}")

    repo_paths = discover_repositories(force_live)

    if not repo_paths:
        print(f"{Colors.RED}❌ No repositories found{Colors.END}")
        return

    print(f"\n{Colors.WHITE}Found {len(repo_paths)} repositories:{Colors.END}")
    for i, repo_path in enumerate(sorted(repo_paths, key=lambda p: p.name), 1):
        print(f"{Colors.BLUE}{i:2d}.{Colors.END} {Colors.BOLD}{repo_path.name}{Colors.END}")

def superclean_targets():
    """Clean target directories across all ecosystem repositories"""
    print(f"{Colors.CYAN}{Colors.BOLD}🧹 SuperClean: Cleaning all target directories in ecosystem{Colors.END}")

    repo_paths = discover_repositories()

    cleaned_count = 0
    total_size_freed = 0

    # Initialize progress spinner
    progress = ProgressSpinner("Initializing cleanup...", len(repo_paths))
    progress.start()

    try:
        for i, repo_path in enumerate(repo_paths):
            progress.update(i, f"Processing {repo_path.name}...")

            target_path = repo_path / "target"
            cargo_toml_path = repo_path / "Cargo.toml"

            # Only process if there's a Cargo.toml file
            if not cargo_toml_path.exists():
                continue

            if target_path.exists() and target_path.is_dir():
                try:
                    progress.update(i, f"Cleaning {repo_path.name}...")

                    # Get size before cleaning
                    result = subprocess.run(['du', '-sh', str(target_path)],
                                          capture_output=True, text=True, timeout=10)
                    size_str = result.stdout.split('\t')[0] if result.returncode == 0 else "unknown"

                    # Use cargo clean in the repo directory
                    result = subprocess.run(['cargo', 'clean'],
                                          cwd=str(repo_path),
                                          capture_output=True, text=True, timeout=60)

                    if result.returncode == 0:
                        cleaned_count += 1
                        # Try to extract numeric size for total
                        if size_str.endswith('M'):
                            total_size_freed += float(size_str[:-1])
                        elif size_str.endswith('G'):
                            total_size_freed += float(size_str[:-1]) * 1024
                        elif size_str.endswith('K'):
                            total_size_freed += float(size_str[:-1]) / 1024

                except subprocess.TimeoutExpired:
                    pass  # Continue with other repos
                except subprocess.CalledProcessError:
                    pass  # Continue with other repos
                except Exception:
                    pass  # Continue with other repos

        # Final update
        progress.update(len(repo_paths), "Cleanup complete!")

    finally:
        progress.stop()

    # Summary
    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SuperClean Complete!{Colors.END}")
    print(f"   🗑️  Cleaned {cleaned_count} target directories")
    if total_size_freed > 0:
        if total_size_freed > 1024:
            print(f"   💾 Freed approximately {total_size_freed/1024:.1f}GB of disk space")
        else:
            print(f"   💾 Freed approximately {total_size_freed:.0f}MB of disk space")

def test_ssh_connection(ssh_profile=None):
    """Test SSH connection with configurable profile

    Args:
        ssh_profile: SSH profile/host. Defaults to RUST_SSH_PROFILE env var or 'github.com'
                    Use 'qodeninja' for your custom profile

    Returns:
        bool: True if SSH connection successful, False otherwise
    """
    # Configure SSH test command with environment variable fallback
    if ssh_profile is None:
        ssh_profile = os.environ.get('RUST_SSH_PROFILE', 'github.com')

    ssh_test_cmd = ['ssh', '-T', f'git@{ssh_profile}']
    expected_success_text = "successfully authenticated"

    # Test SSH connection
    print(f"{Colors.YELLOW}🔐 Testing SSH connection: {' '.join(ssh_test_cmd)}...{Colors.END}")
    try:
        result = subprocess.run(ssh_test_cmd,
                              capture_output=True, text=True, timeout=10)

        # Check for success in both stdout and stderr
        output_text = (result.stdout + result.stderr).lower()
        if expected_success_text in output_text or result.returncode == 0:
            print(f"{Colors.GREEN}✅ SSH connection verified{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}❌ SSH connection failed. Please check your SSH key setup.{Colors.END}")
            print(f"   Test command: {' '.join(ssh_test_cmd)}")
            print(f"   Output: {result.stderr or result.stdout}")
            return False
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}❌ SSH connection timeout{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ SSH test failed: {e}{Colors.END}")
        return False

def tap_repositories(ssh_profile=None):
    """Tap repositories - commit changes always, push only if SSH test passes

    Args:
        ssh_profile: SSH profile/host. Defaults to 'github.com'
                    Use 'qodeninja' for your custom profile
    """
    from datetime import datetime

    print(f"{Colors.CYAN}{Colors.BOLD}🚰 Tap: Auto-committing across ecosystem repositories{Colors.END}")

    # Test SSH connection to determine if we can push
    ssh_ok = test_ssh_connection(ssh_profile)
    if ssh_ok:
        print(f"{Colors.GREEN}🔗 SSH verified - will commit and push changes{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️  SSH failed - will only commit changes (no push){Colors.END}")

    # Get repository list
    repo_paths = discover_repositories()

    committed_count = 0
    pushed_count = 0
    skipped_count = 0
    error_count = 0
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Initialize progress spinner
    progress = ProgressSpinner("Initializing tap...", len(repo_paths))
    progress.start()

    try:
        for i, repo_path in enumerate(repo_paths):
            progress.update(i, f"Tapping {repo_path.name}...")

            # Skip if not a git repository
            if not (repo_path / ".git").exists():
                skipped_count += 1
                continue

            try:
                # Check git status
                result = subprocess.run(['git', 'status', '--porcelain'],
                                      cwd=str(repo_path),
                                      capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    error_count += 1
                    continue

                # If there are changes, add and commit them
                if result.stdout.strip():
                    progress.update(i, f"Committing changes in {repo_path.name}...")

                    # Add all changes
                    add_result = subprocess.run(['git', 'add', '.'],
                                              cwd=str(repo_path),
                                              capture_output=True, text=True, timeout=30)

                    if add_result.returncode != 0:
                        error_count += 1
                        continue

                    # Commit with standardized message
                    commit_message = f"fix: hub batch auto tap {current_date}"
                    commit_result = subprocess.run(['git', 'commit', '-m', commit_message],
                                                 cwd=str(repo_path),
                                                 capture_output=True, text=True, timeout=30)

                    if commit_result.returncode == 0:
                        committed_count += 1

                        # If SSH is OK, also push the changes
                        if ssh_ok:
                            progress.update(i, f"Pushing changes in {repo_path.name}...")
                            push_result = subprocess.run(['git', 'push'],
                                                       cwd=str(repo_path),
                                                       capture_output=True, text=True, timeout=60)

                            if push_result.returncode == 0:
                                pushed_count += 1
                            # Don't count push failure as error - commit succeeded
                    else:
                        error_count += 1
                else:
                    # No changes to commit
                    skipped_count += 1

            except subprocess.TimeoutExpired:
                error_count += 1
            except Exception:
                error_count += 1

        # Final update
        progress.update(len(repo_paths), "Tap complete!")

    finally:
        progress.stop()

    # Summary
    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Tap Complete!{Colors.END}")
    print(f"   📝 Committed changes in {committed_count} repositories")
    if ssh_ok and pushed_count > 0:
        print(f"   🚀 Pushed changes in {pushed_count} repositories")
    elif ssh_ok and committed_count > 0:
        print(f"   📤 SSH OK but no pushes needed")
    elif not ssh_ok and committed_count > 0:
        print(f"   🔒 Changes committed locally only (SSH failed)")
    print(f"   ⏭️  Skipped {skipped_count} repositories (no changes or not git repos)")
    if error_count > 0:
        print(f"   ❌ Errors in {error_count} repositories")

def main():
    def signal_handler(signum, frame):
        """Global signal handler for graceful exit"""
        # Restore cursor visibility before exit
        sys.stdout.write('\033[?25h')
        # Try to restore terminal settings
        try:
            if sys.stdin.isatty():
                # Reset terminal to normal mode
                os.system('stty sane')
        except:
            pass
        sys.stdout.flush()
        print(f"\n{Colors.YELLOW}⚠️  Operation interrupted by user{Colors.END}")
        sys.exit(0)

    # Setup global signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination
    signal.signal(signal.SIGTSTP, signal_handler)  # Ctrl+Z

    parser = argparse.ArgumentParser(description="Rust dependency analyzer with enhanced commands")
    parser.add_argument('command', nargs='?', default='analyze',
                       choices=['analyze', 'query', 'q', 'all', 'export', 'eco', 'review', 'pkg', 'latest', 'hub', 'data', 'superclean', 'tap', 'ssh-test', 'ls', 'fast'],
                       help='Command to run')
    parser.add_argument('package', nargs='?', help='Package name for pkg/latest commands')
    parser.add_argument('--ssh-profile', default=None, help='SSH profile/host for git operations (e.g., "qodeninja" for git@qodeninja)')
    parser.add_argument('--live', action='store_true', help='Force live discovery instead of using cache')
    parser.add_argument('--conflicts', action='store_true', help='Show version conflicts (fast command)')
    parser.add_argument('--pkg-detail', default=None, help='Show package details (fast command)')
    parser.add_argument('--hub-dashboard', action='store_true', help='Show hub dashboard (fast command)')

    args = parser.parse_args()

    try:
        if args.command == 'latest':
            if not args.package:
                print(f"{Colors.RED}❌ Package name required for 'latest' command{Colors.END}")
                print(f"Usage: python deps.py latest <package_name>")
                sys.exit(1)
            check_latest(args.package)
            return

        # For other commands, we need to analyze dependencies first
        dependencies = analyze_dependencies()

        if args.command == 'export':
            export_raw_data(dependencies)
        elif args.command == 'eco':
            detailed_review(dependencies)
        elif args.command == 'review':
            detailed_review(dependencies)
        elif args.command == 'pkg':
            if not args.package:
                print(f"{Colors.RED}❌ Package name required for 'pkg' command{Colors.END}")
                print(f"Usage: python deps.py pkg <package_name>")
                sys.exit(1)
            analyze_package(dependencies, args.package)
        elif args.command == 'all':
            # Show all version conflicts (old analyze behavior)
            format_version_analysis(dependencies)
        elif args.command == 'hub':
            # Show hub package status
            analyze_hub_status(dependencies)
        elif args.command == 'data':
            # Generate structured data cache
            generate_data_cache(dependencies)
        elif args.command == 'test':
            # Test hydration function
            try:
                ecosystem = hydrate_tsv_cache()
                print(f"{Colors.GREEN}✅ Hydration successful!{Colors.END}")
                print(f"   Loaded {len(ecosystem.aggregation)} aggregation metrics")
                print(f"   Loaded {len(ecosystem.repos)} repositories")
                print(f"   Loaded {len(ecosystem.deps)} dependencies")
                print(f"   Loaded {len(ecosystem.latest)} packages")
                print(f"   Loaded {len(ecosystem.version_maps)} version mappings")
                print(f"\n{format_aggregation_summary(ecosystem)}")
            except Exception as e:
                print(f"{Colors.RED}❌ Hydration failed: {e}{Colors.END}")
        elif args.command == 'superclean':
            # Clean all target directories in ecosystem
            superclean_targets()
        elif args.command == 'tap':
            # Auto-commit uncommitted changes across repositories
            tap_repositories(ssh_profile=args.ssh_profile)
        elif args.command == 'ssh-test':
            # Test SSH connection standalone
            test_ssh_connection(ssh_profile=args.ssh_profile)
        elif args.command == 'ls':
            # List repositories
            list_repositories(force_live=args.live)
        elif args.command == 'fast':
            # Fast hydrated view commands
            try:
                ecosystem = hydrate_tsv_cache()
                print(f"✅ Hydration successful: {len(ecosystem.deps)} deps, {len(ecosystem.repos)} repos")

                if args.conflicts:
                    view_conflicts(ecosystem)
                elif args.pkg_detail:
                    view_package_detail(ecosystem, args.pkg_detail)
                elif args.hub_dashboard:
                    view_hub_dashboard(ecosystem)
                else:
                    # Default fast view - show conflicts
                    view_conflicts(ecosystem)
            except Exception as e:
                print(f"❌ Error in fast command: {e}")
                import traceback
                traceback.print_exc()
                return
        else:  # default 'analyze', 'query', 'q'
            # Show package usage analysis
            analyze_package_usage(dependencies)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Operation interrupted by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()