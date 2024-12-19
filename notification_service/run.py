from consumer import EmailConsumer
from notification_scheduler import NotificationSchedulerService
from settings import RABBITMQ_CONFIG
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    while True:
        try:
            # Initialize and start the email consumer
            consumer = EmailConsumer()
            # consumer.start_consuming()
            async_thread = asyncio.to_thread(consumer.start_consuming)
            task_consumer = asyncio.create_task(async_thread)

            # Initialize and start the notification scheduler
            notification_scheduler = NotificationSchedulerService(consumer.email_sender)
            task_notification_scheduler = asyncio.create_task(notification_scheduler.start())
            res = await asyncio.gather(task_consumer, task_notification_scheduler, return_exceptions=True)
            logger.info(res)
        except Exception as e:
            logger.error(e)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Processor stopped.")