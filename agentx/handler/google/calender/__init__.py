import datetime
import json
import logging
from abc import ABC

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from agentx.handler.base import BaseHandler
from agentx.handler.google.exceptions import AuthException
from agentx.utils.helper import sync_to_async

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
        self.service = None
        self.creds = None
        logger.info(f'Calendar client initialization')
        self.credentials = credentials or {}
        self._service = self._connect()
        
    def _connect(self):
        """
            Establish a connection to the Gmail API.

            This private method initializes the connection to the Gmail API
            by managing the OAuth 2.0 authentication process. It verifies
            whether valid credentials are available; if not, it prompts
            the user to authenticate through a local server flow to obtain
            new credentials.

            Returns:
                googleapiclient.discovery.Resource:
                    A service object for the Gmail API, which can be used to
                    make subsequent API calls.

            Raises:
                AuthException:
                    If an error occurs during the authentication process, an
                    exception is raised with a detailed message about the
                    authentication failure.
        """
        try:
            if not self.creds or not self.creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file=self.credentials,
                    scopes=SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            logger.info("Authenticate Success")
            return build(
                serviceName="calendar",
                version="v3",
                credentials=self.creds
            )
        except Exception as ex:
            message = f'Google Calendar Authentication Problem {ex}'
            logger.error(message, exc_info=ex)
            raise AuthException(message)

    async def get_today_events(self):
        """
            Retrieve events occurring for today events.

            This asynchronous method fetches events scheduled for today
            by calling the `get_events_by_days` method with a parameter of 1 day.

            Returns:
                dict: A dictionary containing the event's  information,
                including fields such as timezone, status, and other
                relevant details for today
            """
        return await self.get_events_by_days(days=1)

    async def get_week_events(self):
        """
            Retrieve events occurring in the upcoming week.

            This asynchronous method fetches events scheduled for the next week
            by calling the `get_events_by_days` method with a parameter of 7 days.

            Returns:
                dict: A dictionary containing information about the events,
                      including fields such as timezone, status, and other
                      relevant details for the week.
            """
        return await self.get_events_by_days(days=7)

    async def get_month_events(self):
        """
            Retrieve events occurring in the upcoming month.

            This asynchronous method fetches events scheduled for the next month
            by calling the `get_events_by_days` method with a parameter of 30 days.

            Returns:
                dict: A dictionary containing information about the events,
                      including fields such as timezone, status, and other
                      relevant details for the month.
            """
        return await self.get_events_by_days(days=30)

    async def get_events_by_days(
            self,
            days: int = 1
    ):
        """
            Retrieve upcoming events from Google Calendar for a specified number of days.

            This asynchronous method fetches events from the user's Google Calendar
            for the next specified number of days. If no value is provided, it defaults
            to 1 day. The method utilizes the Google Calendar API to retrieve events.

            Args:
                days (int): The number of days to retrieve events for.
                                   the method will return events
                                   without day filtering, defaulting to 1 day.

            Returns:
                dict: A dictionary containing the event's  information,
                including fields such as timezone, status, and other
                relevant details.

            Raises:
                ValueError: If the provided days value is negative.
                Exception: If there is an error fetching events from the Google Calendar API.
            """
        try:
            if days > 30 or days < 1:
                message = f"Events are only being retrieved within the range of 1 to 30"
                logger.error(message, exc_info=message)
                raise ValueError(message)
            else:
                today = datetime.datetime.today()
                start_date = (datetime.datetime(today.year, today.month, today.day, 00, 00)).isoformat() + 'Z'
                tomorrow = today + datetime.timedelta(days=days)
                end_date = (datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 00, 00)).isoformat() + 'Z'
                events = await sync_to_async(
                    self._service.events
                )
                events_list = await sync_to_async(
                    events.list,
                    calendarId='primary',
                    timeMin=start_date,
                    timeMax=end_date,
                    singleEvents=True,
                    orderBy='startTime'
                )
                return await sync_to_async(
                    events_list.execute
                )
        except Exception as ex:
            message = f"Error while Getting Events"
            logger.error(message, exc_info=ex)
            raise

    async def get_events_by_type(
            self,
            *,
            event_type: str = "default"
    ):
        """
            Retrieve events of a specified type from the Google calendar API.

            This asynchronous method connects to the Google calendar API to fetch events that match
            the given event type. If no event type is specified, it defaults to
            "birthday". This allows for filtering events based on user preferences.

            Args:
                event_type (str, optional): The type of events to retrieve.
                                            Defaults to "default".
                                            Valid types may include "focusTime",
                                            "workingLocation", "birthday" , etc.

            Returns:
                dict: A dictionary containing the event's  information,
                including fields such as timezone, status, and other
                relevant details.

            Raises:
                Exception: If there is an issue connecting to the calendar API.
            """
        try:
            if event_type:
                events = await sync_to_async(
                    self._service.events
                )
                events_list = await sync_to_async(
                    events.list,
                    calendarId='primary',
                    eventTypes=event_type,
                )
                return await sync_to_async(
                    events_list.execute
                )
        except Exception as ex:
            message = f"Error while Getting Events"
            logger.error(message, exc_info=ex)
            raise

    def __dir__(self):
        return (
            'get_today_events',
            'get_week_events',
            'get_month_events',
            'get_events_by_type'
        )
