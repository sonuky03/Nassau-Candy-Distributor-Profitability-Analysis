import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Nassau Candy Profitability Analytics", page_icon="🍬", layout="wide")

st.title("🍬 Nassau Candy Profitability Analytics")
st.caption("Interactive product, division and regional profitability analysis")

@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df.columns = (df.columns.astype(str).str.strip()
                  .str.replace(" ", "_", regex=False)
                  .str.replace("/", "_", regex=False))
    aliases = {
        "Product_Name":"ProductName", "Product":"ProductName",
        "Gross_Profit":"GrossProfit", "Units_Sold":"Units",
        "Order_Date":"OrderDate", "Order_ID":"OrderID"
    }
    df.rename(columns={c: aliases.get(c, c) for c in df.columns}, inplace=True)

    for c in ["Sales", "Cost", "GrossProfit", "Units"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "", regex=False),
                                  errors="coerce")

    if "OrderDate" in df.columns:
        df["OrderDate"] = pd.to_datetime(df["OrderDate"], dayfirst=True, errors="coerce")

    if "GrossProfit" not in df.columns:
        df["GrossProfit"] = df["Sales"] - df["Cost"]

    if "Units" not in df.columns:
        df["Units"] = 0

    df["ProfitMargin"] = np.where(df["Sales"] != 0,
                                  df["GrossProfit"] / df["Sales"], np.nan)
    return df

def money(x):
    return f"${x:,.2f}"

def compact(x):
    x = float(x)
    if abs(x) >= 1_000_000: return f"${x/1_000_000:.2f}M"
    if abs(x) >= 1_000: return f"${x/1_000:.2f}K"
    return f"${x:,.0f}"

st.sidebar.header("📁 Data")

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = BASE_DIR / "Dataset" / "Nassau Candy Distribution.csv"

file = st.sidebar.file_uploader(
    "Upload another Nassau Candy CSV (optional)",
    type=["csv"]
)

try:
    if file is not None:
        df = load_data(file)
    else:
        df = load_data(DEFAULT_DATA_PATH)

except Exception as e:
    st.error(f"Could not read the CSV: {e}")
    st.stop()

required = ["ProductName", "Division", "Region", "Sales", "Cost", "GrossProfit"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.write("Detected columns:", list(df.columns))
    st.stop()

# Filters
st.sidebar.header("🎛️ Filters")
filtered = df.copy()

if "OrderDate" in df.columns and df["OrderDate"].notna().any():
    d1, d2 = df["OrderDate"].min().date(), df["OrderDate"].max().date()
    dates = st.sidebar.date_input("Order Date", (d1, d2), min_value=d1, max_value=d2)
    if isinstance(dates, tuple) and len(dates) == 2:
        filtered = filtered[(filtered["OrderDate"].dt.date >= dates[0]) &
                            (filtered["OrderDate"].dt.date <= dates[1])]

regions = sorted(df["Region"].dropna().astype(str).unique())
sr = st.sidebar.multiselect("Region", regions, default=regions)
filtered = filtered[filtered["Region"].astype(str).isin(sr)]

divisions = sorted(df["Division"].dropna().astype(str).unique())
sd = st.sidebar.multiselect("Division", divisions, default=divisions)
filtered = filtered[filtered["Division"].astype(str).isin(sd)]

# KPIs
orders = filtered["OrderID"].nunique() if "OrderID" in filtered.columns else len(filtered)
sales = filtered["Sales"].sum()
cost = filtered["Cost"].sum()
profit = filtered["GrossProfit"].sum()
units = filtered["Units"].sum()
margin = profit / sales if sales else 0

a,b,c,d,e,f = st.columns(6)
a.metric("Total Orders", f"{orders:,}")
b.metric("Total Sales", compact(sales))
c.metric("Total Cost", compact(cost))
d.metric("Gross Profit", compact(profit))
e.metric("Units Sold", f"{units:,.0f}")
f.metric("Profit Margin", f"{margin:.2%}")

st.divider()

# ============================================================
# DIVISION PERFORMANCE DASHBOARD
# ============================================================

st.subheader("📊 Division Performance Dashboard")

division_df = (
    filtered.groupby("Division", as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Cost=("Cost", "sum"),
        GrossProfit=("GrossProfit", "sum")
    )
)

division_df["ProfitMargin"] = np.where(
    division_df["Revenue"] != 0,
    division_df["GrossProfit"] / division_df["Revenue"],
    0
)

d1, d2 = st.columns(2)

# Revenue vs Profit
with d1:
    division_long = division_df.melt(
        id_vars="Division",
        value_vars=["Revenue", "GrossProfit"],
        var_name="Metric",
        value_name="Amount"
    )

    fig = px.bar(
        division_long,
        x="Division",
        y="Amount",
        color="Metric",
        barmode="group",
        title="Revenue vs Gross Profit by Division",
        text_auto=".2s"
    )

    st.plotly_chart(fig, use_container_width=True)


# Margin Distribution
with d2:
    fig = px.bar(
        division_df,
        x="Division",
        y="ProfitMargin",
        title="Margin Distribution by Division",
        text=division_df["ProfitMargin"].map(
            lambda x: f"{x:.1%}"
        )
    )

    fig.update_yaxes(tickformat=".0%")

    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = px.bar(region_df, x="Region", y="GrossProfit",
                 title="Gross Profit by Region", text_auto=".2s")
    st.plotly_chart(fig, use_container_width=True)

# Product analysis
product = (filtered.groupby(["ProductName","Division"], as_index=False)
           .agg(Total_Sales=("Sales","sum"), Total_Cost=("Cost","sum"),
                Gross_Profit=("GrossProfit","sum"), Units_Sold=("Units","sum")))
product["Profit_Margin"] = np.where(product["Total_Sales"] != 0,
                                    product["Gross_Profit"]/product["Total_Sales"], np.nan)
product = product.sort_values("Gross_Profit", ascending=False)
product["Product_Rank"] = range(1, len(product)+1)

p1,p2 = st.columns(2)
with p1:
    top5 = product.head(5).sort_values("Gross_Profit")
    fig = px.bar(top5, x="Gross_Profit", y="ProductName", orientation="h",
                 title="Top 5 Products by Gross Profit", text_auto=".2s")
    st.plotly_chart(fig, use_container_width=True)

with p2:
    fig = px.scatter(product, x="Total_Sales", y="Gross_Profit",
                     size="Units_Sold", color="Division",
                     hover_name="ProductName",
                     hover_data={"Profit_Margin":":.2%"},
                     title="Sales vs Gross Profit")
    st.plotly_chart(fig, use_container_width=True)

# Cost vs Sales diagnostic
st.subheader("💰 Cost vs Sales Diagnostics")

fig = px.scatter(
    product,
    x="Total_Cost",
    y="Total_Sales",
    size="Gross_Profit",
    color="Division",
    hover_name="ProductName",
    hover_data={
        "Profit_Margin": ":.2%"
    },
    title="Cost vs Sales by Product"
)

st.plotly_chart(fig, use_container_width=True)

# Margin diagnostics
m1,m2 = st.columns(2)
with m1:
    low = product.sort_values("Profit_Margin").head(10)
    fig = px.bar(low, x="Profit_Margin", y="ProductName", orientation="h",
                 title="10 Lowest-Margin Products",
                 text=low["Profit_Margin"].map(lambda x:f"{x:.1%}"))
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

with m2:
    fig = px.scatter(product, x="Total_Cost", y="Profit_Margin",
                     size="Gross_Profit", color="Division",
                     hover_name="ProductName", title="Cost vs Profit Margin")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

# Risk flags
q25 = product["Profit_Margin"].quantile(.25) if len(product) else 0
q75 = product["Gross_Profit"].quantile(.75) if len(product) else 0
median_sales = product["Total_Sales"].median() if len(product) else 0

def flag(r):
    if r["Profit_Margin"] <= q25: return "🔴 Low Margin"
    if r["Total_Sales"] >= median_sales and r["Profit_Margin"] <= q25*1.25:
        return "🟡 High Sales / Margin Watch"
    if r["Gross_Profit"] >= q75: return "🟢 High Profit Contribution"
    return "🔵 Normal"

product["Status"] = product.apply(flag, axis=1)

st.subheader("🚩 Product Risk & Opportunity Flags")
counts = product["Status"].value_counts().rename_axis("Status").reset_index(name="Products")
st.plotly_chart(px.bar(counts, x="Status", y="Products", text_auto=True,
                       title="Product Status Distribution"),
                use_container_width=True)

# ============================================================
# PROFIT CONCENTRATION ANALYSIS
# ============================================================

st.subheader("📈 Profit Concentration Analysis")

pareto = product.copy()

pareto = pareto.sort_values(
    "Gross_Profit",
    ascending=False
).reset_index(drop=True)

total_profit = pareto["Gross_Profit"].sum()

pareto["Cumulative_Profit"] = pareto["Gross_Profit"].cumsum()

pareto["Cumulative_%"] = (
    pareto["Cumulative_Profit"] / total_profit
)

# -----------------------------
# Dependency indicators
# -----------------------------

top5_share = (
    pareto.head(5)["Gross_Profit"].sum()
    / total_profit
)

top10_share = (
    pareto.head(10)["Gross_Profit"].sum()
    / total_profit
)

products_for_80 = (
    (pareto["Cumulative_%"] < 0.80).sum() + 1
)

x1, x2, x3 = st.columns(3)

x1.metric(
    "Top 5 Profit Share",
    f"{top5_share:.1%}"
)

x2.metric(
    "Top 10 Profit Share",
    f"{top10_share:.1%}"
)

x3.metric(
    "Products for 80% Profit",
    f"{products_for_80}"
)

# -----------------------------
# Pareto Chart
# -----------------------------

pareto_display = pareto.head(15)

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=pareto_display["ProductName"],
        y=pareto_display["Gross_Profit"],
        name="Gross Profit"
    )
)

fig.add_trace(
    go.Scatter(
        x=pareto_display["ProductName"],
        y=pareto_display["Cumulative_%"] * 100,
        mode="lines+markers",
        name="Cumulative Profit %",
        yaxis="y2"
    )
)

fig.update_layout(
    title="Pareto Analysis — Gross Profit Concentration",
    xaxis_title="Product",
    yaxis_title="Gross Profit",
    yaxis2=dict(
        title="Cumulative Profit %",
        overlaying="y",
        side="right",
        range=[0, 100],
        ticksuffix="%"
    ),
    xaxis_tickangle=-45
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# -----------------------------
# Dependency indicators
# -----------------------------

st.subheader("🔗 Profit Dependency Indicators")

dependency = pd.DataFrame({
    "Indicator": [
        "Top 5 Profit Share",
        "Top 10 Profit Share",
        "Products Required for 80% of Profit"
    ],
    "Value": [
        f"{top5_share:.1%}",
        f"{top10_share:.1%}",
        str(products_for_80)
    ]
})

st.dataframe(
    dependency,
    use_container_width=True,
    hide_index=True
)

if len(pareto):
    share = pareto.head(5)["Gross_Profit"].sum()/pareto["Gross_Profit"].sum()
    st.info(f"Top 5 products contribute approximately **{share:.1%}** of gross profit for the current selection.")

# Leaderboard
st.subheader("🏆 Product Profitability Leaderboard")
show = product[["Product_Rank","ProductName","Division","Total_Sales",
                "Total_Cost","Gross_Profit","Units_Sold","Profit_Margin","Status"]].copy()
st.dataframe(show.style.format({
    "Total_Sales":"${:,.2f}", "Total_Cost":"${:,.2f}",
    "Gross_Profit":"${:,.2f}", "Units_Sold":"{:,.0f}",
    "Profit_Margin":"{:.2%}"
}), use_container_width=True, hide_index=True)

# Insights
st.subheader("💡 Business Insights")
if len(division_df):
    st.write(f"- **{division_df.iloc[0]['Division']}** leads divisions by gross profit: {money(division_df.iloc[0]['GrossProfit'])}.")
if len(region_df):
    st.write(f"- **{region_df.iloc[0]['Region']}** leads regions by gross profit: {money(region_df.iloc[0]['GrossProfit'])}.")
if len(product):
    st.write(f"- **{product.iloc[0]['ProductName']}** ranks #1 by gross profit: {money(product.iloc[0]['Gross_Profit'])}.")
    lowp = product.sort_values("Profit_Margin").iloc[0]
    st.write(f"- Lowest product margin in the current selection: **{lowp['ProductName']} ({lowp['Profit_Margin']:.2%})**.")

# Data explorer
st.subheader("📥 Data Explorer")
tab1, tab2 = st.tabs(["Filtered Data", "Download"])
with tab1:
    st.dataframe(filtered, use_container_width=True, hide_index=True)
with tab2:
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Filtered CSV", csv,
                       "nassau_candy_filtered_data.csv", "text/csv")

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#6b7280; padding:10px;">
        <b>Developed by Sonu Kumar</b><br>
        Nassau Candy Distributor | Excel → SQL → Power BI → Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
