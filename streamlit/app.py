"""
Streamlit dashboard for Telegram Ads Collector data visualization.
"""
import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collect_stats import get_postgres_config

load_dotenv()

st.set_page_config(
    page_title="Telegram Ads Collector Dashboard",
    page_icon="📊",
    layout="wide"
)

def get_db_manager():
    """Get database manager instance."""
    postgres_config = get_postgres_config()
    return PostgresManager(postgres_config)

@st.cache_data(ttl=60)
def load_campaigns() -> pd.DataFrame:
    """Load campaigns data."""
    try:
        postgres_config = get_postgres_config()
        engine = create_engine(postgres_config['link'])
        with engine.connect() as connection:
            df = pd.read_sql(
                "SELECT * FROM ads.campaigns ORDER BY last_seen DESC",
                connection
            )
        return df
    except Exception as e:
        st.error(f"Error loading campaigns: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_views_stats(campaign_ids: list = None, limit: int = None) -> pd.DataFrame:
    """Load views statistics."""
    try:
        postgres_config = get_postgres_config()
        engine = create_engine(postgres_config['link'])
        query = "SELECT * FROM ads.views_stats"
        if campaign_ids:
            placeholders = ','.join([f"'{cid}'" for cid in campaign_ids])
            query += f" WHERE campaign_id IN ({placeholders})"
        query += " ORDER BY collected_at DESC, date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        return df
    except Exception as e:
        st.error(f"Error loading views stats: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_budget_stats(campaign_ids: list = None, limit: int = None) -> pd.DataFrame:
    """Load budget statistics."""
    try:
        postgres_config = get_postgres_config()
        engine = create_engine(postgres_config['link'])
        query = "SELECT * FROM ads.budget_stats"
        if campaign_ids:
            placeholders = ','.join([f"'{cid}'" for cid in campaign_ids])
            query += f" WHERE campaign_id IN ({placeholders})"
        query += " ORDER BY collected_at DESC, date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        return df
    except Exception as e:
        st.error(f"Error loading budget stats: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("📊 Telegram Ads Collector Dashboard")
    st.markdown("Visualize and explore collected advertising campaign data")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Load campaigns for filter
    campaigns_df = load_campaigns()
    
    if campaigns_df.empty:
        st.warning("No campaigns found in database. Run collection first.")
        return
    
    # Campaign filter
    campaign_options = campaigns_df['campaign_id'].tolist()
    selected_campaigns = st.sidebar.multiselect(
        "Select Campaigns",
        options=campaign_options,
        default=[],
        help="Select campaigns to filter data. Leave empty to show all."
    )
    
    # Row limit filter
    row_limit_options = [100, 500, 1000, 5000, 10000, None]
    row_limit_labels = ["100", "500", "1000", "5000", "10000", "All"]
    selected_limit_idx = st.sidebar.selectbox(
        "Number of Rows",
        options=range(len(row_limit_options)),
        format_func=lambda x: row_limit_labels[x],
        index=2
    )
    row_limit = row_limit_options[selected_limit_idx]
    
    # Date range filter
    st.sidebar.subheader("Date Range")
    use_date_filter = st.sidebar.checkbox("Filter by Date", value=False)
    date_range = None
    if use_date_filter:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now().date())
        if start_date <= end_date:
            date_range = (start_date, end_date)
        else:
            st.sidebar.error("Start date must be before end date")
    
    # Tabs for different tables
    tab1, tab2, tab3 = st.tabs(["📋 Campaigns", "👁️ Views Stats", "💰 Budget Stats"])
    
    # Tab 1: Campaigns
    with tab1:
        st.header("Campaigns Overview")
        
        if not campaigns_df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Campaigns", len(campaigns_df))
            with col2:
                active_count = campaigns_df['is_active'].sum() if 'is_active' in campaigns_df.columns else 0
                st.metric("Active Campaigns", int(active_count))
            with col3:
                inactive_count = len(campaigns_df) - active_count
                st.metric("Inactive Campaigns", inactive_count)
            with col4:
                if 'last_seen' in campaigns_df.columns:
                    latest = pd.to_datetime(campaigns_df['last_seen']).max()
                    st.metric("Latest Update", latest.strftime("%Y-%m-%d") if pd.notna(latest) else "N/A")
            
            # Filter campaigns if selected
            display_df = campaigns_df.copy()
            if selected_campaigns:
                display_df = display_df[display_df['campaign_id'].isin(selected_campaigns)]
            
            # Column selection
            st.subheader("Data Table")
            all_columns = display_df.columns.tolist()
            selected_columns = st.multiselect(
                "Select Columns to Display",
                options=all_columns,
                default=all_columns[:min(8, len(all_columns))],
                key="campaigns_columns"
            )
            
            if selected_columns:
                display_df = display_df[selected_columns]
            
            # Sorting
            if len(display_df) > 0:
                sort_column = st.selectbox(
                    "Sort By",
                    options=display_df.columns.tolist(),
                    index=0 if 'last_seen' in display_df.columns else 0,
                    key="campaigns_sort"
                )
                sort_ascending = st.checkbox("Ascending", value=False, key="campaigns_asc")
                display_df = display_df.sort_values(by=sort_column, ascending=sort_ascending)
            
            # Display table
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"campaigns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No campaigns data available")
    
    # Tab 2: Views Stats
    with tab2:
        st.header("Views Statistics")
        
        views_df = load_views_stats(
            campaign_ids=selected_campaigns if selected_campaigns else None,
            limit=row_limit
        )
        
        if not views_df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(views_df))
            with col2:
                total_views = views_df['Views'].sum() if 'Views' in views_df.columns else 0
                st.metric("Total Views", f"{int(total_views):,}")
            with col3:
                total_clicks = views_df['Clicks'].sum() if 'Clicks' in views_df.columns else 0
                st.metric("Total Clicks", f"{int(total_clicks):,}")
            with col4:
                total_bot_starts = views_df['Started bot'].sum() if 'Started bot' in views_df.columns else 0
                st.metric("Bot Starts", f"{int(total_bot_starts):,}")
            
            # Date filter
            if use_date_filter and date_range and 'date' in views_df.columns:
                views_df['date'] = pd.to_datetime(views_df['date'])
                views_df = views_df[
                    (views_df['date'].dt.date >= date_range[0]) &
                    (views_df['date'].dt.date <= date_range[1])
                ]
            
            # Column selection
            st.subheader("Data Table")
            all_columns = views_df.columns.tolist()
            selected_columns = st.multiselect(
                "Select Columns to Display",
                options=all_columns,
                default=all_columns[:min(8, len(all_columns))],
                key="views_columns"
            )
            
            if selected_columns:
                display_df = views_df[selected_columns].copy()
            else:
                display_df = views_df.copy()
            
            # Sorting
            if len(display_df) > 0:
                sort_column = st.selectbox(
                    "Sort By",
                    options=display_df.columns.tolist(),
                    index=0 if 'collected_at' in display_df.columns else 0,
                    key="views_sort"
                )
                sort_ascending = st.checkbox("Ascending", value=False, key="views_asc")
                display_df = display_df.sort_values(by=sort_column, ascending=sort_ascending)
            
            # Display table
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"views_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No views statistics data available")
    
    # Tab 3: Budget Stats
    with tab3:
        st.header("Budget Statistics")
        
        budget_df = load_budget_stats(
            campaign_ids=selected_campaigns if selected_campaigns else None,
            limit=row_limit
        )
        
        if not budget_df.empty:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", len(budget_df))
            with col2:
                if 'spent_budget' in budget_df.columns:
                    total_budget = budget_df['spent_budget'].sum()
                    st.metric("Total Spent Budget", f"{total_budget:,.2f}")
                else:
                    st.metric("Total Records", len(budget_df))
            with col3:
                if 'collected_at' in budget_df.columns:
                    latest = pd.to_datetime(budget_df['collected_at']).max()
                    st.metric("Latest Collection", latest.strftime("%Y-%m-%d %H:%M") if pd.notna(latest) else "N/A")
            
            # Date filter
            if use_date_filter and date_range and 'date' in budget_df.columns:
                budget_df['date'] = pd.to_datetime(budget_df['date'])
                budget_df = budget_df[
                    (budget_df['date'].dt.date >= date_range[0]) &
                    (budget_df['date'].dt.date <= date_range[1])
                ]
            
            # Column selection
            st.subheader("Data Table")
            all_columns = budget_df.columns.tolist()
            selected_columns = st.multiselect(
                "Select Columns to Display",
                options=all_columns,
                default=all_columns[:min(8, len(all_columns))],
                key="budget_columns"
            )
            
            if selected_columns:
                display_df = budget_df[selected_columns].copy()
            else:
                display_df = budget_df.copy()
            
            # Sorting
            if len(display_df) > 0:
                sort_column = st.selectbox(
                    "Sort By",
                    options=display_df.columns.tolist(),
                    index=0 if 'collected_at' in display_df.columns else 0,
                    key="budget_sort"
                )
                sort_ascending = st.checkbox("Ascending", value=False, key="budget_asc")
                display_df = display_df.sort_values(by=sort_column, ascending=sort_ascending)
            
            # Display table
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"budget_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No budget statistics data available")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Telegram Ads Collector**")
    st.sidebar.markdown("Data collection dashboard")

if __name__ == "__main__":
    main()

