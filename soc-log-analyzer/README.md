# SOC Log Analyzer

A Python script that automates SSH authentication log analysis — simulating real SOC Tier 1 triage tasks.

## What it does

- Parses SSH auth logs and counts failed login attempts by user and IP
- Detects brute force attempts (IPs exceeding a configurable threshold)
- Cross-references active IPs against a known blacklist
- Flags privileged user logins during off-hours (00:00–06:00)
- Generates a structured plain-text report

## Files

| File | Description |
|------|-------------|
| `generate_test_data.py` | Generates simulated SSH log and reference files for testing |
| `analyzer.py` | Main analysis script — reads logs, runs detections, outputs report |
| `sample_data/` | Test data: auth log, blacklist, privileged users list |

## Usage

Generate test data first:
```bash
python generate_test_data.py
```

Then run the analyzer:
```bash
python analyzer.py
```

Report is saved to `output/report.txt`.

## Skills demonstrated

Python · regex · file I/O · collections.Counter · log parsing · threat detection logic