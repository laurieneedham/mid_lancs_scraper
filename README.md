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

## Stats Explained

### Track Statistics

- **Trk Evts** (Track Events): Number of unique track events the club participated in
  - Example: If a club competed in 100m Heat 1, 100m Heat 2, and 200m, this counts as 2 unique events (100m and 200m)

- **Trk Parts** (Track Participations): Total number of times the club's athletes competed in track events
  - Example: If 3 athletes ran in the 100m, 2 in the 200m, and 4 in the 400m, this would be 9 participations
  - This shows the club's overall track activity level

- **Trk Aths** (Track Athletes): Number of unique athletes who competed in track events
  - Example: Even if an athlete competed in 5 different events, they're only counted once

### Field Statistics

- **Fld Evts** (Field Events): Number of unique field events the club participated in
  - Example: Long Jump, High Jump, Shot Put = 3 events

- **Fld Parts** (Field Participations): Total number of times the club's athletes competed in field events
  - Example: If 2 athletes did Long Jump, 3 did Shot Put, and 1 did Javelin, this would be 6 participations
  - This shows the club's overall field activity level

- **Fld Aths** (Field Athletes): Number of unique athletes who competed in field events
  - Example: Even if an athlete competed in 4 different field events, they're only counted once

### Example

```
Club Name                    Trk Evts  Trk Parts  Trk Aths  Fld Evts  Fld Parts  Fld Aths
Preston Harriers                   35        306        95        27         42        31
```

This means Preston Harriers:
- Competed in 35 different track events
- Had 306 total track participations (all athletes × all their track events)
- Had 95 unique athletes compete in track events
- Competed in 27 different field events
- Had 42 total field participations (all athletes × all their field events)
- Had 31 unique athletes compete in field events


