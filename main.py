import logging
from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep
from collect_stats import collect_stats
from logger_decorator import log_function

logging.basicConfig(
    level=logging.INFO,
    filename="main.log",
    filemode="a",
    format="%(asctime)s %(levelname)s %(message)s"
)

scheduler = BackgroundScheduler()

@log_function
def main() -> None:
    """Main data collection function."""
    scheduler.add_job(
        collect_stats,
        trigger='cron',
        hour=0,
        minute=0
    )

    scheduler.start()

    logging.info("Scheduler started. Data collection runs daily at 00:00.")
    
    try:
        while True:
            sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Scheduler stopped.")

if __name__ == "__main__":
    main() 