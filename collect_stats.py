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

# Optional: Specify campaign IDs to track (leave empty to get all from database)
CAMPAIGN_IDS: List[str] = []

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
    If CAMPAIGN_IDS is empty, collects data for all campaigns from database.
    """
    try:
        # Initialize collector and database manager
        postgres_config = get_postgres_config()
        collector = TelegramAdsCollector()
        db_manager = PostgresManager(postgres_config)
        
        # Determine which campaigns to process
        if CAMPAIGN_IDS:
            # Use specified campaign IDs
            campaigns_to_process = CAMPAIGN_IDS
            logger.info(f"Processing {len(campaigns_to_process)} specified campaigns")
        else:
            # Get all campaigns from database
            campaigns_to_process = db_manager.get_all_campaigns()
            if not campaigns_to_process:
                logger.warning("No campaigns found in database. Add campaigns manually first.")
                return
            logger.info(f"Processing {len(campaigns_to_process)} campaigns from database")
        
        # Collect data
        collect_campaign_data(collector, db_manager, campaigns_to_process)
        
        logger.info("Data collection completed successfully")
        
    except Exception as e:
        logger.error(f"Critical error during data collection: {str(e)}")
        raise