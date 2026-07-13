# PeakMetrics

PeakMetrics converts weekly COROS `.fit` activity files into polished Excel and PDF training reports.

## Features

- Weekly training summary dashboard
- Branded daily-mileage chart
- Detailed chronological activity cards
- Lap splits
- Editable activity-type dropdowns
- Persistent activity corrections
- Long-term SQLite training history
- Year-to-date mileage and pace
- Historical average pace
- Weekly mileage trend chart
- One-click Windows launcher

## Requirements

- Windows 10 or Windows 11
- Python 3.12 or newer
- Excel or another program capable of opening `.xlsx` files

## Installation

### 1. Download PeakMetrics

Download or clone the project, then open the PeakMetrics folder.

### 2. Open PowerShell in the project folder

In File Explorer:

1. Open the PeakMetrics folder.
2. Click the address bar.
3. Type `powershell`.
4. Press Enter.

### 3. Create a virtual environment

```powershell
python -m venv .venv
```

### 4. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate it again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Install the required packages

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

Open `config.json` and enter the athlete's information:

```json
{
  "athlete_name": "Athlete Name",
  "team": "Team Name",
  "timezone": "America/Denver"
}
```

The timezone must be a valid IANA timezone.

Examples:

```text
America/Denver
America/Phoenix
America/Los_Angeles
America/Chicago
America/New_York
```

## Generating a report

1. Put the current reporting week's `.fit` files in:

```text
Weekly Runs
```

2. Double-click:

```text
Run PeakMetrics.bat
```

PeakMetrics will:

1. Validate the configuration.
2. Find the FIT files.
3. Generate Excel and PDF reports.
4. Save them in the `Reports` folder.
5. Open the newest Excel report automatically.

## Important weekly workflow

Keep only one reporting week at a time inside the `Weekly Runs` folder.

The history database can store multiple weeks, but every FIT file currently inside `Weekly Runs` is treated as part of the report being generated.

After generating a report:

1. Confirm the report looks correct.
2. Remove the previous week's FIT files.
3. Add the next week's FIT files.
4. Run PeakMetrics again.

## Excel report tabs

### Summary

Displays:

- Weekly mileage
- Weekly time
- Average pace
- Number of runs
- Average heart rate
- Maximum heart rate
- Average power
- Elevation gain
- Daily-mileage chart

### Report

Displays:

- Chronological activities
- Activity classifications
- Distance, time, pace, heart rate, power, cadence, and elevation
- Lap splits
- Editable activity-type dropdowns

### History

Displays:

- Stored weeks
- Historical mileage
- Average weekly mileage
- Highest-mileage week
- Year-to-date mileage
- Year-to-date average pace
- Historical average pace
- Weekly mileage trend
- Weekly statistics table

## Activity corrections

Activity types can be changed using the dropdown in the Excel Report tab.

After making a correction:

1. Save the Excel workbook.
2. Close Excel.
3. Run PeakMetrics again.

The correction will be imported and reused in future reports.

## Project data

PeakMetrics stores local data in:

```text
Data\peakmetrics.db
```

This database contains the athlete's accumulated training history.

Saved activity corrections are stored in:

```text
activity_overrides.json
```

Do not delete these files unless the athlete wants to reset all stored history and corrections.

## Troubleshooting

### No FIT files were found

Place at least one `.fit` file in the `Weekly Runs` folder.

### Excel report does not open

Check the `Reports` folder. The report may have been created even if Windows could not open it automatically.

### Configuration error

Check that `config.json`:

- Uses double quotes
- Contains all three required settings
- Has a valid timezone
- Does not contain comments

### FIT decoding warnings

Some COROS FIT files may produce warnings about an invalid field size. These warnings are normally harmless when the report still generates successfully.

## Privacy

FIT files, generated reports, the training-history database, and activity corrections are personal data. They should not be uploaded to a public repository.