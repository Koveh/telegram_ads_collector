# Streamlit Dashboard

Interactive web dashboard for visualizing Telegram Ads Collector data.

## Features

- **Campaigns Overview**: View all campaigns with metadata
- **Views Statistics**: Analyze views, clicks, and bot starts
- **Budget Statistics**: Track spending data
- **Filters**: Filter by campaigns, date range, and row limits
- **Sorting**: Sort by any column
- **Column Selection**: Choose which columns to display
- **Export**: Download filtered data as CSV

## Usage

### Run Dashboard

```bash
streamlit run streamlit/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Configuration

The dashboard uses the same `.env` file as the main application for database connection.

### Features

1. **Sidebar Filters**:
   - Select specific campaigns (or leave empty for all)
   - Choose number of rows to display (100, 500, 1000, 5000, 10000, or All)
   - Filter by date range

2. **Three Main Tabs**:
   - **Campaigns**: Overview of all campaigns
   - **Views Stats**: Detailed views/clicks statistics
   - **Budget Stats**: Budget spending data

3. **Interactive Features**:
   - Column selection for each table
   - Sorting by any column (ascending/descending)
   - CSV export for filtered data
   - Summary metrics for each table

## Requirements

Install Streamlit:
```bash
pip install streamlit
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

