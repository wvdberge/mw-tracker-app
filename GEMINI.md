# Dutch Minimum Wage Tracker

## Project Overview

This project is a Python-based web application for tracking and visualizing the statutory minimum wage in the Netherlands. It provides a historical view from 2002 onwards and includes projections up to 2026.

The application is built with **Streamlit** for the user interface, **Pandas** for data manipulation, and **Plotly** for creating interactive charts. It includes functionality to compare adult and youth wages, adjust for inflation (real wage) using data from Statistics Netherlands (CBS), and view the impact of policy changes.

The data is sourced from:
- A manually compiled historical CSV.
- A web scraper (`scraper.py`) that fetches the most recent data from the Dutch government's official website (`rijksoverheid.nl`).
- An API client (`fetch_indices.py`) that retrieves inflation and wage indices from the CBS Open Data API.
- A pre-processing script (`create_mw_archive.py`) that consolidates these sources into a master data file.

## Building and Running

### 1. Installation

First, install the required Python packages using the `requirements.txt` file. It's recommended to do this within a virtual environment.

```bash
# Create and activate a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r mw_tracker/requirements.txt
```

### 2. Data Preparation

The application relies on several data files. The scripts to generate them are included in the `mw_tracker` directory.

```bash
# Fetch latest inflation/wage indices from CBS
python3 mw_tracker/fetch_indices.py

# Scrape the latest minimum wage figures from the government website
python3 mw_tracker/scraper.py

# Consolidate historical and scraped data into the master archive
python3 mw_tracker/create_mw_archive.py
```

### 3. Running the Application

Once the dependencies are installed and the data is prepared, you can run the Streamlit application.

```bash
streamlit run mw_tracker/nl_mw_tracker.py
```

This will start a local web server and open the application in your browser.

## Development Conventions

- **Data Flow:** Raw data is collected by `scraper.py` and `fetch_indices.py`. This data is then processed by `create_mw_archive.py` to produce `data/minimum_wage_archive.csv`, which is the final, clean dataset consumed by the Streamlit app (`nl_mw_tracker.py`).
- **Configuration:** Key constants, file paths, and UI text are defined at the top of each script. The main application (`nl_mw_tracker.py`) includes translations for both English and Dutch.
- **Dependencies:** All Python dependencies are explicitly listed in `mw_tracker/requirements.txt`.
- **Modularity:** The project is divided into distinct scripts for different tasks: data fetching, data processing, and presentation.
