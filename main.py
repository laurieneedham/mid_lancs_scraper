import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import re
import sys
import tomllib
from pathlib import Path
import pandas as pd


def get_page_content(url):
    """Fetch and return the HTML content of a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def find_matching_links(base_url, search_text="Mid Lancs Track & Field League"):
    """
    Scan a webpage for HTML links near rows containing the search text.
    Returns a list of matching URLs.
    """
    content = get_page_content(base_url)
    if not content:
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
    matching_links = []
    
    # Strategy: Find rows/elements containing the search text,
    # then look for nearby "HTML" links
    
    # First, find all links with text "HTML"
    html_links = soup.find_all('a', href=True, string=lambda s: s and 'html' in s.lower().strip())
    
    for link in html_links:
        # Check if the search text appears in the same row or nearby parent elements
        # Check parent elements (tr, div, li, p, etc.)
        parent = link.parent
        for _ in range(5):  # Check up to 5 levels up
            if parent is None:
                break
            parent_text = parent.get_text(strip=True)
            if search_text.lower() in parent_text.lower():
                # Found a match! Get the full URL
                href = link.get('href')
                full_url = urljoin(base_url, href)
                if full_url not in matching_links:
                    matching_links.append(full_url)
                break
            parent = parent.parent
    
    return matching_links


def extract_clubs_and_counts(url, config):
    """
    Extract club participation data from a results page.
    Returns a dictionary with DataFrames for detailed analysis.
    """
    content = get_page_content(url)
    if not content:
        return None
    
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    
    if len(tables) < 2:
        print("  Not enough tables found on page.")
        return None
    
    # Extract meeting information from the second table
    meeting_info = None
    if len(tables) >= 2:
        info_table = tables[1]
        info_rows = info_table.find_all('tr')
        if len(info_rows) >= 2:
            # First row has the meeting title
            title_cell = info_rows[0].find('td', class_='style18c')
            if title_cell:
                meeting_title = title_cell.get_text(strip=True)
            else:
                meeting_title = info_rows[0].get_text(strip=True)
            
            # Second row has location and date
            location_date = info_rows[1].get_text(strip=True)
            meeting_info = f"{meeting_title}\n{location_date}"
    
    # Get event keywords from config
    track_keywords = config.get('events', {}).get('track_keywords', [])
    field_keywords = config.get('events', {}).get('field_keywords', [])
    
    # Store detailed results for DataFrame
    results_data = []
    
    # Process each table to extract results
    for table in tables:
        # Find the header row (class='style18c') to get the event name
        header_row = table.find('tr', class_='style18c')
        if not header_row:
            continue
        
        header_cells = header_row.find_all('td')
        if not header_cells:
            continue
        
        event_name = header_cells[0].get_text(strip=True)
        
        # Extract just the event name (before any competitor data)
        # Split at first digit followed by uppercase (competitor number + name)
        event_name = re.split(r'\d+[A-Z]', event_name)[0].strip()
        
        # Skip tables with "overall" in the event name as this is duplicate data
        if 'overall' in event_name.lower():
            continue
        
        # Normalise event name to remove heat distinctions for counting unique events
        # Remove "heat X" to group all heats of the same event together
        normalised_event = re.sub(r'\s+heat\s+\d+', '', event_name, flags=re.IGNORECASE).strip()
        
        # Determine if this is a track or field event
        is_track_event = any(keyword.lower() in normalised_event.lower() for keyword in track_keywords)
        is_field_event = any(keyword.lower() in normalised_event.lower() for keyword in field_keywords)
        
        if not (is_track_event or is_field_event):
            continue
        
        event_type = 'track' if is_track_event else 'field'
        
        # Find result rows (all rows with class='style2')
        result_rows = table.find_all('tr', class_='style2')
        
        for row in result_rows:
            cells = row.find_all('td')
            
            # Skip rows that don't have enough cells (need at least 4: pos, bib, athlete, club)
            if len(cells) < 4:
                continue
            
            # TD[0] contains position, TD[1] contains bib, TD[2] contains athlete name, TD[3] contains club name
            position_text = cells[0].get_text(strip=True)
            bib_text = cells[1].get_text(strip=True)
            athlete_cell_text = cells[2].get_text(strip=True)
            club_cell_text = cells[3].get_text(strip=True)
            
            # Extract athlete name: split at first digit to remove times/results
            athlete_name = re.split(r'\d', athlete_cell_text, maxsplit=1)[0].strip()
            
            # Extract club name: split at first digit to remove times/results
            club_name = re.split(r'\d', club_cell_text, maxsplit=1)[0].strip()
            
            # Get performance data (any remaining cells after club)
            performance = ' '.join([cell.get_text(strip=True) for cell in cells[4:]]) if len(cells) > 4 else ''
            
            if athlete_name and club_name:
                results_data.append({
                    'event_name': event_name,
                    'event_normalised': normalised_event,
                    'event_type': event_type,
                    'position': position_text,
                    'bib': bib_text,
                    'athlete': athlete_name,
                    'club': club_name,
                    'performance': performance
                })
    
    # Create DataFrame from results
    df = pd.DataFrame(results_data)
    
    # Calculate summary statistics
    if len(df) > 0:
        # Count unique athletes and events per club
        summary_data = []
        for club in df['club'].unique():
            club_df = df[df['club'] == club]
            
            track_df = club_df[club_df['event_type'] == 'track']
            field_df = club_df[club_df['event_type'] == 'field']
            
            summary_data.append({
                'club': club,
                'track_events': track_df['event_normalised'].nunique(),
                'track_participations': len(track_df),  # Total number of times athletes competed in track
                'track_athletes': track_df['athlete'].nunique(),  # Unique track athletes
                'field_events': field_df['event_normalised'].nunique(),
                'field_participations': len(field_df),  # Total number of times athletes competed in field
                'field_athletes': field_df['athlete'].nunique(),  # Unique field athletes
                'total_results': len(club_df)
            })
    
        summary_df = pd.DataFrame(summary_data)
        
        # Sort based on configuration
        sort_by = config.get('output', {}).get('sort_by', 'alphabetical').lower()
        if sort_by == 'numerical':
            summary_df = summary_df.sort_values(['track_athletes', 'field_athletes'], ascending=False)
        else:  # Default to alphabetical
            summary_df = summary_df.sort_values('club', ascending=True)
    else:
        summary_df = pd.DataFrame()
    
    return {
        'meeting_info': meeting_info,
        'results_df': df,
        'summary_df': summary_df
    }


def load_config(config_path="config.toml"):
    """Load configuration from TOML file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"Error: Config file '{config_path}' not found.")
        print("Please create a config.toml file with your settings.")
        sys.exit(1)
    
    try:
        with open(config_file, 'rb') as f:
            config = tomllib.load(f)
        return config
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)


def print_club_statistics(meeting_url, summary_df, meeting_info, config):
    """Print formatted statistics for a meeting from DataFrame."""
    # Get column widths from config
    club_width = config.get('output', {}).get('club_column_width', 40)
    count_width = config.get('output', {}).get('count_column_width', 15)
    
    total_width = club_width + (count_width * 6) + 6
    
    print(f"\n{'='*total_width}")
    print(f"Meeting: {meeting_url}")
    print(f"{'='*total_width}")
    
    # Print meeting info from the second table if available
    if meeting_info:
        print(f"\n{meeting_info}")
    
    if summary_df.empty:
        print("No club data found for this meeting.")
        return
    
    print(f"\n{'Club Name':<{club_width}} {'Trk Evts':>{count_width}} {'Trk Parts':>{count_width}} {'Trk Aths':>{count_width}} {'Fld Evts':>{count_width}} {'Fld Parts':>{count_width}} {'Fld Aths':>{count_width}}")
    print(f"{'-'*club_width} {'-'*count_width} {'-'*count_width} {'-'*count_width} {'-'*count_width} {'-'*count_width} {'-'*count_width}")
    
    for _, row in summary_df.iterrows():
        print(f"{row['club']:<{club_width}} {row['track_events']:>{count_width}} {row['track_participations']:>{count_width}} {row['track_athletes']:>{count_width}} {row['field_events']:>{count_width}} {row['field_participations']:>{count_width}} {row['field_athletes']:>{count_width}}")
    
    # Print summary
    total_track_events = summary_df['track_events'].sum()
    total_track_participations = summary_df['track_participations'].sum()
    total_track_athletes = summary_df['track_athletes'].sum()
    total_field_events = summary_df['field_events'].sum()
    total_field_participations = summary_df['field_participations'].sum()
    total_field_athletes = summary_df['field_athletes'].sum()
    print(f"\n{'TOTAL':<{club_width}} {total_track_events:>{count_width}} {total_track_participations:>{count_width}} {total_track_athletes:>{count_width}} {total_field_events:>{count_width}} {total_field_participations:>{count_width}} {total_field_athletes:>{count_width}}")



def main():

    # Load configuration
    config = load_config()
    
    # Get URL and search text from config
    base_url = config.get('scraper', {}).get('url', '')
    search_text = config.get('scraper', {}).get('search_text', 'Mid Lancs Track & Field League')
    
    if not base_url:
        print("Error: No URL specified in config.toml")
        print("Please add a 'url' under the [scraper] section.")
        sys.exit(1)
    
    print(f"Scanning {base_url} for '{search_text}' pages...")
    
    # Find matching links
    matching_links = find_matching_links(base_url, search_text)
    
    if not matching_links:
        print("No matching links found.")
        return
    
    print(f"\nFound {len(matching_links)} matching page(s).")
    
    # Store all competition DataFrames for later analysis
    all_competitions = {}
    
    # Process each matching page
    for i, link in enumerate(matching_links, 1):
        print(f"\n[{i}/{len(matching_links)}] Processing: {link}")
        result = extract_clubs_and_counts(link, config)
        
        if result and not result['results_df'].empty:
            # Store the DataFrames
            competition_key = f"meeting_{i}"
            all_competitions[competition_key] = {
                'url': link,
                'meeting_info': result['meeting_info'],
                'results_df': result['results_df'],
                'summary_df': result['summary_df']
            }
            
            # Print statistics for this meeting
            print_club_statistics(link, result['summary_df'], result['meeting_info'], config)
        else:
            print(f"Could not extract data from {link}")
    
    # Print final summary
    club_width = config.get('output', {}).get('club_column_width', 40)
    count_width = config.get('output', {}).get('count_column_width', 15)
    total_width = club_width + (count_width * 2) + 2
    
    print(f"\n{'='*total_width}")
    print("Scraping complete!")
    print(f"{'='*total_width}")
    
    # Return the DataFrames for further analysis
    return all_competitions


if __name__ == "__main__":
    main()