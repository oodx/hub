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
from pathlib import Path
from collections import defaultdict
from packaging import version
import subprocess
import urllib.request
import urllib.error

# ANSI color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

class Spinner:
    """Simple spinner for showing progress"""
    def __init__(self, message="Working"):
        self.message = message
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.idx = 0
        self.stop_spinner = False
        self.spinner_thread = None

    def spin(self):
        while not self.stop_spinner:
            char = self.spinner_chars[self.idx % len(self.spinner_chars)]
            sys.stdout.write(f'\r{Colors.CYAN}{char}{Colors.END} {self.message}')
            sys.stdout.flush()
            self.idx += 1
            time.sleep(0.1)

    def start(self):
        self.stop_spinner = False
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.start()

    def stop(self, final_message=None):
        self.stop_spinner = True
        if self.spinner_thread:
            self.spinner_thread.join()
        # Clear the spinner line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
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

def get_latest_version(package_name):
    """Get latest version from crates.io"""
    try:
        url = f"https://crates.io/api/v1/crates/{package_name}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data['crate']['max_version']
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError):
        return None

def get_parent_repo(cargo_path):
    """Get parent.repo format - parent folder + project name"""
    project_name = cargo_path.parent.name
    parent_name = cargo_path.parent.parent.name
    return f"{parent_name}.{project_name}"

def find_cargo_files(root_dir):
    """Find all Cargo.toml files, excluding target directories"""
    cargo_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip target directories
        dirs[:] = [d for d in dirs if d != 'target']

        if 'Cargo.toml' in files:
            cargo_path = Path(root) / 'Cargo.toml'
            cargo_files.append(cargo_path)

    return cargo_files

def analyze_dependencies():
    """Main analysis function"""
    rust_dir = Path('/home/xnull/repos/code/rust')
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
    # Cache for latest versions
    latest_cache = {}

    # Show progress for latest version fetching
    print(f"{Colors.GRAY}Fetching latest versions from crates.io...{Colors.END}")

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

        # Get latest version from crates.io
        if dep_name not in latest_cache:
            latest_version = get_latest_version(dep_name)
            latest_cache[dep_name] = latest_version
        else:
            latest_version = latest_cache[dep_name]

        # Check for conflicts (multiple versions)
        has_conflict = len(versions) > 1
        if has_conflict:
            conflicts_found += 1

        # Sort versions
        sorted_versions = sorted(versions)
        min_version = min(sorted_versions) if sorted_versions else None
        max_version = max(sorted_versions) if sorted_versions else None

        # Header with latest version
        conflict_indicator = f"{Colors.RED}⚠️" if has_conflict else f"{Colors.GREEN}✅"
        latest_str = f" (latest: {Colors.CYAN}{latest_version}{Colors.END})" if latest_version else ""
        print(f"{conflict_indicator} {Colors.BOLD}{dep_name}{Colors.END}{latest_str} {f'({len(versions)} versions)' if has_conflict else ''}")

        # Show versions in columns
        for ver in sorted_versions:
            # Color coding: red for lowest, green for highest, yellow for middle
            if len(sorted_versions) > 1:
                if ver == min_version:
                    ver_color = Colors.RED
                elif ver == max_version:
                    ver_color = Colors.GREEN
                else:
                    ver_color = Colors.YELLOW
            else:
                ver_color = Colors.WHITE

            projects_with_version = version_map[ver]
            projects_str = ', '.join([f"{proj}({typ})" if typ == 'dev' else proj
                                    for proj, typ in projects_with_version])

            print(f"  {ver_color}{str(ver):<12}{Colors.END} → {projects_str}")

        print()

    # Summary
    print(f"{Colors.PURPLE}{Colors.BOLD}📈 SUMMARY{Colors.END}")
    print(f"{Colors.PURPLE}{'='*40}{Colors.END}")
    print(f"Total dependencies analyzed: {Colors.BOLD}{len(sorted_deps)}{Colors.END}")
    print(f"Dependencies with version conflicts: {Colors.RED}{Colors.BOLD}{conflicts_found}{Colors.END}")
    print(f"Clean dependencies (single version): {Colors.GREEN}{Colors.BOLD}{len(sorted_deps) - conflicts_found}{Colors.END}")

    if conflicts_found > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 Hub integration will resolve {conflicts_found} version conflicts!{Colors.END}")
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

    # Start spinner
    spinner = Spinner(f"Exporting {total_deps} dependencies with latest versions...")
    spinner.start()

    # Cache for latest versions
    latest_cache = {}
    processed = 0

    try:
        with open(output_file, 'w') as f:
            f.write("Raw Dependency Data Export\n")
            f.write("=" * 50 + "\n\n")

            for dep_name, usages in sorted(filtered_deps.items()):
                processed += 1

                # Update spinner message with progress
                spinner.message = f"Exporting dependencies... ({processed}/{total_deps}) {dep_name}"

                # Get latest version from crates.io
                if dep_name not in latest_cache:
                    latest_version = get_latest_version(dep_name)
                    latest_cache[dep_name] = latest_version
                else:
                    latest_version = latest_cache[dep_name]

                latest_str = f", LATEST: {latest_version}" if latest_version else ""
                f.write(f"DEPENDENCY: {dep_name}{latest_str}\n")
                for parent_repo, ver_str, dep_type, cargo_path in usages:
                    f.write(f"  {parent_repo:<25} {ver_str:<12} {dep_type:<4} {cargo_path}\n")
                f.write("\n")

        # Stop spinner and show success
        spinner.stop(f"{Colors.GREEN}✅ Raw data exported to {Colors.BOLD}{output_file}{Colors.END} ({total_deps} dependencies)")

    except Exception as e:
        spinner.stop(f"{Colors.RED}❌ Export failed: {e}{Colors.END}")
        raise

def detailed_review(dependencies):
    """Show detailed review with latest versions"""
    print(f"{Colors.WHITE}{Colors.BOLD}📋 DETAILED DEPENDENCY REVIEW{Colors.END}")
    print(f"{Colors.GRAY}{'='*80}{Colors.END}\n")

    # Cache for latest versions to avoid repeated API calls
    latest_cache = {}

    # Filter and sort dependencies
    filtered_deps = {}
    for dep_name, usages in dependencies.items():
        version_usages = [(parent_repo, ver, typ, path) for parent_repo, ver, typ, path in usages
                         if ver not in ['path', 'workspace']]
        if version_usages:
            filtered_deps[dep_name] = version_usages

    sorted_deps = sorted(filtered_deps.items())

    # Header
    print(f"{Colors.WHITE}{Colors.BOLD}{'Package':<20} {'Ecosystem':<12} {'Latest':<12} {'Status':<10} {'Repos Using'}{Colors.END}")
    print(f"{Colors.GRAY}{'-' * 80}{Colors.END}")

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

        # Get latest version from crates.io
        if dep_name not in latest_cache:
            latest_version = get_latest_version(dep_name)
            latest_cache[dep_name] = latest_version
        else:
            latest_version = latest_cache[dep_name]

        # Status and colors
        has_conflict = len(versions) > 1
        latest_str = latest_version if latest_version else "unknown"

        if has_conflict:
            status_color = Colors.RED
            status = "CONFLICT"
        elif latest_version and parse_version(latest_version) and parse_version(latest_version) > max_version:
            status_color = Colors.YELLOW
            status = "OUTDATED"
        else:
            status_color = Colors.GREEN
            status = "CURRENT"

        # Latest version color (cyan for latest available)
        latest_color = Colors.CYAN if latest_version else Colors.GRAY

        # Ecosystem version color
        eco_color = Colors.GREEN if not has_conflict else Colors.RED

        # Count repos using this dependency
        repo_count = len(set(parent_repo for parent_repo, _, _, _ in usages))

        print(f"{Colors.WHITE}{dep_name:<20}{Colors.END} "
              f"{eco_color}{ecosystem_version:<12}{Colors.END} "
              f"{latest_color}{latest_str:<12}{Colors.END} "
              f"{status_color}{status:<10}{Colors.END} "
              f"{Colors.GRAY}{repo_count} repos{Colors.END}")

    print(f"\n{Colors.PURPLE}{Colors.BOLD}Legend:{Colors.END}")
    print(f"{Colors.GREEN}CURRENT{Colors.END}  - Using latest version, no conflicts")
    print(f"{Colors.YELLOW}OUTDATED{Colors.END} - Newer version available on crates.io")
    print(f"{Colors.RED}CONFLICT{Colors.END} - Multiple versions in ecosystem")
    print(f"{Colors.CYAN}Latest{Colors.END}   - Latest version from crates.io")

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

def main():
    parser = argparse.ArgumentParser(description="Rust dependency analyzer with enhanced commands")
    parser.add_argument('command', nargs='?', default='analyze',
                       choices=['analyze', 'export', 'review', 'pkg', 'latest'],
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
        elif args.command == 'review':
            detailed_review(dependencies)
        elif args.command == 'pkg':
            if not args.package:
                print(f"{Colors.RED}❌ Package name required for 'pkg' command{Colors.END}")
                print(f"Usage: python deps.py pkg <package_name>")
                sys.exit(1)
            analyze_package(dependencies, args.package)
        else:  # default 'analyze'
            format_version_analysis(dependencies)

    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()