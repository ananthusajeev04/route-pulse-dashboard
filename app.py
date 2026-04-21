import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import StringIO
import requests

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RoutePulse · Shop Visit Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS (Light Theme) ─────────────────────────────────────────────────
st.markdown("""
<style>
/* Base Light Theme */
[data-testid="stAppViewContainer"] { background: #FFFFFF; }
[data-testid="stSidebar"] { background: #F8F9FA; border-right: 1px solid rgba(0,0,0,0.08); }
[data-testid="stSidebar"] * { color: #31333F !important; }
.block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 1400px; }

/* Custom Metric Cards */
.metrics-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
.custom-metric { background: #FFFFFF; border: 1px solid rgba(0,0,0,0.1); border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.custom-metric-label { font-size: 11px; color: #555a72; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.custom-metric-value { font-size: 26px; font-weight: 700; letter-spacing: -0.02em; line-height: 1; margin-bottom: 4px; color: #111827; }
.custom-metric-sub { font-size: 11px; color: #555a72; }
.custom-metric.accent .custom-metric-value { color: #4f7cff; }
.custom-metric.green .custom-metric-value { color: #22c98a; }
.custom-metric.amber .custom-metric-value { color: #ffb547; }
.custom-metric.teal .custom-metric-value { color: #2fd4c8; }
.custom-metric.red .custom-metric-value { color: #ff5b5b; }

/* Titles and Layout */
h1 { color: #111827 !important; font-size: 22px !important; font-weight: 700 !important; letter-spacing: -0.02em; }
h3 { color: #555a72 !important; font-size: 12px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.06em; }
hr { border-color: rgba(0,0,0,0.1) !important; }

/* Late Alert Chip */
.late-alert-chip { display: inline-flex; align-items: center; gap: 5px; font-size: 13px; padding: 6px 12px; border-radius: 6px; background: rgba(255,91,91,0.12); color: #ff5b5b; border: 1px solid rgba(255,91,91,0.2); margin-bottom: 15px; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# ── SEED DATA (Apr 20 2026) ───────────────────────────────────────────────────
SEED_CSV = """Route,User,Visit Time,Shop Name,Shop ID,Route Status,Shop Location Status,Location Accuracy,Sale Done,Sale Not Done Reason,Van Code,Van Name,QR Scanned,Beat,Planned Beat,Route Code,Warehouse Name,Warehouse Code
Alakode Route,Gireesh (660235),2026-04-20 10:22:50,Greenco,1001,Completed,Inside,Yes,Yes,,V01,Van 01,Yes,B1,B1,R01,Kannur Depot,01KN
Alakode Route,Gireesh (660235),2026-04-20 11:16:58,Rasheed,1002,Completed,Inside,Yes,Yes,,V01,Van 01,Yes,B1,B1,R01,Kannur Depot,01KN
Alakode Route,Gireesh (660235),2026-04-20 20:15:03,CC Store,1003,Completed,,No,No,,V01,Van 01,No,B1,B1,R01,Kannur Depot,01KN
Irikoor Route,Abhilash (660554),2026-04-20 10:24:31,DAY 2 DAY Express,2001,Completed,Inside,Yes,No,,V02,Van 02,Yes,B2,B2,R02,Kannur Depot,01KN
Irikoor Route,Abhilash (660554),2026-04-20 10:27:09,CITY SUPER MARKET,2002,Completed,Inside,Yes,Yes,,V02,Van 02,Yes,B2,B2,R02,Kannur Depot,01KN
Irikoor Route,Abhilash (660554),2026-04-20 20:53:36,C P Super,2003,Completed,,No,No,,V02,Van 02,No,B2,B2,R02,Kannur Depot,01KN
Kumali Route,Sonu (660198),2026-04-20 09:16:12,Indian Store,3001,Completed,Inside,Yes,Yes,,V03,Van 03,Yes,B3,B3,R03,Kavalangadu Depot,01KV
"""

# ── BULLETPROOF DATA LOADING ──────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_gsheet_with_counts(url: str):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    
    if "<html" in r.text.lower()[:50]:
        raise ValueError("The link returned a web page instead of a CSV. Make sure you selected 'CSV' when publishing to the web.")
        
    lines = r.text.splitlines()
    total_raw_rows = max(0, len(lines) - 1)
    
    df_clean = parse_df(pd.read_csv(StringIO(r.text)))
    return df_clean, total_raw_rows

def parse_df(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    
    target_col = None
    for col in df.columns:
        if "visit time" in col.lower() or "time" in col.lower():
            target_col = col
            break
            
    if not target_col:
        cols_found = ", ".join(df.columns.tolist()[:5])
        raise ValueError(f"Could not find 'Visit Time' column. Columns found: {cols_found}...")

    df["Visit Time"] = pd.to_datetime(df[target_col], format='mixed', dayfirst=True, errors="coerce")
    df_clean = df.dropna(subset=["Visit Time"]).copy()
    
    if df_clean.empty:
        raise ValueError("Zero dates could be successfully read from your file.")

    df_clean["Date"] = df_clean["Visit Time"].dt.date
    df_clean["TimeStr"] = df_clean["Visit Time"].dt.strftime("%H:%M")
    df_clean["Hour"] = df_clean["Visit Time"].dt.hour + df_clean["Visit Time"].dt.minute / 60
    return df_clean.sort_values(["Route", "Visit Time"])

def load_seed() -> pd.DataFrame:
    return parse_df(pd.read_csv(StringIO(SEED_CSV)))

# ── ANALYTICS ENGINE ──────────────────────────────────────────────────────────
def build_route_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Date" not in df.columns:
        return pd.DataFrame()
        
    rows = []
    for (route, date), grp in df.groupby(["Route", "Date"]):
        grp = grp.reset_index(drop=True)
        n = len(grp)
        loc_acc = round((grp["Location Accuracy"] == "Yes").sum() / n * 100, 1) if n else 0
        sale_done = round((grp["Sale Done"] == "Yes").sum() / n * 100, 1) if n else 0
        
        first_time = grp.iloc[0]["TimeStr"]
        dt = grp.iloc[0]["Visit Time"]
        late = dt.hour > 10 or (dt.hour == 10 and dt.minute > 0)
        
        rows.append({
            "Date": date,
            "Route": route,
            "User": grp.iloc[0].get("User", "—"),
            "Warehouse": grp.iloc[0].get("Warehouse Name", "—"),
            "Total Visits": n,
            "1st Shop": grp.iloc[0]["Shop Name"],
            # Append red dot indicator directly to the text if late
            "1st Time": f"🔴 {first_time}" if late else first_time,
            "1st Sale": grp.iloc[0]["Sale Done"],
            "2nd Shop": grp.iloc[1]["Shop Name"] if n > 1 else "—",
            "2nd Time": grp.iloc[1]["TimeStr"] if n > 1 else "—",
            "2nd Sale": grp.iloc[1]["Sale Done"] if n > 1 else "—",
            "Last Shop": grp.iloc[-1]["Shop Name"],
            "Last Time": grp.iloc[-1]["TimeStr"],
            "Last Sale": grp.iloc[-1]["Sale Done"],
            "Location Acc %": loc_acc,
            "Sale Done %": sale_done,
            "Late Start": late,
        })
    return pd.DataFrame(rows)

# ── CHART HELPERS (Light Theme) ───────────────────────────────────────────────
TEXT_CLR = "#111827"
GRID_CLR = "#E5E7EB"

def light_layout(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color=TEXT_CLR), x=0),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color=TEXT_CLR, size=11),
        margin=dict(l=10, r=10, t=10, b=10),
        hoverlabel=dict(bgcolor="#F8F9FA", font_color="#111827", bordercolor="#4f7cff"),
    )
    fig.update_xaxes(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, tickfont=dict(size=10))
    fig.update_yaxes(gridcolor=GRID_CLR, zerolinecolor="rgba(0,0,0,0)", tickfont=dict(size=10))
    return fig

def color_for_loc(v):
    return "#4f7cff" if v >= 75 else "#ffb547" if v >= 50 else "#ff5b5b"

def color_for_sale(v):
    return "#22c98a" if v >= 50 else "#2fd4c8" if v >= 40 else "#4f7cff"

def bar_chart_loc(df_sorted):
    colors = [color_for_loc(v) for v in df_sorted["Location Acc %"]]
    fig = go.Figure(go.Bar(
        x=df_sorted["Location Acc %"],
        y=df_sorted["Route"].str.replace(" Route", "", regex=False),
        orientation="h",
        marker_color=colors,
        text=[f"{v}%" for v in df_sorted["Location Acc %"]],
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>Location Accuracy: %{x}%<extra></extra>",
    ))
    fig.update_xaxes(range=[0, 115], showgrid=True)
    fig.update_layout(height=max(280, len(df_sorted) * 26 + 40))
    return light_layout(fig)

def bar_chart_sale(df_sorted):
    colors = [color_for_sale(v) for v in df_sorted["Sale Done %"]]
    fig = go.Figure(go.Bar(
        x=df_sorted["Sale Done %"],
        y=df_sorted["Route"].str.replace(" Route", "", regex=False),
        orientation="h",
        marker_color=colors,
        text=[f"{v}%" for v in df_sorted["Sale Done %"]],
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>Sale Done: %{x}%<extra></extra>",
    ))
    fig.update_xaxes(range=[0, 115], showgrid=True)
    fig.update_layout(height=max(280, len(df_sorted) * 26 + 40))
    return light_layout(fig)

# ── TABLE STYLING (Light Theme) ───────────────────────────────────────────────
def style_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def row_color(row):
        # A faint red background for late starts that looks good on light themes
        if row["Late Start"]:
            return ["background-color: rgba(255, 91, 91, 0.10); color: #111827;"] * len(row)
        else:
            return ["color: #111827;"] * len(row)

    def time_color(val):
        # Highlights the 🔴 and the time in bold red
        if "🔴" in str(val):
            return "color: #ff5b5b; font-weight: 800;"
        return ""

    def sale_color(val):
        if val == "Yes":   return "color: #22c98a; font-weight: 600;"
        if val == "No":    return "color: #ff5b5b;"
        if val == "Cancelled": return "color: #ffb547;"
        return ""

    display_cols = ["Route", "User", "Total Visits",
                    "1st Shop", "1st Time", "1st Sale",
                    "2nd Shop", "2nd Time", "2nd Sale",
                    "Last Shop", "Last Time", "Last Sale",
                    "Location Acc %", "Sale Done %", "Warehouse", "Late Start"]
    
    df_disp = df[display_cols].copy()

    styler = df_disp.style.apply(row_color, axis=1)
    styler = styler.map(time_color, subset=["1st Time"])
    for col in ["1st Sale", "2nd Sale", "Last Sale"]:
        styler = styler.map(sale_color, subset=[col])
        
    return styler

# ── SIDEBAR & FILTERS ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 RoutePulse")
    st.markdown("---")

    st.markdown("### Data source")
    source = st.radio("", ["Use sample data", "Upload CSV", "Google Sheet URL"],
                      label_visibility="collapsed")

    raw_df = None

    if source == "Use sample data":
        raw_df = load_seed()
        st.success("Sample data loaded")
        
    elif source == "Upload CSV":
        uploaded = st.file_uploader("Upload your CSV", type=["csv"])
        if uploaded:
            try:
                raw_df = parse_df(pd.read_csv(uploaded))
                st.success(f"✅ {len(raw_df):,} rows loaded")
            except Exception as e:
                st.error(f"Parse error: {str(e)}")
                
    elif source == "Google Sheet URL":
        gurl = st.text_input("Paste published CSV URL",
                             placeholder="https://docs.google.com/spreadsheets/...")
        if gurl:
            if st.button("🔄 Fetch / Refresh", use_container_width=True):
                st.cache_data.clear()
            try:
                raw_df, total_raw_rows = fetch_gsheet_with_counts(gurl)
                if not raw_df.empty:
                    st.success(f"✅ {len(raw_df):,} valid rows processed.")
                    if len(raw_df) < total_raw_rows:
                        skipped = total_raw_rows - len(raw_df)
                        st.info(f"ℹ️ {skipped:,} rows were skipped because they were totally blank or the 'Visit Time' was unreadable.")
            except Exception as e:
                st.error(f"Fetch failed: {str(e)}")

    st.markdown("---")
    
    if raw_df is not None and not raw_df.empty:
        st.markdown("### 🎛️ Advanced Filters")
        
        dates = sorted(raw_df["Date"].unique(), reverse=True)
        selected_date = st.selectbox("📅 Select Date", dates)

        temp_summary = build_route_summary(raw_df)
        day_data_raw = temp_summary[temp_summary["Date"].astype(str) == str(selected_date)].copy()

        warehouses = sorted(day_data_raw["Warehouse"].dropna().unique().tolist())
        selected_wh = st.multiselect("🏢 Warehouses", options=warehouses, default=warehouses)

        users = sorted(day_data_raw["User"].dropna().unique().tolist())
        selected_users = st.multiselect("👤 Salespersons", options=users, default=users)

        st.markdown("---")
        sort_by = st.selectbox("↕️ Sort table by", [
            "Route A–Z", "Location Acc ↓", "Sale Done % ↓",
            "Visits ↓", "Late starts first"
        ])
    else:
        selected_date, selected_wh, selected_users, sort_by = None, [], [], "Route A–Z"

# ── MAIN CONTENT ─────────────────────────────────────────────────────────────
st.markdown("# 📍 Shop Visit Route Dashboard")

if raw_df is None or raw_df.empty:
    st.info("👈 Select a valid data source to get started.")
    st.stop()

summary = build_route_summary(raw_df)

if summary.empty:
    st.error("No valid summaries could be built. Check data formatting.")
    st.stop()

day_data = summary[summary["Date"].astype(str) == str(selected_date)].copy()

if selected_wh:
    day_data = day_data[day_data["Warehouse"].isin(selected_wh)]
else:
    day_data = pd.DataFrame(columns=day_data.columns)

if selected_users:
    day_data = day_data[day_data["User"].isin(selected_users)]
else:
    day_data = pd.DataFrame(columns=day_data.columns)

if sort_by == "Location Acc ↓":
    day_data = day_data.sort_values("Location Acc %", ascending=False)
elif sort_by == "Sale Done % ↓":
    day_data = day_data.sort_values("Sale Done %", ascending=False)
elif sort_by == "Visits ↓":
    day_data = day_data.sort_values("Total Visits", ascending=False)
elif sort_by == "Late starts first":
    day_data = day_data.sort_values(["Late Start", "Route"], ascending=[False, True])
else:
    day_data = day_data.sort_values("Route")

if day_data.empty:
    st.warning("No data matches your current filter selections. Try adding back a Warehouse or Salesperson in the sidebar.")
    st.stop()

# ── CUSTOM HTML METRICS ──────────────────────────────────────────────────────
total_visits = day_data["Total Visits"].sum()
avg_loc = day_data["Location Acc %"].mean()
avg_sale = day_data["Sale Done %"].mean()

best_loc_route = day_data.loc[day_data["Location Acc %"].idxmax()]
best_sale_route = day_data.loc[day_data["Sale Done %"].idxmax()]
late_count = day_data["Late Start"].sum()

loc_color_class = "green" if avg_loc >= 75 else "amber" if avg_loc >= 50 else "red"

metrics_html = f"""
<div class="metrics-container">
    <div class="custom-metric accent">
        <div class="custom-metric-label">Routes</div>
        <div class="custom-metric-value">{len(day_data)}</div>
        <div class="custom-metric-sub">{selected_date}</div>
    </div>
    <div class="custom-metric teal">
        <div class="custom-metric-label">Total visits</div>
        <div class="custom-metric-value">{int(total_visits):,}</div>
        <div class="custom-metric-sub">shop stops today</div>
    </div>
    <div class="custom-metric {loc_color_class}">
        <div class="custom-metric-label">Avg location accuracy</div>
        <div class="custom-metric-value">{avg_loc:.1f}%</div>
        <div class="custom-metric-sub">Best: {best_loc_route['Route'].split(' ')[0]} ({best_loc_route['Location Acc %']}%)</div>
    </div>
    <div class="custom-metric green">
        <div class="custom-metric-label">Avg sale done</div>
        <div class="custom-metric-value">{avg_sale:.1f}%</div>
        <div class="custom-metric-sub">Best: {best_sale_route['Route'].split(' ')[0]} ({best_sale_route['Sale Done %']}%)</div>
    </div>
    <div class="custom-metric red">
        <div class="custom-metric-label">Late starts (after 10 AM)</div>
        <div class="custom-metric-value">{late_count}</div>
        <div class="custom-metric-sub">of {len(day_data)} routes — negative trend</div>
    </div>
</div>
"""
st.markdown(metrics_html, unsafe_allow_html=True)

if late_count > 0:
    st.markdown(f'<div class="late-alert-chip">⚠ {late_count} route(s) started after 10:00 AM</div>', unsafe_allow_html=True)

# ── BAR CHARTS ───────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    st.markdown("### Location accuracy % per route")
    st.plotly_chart(
        bar_chart_loc(day_data.sort_values("Location Acc %", ascending=True)),
        use_container_width=True, config={"displayModeBar": False}
    )
with c2:
    st.markdown("### Sale done % per route")
    st.plotly_chart(
        bar_chart_sale(day_data.sort_values("Sale Done %", ascending=True)),
        use_container_width=True, config={"displayModeBar": False}
    )

# ── PROGRESS BAR TABLE ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗂 Route details — first, 2nd & last shop visits")
st.caption("🔴 A red circle next to the 1st Time indicates a late start (after 10:00 AM)")

st.dataframe(
    style_table(day_data),
    use_container_width=True,
    height=min(600, len(day_data) * 38 + 50),
    hide_index=True,
    column_config={
        "Location Acc %": st.column_config.ProgressColumn(
            "Location Acc %",
            help="Percentage of accurate locations",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "Sale Done %": st.column_config.ProgressColumn(
            "Sale Done %",
            help="Percentage of sales completed",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        # This completely hides the useless checkbox column from the interface!
        "Late Start": None, 
    }
)
