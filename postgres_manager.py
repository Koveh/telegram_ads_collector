"""
PostgreSQL database manager module.
Includes functionality for creating tables and saving advertising campaign data.
"""

import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, DateTime, Boolean
from datetime import datetime
import logging
from typing import Dict, Optional, List
from logger_decorator import log_function

logger = logging.getLogger(__name__)

class PostgresManager:
    """Class for managing PostgreSQL database operations."""
    
    def __init__(self, connection_params: Dict[str, str]):
        """
        Initialize PostgreSQL manager.
        
        Args:
            connection_params: Database connection parameters
        """
        self.connection_params = connection_params
        self.engine = create_engine(connection_params['link'])
        self.metadata = MetaData(schema='ads')
        
        # Создаем таблицы при инициализации
        self._create_tables()

    @log_function
    def _create_tables(self) -> None:
        """Creates necessary tables in the database if they don't exist."""
        try:
            # Check if schema exists
            with self.engine.connect() as connection:
                schema_exists = connection.execute(
                    text("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'ads')")
                ).scalar()
                
                if not schema_exists:
                    logger.info("Creating 'ads' schema...")
                    connection.execute(text('CREATE SCHEMA ads'))
                    connection.commit()
                else:
                    logger.info("Schema 'ads' already exists")
            
            # Define tables
            self.campaigns_table = Table(
                'campaigns', self.metadata,
                Column('campaign_id', String, primary_key=True),
                Column('title', String),
                Column('description', String),
                Column('bot_link', String),
                Column('target_channel', String),
                Column('first_seen', DateTime),
                Column('last_seen', DateTime),
                Column('is_active', Boolean),
                Column('last_status', String)
            )
            
            self.views_stats_table = Table(
                'views_stats', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('campaign_id', String),
                Column('collected_at', DateTime),
                Column('Views', Integer),
                Column('Clicks', Integer),
                Column('Started bot', Integer),
                Column('date', DateTime)
            )
            
            self.budget_stats_table = Table(
                'budget_stats', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('campaign_id', String),
                Column('collected_at', DateTime),
                Column('spent_budget', Float),
                Column('date', DateTime)
            )
            
            # Create tables if they don't exist
            self.metadata.create_all(self.engine, checkfirst=True)
            logger.info("Tables checked/created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise

    @log_function
    def update_campaign_info(self, campaign_data: Dict) -> None:
        """
        Updates campaign information.
        
        Args:
            campaign_data: Campaign data dictionary
        """
        try:
            current_time = datetime.utcnow()
            
            # Подготавливаем данные
            upsert_data = {
                'campaign_id': campaign_data['campaign_id'],
                'title': campaign_data['title'],
                'description': campaign_data['description'],
                'bot_link': campaign_data['bot_link'],
                'target_channel': campaign_data['target_channel'],
                'last_seen': current_time,
                'is_active': campaign_data['is_active'],
                'last_status': campaign_data['status']
            }
            
            # Проверяем существование записи
            with self.engine.begin() as connection:
                result = connection.execute(
                    text('SELECT campaign_id, first_seen FROM ads.campaigns WHERE campaign_id = :campaign_id'),
                    {'campaign_id': campaign_data['campaign_id']}
                ).fetchone()
                
                if result:
                    # Обновляем существующую запись
                    connection.execute(
                        text('''
                            UPDATE ads.campaigns 
                            SET title = :title, 
                                description = :description,
                                bot_link = :bot_link,
                                target_channel = :target_channel,
                                last_seen = :last_seen,
                                is_active = :is_active,
                                last_status = :last_status
                            WHERE campaign_id = :campaign_id
                        '''),
                        upsert_data
                    )
                else:
                    # Создаем новую запись
                    upsert_data['first_seen'] = current_time
                    connection.execute(
                        text('''
                            INSERT INTO ads.campaigns 
                            (campaign_id, title, description, bot_link, target_channel, 
                             first_seen, last_seen, is_active, last_status)
                            VALUES 
                            (:campaign_id, :title, :description, :bot_link, :target_channel,
                             :first_seen, :last_seen, :is_active, :last_status)
                        '''),
                        upsert_data
                    )
                
                logger.info(f"Campaign info updated: {campaign_data['campaign_id']}")
                
        except Exception as e:
            logger.error(f"Error updating campaign info: {str(e)}")
            raise

    @log_function
    def save_campaign_stats(self, campaign_id: str, stats_df: pd.DataFrame) -> None:
        """
        Saves campaign statistics to database.
        
        Args:
            campaign_id: Campaign identifier
            stats_df: DataFrame with statistics
        """
        try:
            logger.info(f"DataFrame columns: {stats_df.columns}")
            # Разделяем данные на статистику просмотров и бюджета
            # Проверяем наличие колонок перед извлечением
            required_cols = ['date', 'Views', 'Clicks']
            optional_cols = ['Started bot']
            
            available_cols = [col for col in required_cols + optional_cols if col in stats_df.columns]
            views_data = stats_df[available_cols].copy()
            
            # Если колонки нет, создаем с нулевыми значениями
            if 'Started bot' not in views_data.columns:
                views_data['Started bot'] = 0
            
            views_data['campaign_id'] = campaign_id
            views_data['collected_at'] = datetime.utcnow()
            
            # budget_data = stats_df[['date', 'spent_budget']].copy()
            budget_data = stats_df[['date']].copy()
            budget_data['campaign_id'] = campaign_id
            budget_data['collected_at'] = datetime.utcnow()
            
            # Сохраняем данные
            with self.engine.begin() as connection:
                views_data.to_sql('views_stats', connection, schema='ads', 
                                if_exists='append', index=False)
                budget_data.to_sql('budget_stats', connection, schema='ads', 
                                 if_exists='append', index=False)
                
            logger.info(f"Campaign stats saved: {campaign_id}")
            
        except Exception as e:
            logger.error(f"Error saving campaign stats: {str(e)}")
            raise

    @log_function
    def get_active_campaigns(self) -> List[str]:
        """
        Gets list of active campaigns.
        
        Returns:
            List of active campaign identifiers
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    text('SELECT campaign_id FROM ads.campaigns WHERE is_active = true')
                ).fetchall()
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting active campaigns: {str(e)}")
            return []
    
    @log_function
    def get_all_campaigns(self) -> List[str]:
        """
        Gets list of all campaigns from database.
        
        Returns:
            List of all campaign identifiers
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    text('SELECT campaign_id FROM ads.campaigns')
                ).fetchall()
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting all campaigns: {str(e)}")
            return [] 