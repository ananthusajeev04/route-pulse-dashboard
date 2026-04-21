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

# ── CUSTOM CSS (From your HTML design) ───────────────────────────────────────
st.markdown("""
<style>
/* Base Dark Theme */
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stSidebar"] { background: #1a1d27; border-right: 1px solid rgba(255,255,255,0.08); }
[data-testid="stSidebar"] * { color: #c8cad8 !important; }
.block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 1400px; }

/* Custom Metric Cards matching your HTML */
.metrics-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
.custom-metric { background: #1a1d27; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 16px; }
.custom-metric-label { font-size: 11px; color: #555a72; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.custom-metric-value { font-size: 26px; font-weight: 700; letter-spacing: -0.02em; line-height: 1; margin-bottom: 4px; color: #e8eaf0; }
.custom-metric-sub { font-size: 11px; color: #8b90a8; }
.custom-metric.accent .custom-metric-value { color: #4f7cff; }
.custom-metric.green .custom-metric-value { color: #22c98a; }
.custom-metric.amber .custom-metric-value { color: #ffb547; }
.custom-metric.teal .custom-metric-value { color: #2fd4c8; }
.custom-metric.red .custom-metric-value { color: #ff5b5b; }

/* Titles and Layout */
h1 { color: #e8eaf0 !important; font-size: 22px !important; font-weight: 700 !important; letter-spacing: -0.02em; }
h3 { color: #8b90a8 !important; font-size: 12px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.06em; }
hr { border-color: rgba(255,255,255,0.08) !important; }

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
Kumali Route,Sonu (660198),2026-04-20 10:16:54,Cochin Coffe,3002,Completed,Inside,Yes,Yes,,V03,Van 03,Yes,B3,B3,R03,Kavalangadu Depot,01KV
Kumali Route,Sonu (660198),2026-04-20 17:53:51,St Martin Store,3003,Completed,Inside,Yes,Yes,,V03,Van 03,Yes,B3,B3,R03,Kavalangadu Depot,01KV
Omalloor Route,Pratheesh (660494),2026-04-20 09:44:21,JAGANNADH GENERAL STORE,4001,Completed,Inside,Yes,Yes,,V04,Van 04,Yes,B4,B4,R04,Valakom Depot,01VK
Omalloor Route,Pratheesh (660494),2026-04-20 09:53:40,MARGIN FREE MARKET,4002,Completed,,No,No,,V04,Van 04,No,B4,B4,R04,Valakom Depot,01VK
Omalloor Route,Pratheesh (660494),2026-04-20 18:09:21,Manna Bakery,4003,Completed,,No,No,,V04,Van 04,No,B4,B4,R04,Valakom Depot,01VK
Charumoodu Route,Renjth (660473),2026-04-20 10:18:09,Rajakumari,5001,Completed,Inside,Yes,Yes,,V05,Van 05,Yes,B5,B5,R05,Valakom Depot,01VK
Charumoodu Route,Renjth (660473),2026-04-20 10:40:40,HILAL STORE,5002,Completed,Inside,Yes,Yes,,V05,Van 05,Yes,B5,B5,R05,Valakom Depot,01VK
Charumoodu Route,Renjth (660473),2026-04-20 20:57:44,Karthik Store,5003,Completed,,No,No,Low stock,V05,Van 05,No,B5,B5,R05,Valakom Depot,01VK
"""

# ── DATA LOADING ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_gsheet(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return parse_df(pd.read_csv(StringIO(r.text)))

def parse_df(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    df["Visit Time"] = pd.to_datetime(df["Visit Time"], errors="coerce")
    df = df.dropna(subset=["Visit Time"])
    df["Date"] = df["Visit Time"].dt.date
    df["TimeStr"] = df["Visit Time"].dt.strftime("%H:%M")
    df["Hour"] = df["Visit Time"].dt.hour + df["Visit Time"].dt.minute / 60
    return df.sort_values(["Route", "Visit Time"])

def load_seed() -> pd.DataFrame:
    return parse_df(pd.read_csv(StringIO(SEED_CSV)))

# ── ANALYTICS ENGINE ──────────────────────────────────────────────────────────
def build_route_summary(df: pd.DataFrame) -> pd.DataFrame:
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
            "1st Time": first_time,
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

# ── CHART HELPERS ─────────────────────────────────────────────────────────────
DARK_BG = "#0f1117"
TEXT_CLR = "#8b90a8"
GRID_CLR = "rgba(255,255,255,0.05)"

def dark_layout(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color=TEXT_CLR), x=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_CLR, size=11),
        margin=dict(l=10, r=10, t=10, b=10),
        hoverlabel=dict(bgcolor="#22263a", font_color="#e8eaf0", bordercolor="#4f7cff"),
    )
    fig.update_xaxes(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, tickfont=dict(size=10))
    fig.update_yaxes(gridcolor=GRID_CLR, zerolinecolor="rgba(0,0,0,0)", tickfont=dict(size=10))
    return fig

# Custom logic perfectly matching your HTML file
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
    return dark_layout(fig)

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
    return dark_layout(fig)

# ── TABLE STYLING ─────────────────────────────────────────────────────────────
def style_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def row_color(row):
        base = "background-color: rgba(255,91,91,0.06); color: #e8eaf0; border-left: 3px solid #ff5b5b;" if row["Late Start"] else "background-color: #1a1d27; color: #e8eaf0;"
        return [base] * len(row)

    display_cols = ["Route", "User", "Total Visits",
                    "1st Shop", "1st Time", "1st Sale",
                    "2nd Shop", "2nd Time", "2nd Sale",
                    "Last Shop", "Last Time", "Last Sale",
                    "Location Acc %", "Sale Done %", "Warehouse", "Late Start"]
    df_disp = df[display_cols].copy()

    styler = df_disp.style.apply(row_color, axis=1)
    return styler

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
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
                st.success(f"{len(raw_df):,} rows loaded")
            except Exception as e:
                st.error(f"Parse error: {e}")
    elif source == "Google Sheet URL":
        gurl = st.text_input("Paste published CSV URL",
                             placeholder="https://docs.google.com/spreadsheets/...")
        if gurl:
            if st.button("🔄 Fetch / Refresh", use_container_width=True):
                st.cache_data.clear()
            try:
                raw_df = fetch_gsheet(gurl)
                st.success(f"{len(raw_df):,} rows fetched")
            except Exception as e:
                st.error(f"Fetch failed: {e}")

    st.markdown("---")
    if raw_df is not None:
        st.markdown("### Filters")
        dates = sorted(raw_df["Date"].unique(), reverse=True)
        selected_date = st.selectbox("Date", dates)

        warehouses = ["All"] + sorted(raw_df["Warehouse Name"].dropna().unique().tolist())
        selected_wh = st.selectbox("Warehouse", warehouses)

        sort_by = st.selectbox("Sort table by", [
            "Route A–Z", "Location Acc ↓", "Sale Done % ↓",
            "Visits ↓", "Late starts first"
        ])

# ── MAIN CONTENT ─────────────────────────────────────────────────────────────
st.markdown("# 📍 Shop Visit Route Dashboard")

if raw_df is None:
    st.info("👈 Select a data source from the sidebar to get started.")
    st.stop()

# Build summary
summary = build_route_summary(raw_df)
day_data = summary[summary["Date"].astype(str) == str(selected_date)].copy()

if selected_wh != "All":
    day_data = day_data[day_data["Warehouse"] == selected_wh]

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
    st.warning("No data for the selected filters.")
    st.stop()

# ── CUSTOM HTML METRICS (Matching your design) ───────────────────────────────
total_visits = day_data["Total Visits"].sum()
avg_loc = day_data["Location Acc %"].mean()
avg_sale = day_data["Sale Done %"].mean()

# Calculate "Bests"
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
st.caption("🟥 Red tinted rows indicate a first visit after 10:00 AM")

# We use st.column_config to recreate your HTML progress bars natively!
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
        "Late Start": st.column_config.CheckboxColumn("Late (>10AM)"),
    }
)
