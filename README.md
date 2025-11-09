# systemd_last_run.py

A simple CLI tool to query systemd units and display when they last ran, sorted by timestamp.

This script queries systemd (both system and user level units) and displays the last activation time for each unit. Units are sorted by their last run time, with oldest runs first and most recent runs last. This is useful for auditing which services have been active and when.

Created with assistance from [aider.chat](https://github.com/Aider-AI/aider/).

## Usage

The script uses PEP 723 inline dependencies, so you can run it directly with `uv`:

```bash
uv run systemd_last_run.py
```

This will query both system and user units by default.

## Options

- `--system`: Query only system units
- `--user`: Query only user units
- `--verbose` / `-v`: Enable verbose logging output

## Examples

Query all units (system and user):
```bash
uv run systemd_last_run.py
```

Query only system units:
```bash
uv run systemd_last_run.py --system
```

Query only user units with verbose output:
```bash
uv run systemd_last_run.py --user --verbose
```

## Output

The script displays a table with three columns:
- **Unit**: The systemd unit name (e.g., `ssh.service`, `bluetooth.target`)
- **Scope**: Either `system` or `user` indicating which systemd instance manages this unit
- **Last Run**: The timestamp when the unit last entered the active state, or "Never/Unknown" if it hasn't run

Units are sorted with the oldest activation times first, making it easy to identify long-running or infrequently activated units.

## Dependencies

- click
- loguru

These are automatically installed when using `uv run` thanks to the PEP 723 inline script metadata.
