import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# --- 1. CONFIG & CONSTANTS ---
st.set_page_config(page_title="NL Minimum Wage Tracker", layout="wide", page_icon="🇳🇱")

# Use internal keys for logic, map to UI labels later
DEFLATOR_KEYS = ["None", "M_CPI", "M_CAO", "Y_CPI", "Y_CAO"]

TRANSLATIONS = {
    "en": {
        "title": "🇳🇱 Dutch Minimum Wage Evolution (2002–2026+)",
        "desc": "Tracks statutory minimum wage. **Pre-2024:** Based on workweek. **2024+:** Universal hourly wage.",
        "sb_config": "Configuration",
        "sb_lang": "Language / Taal",
        "sb_adult": "Show Adult Wage",
        "sb_youth": "Compare with Youth Ages:",
        "sb_basis": "Pre-2024 Hourly Basis:",
        "sb_deflation": "Adjust for Inflation (Real Wage):",
        "sb_policy": "Policy Milestones",
        "sb_policy_label": "Show vertical markers for:",
        "calc_title": "📈 Wage Growth Calculator",
        "calc_start": "Start Date",
        "calc_end": "End Date",
        "calc_group": "Target Group",
        "calc_metric_start": "Wage in",
        "calc_metric_end": "Wage in",
        "calc_metric_growth": "Total Growth",
        "expander_data": "Show Data Archive",
        "warning_select": "Please select at least one age group or 'Adult'.",
        "error_file": "Data file not found.",
        "y_axis_nominal": "Wage per Hour (€ Nominal)",
        "y_axis_real": "Real Wage (€ - {})",
        "base_today": "Today's Purchasing Power",
        "base_index": "Index Base Year",
        "cat_adult": "Adult",
        "cat_age": "Age: ",
        "defl_labels": ["None (Nominal)", "Monthly CPI", "Monthly CAO", "Yearly CPI", "Yearly CAO"],
        "wage_type": "Wage Type",
        "wage_type_opts": ["Nominal", "Real (CPI)"]
    },
    "nl": {
        "title": "🇳🇱 Verloop Wettelijk Minimumloon (2002–2026+)",
        "desc": "Toont het wettelijk minimumloon. **Voor 2024:** Op basis van werkweek. **Vanaf 2024:** Uniform uurloon.",
        "sb_config": "Instellingen",
        "sb_lang": "Taal / Language",
        "sb_adult": "Toon Volwassen Loon",
        "sb_youth": "Vergelijk met Jeugdleeftijden:",
        "sb_basis": "Basis Uurwerkweek (voor 2024):",
        "sb_deflation": "Corrigeer voor Inflatie (Reëel Loon):",
        "sb_policy": "Beleidsmijlpalen",
        "sb_policy_label": "Toon verticale markeringen voor:",
        "calc_title": "📈 Loonstijging Calculator",
        "calc_start": "Startdatum",
        "calc_end": "Einddatum",
        "calc_group": "Doelgroep",
        "calc_metric_start": "Loon in",
        "calc_metric_end": "Loon in",
        "calc_metric_growth": "Totale Groei",
        "expander_data": "Toon Data Archief",
        "warning_select": "Selecteer ten minste één leeftijdsgroep of 'Volwassen'.",
        "error_file": "Databestand niet gevonden.",
        "y_axis_nominal": "Uurloon (€ Nominaal)",
        "y_axis_real": "Reëel Loon (€ - {})",
        "base_today": "Koopkracht van Vandaag",
        "base_index": "Index Basisjaar",
        "cat_adult": "Volwassen",
        "cat_age": "Leeftijd: ",
        "defl_labels": ["Geen (Nominaal)", "Maandelijkse CPI", "Maandelijkse CAO", "Jaarlijkse CPI", "Jaarlijkse CAO"],
        "wage_type": "Loontype",
        "wage_type_opts": ["Nominaal", "Reëel (CPI)"]
    }
}

POLICY_EVENTS = {
    "July 2017": {"date": "2017-07-01", "label": {"en": "Youth Hike I", "nl": "Jeugdverhoging I"}},
    "July 2019": {"date": "2019-07-01", "label": {"en": "Youth Hike II", "nl": "Jeugdverhoging II"}},
    "Jan 2023":  {"date": "2023-01-01", "label": {"en": "+8.05% Boost", "nl": "+8.05% Extra"}},
    "Jan 2024":  {"date": "2024-01-01", "label": {"en": "Hourly Intro", "nl": "Uurloon Intro"}}
}

# --- 2. DATA LOADING ---
@st.cache_data
def load_data():
    """Loads and merges wage and index data."""
    path_archive = 'data/minimum_wage_archive.csv'
    path_latest = 'data/latest_scraped_raw.csv'
    path_indices = 'data/deflation_indices_4cols.csv'

    if not os.path.exists(path_archive):
        return None
    
    df_wages = pd.read_csv(path_archive)
    
    # Optional: Load latest scraped data
    if os.path.exists(path_latest):
        df_latest = pd.read_csv(path_latest)
        # Optimized string cleaning using Regex
        if df_latest['Hourly_Statutory'].dtype == object:
            df_latest['Hourly_Statutory'] = (
                df_latest['Hourly_Statutory']
                .astype(str)
                .str.replace(r'[€.]', '', regex=True) # Remove € and thousand separators
                .str.replace(',', '.', regex=False)   # Fix decimals
                .astype(float)
            )
        df_wages = pd.concat([df_wages, df_latest], ignore_index=True)

    # Load Indices
    if os.path.exists(path_indices):
        df_indices = pd.read_csv(path_indices)
    else:
        df_indices = pd.DataFrame(columns=['Year', 'Period', 'monthly_cao', 'monthly_cpi', 'yearly_cao', 'yearly_cpi'])

    # Merge
    df = pd.merge(df_wages, df_indices, on=['Year', 'Period'], how='left')

    # Date handling
    month_map = {"January": "01", "July": "07"}
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + "-" + df['Period'].map(month_map) + "-01")
    
    # Fill missing index data
    idx_cols = ['monthly_cao', 'monthly_cpi', 'yearly_cao', 'yearly_cpi']
    df = df.sort_values('Date')
    df[idx_cols] = df[idx_cols].ffill()

    return df

df = load_data()

# --- 3. UI & SIDEBAR ---
# Initialize language settings first as they control all text
st.sidebar.title("Configuration")
lang_choice = st.sidebar.radio("Language / Taal", ["🇬🇧 English", "🇳🇱 Nederlands"], horizontal=True)
lang = "en" if "English" in lang_choice else "nl"
txt = TRANSLATIONS[lang]

if df is None:
    st.error(txt["error_file"])
    st.stop()

# --- Main Page Title ---
st.title(txt["title"])
st.markdown(txt["desc"])

# --- Define Controls ---
# Main wage type toggle
wage_type_choice = st.radio(
    txt["wage_type"],
    options=txt["wage_type_opts"],
    index=1,  # Default to "Real (CPI)"
    horizontal=True,
)
deflator_key = "Y_CPI" if wage_type_choice == txt["wage_type_opts"][1] else "None"


# Advanced controls in a main page expander
with st.expander("⚙️ Advanced Settings"):
    show_adult = st.toggle(txt["sb_adult"], value=True)

    all_ages = [a for a in df['Age'].unique() if a not in ['23+', '22+', '21+', 'Adult']]
    sorted_ages = sorted(all_ages, key=lambda x: int(x) if x.isdigit() else 0)
    selected_youth = st.multiselect(
        txt["sb_youth"], options=sorted_ages, default=[]
    )

    hour_basis = st.radio(txt["sb_basis"], options=[36, 38, 40], index=0, horizontal=True)
    st.markdown("---") # Visual separator
    selected_events = st.multiselect(
        txt["sb_policy_label"],
        options=list(POLICY_EVENTS.keys()),
        default=[],
        format_func=lambda x: f"{x}: {POLICY_EVENTS[x]['label'][lang]}"
    )

# --- 4. DATA PROCESSING ---
# 4.1 Calculate Nominal Wage
pre_2024_col = f"Hourly_{hour_basis}h"
df['NominalWage'] = np.where(df['Year'] < 2024, df[pre_2024_col], df['Hourly_Statutory'])

# 4.2 Calculate Display Wage (Deflation) 
base_year_txt = ""
if deflator_key == "None":
    df['DisplayWage'] = df['NominalWage']
    y_axis_title = txt["y_axis_nominal"]
else:
    # Logic Map: (Primary Column, Fallback Column)
    col_map = {
        "M_CPI": ('monthly_cpi', 'yearly_cpi'),
        "M_CAO": ('monthly_cao', 'yearly_cao'),
        "Y_CPI": ('yearly_cpi', 'yearly_cpi'),
        "Y_CAO": ('yearly_cao', 'yearly_cao')
    }
    
    p_col, f_col = col_map[deflator_key]
    df['Effective_Index'] = df[p_col].combine_first(df[f_col])
    
    # Calculate Real Wage (Base = Today)
    current_index = df['Effective_Index'].iloc[-1]
    if pd.notna(current_index) and current_index != 0:
        df['DisplayWage'] = df['NominalWage'] / (df['Effective_Index'] / current_index)
        base_year_txt = txt["base_today"]
    else:
        # Fallback if current index missing
        df['DisplayWage'] = df['NominalWage'] / (df['Effective_Index'] / 100)
        base_year_txt = txt["base_index"]
        
    y_axis_title = txt["y_axis_real"].format(base_year_txt)

# 4.3 Filter Data for Plotting (Vectorized)
mask_adult = (df['IsAdult'] == True) & (show_adult)
mask_youth = (df['Age'].isin(selected_youth)) & (df['IsAdult'] == False)

final_df = df[mask_adult | mask_youth].copy()

# Add readable Category column
final_df['Category'] = np.where(
    final_df['IsAdult'], 
    txt["cat_adult"], 
    txt["cat_age"] + final_df['Age'].astype(str)
)

# --- 5. VISUALIZATION ---
if final_df.empty:
    st.warning(txt["warning_select"])
else:
    # Main Plot
    fig = px.line(
        final_df, 
        x="Date", 
        y="DisplayWage", 
        color="Category", 
        markers=True,
        title=txt['title'],
        labels={"DisplayWage": y_axis_title, "Date": "Jaar" if lang == "nl" else "Year"}
    )
    
    # Policy Events 
    y_stagger = [0.96, 0.90, 0.84, 0.78]
    
    for i, event_key in enumerate(selected_events):
        event = POLICY_EVENTS[event_key]
        d_ts = pd.Timestamp(event["date"]).timestamp() * 1000
        
        # Draw line using native Plotly shape (Optimized)
        fig.add_vline(
            x=event["date"], 
            line_width=1, 
            line_dash="dash", 
            line_color="gray"
        )
        
        # Add Label
        fig.add_annotation(
            x=d_ts,
            y=y_stagger[i % len(y_stagger)],
            yref="paper",
            text=event["label"][lang],
            showarrow=False,
            xanchor="left",
            xshift=5,
            font=dict(size=10, color="#555"),
            bgcolor="rgba(255,255,255,0.7)"
        )

    # Layout Polish
    fig.update_layout(
        yaxis=dict(range=[12, 15], tickprefix="€ ", tickformat=".2f"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=80, l=50, r=50, b=50) # Adjusted top margin
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. CALCULATOR ---
    st.divider()
    st.subheader(txt["calc_title"])

    # Optimized Calculator Logic
    available_dates = final_df['Date'].dt.strftime('%Y-%m').unique() # sorted by default if df is sorted
    
    c1, c2, c3 = st.columns(3)
    s_date_str = c1.selectbox(txt["calc_start"], available_dates, index=0)
    e_date_str = c2.selectbox(txt["calc_end"], available_dates, index=len(available_dates)-1)
    target_cat = c3.selectbox(txt["calc_group"], final_df['Category'].unique())
    
    # Fast filtering
    subset = final_df[final_df['Category'] == target_cat]
    row_start = subset[subset['Date'].dt.strftime('%Y-%m') == s_date_str]
    row_end = subset[subset['Date'].dt.strftime('%Y-%m') == e_date_str]

    if not row_start.empty and not row_end.empty:
        val1 = row_start['DisplayWage'].values[0]
        val2 = row_end['DisplayWage'].values[0]
        diff = val2 - val1
        pct = (diff / val1) * 100 if val1 != 0 else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"{txt['calc_metric_start']} {s_date_str}", f"€{val1:.2f}")
        m2.metric(f"{txt['calc_metric_end']} {e_date_str}", f"€{val2:.2f}", f"€{diff:+.2f}")
        m3.metric(txt["calc_metric_growth"], f"{pct:+.1f}%")

    # --- 7. DATA TABLE ---
    with st.expander(txt["expander_data"]):
        st.dataframe(
            final_df[['Date', 'Category', 'NominalWage', 'DisplayWage']]
            .sort_values(['Date', 'Category'], ascending=[False, True]),
            use_container_width=True,
            hide_index=True
        )