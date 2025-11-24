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
    Получает весь HTML-контент страницы Telegram Ads.
    
    Args:
        url (str): URL страницы Telegram Ads
        
    Returns:
        dict: Словарь с HTML-контентом и метаданными
    """
    try:
        # Добавляем headers для имитации браузера
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Отправляем GET запрос
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Создаем объект BeautifulSoup для форматированного вывода
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Собираем данные
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
        logger.error(f"Ошибка при получении страницы: {str(e)}")
        return None

if __name__ == "__main__":
    url = "https://ads.telegram.org/stats/yB38m696d4qybz4d"
    page_data = collect_telegram_ads_page(url)
    
    if page_data:
        # Выводим основную информацию
        print(f"Статус код: {page_data['status_code']}")
        print(f"Время сбора: {page_data['collected_at']}")
        print("\nЗаголовки ответа:")
        print(json.dumps(page_data['headers'], indent=2, ensure_ascii=False))
        print("\nHTML контент:")
        print(page_data['html_content'])
