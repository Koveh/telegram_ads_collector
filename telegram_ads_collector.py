"""
Module for collecting data from Telegram Ads.
Includes functionality for collecting HTML data and CSV statistics files.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, Optional, Union
import json
from logger_decorator import log_function

logger = logging.getLogger(__name__)

class TelegramAdsCollector:
    """Class for collecting data from Telegram Ads."""
    
    BASE_URL = "https://ads.telegram.org"
    
    def __init__(self):
        """Initialize collector."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    @log_function
    def get_campaign_info(self, campaign_id: str) -> Optional[Dict[str, Union[str, int, float, None]]]:
        """
        Collects information about an advertising campaign from HTML page.
        
        Args:
            campaign_id: Campaign identifier from URL
            
        Returns:
            Dictionary with campaign information
        """
        url = f"{self.BASE_URL}/stats/{campaign_id}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main data
            # Get title from ad preview
            title_elem = soup.find('div', {'class': 'ad-msg-link-preview-title'})
            title = title_elem.text.strip() if title_elem else None
            
            # Get description from ad preview
            desc_elem = soup.find('div', {'class': 'ad-msg-link-preview-desc'})
            description = desc_elem.text.strip() if desc_elem else None
            
            # Get bot link
            bot_link = self._safe_extract_href(soup, 'a', {'href': lambda x: x and 't.me' in x})
            
            # Get status, CPM, Views
            status = self._safe_extract(soup, text='Status', next_sibling=True)
            cpm = self._safe_extract(soup, text='CPM', next_sibling=True)
            views = self._safe_extract(soup, text='Views', next_sibling=True)
            
            # Get target channels and remove "Will be shown in" prefix
            target_channel_elem = soup.find('div', {'class': 'pr-form-info-block plus'})
            target_channel = None
            if target_channel_elem:
                target_channel = target_channel_elem.text.strip()
                # Remove "Will be shown in" prefix if present
                if target_channel.startswith('Will be shown in '):
                    target_channel = target_channel.replace('Will be shown in ', '', 1)
            
            data = {
                'campaign_id': campaign_id,
                'title': title,
                'description': description,
                'bot_link': bot_link,
                'status': status,
                'cpm': cpm,
                'views': views,
                'target_channel': target_channel,
                'collected_at': datetime.utcnow().isoformat(),
                'is_active': self._check_if_active(soup)
            }
            
            # Get CSV links
            data.update(self._extract_csv_links(soup))
            
            return data
            
        except Exception as e:
            logger.error(f"Error collecting campaign data {campaign_id}: {str(e)}")
            return None

    @log_function
    def get_campaign_stats(self, campaign_id: str, period: str = 'day') -> Optional[pd.DataFrame]:
        """
        Загружает статистику кампании в формате CSV.
        
        Args:
            campaign_id (str): Идентификатор кампании
            period (str): Период статистики ('day' или '5min')
            
        Returns:
            pd.DataFrame: DataFrame с данными статистики
        """
        try:
            # Сначала получаем информацию о кампании для извлечения ссылок на CSV
            campaign_info = self.get_campaign_info(campaign_id)
            if not campaign_info:
                return None

            stats_data = []

            logger.info(f"Данные компании - {campaign_info}")
            
            # Загружаем статистику просмотров/кликов
            if campaign_info.get('views_csv_link'):
                logger.info(f"Ссылка до ошибки - {self.BASE_URL}{campaign_info['views_csv_link']}")
                # views_df = pd.read_csv(f"{self.BASE_URL}{campaign_info['views_csv_link'].replace('\\/', '/', 1)}")
                views_df = pd.read_csv(f"{self.BASE_URL}{campaign_info['views_csv_link'].replace('\\/', '/', 1)}", sep='\t')
                
                stats_data.append(views_df)
            # Загружаем статистику бюджета
            if campaign_info.get('budget_csv_link'):
                logger.info(f"Ссылка до ошибки - {self.BASE_URL}{campaign_info['budget_csv_link']}")
                # budget_df = pd.read_csv(f"{self.BASE_URL}{campaign_info['budget_csv_link'].replace('\\/', '/', 1)}")
                budget_df = pd.read_csv(f"{self.BASE_URL}{campaign_info['budget_csv_link'].replace('\\/', '/', 1)}", sep='\t')
                stats_data.append(budget_df)
            if not stats_data:
                return None
                
            # Объединяем все данные
            result_df = pd.concat(stats_data, axis=1)
            result_df['campaign_id'] = campaign_id
            result_df['collected_at'] = datetime.utcnow().isoformat()

            
            logger.info(f"Статистика для кампании {campaign_id} успешно загружена - {result_df.columns}")
            return result_df
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке CSV для кампании {campaign_id}: {str(e)}")
            return None

    def _safe_extract(self, soup: BeautifulSoup, tag: str = None, attrs: dict = None, text: str = None, next_sibling: bool = False) -> Optional[str]:
        """Safely extract text from HTML."""
        try:
            if text:
                element = soup.find(text=text)
                return element.find_next().text.strip() if element and next_sibling else element.text.strip()
            element = soup.find(tag, attrs)
            return element.text.strip() if element else None
        except Exception:
            return None

    def _safe_extract_href(self, soup: BeautifulSoup, tag: str, attrs: dict) -> Optional[str]:
        """Safely extract link from HTML."""
        try:
            element = soup.find(tag, attrs)
            return element['href'] if element else None
        except Exception:
            return None

    def _check_if_active(self, soup: BeautifulSoup) -> bool:
        """Checks if campaign is active."""
        try:
            status = self._safe_extract(soup, text='Status', next_sibling=True)
            return status.lower() != 'on hold' if status else False
        except Exception:
            return False

    def _extract_csv_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extracts CSV file links from HTML."""
        try:
            # Find all scripts on the page
            scripts = soup.find_all('script')
            csv_links = {}
            
            for script in scripts:
                if script.string and 'csvExport' in script.string:
                    # Extract CSV links from JavaScript
                    if 'budget' in script.string:
                        csv_links['budget_csv_link'] = script.string.split('csvExport":"')[1].split('"')[0]
                    else:
                        csv_links['views_csv_link'] = script.string.split('csvExport":"')[1].split('"')[0]
            
            return csv_links
        except Exception:
            return {} 