import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import Dict, Optional
from logger_decorator import log_function

@log_function
def collect_telegram_ads_page(url: str) -> Optional[Dict]:
    """
    Gets full HTML content from Telegram Ads page.
    
    Args:
        url: Telegram Ads page URL
        
    Returns:
        Dictionary with HTML content and metadata
    """
    try:
        # Add headers to mimic browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Send GET request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Create BeautifulSoup object for formatted output
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Collect data
        data = {
            'html_content': soup.prettify(),
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'collected_at': datetime.utcnow().isoformat(),
            'source_url': url
        }
        
        return data
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting page: {str(e)}")
        return None

if __name__ == "__main__":
    url = "https://ads.telegram.org/stats/yB38m696d4qybz4d"
    page_data = collect_telegram_ads_page(url)
    
    if page_data:
        # Print main information
        print(f"Status code: {page_data['status_code']}")
        print(f"Collection time: {page_data['collected_at']}")
        print("\nResponse headers:")
        print(json.dumps(page_data['headers'], indent=2, ensure_ascii=False))
        print("\nHTML content:")
        print(page_data['html_content'])
