import streamlit as st
import pandas as pd
import plotly.express as px
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

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Base - Pure White Minimalist Theme */
[data-testid="stAppViewContainer"] { background: #FFFFFF; }
[data-testid="stSidebar"] { background: #F8F9FA; border-right: 1px solid rgba(0,0,0,0.08); }
[data-testid="stSidebar"] * { color: #31333F !important; }
.block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 1400px; }

/* Metric cards */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
[data-testid="stMetricLabel"] { font-size: 11px !important; color: #555a72 !important; text-transform: uppercase; letter-spacing: 0.06em; }
[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700 !important; color: #111827 !important; }

/* Title */
h1 { color: #111827 !important; font-size: 22px !important; font-weight: 700 !important; letter-spacing: -0.02em; }
h2 { color: #111827 !important; font-size: 16px !important; font-weight: 600 !important; }
h3 { color: #555a72 !important; font-size: 12px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.06em; }

/* Late row highlight */
.late-highlight { background: rgba(255,91,91,0.12) !important; }

/* Divider */
hr { border-color: rgba(0,0,0,0.1) !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid rgba(0,0,0,0.1); }
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
        cancelled = round((grp["Sale Done"] == "Cancelled").sum() / n * 100, 1) if n else 0
        first_time = grp.iloc[0]["TimeStr"]
        first_h = grp.iloc[0]["Hour"]
        late = first_h > 10.0
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
            "Cancelled %": cancelled,
            "Late Start": late,
        })
    return pd.DataFrame(rows)

# ── CHART HELPERS ─────────────────────────────────────────────────────────────
TEXT_CLR = "#111827"
GRID_CLR = "#E5E7EB"

def light_layout(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color=TEXT_CLR), x=0),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color=TEXT_CLR, size=11),
        margin=dict(l=10, r=10, t=30 if title else 10, b=10),
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

def late_start_chart(df_day):
    df_sorted = df_day.sort_values("1st Time")
    colors = ["#ff5b5b" if late else "#22c98a" for late in df_sorted["Late Start"]]
    short = df_sorted["Route"].str.replace(" Route", "", regex=False)
    fig = go.Figure(go.Bar(
        x=short,
        y=df_sorted["1st Time"].apply(lambda t: int(t.split(":")[0]) + int(t.split(":")[1]) / 60 if t != "—" else 0),
        marker_color=colors,
        text=df_sorted["1st Time"],
        textposition="outside",
        textfont=dict(size=9),
        hovertemplate="<b>%{x}</b><br>First visit: %{text}<extra></extra>",
    ))
    fig.add_hline(y=10, line_dash="dash", line_color="#ffb547", line_width=1.5,
                  annotation_text="10:00 AM threshold", annotation_font_color="#ffb547",
                  annotation_font_size=10)
    fig.update_yaxes(tickvals=[8, 9, 10, 11, 12, 13, 14],
                     ticktext=["8 AM", "9 AM", "10 AM", "11 AM", "12 PM", "1 PM", "2 PM"])
    fig.update_layout(height=300, showlegend=False)
    return light_layout(fig, "First visit time per route (red = after 10 AM)")

# ── TABLE STYLING ─────────────────────────────────────────────────────────────
def style_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def row_color(row):
        base = "background-color: rgba(255,91,91,0.10); color: #111827;" if row["Late Start"] else "background-color: #FFFFFF; color: #111827;"
        return [base] * len(row)

    def sale_color(val):
        if val == "Yes":   return "color: #22c98a; font-weight: 600;"
        if val == "No":    return "color: #ff5b5b;"
        if val == "Cancelled": return "color: #ffb547;"
        return ""

    def time_color(val):
        if val == "—": return "color: #555a72;"
        try:
            h = int(val.split(":")[0])
            return "color: #ff5b5b; font-weight: 600;" if h >= 10 and val != "—" else "color: #22c98a; font-weight: 600;"
        except: return ""

    display_cols = ["Route", "User", "Total Visits",
                    "1st Shop", "1st Time", "1st Sale",
                    "2nd Shop", "2nd Time", "2nd Sale",
                    "Last Shop", "Last Shop Time", "Last Sale",
                    "Location Acc %", "Sale Done %", "Warehouse", "Late Start"]
    
    # Rename "Last Time" to "Last Shop Time" internally for display to match your request
    df_disp = df.rename(columns={"Last Time": "Last Shop Time"}).copy()
    
    styler = df_disp[display_cols].style.apply(row_color, axis=1)
    for col in ["1st Sale", "2nd Sale", "Last Sale"]:
        styler = styler.map(sale_color, subset=[col])
    styler = styler.map(time_color, subset=["1st Time"])
    styler = styler.format({"Location Acc %": "{:.1f}%", "Sale Done %": "{:.1f}%"})
    styler = styler.set_table_styles([
        {"selector": "th", "props": [("background", "#F8F9FA"), ("color", "#555a72"),
                                      ("font-size", "11px"), ("text-transform", "uppercase"),
                                      ("letter-spacing", "0.05em"), ("padding", "8px 12px")]},
        {"selector": "td", "props": [("padding", "7px 12px"), ("font-size", "12px"),
                                      ("border-bottom", "1px solid #E5E7EB")]},
    ])
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
        else:
            st.info("Upload your daily CSV export")
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
                st.caption("Make sure sheet is published: File → Share → Publish to web → CSV")

    st.markdown("---")
    if raw_df is not None:
        st.markdown("### Filters")
        dates = sorted(raw_df["Date"].unique(), reverse=True)
        selected_date = st.selectbox("Date", dates,
                                     format_func=lambda d: d.strftime("%d %b %Y") if hasattr(d, "strftime") else str(d))

        warehouses = ["All"] + sorted(raw_df["Warehouse Name"].dropna().unique().tolist())
        selected_wh = st.selectbox("Warehouse", warehouses)

        sort_by = st.selectbox("Sort table by", [
            "Route A–Z", "Location Acc ↓", "Sale Done % ↓",
            "Visits ↓", "Late starts first"
        ])

    st.markdown("---")
    st.markdown("### Legend")
    st.markdown("🟥 **Red row** = first visit after 10 AM")
    st.markdown("🟩 **Green row** = first visit by 10 AM")
    st.markdown("🔵 **Blue bar** = loc acc ≥ 75%")
    st.markdown("🟡 **Amber bar** = loc acc 50–74%")
    st.markdown("🔴 **Red bar** = loc acc < 50%")

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

# ── METRIC CARDS ─────────────────────────────────────────────────────────────
late_count = day_data["Late Start"].sum()
avg_loc = day_data["Location Acc %"].mean()
avg_sale = day_data["Sale Done %"].mean()
total_visits = day_data["Total Visits"].sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Routes", len(day_data))
col2.metric("Total Visits", f"{int(total_visits):,}")
col3.metric("Avg Location Acc.", f"{avg_loc:.1f}%")
col4.metric("Avg Sale Done", f"{avg_sale:.1f}%")
col5.metric("⚠ Late Starts (>10 AM)", int(late_count))

st.markdown("---")

# ── LATE START TIMELINE ───────────────────────────────────────────────────────
st.markdown("### ⏰ First visit time — late start analysis")
st.plotly_chart(late_start_chart(day_data), use_container_width=True, config={"displayModeBar": False})

# ── BAR CHARTS ───────────────────────────────────────────────────────────────
st.markdown("### 📊 Performance by route")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Location accuracy %**")
    st.plotly_chart(
        bar_chart_loc(day_data.sort_values("Location Acc %", ascending=True)),
        use_container_width=True, config={"displayModeBar": False}
    )
with c2:
    st.markdown("**Sale done %**")
    st.plotly_chart(
        bar_chart_sale(day_data.sort_values("Sale Done %", ascending=True)),
        use_container_width=True, config={"displayModeBar": False}
    )

# ── DETAIL TABLE ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗂 Route details — first, 2nd & last shop visits")

late_routes = day_data[day_data["Late Start"]]["Route"].tolist()
if late_routes:
    st.error(f"⚠ **{len(late_routes)} route(s) started after 10:00 AM:** {', '.join(late_routes)}")

st.dataframe(
    style_table(day_data),
    use_container_width=True,
    height=min(600, len(day_data) * 38 + 50),
    hide_index=True,
)

# ── DOWNLOAD ─────────────────────────────────────────────────────────────────
st.markdown("---")
csv_out = day_data.drop(columns=["Late Start"]).to_csv(index=False)
st.download_button(
    "⬇ Download filtered report (CSV)",
    csv_out,
    file_name=f"route_report_{selected_date}.csv",
    mime="text/csv",
)  make correction in this code so i could run in google colab to see how it actuly works.
