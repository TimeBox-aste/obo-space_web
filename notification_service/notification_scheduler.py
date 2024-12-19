import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Dict, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.db.models import Notifications, Statuses
from core.connector.postgresql_connector import PostgreSQLConnector
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NotificationSchedulerService:
    def __init__(self, email_sender, session_factory=None):
        if session_factory is None:
            session_factory = PostgreSQLConnector()
        self.email_sender = email_sender
        self.session_factory = session_factory
        self.scheduled_tasks: Dict[int, Set[asyncio.Task]] = {}  # notification_id -> set of scheduled tasks
        self.retry_delay = 30  # seconds

    async def start(self):
        """Start the notification scheduler service"""
        while True:
            try:
                await self.process_pending_notifications()
                # await self.execute_tasks()
            except Exception as e:
                logger.error(f"Error in notification scheduler: "+("\n".join([
                    "-"*10,
                    str(e),
                    str(traceback.format_exc()),
                    "-"*10,
                ])))
            await asyncio.sleep(10)  # Check for new notifications every 10 seconds

    async def execute_tasks(self):
        logger.info(f"Executing tasks: {self.scheduled_tasks}")
        for notification_id, tasks in self.scheduled_tasks.items():
            # tasks_res = await asyncio.gather(*tasks)
            # logger.info(f"Tasks result: {tasks_res}")
            print("check", sum(task.done() for task in tasks), len(tasks))
            #         task.cancel()
            # self.scheduled_tasks.pop(notification_id)

    async def process_pending_notifications(self):

        async with self.session_factory.get_async_db() as session:
            # async with session_factory as session:
            """Process all pending notifications"""
            # Get pending status ID
            pending_status = await self.get_status_by_name(session, 'pending')

            # Query pending notifications
            query = select(Notifications).where(
                Notifications.id_status_sending == pending_status.id,
                Notifications.attempts < Notifications.max_attempts
            )
            result = await session.execute(query)
            notifications = result.scalars().all()

            for notification in notifications:
                if notification.id not in self.scheduled_tasks:
                    self.scheduled_tasks[notification.id] = set()
                    task = asyncio.create_task(self.process_notification(notification.id))
                    self.scheduled_tasks[notification.id].add(task)

    async def process_notification(self, notification_id: int):
        try:
            async with self.session_factory.get_async_db() as session:
                notification = await session.get(Notifications, notification_id)
                if not notification:
                    return False
                # for b1 in await notification.copy.awaitable_attrs.bs:
                #     print(b1)
                # Run the synchronous email sending in a thread pool
                copy = await notification.awaitable_attrs.copy
                success = await asyncio.to_thread(
                    self.email_sender.send_registration_email,
                    (await copy.awaitable_attrs.user).email,
                    copy.name_file_uuid
                )
                logger.info(f"status of the sending {success=}")
                await (self.handle_success if success else self.handle_failure)(session, notification)
            print("yayaya")
            return success


        except Exception as e:
            logger.error(f"Error processing notification {notification_id}: "+("\n".join([
                    "-"*10,
                    str(e),
                    str(traceback.format_exc()),
                    "-"*10,
                ])))
            async with self.session_factory.get_async_db() as session:
                async with session.begin():
                    notification = await session.get(Notifications, notification_id)
                    if notification:
                        await self.handle_failure(session, notification)
            return False

    async def handle_success(self, session: AsyncSession, notification: Notifications):
        """Handle successful notification sending"""
        success_status = await self.get_status_by_name(session, 'success')
        notification.id_status_sending = success_status.id
        notification.dt_sent = datetime.utcnow()
        await session.commit()
        print(notification.id_status_sending)
        self.cancel_scheduled_tasks(notification.id)
        # Remove explicit commit as it's handled by the transaction context

    async def handle_failure(self, session: AsyncSession, notification: Notifications):
        """Handle failed notification sending"""
        notification.attempts += 1

        await session.commit()
        print(notification.attempts >= notification.max_attempts, notification.attempts, notification.max_attempts)
        if notification.attempts < notification.max_attempts:
            print("ay")
            failed_status = await self.get_status_by_name(session, 'failed')
            notification.id_status_sending = failed_status.id
            self.cancel_scheduled_tasks(notification.id)
        else:
            # Schedule retry
            task = asyncio.create_task(self.schedule_retry(notification.id))
            self.scheduled_tasks[notification.id].add(task)

        await session.commit()

    async def schedule_retry(self, notification_id: int):
        """Schedule a retry for failed notification"""
        await asyncio.sleep(self.retry_delay)
        task = asyncio.create_task(self.process_notification(notification_id))
        self.scheduled_tasks[notification_id].add(task)

    def cancel_scheduled_tasks(self, notification_id: int):
        """Cancel all scheduled tasks for a notification"""
        if notification_id in self.scheduled_tasks:
            for task in self.scheduled_tasks[notification_id]:
                if not task.done():
                    task.cancel()
            self.scheduled_tasks.pop(notification_id)

    @staticmethod
    async def get_status_by_name(session: AsyncSession, status_name: str) -> Statuses:
        """Get status by name"""
        query = select(Statuses).where(Statuses.name == status_name)
        result = await session.execute(query)
        return result.scalar_one()
