# Mid Lancs Track & Field League Scraper

A Python script that scrapes athletics meeting results from the Mid Lancs Track & Field League.

## Requirements

- Python 3.11+
- UV package manager

## Installation

### 1. Install UV

If you don't have UV installed, install it using one of these methods:


**On Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Set Up the Project

1. Clone the repository or navigate to the project directory

2. Install dependencies using UV:
```bash
uv sync
```

This will create a virtual environment and install all required dependencies (requests, beautifulsoup4, pandas).

## Quick Start

1. **Configure the scraper** by editing `config.toml`:

```toml
[scraper]
# The base URL to scan for Mid Lancs Track & Field League pages
url = "https://www.race-results.co.uk/results/2025/#9"

# The search text to look for in links (case-insensitive)
search_text = "Mid Lancs Track & Field League"
```

2. **Run the script**:

```bash
uv run main.py
```


## Configuration

The `config.toml` file supports the following options:

### [scraper] section
- `url`: The base URL to scan for meeting results (required)
- `search_text`: The text to search for in links (default: "Mid Lancs Track & Field League")

### [events] section
- `track_keywords`: List of keywords to identify track events (case-insensitive)
  
- `field_keywords`: List of keywords to identify field events (case-insensitive)

### [output] section
- `club_column_width`: Width of the club name column in characters (default: 40)
- `count_column_width`: Width of the count columns in characters (default: 15)
- `sort_by`: How to sort club statistics tables (default: "alphabetical")
  - `"alphabetical"`: Sort clubs by name (A-Z)
  - `"numerical"`: Sort clubs by participation (highest track athletes first)

**Example:**
```toml
[output]
club_column_width = 40
count_column_width = 15
sort_by = "alphabetical"  # or "numerical"
```


