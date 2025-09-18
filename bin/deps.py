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
import toml
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
            with open(cargo_path, 'r') as f:
                cargo_data = toml.load(f)

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

def extract_repo_metadata_batch(cargo_files: List[Path]) -> List[RepoData]:
    """Extract repository metadata from all Cargo.toml files"""
    repos = []
    repo_id = 100

    for cargo_path in cargo_files:
        try:
            with open(cargo_path, 'r') as f:
                cargo_data = toml.load(f)

            # Get basic repo info
            package_info = cargo_data.get('package', {})
            repo_name = package_info.get('name', cargo_path.parent.name)
            cargo_version = package_info.get('version', '0.0.0')

            # Get parent and relative path
            rel_path = get_relative_path(cargo_path)
            parent_repo = get_parent_repo(cargo_path)

            # Get git timestamp (simplified for now)
            last_update = int(cargo_path.stat().st_mtime)

            # Check for hub usage (placeholder for now)
            hub_usage = "NONE"
            hub_status = "none"

            repos.append(RepoData(
                repo_id=repo_id,
                repo_name=repo_name,
                path=rel_path,
                parent=parent_repo.split('.')[0],  # Just parent part
                last_update=last_update,
                cargo_version=cargo_version,
                hub_usage=hub_usage,
                hub_status=hub_status
            ))
            repo_id += 1

        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Warning: Could not parse {cargo_path}: {e}{Colors.END}")

    return repos

def extract_dependencies_batch(cargo_files: List[Path]) -> List[DepData]:
    """Extract all dependencies from all Cargo.toml files"""
    deps = []
    dep_id = 1000

    # Create repo_id lookup
    repo_lookup = {}
    repo_id = 100
    for cargo_path in cargo_files:
        repo_lookup[str(cargo_path)] = repo_id
        repo_id += 1

    for cargo_path in cargo_files:
        try:
            with open(cargo_path, 'r') as f:
                cargo_data = toml.load(f)

            current_repo_id = repo_lookup[str(cargo_path)]

            # Process regular dependencies
            if 'dependencies' in cargo_data:
                for dep_name, dep_info in cargo_data['dependencies'].items():
                    dep_version, features = parse_dependency_info(dep_info)
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
                    dep_version, features = parse_dependency_info(dep_info)
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

def parse_dependency_info(dep_info) -> Tuple[Optional[str], str]:
    """Parse dependency info and return (version, features)"""
    if isinstance(dep_info, str):
        return dep_info, "NONE"
    elif isinstance(dep_info, dict):
        if 'version' in dep_info:
            features = ','.join(dep_info.get('features', [])) or "NONE"
            return dep_info['version'], features
        elif 'path' in dep_info:
            features = ','.join(dep_info.get('features', [])) or "NONE"
            return f"path:{dep_info['path']}", features
        elif 'workspace' in dep_info and dep_info['workspace']:
            features = ','.join(dep_info.get('features', [])) or "NONE"
            return "workspace:true", features
        elif 'git' in dep_info:
            features = ','.join(dep_info.get('features', [])) or "NONE"
            git_ref = dep_info.get('rev', dep_info.get('branch', dep_info.get('tag', 'HEAD')))
            return f"git:{dep_info['git']}#{git_ref}", features
    return None, "NONE"

def collect_unique_packages(deps: List[DepData]) -> Set[str]:
    """Collect unique package names that need latest version lookup"""
    packages = set()
    for dep in deps:
        # Only collect crates.io packages (not path/git/workspace)
        if not dep.pkg_version.startswith(('path:', 'git:', 'workspace:')):
            packages.add(dep.pkg_name)
    return packages

def batch_fetch_latest_versions(package_names: Set[str]) -> Dict[str, LatestData]:
    """Batch fetch latest versions for all packages"""
    latest_data = {}
    pkg_id = 200

    total = len(package_names)
    progress = ProgressSpinner(f"Fetching latest versions...", total)
    progress.start()

    try:
        processed = 0
        for pkg_name in sorted(package_names):
            processed += 1
            progress.update(processed, f"Fetching {pkg_name}...")

            latest_version = get_latest_version(pkg_name)
            if latest_version:
                # Placeholder hub info (will enhance later)
                hub_version = "NONE"
                hub_status = "gap"

                latest_data[pkg_name] = LatestData(
                    pkg_id=pkg_id,
                    pkg_name=pkg_name,
                    latest_version=latest_version,
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
        # Section 1: REPO LIST
        f.write("#------ SECTION : REPO LIST --------#\n")
        f.write("REPO_ID\tREPO_NAME\tPATH\tPARENT\tLAST_UPDATE\tCARGO_VERSION\n")
        for repo in repos:
            f.write(f"{repo.repo_id}\t{repo.repo_name}\t{repo.path}\t{repo.parent}\t{repo.last_update}\t{repo.cargo_version}\n")
        f.write("\n")

        # Section 2: DEPS VERSIONS LIST
        f.write("#------ SECTION : DEP VERSIONS LIST --------#\n")
        f.write("DEP_ID\tREPO_ID\tPKG_NAME\tPKG_VERSION\tDEP_TYPE\tFEATURES\n")
        for dep in deps:
            f.write(f"{dep.dep_id}\t{dep.repo_id}\t{dep.pkg_name}\t{dep.pkg_version}\t{dep.dep_type}\t{dep.features}\n")
        f.write("\n")

        # Section 3: LATEST LIST
        f.write("#------ SECTION : DEP LATEST LIST --------#\n")
        f.write("PKG_ID\tPKG_NAME\tLATEST_VERSION\n")
        for latest in latest_versions.values():
            f.write(f"{latest.pkg_id}\t{latest.pkg_name}\t{latest.latest_version}\n")
        f.write("\n")

        # Section 4: VERSION MAP LIST
        f.write("#------ SECTION : VERSION MAP LIST --------#\n")
        f.write("MAP_ID\tDEP_ID\tPKG_ID\tREPO_ID\tVERSION_STATE\tBREAKING_TYPE\tECOSYSTEM_STATUS\n")
        for vm in version_maps:
            f.write(f"{vm.map_id}\t{vm.dep_id}\t{vm.pkg_id}\t{vm.repo_id}\t{vm.version_state}\t{vm.breaking_type}\t{vm.ecosystem_status}\n")

def get_hub_dependencies():
    """Get dependencies from hub's Cargo.toml"""
    hub_deps = {}
    hub_cargo_path = Path(RUST_REPO_ROOT) / "oodx" / "projects" / "hub" / "Cargo.toml"

    if hub_cargo_path.exists():
        try:
            with open(hub_cargo_path, 'r') as f:
                cargo_data = toml.load(f)

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

    # Phase 1: Discovery
    print(f"{Colors.CYAN}Phase 1: Discovering Cargo.toml files...{Colors.END}")
    cargo_files = find_all_cargo_files_fast()
    print(f"Found {len(cargo_files)} Cargo.toml files")

    # Phase 2: Extract repo metadata
    print(f"{Colors.CYAN}Phase 2: Extracting repository metadata...{Colors.END}")
    repos = extract_repo_metadata_batch(cargo_files)
    print(f"Processed {len(repos)} repositories")

    # Phase 3: Extract dependencies
    print(f"{Colors.CYAN}Phase 3: Extracting dependencies...{Colors.END}")
    deps = extract_dependencies_batch(cargo_files)
    unique_packages = collect_unique_packages(deps)
    hub_using_repos = len([r for r in repos if r.hub_status in ['using', 'path', 'workspace']])
    print(f"Found {len(deps)} dependency entries, {len(unique_packages)} unique packages, {hub_using_repos} repos using hub")

    # Phase 4: Batch fetch latest versions
    print(f"{Colors.CYAN}Phase 4: Fetching latest versions...{Colors.END}")
    latest_versions = batch_fetch_latest_versions(unique_packages)
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
                       choices=['analyze', 'query', 'q', 'all', 'export', 'eco', 'review', 'pkg', 'latest', 'hub', 'data'],
                       help='Command to run')
    parser.add_argument('package', nargs='?', help='Package name for pkg/latest commands')

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