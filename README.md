# Telegram Ads Collector

Automated collection system for Telegram advertising campaign statistics. This tool collects campaign data, statistics, and stores them in PostgreSQL for analysis.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Ads Collector                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │     TelegramAdsCollector              │
        │  - get_campaign_info()                │
        │  - get_campaign_stats()               │
        └──────────────────────────────────────┘
                      │                    │
        ┌─────────────┘                    └─────────────┐
        ▼                                                ▼
┌──────────────┐                              ┌──────────────┐
│  HTML Parser │                              │  CSV Loader  │
│ (Beautiful   │                              │  (Pandas)    │
│  Soup)       │                              │              │
└──────────────┘                              └──────────────┘
        │                                                │
        └──────────────────┬─────────────────────────────┘
                           ▼
        ┌──────────────────────────────────────┐
        │      PostgresManager                 │
        │  - update_campaign_info()            │
        │  - save_campaign_stats()            │
        │  - get_active_campaigns()            │
        └──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │      PostgreSQL Database              │
        │  Schema: ads                         │
        │  - campaigns                         │
        │  - views_stats                       │
        │  - budget_stats                      │
        └──────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                     ▼
┌──────────────┐                    ┌──────────────┐
│  main.py     │                    │ collect_stats│
│  (Scheduler) │                    │  (Manual)    │
└──────────────┘                    └──────────────┘
```

## Components

### 1. `telegram_ads_collector.py`
Main collector class that:
- Scrapes campaign information from Telegram Ads pages
- Extracts CSV download links from JavaScript
- Downloads and parses campaign statistics

### 2. `postgres_manager.py`
Database manager that:
- Creates and manages database schema (`ads`)
- Stores campaign metadata in `campaigns` table
- Stores statistics in `views_stats` and `budget_stats` tables

### 3. `collect_stats.py`
Main collection script that:
- Loads configuration from environment variables
- If `CAMPAIGN_IDS` is empty, collects data for all campaigns from database
- If `CAMPAIGN_IDS` is specified, collects data only for those campaigns

### 4. `main.py`
Scheduler that runs collection daily at midnight (00:00)

### 5. `utils/` folder
Utility scripts for manual operations:
- `collect_from_link.py`: Collect HTML content from a single Telegram Ads URL
- `manual_get_data.py`: Manual data collection script
- `test_connection.py`: Test database connection

### 6. `streamlit/` folder
Interactive web dashboard:
- `app.py`: Streamlit application for data visualization
- View campaigns, views stats, and budget stats
- Filter, sort, and export data

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_DB=your_database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
# OR use full URL:
# POSTGRES_URL=postgresql://user:password@host:port/database
```

## Usage

### Manual Collection
```bash
python collect_stats.py
```

### Scheduled Collection (via main.py)
```bash
python main.py
```

### Collect Single Campaign HTML
```bash
python utils/collect_from_link.py
```

### Test Database Connection
```bash
python utils/test_connection.py
```

### View Dashboard
```bash
# Option 1: Using run script
./streamlit/run.sh

# Option 2: Using venv directly
source venv/bin/activate
streamlit run streamlit/app.py

# Option 3: Using venv python
venv/bin/streamlit run streamlit/app.py
```
The dashboard will open at `http://localhost:8501`

## Database Schema

### `ads.campaigns`
- `campaign_id` (PK): Campaign identifier (from share stats URL)
- `title`: Campaign title (from ad preview)
- `description`: Campaign description (from ad preview)
- `bot_link`: Link to Telegram bot
- `target_channel`: Target channels list (without "Will be shown in" prefix)
- `first_seen`: First collection timestamp
- `last_seen`: Last collection timestamp
- `is_active`: Active status
- `last_status`: Last known status
- `cpm`: Cost per mille (CPM)
- `views`: Total views count

### `ads.views_stats`
- `id` (PK): Auto-increment ID
- `campaign_id`: Campaign identifier
- `collected_at`: Collection timestamp
- `date`: Statistics date
- `Views`: Number of views
- `Clicks`: Number of clicks
- `Started bot`: Number of bot starts

### `ads.budget_stats`
- `id` (PK): Auto-increment ID
- `campaign_id`: Campaign identifier
- `collected_at`: Collection timestamp
- `date`: Statistics date
- `spent_budget`: Budget spent in TON (from CSV, handles conflicts by keeping larger value)

## Configuration

### Campaign IDs

Campaign IDs must be manually obtained from Telegram Ads platform. They are configured in `collect_stats.py`.

**How to get a Campaign ID:**

1. Go to your Telegram Ads campaign (e.g., `mydietarybot-lifestyle`)
2. Click on **Statistics**
3. Click on **Share Stats** button
4. Copy the Campaign ID from the URL
   - Example: `https://ads.telegram.org/stats/T7joQFHQxN7zs7Az`
   - Campaign ID: `T7joQFHQxN7zs7Az`

**Configuration:**

Add campaign IDs to `collect_stats.py`:
```python
CAMPAIGN_IDS = [
    "T7joQFHQxN7zs7Az",
    "X7JRhMZxu2IPuwZd",
    # ... more campaign IDs
]
```

**Important Notes:**
- Campaign IDs cannot be automatically discovered - they must be manually obtained
- Each campaign ID is unique and can only be accessed if you have the share link
- The system will collect data for all campaigns specified in `CAMPAIGN_IDS`
- New campaigns are automatically added to the database when first encountered

### Database Configuration

Edit `.env` file with your PostgreSQL credentials:
```bash
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_DB=your_database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

Or use full connection URL:
```bash
POSTGRES_URL=postgresql://user:password@host:port/database
```

### What to Change and Where

- **Campaign IDs**: Edit `CAMPAIGN_IDS` in `collect_stats.py` (line ~44)
- **Database connection**: Edit `.env` file
- **Collection schedule**: Edit `main.py` cron schedule (line ~22, default: daily at 00:00)
- **Logging**: Logs are written to `main.log` (configured in `main.py` and `logger_decorator.py`)

## Logging

All functions use the `@log_function` decorator for automatic logging. Logs are written to `main.log`.

## Systemd Integration

The project includes systemd service and timer files:
- `telegram-ads-collector.service`: Service definition
- `telegram-ads-collector.timer`: Timer for daily execution

## License

Open source - ready for publication

