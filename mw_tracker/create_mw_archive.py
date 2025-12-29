import pandas as pd
import numpy as np

# Files needed in your folder:
# 1. historical_weekly_adult_MW.csv (from 2002 onwards, weekly wages)
# 2. 'minimum_wages_2019_2026.csv' (weekly wages scraped from Rijksoverheid website)

HISTORICAL_FILE = 'data/historical_weekly_adult_MW.csv' 
SCRAPED_FILE = 'data/minimum_wages_2019_2026.csv'

# Official Historical Percentages (Staffels)
STAFFEL_PRE_2017 = {'22': 0.85, '21': 0.725, '20': 0.615, '19': 0.525, '18': 0.455, '17': 0.395, '16': 0.345, '15': 0.30}
STAFFEL_POST_2017 = {'21': 0.85, '20': 0.70, '19': 0.55, '18': 0.475, '17': 0.395, '16': 0.345, '15': 0.30}

def clean_currency(val):
    if pd.isna(val) or val == '': return np.nan
    val = str(val).replace('€', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(val)
    except: return np.nan

def create_archive():
    # --- PART 1: PROCESS HISTORY (2002-2018) ---
    df_old = pd.read_csv(HISTORICAL_FILE)
    archive_rows = []
    
    for _, row in df_old.iterrows():
        period_str = str(row.iloc[0])
        if '-' not in period_str: continue
        year = int(period_str.split('-')[0])
        month = int(period_str.split('-')[1])
        
        if year >= 2019: continue
        
        period = "January" if month == 1 else "July"
        nominal = row['Nominal']
        
        # Determine legal adult age (23 vs 22)
        is_pre_july_2017 = (year < 2017) or (year == 2017 and month == 1)
        adult_age, staffel = ("23+", STAFFEL_PRE_2017) if is_pre_july_2017 else ("22+", STAFFEL_POST_2017)
        
        # Add Adult
        archive_rows.append({'Year': year, 'Period': period, 'Age': adult_age, 'IsAdult': True,
                            'Hourly_36h': round(nominal/36, 2), 'Hourly_38h': round(nominal/38, 2), 
                            'Hourly_40h': round(nominal/40, 2), 'Hourly_Statutory': np.nan})
        # Add Youth
        for age, pct in staffel.items():
            archive_rows.append({'Year': year, 'Period': period, 'Age': age, 'IsAdult': False,
                                'Hourly_36h': round((nominal*pct)/36, 2), 'Hourly_38h': round((nominal*pct)/38, 2), 
                                'Hourly_40h': round((nominal*pct)/40, 2), 'Hourly_Statutory': np.nan})

    # --- PART 2: PROCESS SCRAPED (2019-2025) ---
    df_s = pd.read_csv(SCRAPED_FILE)
    # Clean currency
    cols_to_clean = ['21 jaar en ouder', '20 jaar', '19 jaar', '18 jaar', '17 jaar', '16 jaar', '15 jaar', '22 jaar en ouder', '21 jaar', 'Minimumloon per uur']
    for col in cols_to_clean:
        if col in df_s.columns: df_s[col] = df_s[col].apply(clean_currency)

    for year in sorted(df_s['Year'].unique()):
        if year > 2025: continue # Keep archive up to 2025
        y_df = df_s[df_s['Year'] == year]
        
        if year < 2024:
            indices = y_df[y_df['Fulltime werkweek in bedrijf'].notna()].index.tolist()
            blocks = [indices[i:i + 3] for i in range(0, len(indices), 3)]
            for idx, block in enumerate(blocks):
                sect = y_df.loc[block]
                period = 'July' if idx == 0 else 'January'
                for col in sect.columns:
                    if 'jaar' in col or '21+' in col:
                        age = col.replace(' jaar en ouder', '+').replace(' jaar', '')
                        is_adult = (year == 2019 and period == 'January' and age == '22+') or \
                                   (year == 2019 and period == 'July' and age == '21+') or \
                                   (year > 2019 and age == '21+')
                        
                        archive_rows.append({
                            'Year': year, 'Period': period, 'Age': age, 'IsAdult': is_adult,
                            'Hourly_36h': sect[sect['Fulltime werkweek in bedrijf'].str.contains('36', na=False)][col].values[0],
                            'Hourly_38h': sect[sect['Fulltime werkweek in bedrijf'].str.contains('38', na=False)][col].values[0],
                            'Hourly_40h': sect[sect['Fulltime werkweek in bedrijf'].str.contains('40', na=False)][col].values[0],
                            'Hourly_Statutory': np.nan
                        })
        else:
            # 2024+ logic
            for section in y_df['Section'].unique():
                period = 'January' if 'januari' in section.lower() else 'July'
                s_df = y_df[y_df['Section'] == section]
                for _, row in s_df.iterrows():
                    age = str(row['Leeftijd']).replace(' jaar en ouder', '+').replace(' jaar', '')
                    archive_rows.append({
                        'Year': year, 'Period': period, 'Age': age, 'IsAdult': (age == '21+'),
                        'Hourly_36h': np.nan, 'Hourly_38h': np.nan, 'Hourly_40h': np.nan,
                        'Hourly_Statutory': row['Minimumloon per uur']
                    })

    pd.DataFrame(archive_rows).to_csv('data/minimum_wage_archive.csv', index=False)
    print("Master Archive 'minimum_wage_archive.csv' created successfully!")

if __name__ == "__main__":
    create_archive()