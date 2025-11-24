#!/usr/bin/env python3
"""
Script for collecting Telegram advertising campaign statistics.
Can be run via systemd timer for daily data collection.
"""
import os
import logging
from dotenv import load_dotenv
from telegram_ads_collector import TelegramAdsCollector
from postgres_manager import PostgresManager
from typing import List, Dict, Optional
from logger_decorator import log_function

load_dotenv()

logger = logging.getLogger(__name__)

def get_postgres_config() -> Dict[str, str]:
    """
    Gets PostgreSQL configuration from environment variables.
    
    Returns:
        Dictionary with database connection parameters
    """
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "dietary_bot")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        postgres_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    return {
        "host": host,
        "port": int(port),
        "database": database,
        "user": user,
        "password": password,
        "link": postgres_url
    }

# Campaign IDs must be manually obtained from Telegram Ads platform
# See README.md for instructions on how to get campaign IDs
CAMPAIGN_IDS: List[str] = [
    # Add your campaign IDs here, e.g.:
    # "T7joQFHQxN7zs7Az",
    # "X7JRhMZxu2IPuwZd",
]

@log_function
def collect_campaign_data(collector: TelegramAdsCollector, 
                         db_manager: PostgresManager,
                         campaign_ids: List[str]) -> None:
    """
    Collects data for a list of advertising campaigns.
    
    Args:
        collector: TelegramAdsCollector instance
        db_manager: PostgresManager instance
        campaign_ids: List of campaign identifiers
    """
    for campaign_id in campaign_ids:
        try:
            # Get campaign information
            campaign_info = collector.get_campaign_info(campaign_id)
            if not campaign_info:
                logger.error(f"Failed to get info for campaign {campaign_id}")
                continue
                
            # Update campaign info in database
            db_manager.update_campaign_info(campaign_info)
            
            # Get statistics
            stats_df = collector.get_campaign_stats(campaign_id, period='day')
            if stats_df is not None:
                db_manager.save_campaign_stats(campaign_id, stats_df)
            else:
                logger.warning(f"No statistics available for campaign {campaign_id}")
                
        except Exception as e:
            logger.error(f"Error processing campaign {campaign_id}: {str(e)}")

@log_function
def collect_stats() -> None:
    """
    Main function for collecting advertising campaign statistics.
    Campaign IDs must be manually specified in CAMPAIGN_IDS list.
    """
    try:
        # Check if campaign IDs are specified
        if not CAMPAIGN_IDS:
            logger.warning("No campaign IDs specified. Please add campaign IDs to CAMPAIGN_IDS list in collect_stats.py")
            logger.info("See README.md for instructions on how to obtain campaign IDs")
            return
        
        # Initialize collector and database manager
        postgres_config = get_postgres_config()
        collector = TelegramAdsCollector()
        db_manager = PostgresManager(postgres_config)
        
        logger.info(f"Processing {len(CAMPAIGN_IDS)} specified campaigns")
        
        # Collect data
        collect_campaign_data(collector, db_manager, CAMPAIGN_IDS)
        
        logger.info("Data collection completed successfully")
        
    except Exception as e:
        logger.error(f"Critical error during data collection: {str(e)}")
        raise