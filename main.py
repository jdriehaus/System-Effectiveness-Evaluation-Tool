import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
from datetime import datetime
import io

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect('evaluations.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            system TEXT,
            department TEXT,
            usability INTEGER,
            integration INTEGER,
            support INTEGER,
            customization INTEGER,
            comments TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_evaluation(system, department, usability, integration, support, customization, comments):
    conn = sqlite3.connect('evaluations.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO evaluations (timestamp, system, department, usability, integration, support, customization, comments)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datetime.now().isoformat(), system, department, usability, integration, support, customization, comments))
    conn.commit()
    conn.close()

def get_filtered_data(system_filter=None, dept_filter=None, days_filter=None):
    conn = sqlite3.connect('evaluations.db')
    df = pd.read_sql_query('SELECT * FROM evaluations', conn, parse_dates=["timestamp"])
    conn.close()

    if system_filter and system_filter != "All":
        df = df[df['system'] == system_filter]

    if dept_filter and dept_filter != "All":
        df = df[df['department'] == dept_filter]

    if days_filter:
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days_filter)
        df = df[df['timestamp'] >= cutoff]

    return df

# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="System Effectiveness Evaluation Tool", layout="wide")
init_db()

st.title("System Effectiveness Evaluation Tool")

# Tabs
tab1, tab2 = st.tabs(["Submit Evaluation", "Dashboard"])

# ---------- TAB 1: Evaluation Form ----------
with tab1:
    st.header("Submit a New Evaluation")

    with st.form("evaluation_form"):
        col1, col2 = st.columns(2)
        with col1:
            system = st.selectbox("Select System", ["Nulogy", "NetSuite", "UKG", "Workato"])
        with col2:
            department = st.selectbox("Department", ["Operations", "IT", "Finance", "HR", "Planning", "All"])

        usability = st.slider("Usability (1-10)", 1, 10, 5)
        integration = st.slider("Integration (1-10)", 1, 10, 5)
        support = st.slider("Support Quality (1-10)", 1, 10, 5)
        customization = st.slider("Customizability (1-10)", 1, 10, 5)

        comments = st.text_area("Additional Comments", "", height=100)
        submitted = st.form_submit_button("Submit Evaluation")

        if submitted:
            insert_evaluation(system, department, usability, integration, support, customization, comments)
            st.success("Your evaluation has been submitted!")

# ---------- TAB 2: Dashboard ----------
with tab2:
    st.header("System Evaluation Dashboard")

    st.subheader("Filter Options")
    col1, col2, col3 = st.columns(3)
    with col1:
        system_filter = st.selectbox("Filter by System", ["All", "Nulogy", "NetSuite", "UKG", "Workato"])
    with col2:
        dept_filter = st.selectbox("Filter by Department", ["All", "Operations", "IT", "Finance", "HR", "Planning"])
    with col3:
        days_filter = st.selectbox("Timeframe", ["All time", "Last 7 days", "Last 30 days", "Last 90 days"])
        days_map = {"All time": None, "Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
        days_filter_value = days_map[days_filter]

    filtered_df = get_filtered_data(system_filter, dept_filter, days_filter_value)

    st.subheader("Average Scores")
    if not filtered_df.empty:
        avg_df = filtered_df.groupby('system').agg({
            'usability': 'mean',
            'integration': 'mean',
            'support': 'mean',
            'customization': 'mean'
        }).round(2).reset_index()

        st.dataframe(avg_df)

        # Vertical Bar Chart (Altair)
        melted_df = avg_df.melt(id_vars='system', var_name='KPI', value_name='Score')
        bar_chart = alt.Chart(melted_df).mark_bar().encode(
        x=alt.X('system:N', title="System", axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Score:Q', title="Average Score"),
        color=alt.Color('KPI:N', legend=alt.Legend(title="KPI")),
        tooltip=['system:N', 'KPI:N', 'Score:Q']
        ).properties(
        width=500,
        height=400,
        title="Average KPI Scores by System"
        )
    
        st.altair_chart(bar_chart, use_container_width=True)

    else:
        st.warning("No data to display for selected filters.")

    st.subheader("Recent Feedback")
    if not filtered_df.empty:
        st.dataframe(filtered_df.sort_values('timestamp', ascending=False).head(10)[[
            'timestamp', 'system', 'department', 'usability', 'integration', 'support', 'customization', 'comments'
        ]])
    else:
        st.info("No recent submissions found.")

    # ---------- Export Section ----------
    '''
    st.subheader("Export Evaluations")

    export_format = st.radio("Select Export Format", ["Excel", "CSV"], horizontal=True)

    if export_format == "Excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Evaluations')
        st.download_button("Download Excel File", data=output.getvalue(), file_name="evaluations.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        csv = filtered_df.to_csv(index=False)
        st.download_button("Download CSV File", data=csv, file_name="evaluations.csv", mime="text/csv")
    '''
    # ---------- KPI Trends ----------
    st.subheader("KPI Trends Over Time")

    kpi_to_chart = st.selectbox("Select KPI to view trend", ["usability", "integration", "support", "customization"])
    if not filtered_df.empty:
        trend_df = filtered_df[['timestamp', 'system', kpi_to_chart]]
        trend_chart = alt.Chart(trend_df).mark_line(point=True).encode(
            x='timestamp:T',
            y=alt.Y(f'{kpi_to_chart}:Q', title=kpi_to_chart.capitalize()),
            color='system:N'
        ).properties(height=400)

        st.altair_chart(trend_chart, use_container_width=True)
    else:
        st.info("Not enough data to show trend.")
