import pandas as pd
import cbsodata
import numpy as np

# --- CONFIGURATION ---
START_YEAR = 2002
CPI_TABLE = '83131NED'
CAO_TABLE = '85663NED'

def get_cbs_data(table_id, filters=None):
    """Generic fetcher for CBS data."""
    try:
        data = cbsodata.get_data(table_id, filters=filters)
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching {table_id}: {e}")
        return pd.DataFrame()

def parse_periods(df, value_col):
    """
    Splits the raw CBS dataframe into two separate DataFrames:
    1. monthly_df: Contains only January and July values
    2. yearly_df: Contains only Yearly values
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Standardize column names
    df = df[['Perioden', value_col]].copy()
    df.columns = ['Perioden', 'Value']
    
    # Ensure value is numeric
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

    # Standardize string format for parsing
    df['RawCode'] = df['Perioden'].astype(str).str.strip().str.lower()
    
    # Extract Year (first 4 digits)
    df['Year'] = df['RawCode'].str.extract(r'(\d{4})').astype(int)

    # --- 1. Extract Yearly Data (Matches "2020", "2020jj00") ---
    mask_yearly = df['RawCode'].str.contains('jj00') | (df['RawCode'].str.len() == 4)
    yearly_df = df[mask_yearly][['Year', 'Value']].copy()
    
    # Deduplicate yearly (keep last if multiple)
    yearly_df = yearly_df.groupby('Year').last().reset_index()

    # --- 2. Extract Monthly Data (Jan & July Only) ---
    conditions = [
        df['RawCode'].str.contains('mm01|januari'), # January
        df['RawCode'].str.contains('mm07|juli')     # July
    ]
    choices = ['January', 'July']
    
    df['Period'] = np.select(conditions, choices, default=None)
    
    # Filter only for Jan/July rows
    monthly_df = df[df['Period'].notna()][['Year', 'Period', 'Value']].copy()

    return monthly_df, yearly_df

def process_indices():
    # ==============================================================================
    # 1. FETCH CPI
    # ==============================================================================
    print(f"--- Fetching CPI ({CPI_TABLE}) ---")
    cpi_raw = get_cbs_data(CPI_TABLE, filters=f"Perioden ge '{START_YEAR}MM01'")
    
    if 'Bestedingscategorieen' in cpi_raw.columns:
        mask = cpi_raw['Bestedingscategorieen'].astype(str).str.contains('Alle bestedingen|T001112|000000', case=False)
        cpi_raw = cpi_raw[mask].copy()

    cpi_monthly, cpi_yearly = parse_periods(cpi_raw, 'CPI_1')

    # ==============================================================================
    # 2. FETCH CAO
    # ==============================================================================
    print(f"--- Fetching CAO ({CAO_TABLE}) ---")
    cao_raw = get_cbs_data(CAO_TABLE, filters="CaoSectoren eq 'T001020' and BedrijfstakkenBranchesSBI2008 eq 'T001081'")
    
    target_cols = [c for c in cao_raw.columns if 'Excl' in c and 'Uur' in c]
    cao_col = target_cols[0] if target_cols else None
    
    if cao_col:
        print(f"   > Found CAO column: {cao_col}")
        cao_monthly, cao_yearly = parse_periods(cao_raw, cao_col)
    else:
        print("   > Error: Could not find correct CAO column")
        return

    # ==============================================================================
    # 3. BUILD SKELETON (Jan & July for every year)
    # ==============================================================================
    years = range(START_YEAR, pd.Timestamp.now().year + 2)
    skeleton = []
    for y in years:
        skeleton.append({'Year': y, 'Period': 'January'})
        skeleton.append({'Year': y, 'Period': 'July'})
    
    df_final = pd.DataFrame(skeleton)

    # ==============================================================================
    # 4. MERGE DATA (4 Columns)
    # ==============================================================================
    
    # --- Helper to attach data ---
    def attach_data(base, monthly, yearly, prefix):
        # Attach Yearly (matches on Year)
        # Note: This naturally repeats the yearly value for both Jan and July rows
        tmp = pd.merge(base, yearly, on='Year', how='left')
        tmp = tmp.rename(columns={'Value': f'yearly_{prefix}'})
        
        # Attach Monthly (matches on Year + Period)
        tmp = pd.merge(tmp, monthly, on=['Year', 'Period'], how='left')
        tmp = tmp.rename(columns={'Value': f'monthly_{prefix}'})
        
        return tmp

    # Attach CPI
    df_final = attach_data(df_final, cpi_monthly, cpi_yearly, 'cpi')
    
    # Attach CAO
    df_final = attach_data(df_final, cao_monthly, cao_yearly, 'cao')

    # ==============================================================================
    # 5. CLEANUP & SAVE
    # ==============================================================================
    
    # Filter 2003+ (Start Year)
    df_final = df_final[df_final['Year'] >= START_YEAR]

    # Optional: Fill gaps? 
    # Current behavior: Leaves NaNs so you can see exactly what is missing.
    
    # Reorder columns for clarity
    cols = ['Year', 'Period', 'monthly_cao', 'monthly_cpi', 'yearly_cao', 'yearly_cpi']
    df_final = df_final[cols]

    print("\n[DEBUG] Sample check for 2010 (Should show Yearly data even if Monthly is missing):")
    print(df_final[df_final['Year'] == 2010])

    df_final.to_csv('data/deflation_indices_4cols.csv', index=False)
    print(f"\nSuccess! Saved 'deflation_indices_4cols.csv' with {len(df_final)} rows.")
    print(df_final.head())

if __name__ == "__main__":
    process_indices()