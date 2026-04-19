import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar

from database import (
    init_db, insert_expense, get_all_expenses_as_df,
    update_expense, delete_expense, seed_synthetic_data,
    get_monthly_summary, get_budget_vs_actual, bulk_insert_expenses,
    insert_income, get_all_income_as_df, update_income, delete_income,
    get_monthly_income_summary, INCOME_SOURCES,
)
from data_generator import generate_synthetic_expenses, CATEGORIES, PAYMENT_METHODS

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Expense Tracker Pro",
    layout="wide",
    page_icon="₹",
    initial_sidebar_state="expanded",
)

CURRENCY = "₹"

st.markdown("""
<style>
[data-testid="metric-container"] {
    background: linear-gradient(135deg,#f0f4ff 0%,#e8eeff 100%);
    border: 1px solid #c8d4f8;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(80,100,200,.10);
}
[data-testid="metric-container"] label {
    color:#5566aa!important; font-size:.8rem!important;
    letter-spacing:.06em; text-transform:uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color:#1a237e!important; font-size:1.5rem!important; font-weight:700;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size:.8rem!important; }

[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#f0f4ff 0%,#e8eeff 100%);
    border-right:1px solid #c8d4f8;
}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color:#1a237e!important; }
[data-testid="stSidebar"] .stFormSubmitButton>button {
    background:linear-gradient(135deg,#3949ab,#5c6bc0)!important;
    color:#fff!important; border:none!important;
    border-radius:8px!important; font-weight:600!important;
}
[data-testid="stSidebar"] .stFormSubmitButton>button:hover {
    background:linear-gradient(135deg,#283593,#3949ab)!important;
}

.income-metric {
    background:linear-gradient(135deg,#e8f5e9,#f1f8e9);
    border:1px solid #a5d6a7; border-radius:12px;
    padding:16px 20px; box-shadow:0 2px 8px rgba(40,160,80,.10);
}
.expense-metric {
    background:linear-gradient(135deg,#fce4ec,#fff3e0);
    border:1px solid #f48fb1; border-radius:12px;
    padding:16px 20px; box-shadow:0 2px 8px rgba(200,60,80,.10);
}
.savings-metric {
    background:linear-gradient(135deg,#e3f2fd,#e8eaf6);
    border:1px solid #90caf9; border-radius:12px;
    padding:16px 20px; box-shadow:0 2px 8px rgba(30,100,200,.10);
}
.upload-info {
    background:#f0f4ff; border:1px dashed #7986cb;
    border-radius:10px; padding:12px 16px;
    color:#3949ab; font-size:.9rem; margin-bottom:12px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INIT
# ══════════════════════════════════════════════════════════════════════════════
init_db()
seed_synthetic_data(generate_synthetic_expenses())

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("## ₹ Expense Tracker Pro")
st.sidebar.markdown("---")

# ── ADD EXPENSE ───────────────────────────────────────────────────────────────
st.sidebar.markdown("### ➕ Add New Expense")
with st.sidebar.form("add_expense_form", clear_on_submit=True):
    exp_date   = st.date_input("Date", datetime.today(), key="exp_date")
    exp_cat    = st.selectbox("Category", CATEGORIES, key="exp_cat")
    exp_amt    = st.number_input(f"Amount ({CURRENCY})", min_value=0.01, step=10.0, format="%.2f", key="exp_amt")
    exp_pm     = st.selectbox("Payment Method", PAYMENT_METHODS, key="exp_pm")
    exp_note   = st.text_input("Note (optional)", placeholder="e.g. Lunch with team", key="exp_note")
    exp_submit = st.form_submit_button("💾 Add Expense", use_container_width=True)
    if exp_submit and exp_amt > 0:
        insert_expense(str(exp_date), exp_cat, exp_amt, exp_pm, exp_note)
        st.sidebar.success("✅ Expense added!")
        st.rerun()

st.sidebar.markdown("---")

# ── ADD INCOME ────────────────────────────────────────────────────────────────
st.sidebar.markdown("### 💵 Add New Income")
with st.sidebar.form("add_income_form", clear_on_submit=True):
    inc_date   = st.date_input("Date", datetime.today(), key="inc_date")
    inc_source = st.selectbox("Income Source", INCOME_SOURCES, key="inc_source")
    inc_amt    = st.number_input(f"Amount ({CURRENCY})", min_value=0.01, step=100.0, format="%.2f", key="inc_amt")
    inc_note   = st.text_input("Note (optional)", placeholder="e.g. Monthly salary", key="inc_note")
    inc_submit = st.form_submit_button("💾 Add Income", use_container_width=True)
    if inc_submit and inc_amt > 0:
        insert_income(str(inc_date), inc_source, inc_amt, inc_note)
        st.sidebar.success("✅ Income added!")
        st.rerun()

st.sidebar.markdown("---")

# ── MONTHLY BUDGETS ───────────────────────────────────────────────────────────
st.sidebar.markdown("### 🎯 Monthly Budgets (₹)")
DEFAULT_BUDGETS = {
    'Food': 8000, 'Rent': 15000, 'Utilities': 3000,
    'Transport': 3000, 'Entertainment': 3000,
    'Healthcare': 3000, 'Shopping': 5000,
}
budgets = {}
for cat in CATEGORIES:
    budgets[cat] = st.sidebar.number_input(
        cat, min_value=0, value=DEFAULT_BUDGETS[cat], step=500, key=f"budget_{cat}"
    )

# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
df_raw = get_all_expenses_as_df()
inc_raw = get_all_income_as_df()

if df_raw.empty:
    st.info("No expenses yet. Add some using the sidebar.")
    st.stop()

if 'id' not in df_raw.columns:
    df_raw = df_raw.reset_index(drop=False).rename(columns={'index': 'id'})
if 'source' not in df_raw.columns:
    df_raw['source'] = 'manual'

df_raw['date'] = pd.to_datetime(df_raw['date'])

if not inc_raw.empty:
    inc_raw['date'] = pd.to_datetime(inc_raw['date'])

# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER & FILTERS
# ══════════════════════════════════════════════════════════════════════════════
st.title("₹ Advanced Expense & Income Tracker")
st.markdown("#### Track, analyse, and optimise your finances")
st.markdown("---")

fc1, fc2, fc3 = st.columns([1, 1, 2])
with fc1:
    start_date = st.date_input("📅 From", df_raw['date'].min().date())
with fc2:
    end_date   = st.date_input("📅 To",   df_raw['date'].max().date())
with fc3:
    cat_filter = st.multiselect(
        "📂 Categories",
        options=sorted(df_raw['category'].unique()),
        default=sorted(df_raw['category'].unique()),
    )

mask = (
    (df_raw['date'].dt.date >= start_date) &
    (df_raw['date'].dt.date <= end_date) &
    (df_raw['category'].isin(cat_filter))
)
df = df_raw[mask].copy()

if df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# ── Income filtered to same window ───────────────────────────────────────────
if not inc_raw.empty:
    inc_mask = (
        (inc_raw['date'].dt.date >= start_date) &
        (inc_raw['date'].dt.date <= end_date)
    )
    inc_df = inc_raw[inc_mask].copy()
else:
    inc_df = pd.DataFrame(columns=['id', 'date', 'source', 'amount', 'note'])

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL KPIs
# ══════════════════════════════════════════════════════════════════════════════
total_expense   = df['amount'].sum()
total_income    = inc_df['amount'].sum() if not inc_df.empty else 0.0
net_savings     = total_income - total_expense
savings_rate    = (net_savings / total_income * 100) if total_income > 0 else 0
unique_days     = df['date'].nunique()
avg_daily_exp   = total_expense / unique_days if unique_days > 0 else 0
total_txns      = len(df)

# Current & previous month totals (expenses)
curr_month = pd.Timestamp.today().to_period('M')
prev_month = (pd.Timestamp.today() - pd.DateOffset(months=1)).to_period('M')

curr_exp = df_raw[df_raw['date'].dt.to_period('M') == curr_month]['amount'].sum()
prev_exp = df_raw[df_raw['date'].dt.to_period('M') == prev_month]['amount'].sum()
curr_inc = inc_raw[inc_raw['date'].dt.to_period('M') == curr_month]['amount'].sum() if not inc_raw.empty else 0.0

mom_delta = curr_exp - prev_exp

# ── Row 1: Income / Expense / Savings ────────────────────────────────────────
r1c1, r1c2, r1c3 = st.columns(3)

r1c1.markdown(
    f'<div class="income-metric">'
    f'<div style="color:#2e7d32;font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase">💚 Total Income</div>'
    f'<div style="color:#1b5e20;font-size:1.6rem;font-weight:800">{CURRENCY}{total_income:,.0f}</div>'
    f'<div style="color:#388e3c;font-size:.8rem">This month: {CURRENCY}{curr_inc:,.0f}</div>'
    f'</div>',
    unsafe_allow_html=True
)

r1c2.markdown(
    f'<div class="expense-metric">'
    f'<div style="color:#c62828;font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase">❤️ Total Expenses</div>'
    f'<div style="color:#b71c1c;font-size:1.6rem;font-weight:800">{CURRENCY}{total_expense:,.0f}</div>'
    f'<div style="color:#e53935;font-size:.8rem">This month: {CURRENCY}{curr_exp:,.0f} '
    f'({("▲" if mom_delta >= 0 else "▼")} {CURRENCY}{abs(mom_delta):,.0f} vs last)</div>'
    f'</div>',
    unsafe_allow_html=True
)

savings_color = "#1565c0" if net_savings >= 0 else "#b71c1c"
r1c3.markdown(
    f'<div class="savings-metric">'
    f'<div style="color:#1565c0;font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase">💙 Net Savings</div>'
    f'<div style="color:{savings_color};font-size:1.6rem;font-weight:800">{CURRENCY}{net_savings:,.0f}</div>'
    f'<div style="color:#1976d2;font-size:.8rem">Savings rate: {savings_rate:.1f}%</div>'
    f'</div>',
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 2: transaction stats ──────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("🔢 Transactions",       f"{total_txns:,}")
k2.metric("📊 Avg Transaction",    f"{CURRENCY}{df['amount'].mean():.0f}")
k3.metric("📈 Avg Daily Spend",    f"{CURRENCY}{avg_daily_exp:.0f}")
k4.metric("🏆 Top Category",       df.groupby('category')['amount'].sum().idxmax())

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_overview, tab_income, tab_budget, tab_records, tab_insights, tab_upload = st.tabs([
    "📈 Overview", "💵 Income", "🎯 Budget", "📋 Records", "🧠 Insights", "📤 Import CSV"
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 – OVERVIEW (expense charts)
# ──────────────────────────────────────────────────────────────────────────────
with tab_overview:

    # ── Monthly income vs expense comparison ──────────────────────────────────
    if not inc_df.empty:
        monthly_exp = (
            df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
            .reset_index().rename(columns={'amount': 'Expenses'})
        )
        monthly_exp['date'] = monthly_exp['date'].astype(str)

        monthly_inc = (
            inc_df.groupby(inc_df['date'].dt.to_period('M'))['amount'].sum()
            .reset_index().rename(columns={'amount': 'Income'})
        )
        monthly_inc['date'] = monthly_inc['date'].astype(str)

        merged_monthly = pd.merge(monthly_exp, monthly_inc, on='date', how='outer').fillna(0)
        merged_monthly['Savings'] = merged_monthly['Income'] - merged_monthly['Expenses']

        fig_inc_exp = go.Figure()
        fig_inc_exp.add_trace(go.Bar(name='Income',   x=merged_monthly['date'], y=merged_monthly['Income'],   marker_color='rgba(56,142,60,.85)'))
        fig_inc_exp.add_trace(go.Bar(name='Expenses', x=merged_monthly['date'], y=merged_monthly['Expenses'], marker_color='rgba(229,57,53,.85)'))
        fig_inc_exp.add_trace(go.Scatter(name='Savings', x=merged_monthly['date'], y=merged_monthly['Savings'],
                                          mode='lines+markers', line=dict(color='#1976d2', width=2.5),
                                          marker=dict(size=7)))
        fig_inc_exp.update_layout(
            barmode='group', title=f"📊 Monthly Income vs Expenses ({CURRENCY})",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#444', yaxis_title=f"Amount ({CURRENCY})",
        )
        st.plotly_chart(fig_inc_exp, use_container_width=True)
    else:
        st.info("💡 Add income entries to see the Income vs Expenses comparison chart.")

    # ── Monthly expense trend ─────────────────────────────────────────────────
    monthly_exp_only = (
        df.groupby(df['date'].dt.to_period('M'))['amount'].sum().reset_index()
    )
    monthly_exp_only['date'] = monthly_exp_only['date'].astype(str)
    fig_trend = px.area(
        monthly_exp_only, x='date', y='amount',
        title=f"📅 Monthly Expense Trend ({CURRENCY})",
        labels={'amount': f'Total ({CURRENCY})', 'date': 'Month'},
        color_discrete_sequence=['#ef5350'],
    )
    fig_trend.update_traces(fill='tozeroy', line_color='#e53935')
    fig_trend.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#444'
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        cat_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False).reset_index()
        fig_cat = px.bar(
            cat_totals, x='category', y='amount', color='category',
            title=f"📂 Spend by Category ({CURRENCY})", labels={'amount': CURRENCY},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_cat.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
                               paper_bgcolor='rgba(0,0,0,0)', font_color='#444')
        st.plotly_chart(fig_cat, use_container_width=True)

    with cr:
        pay_totals = df.groupby('payment_method')['amount'].sum().reset_index()
        fig_pay = px.pie(
            pay_totals, values='amount', names='payment_method',
            title="💳 Spend by Payment Method", hole=0.42,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_pay.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                               paper_bgcolor='rgba(0,0,0,0)', font_color='#444')
        st.plotly_chart(fig_pay, use_container_width=True)

    # ── Stacked category over time ────────────────────────────────────────────
    monthly_cat = (
        df.groupby([df['date'].dt.to_period('M'), 'category'])['amount'].sum().reset_index()
    )
    monthly_cat['date'] = monthly_cat['date'].astype(str)
    fig_stack = px.area(
        monthly_cat, x='date', y='amount', color='category',
        title=f"📊 Category Spend Over Time ({CURRENCY})",
        labels={'amount': CURRENCY, 'date': 'Month'},
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_stack.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                             paper_bgcolor='rgba(0,0,0,0)', font_color='#444')
    st.plotly_chart(fig_stack, use_container_width=True)

    # ── Heatmap ───────────────────────────────────────────────────────────────
    df['weekday'] = df['date'].dt.day_name()
    df['week']    = df['date'].dt.isocalendar().week.astype(int)
    heatmap_data  = df.groupby(['weekday', 'week'])['amount'].sum().reset_index()
    weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    fig_heat = px.density_heatmap(
        heatmap_data, x='week', y='weekday', z='amount',
        category_orders={'weekday': weekday_order},
        title="🌡️ Daily Spend Intensity Heatmap",
        color_continuous_scale='Reds',
    )
    fig_heat.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)', font_color='#444')
    st.plotly_chart(fig_heat, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 – INCOME
# ──────────────────────────────────────────────────────────────────────────────
with tab_income:
    st.markdown("### 💵 Income Tracker")

    if inc_df.empty:
        st.info("No income entries yet. Use the **Add New Income** form in the sidebar to get started.")
    else:
        # ── KPIs ─────────────────────────────────────────────────────────────
        ik1, ik2, ik3, ik4 = st.columns(4)
        ik1.metric("💚 Total Income",       f"{CURRENCY}{total_income:,.0f}")
        ik2.metric("📅 This Month",         f"{CURRENCY}{curr_inc:,.0f}")
        ik3.metric("📊 Avg per Entry",      f"{CURRENCY}{inc_df['amount'].mean():,.0f}")
        ik4.metric("🔢 Total Entries",      f"{len(inc_df):,}")

        st.markdown("---")

        il, ir = st.columns(2)

        with il:
            inc_monthly = (
                inc_df.groupby(inc_df['date'].dt.to_period('M'))['amount'].sum().reset_index()
            )
            inc_monthly['date'] = inc_monthly['date'].astype(str)
            fig_inc_trend = px.bar(
                inc_monthly, x='date', y='amount',
                title=f"📅 Monthly Income ({CURRENCY})",
                labels={'amount': CURRENCY, 'date': 'Month'},
                color_discrete_sequence=['#43a047'],
            )
            fig_inc_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                                         paper_bgcolor='rgba(0,0,0,0)', font_color='#444')
            st.plotly_chart(fig_inc_trend, use_container_width=True)

        with ir:
            inc_source_totals = inc_df.groupby('source')['amount'].sum().reset_index()
            fig_inc_src = px.pie(
                inc_source_totals, values='amount', names='source',
                title="💼 Income by Source", hole=0.42,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_inc_src.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                                       paper_bgcolor='rgba(0,0,0,0)', font_color='#444')
            st.plotly_chart(fig_inc_src, use_container_width=True)

        # ── Savings rate over time ─────────────────────────────────────────────
        monthly_inc_ts = (
            inc_df.groupby(inc_df['date'].dt.to_period('M'))['amount']
            .sum().reset_index().rename(columns={'amount': 'income'})
        )
        monthly_inc_ts['date'] = monthly_inc_ts['date'].astype(str)

        monthly_exp_ts = (
            df.groupby(df['date'].dt.to_period('M'))['amount']
            .sum().reset_index().rename(columns={'amount': 'expense'})
        )
        monthly_exp_ts['date'] = monthly_exp_ts['date'].astype(str)

        savings_ts = pd.merge(monthly_inc_ts, monthly_exp_ts, on='date', how='outer').fillna(0)
        savings_ts['savings_rate'] = savings_ts.apply(
            lambda r: (r['income'] - r['expense']) / r['income'] * 100 if r['income'] > 0 else 0, axis=1
        )
        fig_sr = px.line(
            savings_ts, x='date', y='savings_rate',
            title="📈 Monthly Savings Rate (%)",
            labels={'savings_rate': 'Savings Rate (%)', 'date': 'Month'},
            markers=True, color_discrete_sequence=['#1976d2'],
        )
        fig_sr.add_hline(y=20, line_dash='dash', line_color='#43a047',
                          annotation_text="20% target", annotation_position="top right")
        fig_sr.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                              paper_bgcolor='rgba(0,0,0,0)', font_color='#444')
        st.plotly_chart(fig_sr, use_container_width=True)

        # ── Income records table ───────────────────────────────────────────────
        st.markdown("#### 📋 Income Records")
        disp_inc = inc_df.copy()
        disp_inc['date'] = disp_inc['date'].dt.strftime('%Y-%m-%d')
        edited_inc = st.data_editor(
            disp_inc,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id":     st.column_config.NumberColumn("ID", disabled=True),
                "date":   st.column_config.TextColumn("Date"),
                "source": st.column_config.SelectboxColumn("Source", options=INCOME_SOURCES),
                "amount": st.column_config.NumberColumn(f"Amount ({CURRENCY})", step=1.0, format="%.2f"),
                "note":   st.column_config.TextColumn("Note"),
            },
            disabled=['id'],
            key="income_editor",
        )
        isave, idel = st.columns(2)
        with isave:
            if st.button("💾 Save Income Changes", use_container_width=True):
                for _, row in edited_inc.iterrows():
                    update_income(row['id'], row['date'], row['source'], row['amount'], row['note'])
                st.success("✅ Income records saved!")
                st.rerun()
        with idel:
            with st.expander("🗑️ Delete an Income Entry"):
                del_inc_id = st.number_input("Income ID to delete", min_value=1, step=1, key="del_inc")
                if st.button("Delete Income", type="primary", key="del_inc_btn"):
                    delete_income(int(del_inc_id))
                    st.success(f"Deleted income ID {del_inc_id}.")
                    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 – BUDGET
# ──────────────────────────────────────────────────────────────────────────────
with tab_budget:
    st.markdown("### 🎯 Budget vs Actual — Current Month")

    # Month selector
    available_months = sorted(df_raw['date'].dt.to_period('M').unique().astype(str), reverse=True)
    selected_month   = st.selectbox("Select Month", available_months, index=0, key="budget_month")

    budget_df = get_budget_vs_actual(budgets, month=selected_month)
    month_inc = inc_raw[inc_raw['date'].dt.to_period('M').astype(str) == selected_month]['amount'].sum() if not inc_raw.empty else 0.0
    month_exp = df_raw[df_raw['date'].dt.to_period('M').astype(str) == selected_month]['amount'].sum()

    bk1, bk2, bk3, bk4 = st.columns(4)
    bk1.metric("💚 Month Income",   f"{CURRENCY}{month_inc:,.0f}")
    bk2.metric("❤️ Month Expenses", f"{CURRENCY}{month_exp:,.0f}")
    bk3.metric("💙 Net",            f"{CURRENCY}{month_inc - month_exp:,.0f}")
    bk4.metric("🎯 Total Budget",   f"{CURRENCY}{sum(budgets.values()):,.0f}")

    st.markdown("---")

    if budget_df.empty:
        st.info(f"No expense transactions in {selected_month}.")
    else:
        # ── Progress bars ─────────────────────────────────────────────────────
        cols_per_row = 2
        rows = [list(budget_df.iterrows())[i:i+cols_per_row]
                for i in range(0, len(budget_df), cols_per_row)]
        for row_items in rows:
            rcols = st.columns(cols_per_row)
            for ci, (_, brow) in enumerate(row_items):
                cat      = brow['category']
                actual   = brow['actual']
                bval     = budgets.get(cat, 0)
                pct      = (actual / bval * 100) if bval > 0 else 0
                emoji    = "🔴" if pct > 90 else ("🟡" if pct > 70 else "🟢")
                with rcols[ci]:
                    st.markdown(
                        f"**{emoji} {cat}** — {CURRENCY}{actual:,.0f} / {CURRENCY}{bval:,.0f} &nbsp;`{pct:.0f}%`"
                    )
                    st.progress(min(pct / 100, 1.0))

        st.markdown("---")

        # ── Budget vs Actual bar chart ────────────────────────────────────────
        merged_b = budget_df.copy()
        merged_b['budget'] = merged_b['category'].map(budgets)
        fig_bv = go.Figure()
        fig_bv.add_trace(go.Bar(name='Budget', x=merged_b['category'], y=merged_b['budget'],
                                 marker_color='rgba(96,160,255,.6)'))
        fig_bv.add_trace(go.Bar(name='Actual', x=merged_b['category'], y=merged_b['actual'],
                                 marker_color='rgba(255,80,80,.85)'))
        fig_bv.update_layout(
            barmode='group', title=f"Budget vs Actual — {selected_month} ({CURRENCY})",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#444',
        )
        st.plotly_chart(fig_bv, use_container_width=True)

        # ── Remaining budget waterfall ────────────────────────────────────────
        merged_b['remaining'] = merged_b['budget'] - merged_b['actual']
        fig_rem = px.bar(
            merged_b, x='category', y='remaining', color='remaining',
            color_continuous_scale=['#ef5350', '#ffee58', '#66bb6a'],
            title=f"💰 Remaining Budget per Category ({CURRENCY})",
            labels={'remaining': f'Remaining ({CURRENCY})'},
        )
        fig_rem.add_hline(y=0, line_dash='dash', line_color='#333')
        fig_rem.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                               paper_bgcolor='rgba(0,0,0,0)', font_color='#444')
        st.plotly_chart(fig_rem, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 – RECORDS
# ──────────────────────────────────────────────────────────────────────────────
with tab_records:
    st.markdown("### 📋 Expense Records")

    display_cols   = ['id', 'date', 'category', 'amount', 'payment_method', 'note', 'source']
    available_cols = [c for c in display_cols if c in df.columns]
    display_df     = df[available_cols].copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    for col in display_cols:
        if col not in display_df.columns:
            display_df[col] = ''
    display_df = display_df[display_cols]

    edited_df = st.data_editor(
        display_df, use_container_width=True, hide_index=True,
        column_config={
            "id":             st.column_config.NumberColumn("ID", disabled=True),
            "date":           st.column_config.TextColumn("Date"),
            "category":       st.column_config.SelectboxColumn("Category", options=CATEGORIES),
            "amount":         st.column_config.NumberColumn(f"Amount ({CURRENCY})", step=1.0, format="%.2f"),
            "payment_method": st.column_config.SelectboxColumn("Payment", options=PAYMENT_METHODS),
            "note":           st.column_config.TextColumn("Note"),
            "source":         st.column_config.TextColumn("Source", disabled=True),
        },
        disabled=['id', 'source'],
        key="data_editor",
        num_rows="fixed",
    )

    sc, dc = st.columns(2)
    with sc:
        if st.button("💾 Save All Changes", use_container_width=True):
            for _, row in edited_df.iterrows():
                update_expense(row['id'], row['date'], row['category'],
                               row['amount'], row['payment_method'], row['note'])
            st.success("✅ Saved!")
            st.rerun()
    with dc:
        with st.expander("🗑️ Delete an Expense"):
            del_id = st.number_input("Expense ID to delete", min_value=1, step=1)
            if st.button("Delete", type="primary"):
                if del_id in df['id'].values:
                    delete_expense(int(del_id))
                    st.success(f"Deleted expense ID {del_id}.")
                    st.rerun()
                else:
                    st.error("ID not found in current view.")

    st.markdown("---")
    csv_dl = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Filtered Expenses as CSV",
        data=csv_dl,
        file_name=f"expenses_{start_date}_{end_date}.csv",
        mime="text/csv",
    )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 5 – INSIGHTS
# ──────────────────────────────────────────────────────────────────────────────
with tab_insights:
    st.markdown("### 🧠 Smart Insights & Recommendations")

    cat_totals     = df.groupby('category')['amount'].sum()
    top_cat        = cat_totals.idxmax()
    top_pct        = cat_totals.max() / cat_totals.sum() * 100
    monthly_totals = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
    monthly_avg    = monthly_totals.mean()

    # ── Health banner ─────────────────────────────────────────────────────────
    if total_income > 0:
        if savings_rate < 0:
            st.error(f"🚨 **You are spending more than you earn!** Net savings: {CURRENCY}{net_savings:,.0f} ({savings_rate:.1f}%)")
        elif savings_rate < 10:
            st.warning(f"⚠️ **Low savings rate: {savings_rate:.1f}%.** Aim for at least 20%.")
        elif savings_rate < 20:
            st.warning(f"🟡 **Savings rate {savings_rate:.1f}%** — room for improvement. Target: 20%+")
        else:
            st.success(f"✅ **Great savings rate: {savings_rate:.1f}%!** Keep it up.")
    else:
        if curr_exp > monthly_avg * 1.2:
            st.error(f"⚠️ **Overspending Alert!** This month: {CURRENCY}{curr_exp:,.0f} is >20% above your avg of {CURRENCY}{monthly_avg:,.0f}.")
        else:
            st.success(f"✅ Spending on track. Average monthly: {CURRENCY}{monthly_avg:,.0f}")

    st.markdown("---")
    ic1, ic2 = st.columns(2)

    with ic1:
        st.markdown("#### 🏆 Top 5 Spending Categories")
        for cat, amt in cat_totals.sort_values(ascending=False).head(5).items():
            pct = amt / cat_totals.sum() * 100
            st.markdown(f"- **{cat}**: {CURRENCY}{amt:,.0f} &nbsp; `{pct:.1f}%`")

    with ic2:
        st.markdown("#### 💳 Payment Method Breakdown")
        pay_totals = df.groupby('payment_method')['amount'].sum().sort_values(ascending=False)
        for method, amt in pay_totals.items():
            pct = amt / pay_totals.sum() * 100
            st.markdown(f"- **{method}**: {CURRENCY}{amt:,.0f} &nbsp; `{pct:.1f}%`")

    st.markdown("---")
    st.markdown("#### 📌 Personalised Recommendations")

    # Rec 1: budget cap suggestion
    suggested_cap = cat_totals[top_cat] * 0.90 / max(len(monthly_totals), 1)
    st.markdown(
        f"💡 **Cap {top_cat} spending:** Consider a limit of **{CURRENCY}{suggested_cap:,.0f}/month** "
        f"(10% below your average) — it accounts for ~{top_pct:.0f}% of your total spend."
    )

    # Rec 2: cash usage
    cash_pct = df[df['payment_method'] == 'Cash']['amount'].sum() / df['amount'].sum() * 100
    if cash_pct > 30:
        st.markdown(
            f"💡 **Go Digital:** {cash_pct:.0f}% of spend is Cash — switching to UPI/Card "
            "gives full transaction history and potential cashback."
        )

    # Rec 3: weekend vs weekday
    df['is_weekend'] = df['date'].dt.dayofweek >= 5
    wknd_avg  = df[df['is_weekend']]['amount'].mean()
    wkday_avg = df[~df['is_weekend']]['amount'].mean()
    if pd.notna(wknd_avg) and pd.notna(wkday_avg) and wknd_avg > wkday_avg * 1.3:
        st.markdown(
            f"💡 **Weekend Spending:** Avg weekend txn ({CURRENCY}{wknd_avg:.0f}) is significantly "
            f"higher than weekday ({CURRENCY}{wkday_avg:.0f}). Plan leisure in advance."
        )

    # Rec 4: income-based saving target
    if total_income > 0:
        target_savings = total_income * 0.20
        actual_savings = total_income - total_expense
        if actual_savings < target_savings:
            gap = target_savings - actual_savings
            st.markdown(
                f"💡 **Savings Target:** To save 20% of income ({CURRENCY}{target_savings:,.0f}), "
                f"you need to cut expenses by **{CURRENCY}{gap:,.0f}** more."
            )

    # Rec 5: volatility
    cv = monthly_totals.std() / monthly_totals.mean() * 100 if monthly_totals.mean() > 0 else 0
    if cv > 25:
        st.markdown(
            f"💡 **Irregular Spending:** Monthly spend varies ±{cv:.0f}%. "
            "A monthly envelope budget could smooth this out."
        )

    # ── Month-end forecast ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔮 Month-End Forecast")
    today         = datetime.today()
    days_elapsed  = today.day
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    if days_elapsed > 0 and curr_exp > 0:
        projected    = curr_exp / days_elapsed * days_in_month
        total_budget = sum(budgets.values())
        diff         = projected - total_budget
        col_flag     = "🔴" if diff > 0 else "🟢"
        st.markdown(
            f"{col_flag} Projected month-end spend: **{CURRENCY}{projected:,.0f}** "
            f"(Budget: {CURRENCY}{total_budget:,.0f} | "
            f"{'Over' if diff > 0 else 'Under'} by **{CURRENCY}{abs(diff):,.0f}**)"
        )
        if total_income > 0:
            proj_savings = curr_inc - projected
            proj_sr      = proj_savings / curr_inc * 100 if curr_inc > 0 else 0
            st.markdown(
                f"📊 Projected savings this month: **{CURRENCY}{proj_savings:,.0f}** "
                f"({proj_sr:.1f}% savings rate)"
            )
    else:
        st.info("Add current-month data to see a projection.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 6 – CSV IMPORT
# ──────────────────────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown("### 📤 Import Expenses from CSV")

    st.markdown(
        '<div class="upload-info">'
        '📋 <strong>Only <code>category</code> and <code>amount</code> are truly required.</strong><br>'
        '📅 If your CSV has no <code>date</code> column you can set a default date below.<br>'
        '💳 If your CSV has no <code>payment_method</code> column you can set a default below.<br>'
        '📝 Optional: <code>note</code> — you can also combine two columns (e.g. merchant + description).<br>'
        '🔠 Column names are case-insensitive.'
        '</div>',
        unsafe_allow_html=True,
    )

    sample_rows = pd.DataFrame([
        {'date': '2024-03-15', 'category': 'Food',      'amount': 250,  'payment_method': 'UPI',         'note': 'Lunch'},
        {'date': '2024-03-16', 'category': 'Transport', 'amount': 80,   'payment_method': 'Cash',        'note': 'Auto rickshaw'},
        {'date': '2024-03-17', 'category': 'Shopping',  'amount': 1299, 'payment_method': 'Credit Card', 'note': 'Clothes'},
    ])
    st.download_button(
        "📄 Download CSV Template",
        data=sample_rows.to_csv(index=False).encode('utf-8'),
        file_name="expense_template.csv", mime="text/csv",
    )
    st.markdown("---")

    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            preview_df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"❌ Could not read the file: {e}")
            st.stop()

        st.markdown("#### 👀 Preview (first 10 rows)")
        st.dataframe(preview_df.head(10), use_container_width=True)

        csv_cols_opt = ['(skip)'] + list(preview_df.columns)

        def _auto(field):
            return next((c for c in preview_df.columns if c.strip().lower() == field), '(skip)')

        st.markdown("#### 🔧 Step 1 — Map Your Columns")
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        map_date = mc1.selectbox("`date` *",           csv_cols_opt, index=csv_cols_opt.index(_auto('date')),           key="map_date")
        map_cat  = mc2.selectbox("`category` *",       csv_cols_opt, index=csv_cols_opt.index(_auto('category')),       key="map_cat")
        map_amt  = mc3.selectbox("`amount` *",         csv_cols_opt, index=csv_cols_opt.index(_auto('amount')),         key="map_amt")
        map_pm   = mc4.selectbox("`payment_method` *", csv_cols_opt, index=csv_cols_opt.index(_auto('payment_method')), key="map_pm")
        map_note = mc5.selectbox("`note` (optional)",  csv_cols_opt, index=csv_cols_opt.index(_auto('note')),           key="map_note")

        st.markdown("#### 📝 Step 2 — Build the Note (optional)")
        nb1, nb2, nb3 = st.columns([1, 1, 2])
        note_col_a = nb1.selectbox("First column",  csv_cols_opt, index=csv_cols_opt.index(_auto('merchant')),    key="note_a")
        note_col_b = nb2.selectbox("Second column", csv_cols_opt, index=csv_cols_opt.index(_auto('description')), key="note_b")
        note_sep   = nb3.text_input("Separator", value=" — ", key="note_sep")

        st.markdown("#### ⚙️ Step 3 — Defaults for Missing Columns")
        d1, d2 = st.columns(2)
        default_date = d1.date_input("📅 Default date", value=datetime.today(), key="default_date") if map_date == '(skip)' else None
        default_pm   = d2.selectbox("💳 Default payment method", PAYMENT_METHODS, key="default_pm") if map_pm == '(skip)' else None
        if map_date == '(skip)': d1.info("ℹ️ All rows get this date.")
        if map_pm   == '(skip)': d2.info("ℹ️ All rows get this payment method.")

        if map_amt == '(skip)':
            st.error("❌ `amount` column must be mapped."); st.stop()
        if map_cat == '(skip)':
            st.error("❌ `category` column must be mapped."); st.stop()

        # Category remap
        raw_cats     = preview_df[map_cat].dropna().unique().tolist()
        cat_lower_map = {c.lower(): c for c in CATEGORIES}
        unknown_cats = [c for c in raw_cats if str(c).strip().lower() not in cat_lower_map]
        cat_remap    = {}
        if unknown_cats:
            st.markdown("#### 🗂️ Step 4 — Remap Unknown Categories")
            remap_cols = st.columns(min(len(unknown_cats), 4))
            for i, uc in enumerate(unknown_cats):
                cat_remap[str(uc)] = remap_cols[i % 4].selectbox(f'"{uc}" →', CATEGORIES, key=f"remap_cat_{i}")

        # Payment method remap
        pm_remap = {}
        if map_pm != '(skip)':
            raw_pms = preview_df[map_pm].dropna().unique().tolist()
            unk_pms = [p for p in raw_pms if str(p).strip() not in PAYMENT_METHODS]
            if unk_pms:
                st.markdown("#### 💳 Step 5 — Remap Unknown Payment Methods")
                pm_cols = st.columns(min(len(unk_pms), 4))
                for i, up in enumerate(unk_pms):
                    pm_remap[str(up)] = pm_cols[i % 4].selectbox(f'"{up}" →', PAYMENT_METHODS, key=f"remap_pm_{i}")

        st.markdown("---")
        dupe_check = st.checkbox("🔍 Skip duplicates (date + category + amount)", value=True)
        st.info(f"📊 {len(preview_df)} rows · {len(preview_df.columns)} columns: {', '.join(preview_df.columns.tolist())}")

        if st.button("⬆️ Import into Database", type="primary", use_container_width=True):
            import_df = pd.DataFrame()
            import_df['date']     = preview_df[map_date] if map_date != '(skip)' else str(default_date)
            import_df['category'] = preview_df[map_cat].astype(str).str.strip()
            import_df['amount']   = preview_df[map_amt]
            import_df['payment_method'] = preview_df[map_pm].astype(str).str.strip() if map_pm != '(skip)' else default_pm

            na_mapped = note_col_a != '(skip)'
            nb_mapped = note_col_b != '(skip)'
            if na_mapped or nb_mapped:
                parts = []
                if na_mapped: parts.append(preview_df[note_col_a].fillna('').astype(str).str.strip())
                if nb_mapped: parts.append(preview_df[note_col_b].fillna('').astype(str).str.strip())
                import_df['note'] = parts[0] + note_sep + parts[1] if len(parts) == 2 else parts[0]
            elif map_note != '(skip)':
                import_df['note'] = preview_df[map_note].fillna('').astype(str)
            else:
                import_df['note'] = ''

            if cat_remap: import_df['category'] = import_df['category'].replace(cat_remap)
            if pm_remap:  import_df['payment_method'] = import_df['payment_method'].replace(pm_remap)
            import_df['category'] = import_df['category'].str.lower().map(cat_lower_map).fillna(import_df['category'])

            if dupe_check:
                existing = get_all_expenses_as_df()
                if not existing.empty:
                    existing['_key'] = existing['date'].astype(str) + '|' + existing['category'] + '|' + existing['amount'].astype(str)
                    import_df['_ds'] = pd.to_datetime(import_df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
                    import_df['_key'] = import_df['_ds'].fillna('') + '|' + import_df['category'] + '|' + pd.to_numeric(import_df['amount'], errors='coerce').astype(str)
                    mask_dup = import_df['_key'].isin(existing['_key'])
                    n_dup    = mask_dup.sum()
                    import_df = import_df[~mask_dup].drop(columns=['_key','_ds'], errors='ignore')
                    if n_dup: st.info(f"ℹ️ Skipped {n_dup} duplicate(s).")

            if import_df.empty:
                st.warning("⚠️ No new rows to import.")
            else:
                with st.spinner("Importing…"):
                    n_ins, errs = bulk_insert_expenses(import_df, source='csv_upload')
                for e in errs: st.warning(f"⚠️ {e}")
                if n_ins > 0:
                    st.success(f"✅ Imported **{n_ins}** expense(s)!")
                    st.balloons(); st.rerun()
                else:
                    st.error("❌ No rows imported. Check warnings above.")

    with st.expander("📊 Import History"):
        all_exp = get_all_expenses_as_df()
        if 'source' in all_exp.columns:
            sc = all_exp['source'].value_counts().reset_index()
            sc.columns = ['Source', 'Rows']
            st.dataframe(sc, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Built with Streamlit · SQLite · Plotly  —  Expense Tracker Pro v3.0 · ₹ INR Edition")