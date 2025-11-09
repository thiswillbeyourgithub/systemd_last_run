# /// script
# dependencies = [
#   "click",
#   "loguru",
# ]
# ///
"""
Query systemd units and display their last run times.

This script uses systemctl to fetch all systemd units (system and/or user level)
and displays when each unit last ran, sorted by timestamp (oldest first).
Created with assistance from aider.chat.
"""

import subprocess
from datetime import datetime
from typing import Optional

import click
from loguru import logger


def get_units(scope: str) -> list[str]:
    """
    Get list of all systemd units for the specified scope.

    Parameters
    ----------
    scope : str
        Either '--system' or '--user' to specify which systemd instance to query.

    Returns
    -------
    list[str]
        List of unit names (e.g., 'ssh.service', 'bluetooth.target').
    """
    cmd = ["systemctl", scope, "list-units", "--all", "--no-pager", "--no-legend", "--plain"]
    logger.debug(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get units for {scope}: {e}")
        return []
    
    # Parse output - first column is the unit name
    units = []
    for line in result.stdout.strip().split("\n"):
        if line:
            # Split on whitespace and take first field which is the unit name
            unit_name = line.split()[0]
            units.append(unit_name)
    
    logger.info(f"Found {len(units)} units for {scope}")
    return units


def get_last_run_time(unit: str, scope: str) -> Optional[datetime]:
    """
    Get the last run timestamp for a systemd unit.

    Uses ActiveEnterTimestamp which indicates when the unit last entered the active state.
    This is the most relevant timestamp for determining when a service last ran.

    Parameters
    ----------
    unit : str
        The unit name to query.
    scope : str
        Either '--system' or '--user' to specify which systemd instance to query.

    Returns
    -------
    Optional[datetime]
        The datetime when the unit last ran, or None if unavailable.
    """
    cmd = ["systemctl", scope, "show", unit, "--property=ActiveEnterTimestamp"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        logger.debug(f"Failed to get timestamp for {unit}")
        return None
    
    # Output format: ActiveEnterTimestamp=Sat 2025-11-09 10:30:45 UTC
    output = result.stdout.strip()
    if "=" not in output:
        return None
    
    timestamp_str = output.split("=", 1)[1]
    
    # Empty timestamp or not set
    if not timestamp_str or timestamp_str == "n/a":
        return None
    
    try:
        # Parse the timestamp - systemd uses locale-specific format
        # We'll try to parse it, handling various formats
        dt = datetime.strptime(timestamp_str, "%a %Y-%m-%d %H:%M:%S %Z")
        return dt
    except ValueError:
        # If parsing fails, log but continue - some units might have unusual formats
        logger.debug(f"Could not parse timestamp '{timestamp_str}' for {unit}")
        return None


@click.command()
@click.option(
    "--system",
    "mode",
    flag_value="system",
    help="Query only system units",
)
@click.option(
    "--user",
    "mode",
    flag_value="user",
    help="Query only user units",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(mode: Optional[str], verbose: bool) -> None:
    """
    Display systemd units sorted by their last run time.

    By default, queries both system and user units. Use --system or --user
    to query only one scope. Units are displayed sorted by last run time,
    with oldest runs first and most recent runs last.
    """
    # Configure logging based on verbosity
    if not verbose:
        logger.remove()
        logger.add(lambda msg: None)  # Suppress all output unless verbose
    
    # Determine which scopes to query
    # By default, fetch both system and user units
    scopes = []
    if mode is None:
        scopes = ["--system", "--user"]
    elif mode == "system":
        scopes = ["--system"]
    elif mode == "user":
        scopes = ["--user"]
    
    # Collect all units with their timestamps
    # Store as (unit_name, scope, timestamp) tuples
    unit_data = []
    
    for scope in scopes:
        units = get_units(scope=scope)
        
        for unit in units:
            timestamp = get_last_run_time(unit=unit, scope=scope)
            # Include units even without timestamp (they'll sort to the beginning)
            unit_data.append((unit, scope, timestamp))
    
    # Sort by timestamp, with None values (no timestamp) first
    # This puts oldest runs first, most recent last as requested
    unit_data.sort(key=lambda x: (x[2] is not None, x[2] if x[2] else datetime.min))
    
    # Pretty print the results
    print(f"{'Unit':<50} {'Scope':<10} {'Last Run':<30}")
    print("=" * 90)
    
    for unit, scope, timestamp in unit_data:
        scope_display = scope.replace("--", "")
        timestamp_display = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "Never/Unknown"
        print(f"{unit:<50} {scope_display:<10} {timestamp_display:<30}")


if __name__ == "__main__":
    main()
