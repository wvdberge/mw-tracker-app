import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import datetime
import os
import logging

# --- CONFIGURATION ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}
BASE_URL = "https://www.rijksoverheid.nl"
OVERVIEW_URL = "https://www.rijksoverheid.nl/onderwerpen/minimumloon/bedragen-minimumloon"
OUTPUT_FILE = os.path.join('data', 'latest_scraped_raw.csv')
MIN_YEAR = 2026  # Set to 2025 if you want to test with current data

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def clean_money(val_str):
    """Converts '€ 13,27' or '13,27' to float 13.27."""
    if not val_str:
        return None
    # Remove € symbol and thousands separators, replace decimal comma with dot
    clean = re.sub(r'[^\d,]', '', val_str).replace(',', '.')
    try:
        return float(clean)
    except ValueError:
        return None

def determine_period(text_sources):
    """
    Scans a list of text strings (url, title, header) to find 'januari' or 'juli'.
    Returns 'January', 'July', or None.
    """
    for text in text_sources:
        t = text.lower()
        if 'januari' in t or 'jan' in t:
            return 'January'
        if 'juli' in t or 'jul' in t:
            return 'July'
    return None

def scrape_latest():
    current_year = datetime.datetime.now().year
    logging.info(f"Scanning for minimum wage updates for year {MIN_YEAR}+ ...")
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    try:
        res = session.get(OVERVIEW_URL)
        res.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch overview: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    all_data = []
    
    # Iterate through all links in the main content area
    # (narrowing scope to 'content' div usually avoids footer links, but 'a' is fine)
    seen_urls = set()
    
    for a in soup.find_all('a', href=True):
        link_text = a.get_text(strip=True)
        href = a['href']
        
        # Regex to find years like 2025, 2026, 2027
        year_match = re.search(r'20\d{2}', link_text)
        
        if year_match:
            year = int(year_match.group())
            
            if year >= MIN_YEAR:
                full_url = href if href.startswith('http') else BASE_URL + href
                
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                logging.info(f"Found potential data for {year}: {full_url}")
                
                try:
                    page = session.get(full_url)
                    psoup = BeautifulSoup(page.text, 'html.parser')
                    
                    # 1. Try to detect Period from Link Text or Page Title first
                    period_guess = determine_period([link_text, psoup.title.string or ""])
                    
                    tables = psoup.find_all('table')
                    if not tables:
                        logging.warning(f"No tables found on page for {year}")
                        continue

                    for table in tables:
                        # 2. Fallback: Detect Period from preceding headers if not found yet
                        # or if the page contains multiple periods (rare now, but possible)
                        if not period_guess:
                            header_node = table.find_previous(['h2', 'h3', 'h4'])
                            header_text = header_node.get_text() if header_node else ""
                            current_period = determine_period([header_text]) or "Unknown"
                        else:
                            current_period = period_guess

                        # Parse Rows
                        # Skipping header usually works, but specific class checks are safer. 
                        # We assume standard Rijksoverheid table structure here.
                        rows = table.find_all('tr')[1:] 
                        
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                age_text = cells[0].get_text(strip=True)
                                wage_raw = cells[-1].get_text(strip=True)
                                
                                # Skip rows that clearly aren't age/wage (e.g. footnotes)
                                if not any(char.isdigit() for char in age_text):
                                    continue
                                
                                # Normalize Age
                                age_clean = age_text.replace(' jaar en ouder', '+').replace(' jaar', '').strip()
                                is_adult = "21" in age_clean and "+" in age_clean 
                                
                                # Normalize Wage
                                wage_float = clean_money(wage_raw)
                                
                                if wage_float:
                                    all_data.append({
                                        'Year': year,
                                        'Period': current_period,
                                        'Age': age_clean,
                                        'IsAdult': is_adult,
                                        'Hourly_Statutory': wage_float
                                    })
                                    
                except Exception as e:
                    logging.error(f"Error scraping {full_url}: {e}")

    # --- SAVE ---
    if all_data:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        new_df = pd.DataFrame(all_data)
        # Sort for cleanliness
        new_df = new_df.sort_values(by=['Year', 'Period', 'Age'], ascending=[False, True, False])
        
        new_df.to_csv(OUTPUT_FILE, index=False)
        logging.info(f"✅ Success! Saved {len(new_df)} rows to {OUTPUT_FILE}")
        print(new_df.head()) # Preview
    else:
        logging.info("No new data found for the specified years.")

if __name__ == "__main__":
    scrape_latest()