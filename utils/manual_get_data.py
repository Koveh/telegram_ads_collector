#!/usr/bin/env python3
"""
Manual script to get campaign data for testing.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_ads_collector import TelegramAdsCollector

campaign_id = "yB38m696d4qybz4d"
collector = TelegramAdsCollector()
campaign_info = collector.get_campaign_info(campaign_id)

print(campaign_info)