import datetime
import json
import logging
from abc import ABC
from agentx.handler.base import BaseHandler
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from agentx.handler.google.exceptions import AuthException

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]


class CalenderHandler(BaseHandler, ABC):
    def __init__(
            self,
            *,
            credentials: dict
    ):
        self.creds = None
        logger.info(f'Google client initialization')
        self.credentials = credentials or {}
        self.service = self._connect()

    def _connect(self):
        try:
            if not self.creds or not self.creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials, SCOPES)
                self.creds = flow.run_local_server(port=0)
            logger.info(self.creds)
            service = build("calendar", "v3", credentials=self.creds)
            logger.info("Authenticate Success")
            return service
        except Exception as ex:
            message = f'Google Sheets Handler Authentication Problem {ex}'
            logger.error(message, exc_info=ex)
            raise AuthException(message)

    async def get_today_events(self):
        today_events = await self.get_events_by_days(days=1)
        logger.info(today_events)
        return today_events

    async def get_week_events(self):
        week_events = await self.get_events_by_days(days=7)
        logger.info(week_events)
        return week_events

    async def get_month_events(self):
        month_events = await self.get_events_by_days(days=30)
        logger.info(month_events)
        return month_events

    async def get_events_by_days(
            self,
            days: int | None = 1
    ):
        try:
            if days > 30:
                message = f"Events are only being retrieved within the range of 1 to 30"
                logger.error(message, exc_info=message)
                raise Exception(message)
            else:
                today = datetime.datetime.today()
                startDate = (datetime.datetime(today.year, today.month, today.day, 00, 00)).isoformat() + 'Z'
                tomorrow = today + datetime.timedelta(days=days)
                endDate = (datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 00, 00)).isoformat() + 'Z'
                events_results = self.service.events().list(
                    calendarId='primary',
                    timeMin=startDate,
                    timeMax=endDate,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                parsed_events = json.dumps(events_results)
                return parsed_events
        except Exception as ex:
            message = f"Error while Getting Profile"
            logger.error(message, exc_info=ex)
            raise

    def get_events_by_type(
            self,
            *,
            eventType: str | None = "birthday"
    ):
        try:
            if eventType:
                events_results = self.service.events().list(
                    calendarId='primary',
                    eventTypes=eventType,
                ).execute()
                parsed_events = json.dumps(events_results)
                logger.info(parsed_events)
                return parsed_events
        except Exception as ex:
            message = f"Error while Getting Event"
            logger.error(message, exc_info=ex)
            raise

    def __dir__(self):
        return (
            'get_today_events',
            'get_week_events',
            'get_month_events',
            'get_events_by_type'
        )
