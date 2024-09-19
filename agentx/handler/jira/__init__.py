import logging
from enum import Enum
from typing import Any

from jira import JIRA

from agentx.handler.base import BaseHandler
from agentx.handler.exceptions import InvalidAction
from agentx.handler.jira.exceptions import SprintException, AuthException, ProjectException, TaskException
from agentx.utils.helper import sync_to_async

logger = logging.getLogger(__name__)


class JiraActions(str, Enum):
    PROJECT = 'project'
    ACTIVE_SPRINT = 'active_sprint'
    CREATE_SPRINT = 'create_sprint'
    GET_ISSUE = 'get_issue'
    ADD_ISSUE_TO_SPRINT = 'add_issue_to_sprint'
    MOVE_TO_BACKLOG = 'move_to_backlog'
    ADD_COMMENT = 'add_comment'
    CREATE_ISSUE = 'create_issue'
    ASSIGN_ISSUE = 'assign_issue'


class JiraHandler(BaseHandler):

    def __init__(
            self,
            *,
            email: str,
            token: str,
            organization: str
    ):
        self.email = email
        self.token = token
        self.organization = organization
        self._connection: JIRA = self._connect()

    def _connect(self) -> JIRA:
        try:
            jira = JIRA(
                server=f'https://{self.organization}.atlassian.net',
                basic_auth=(self.email, self.token)
            )
            logger.debug("Authenticate Success")
            return jira
        except Exception as ex:
            message = f'JIRA Handler Authentication Problem {ex}'
            logger.error(message, exc_info=ex)
            raise AuthException(message)

    def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:

        """
           params:
               action(str): Give a action what has given in the Enum.
        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case JiraActions.PROJECT:
                return self.get_list_projects()
            case JiraActions.ACTIVE_SPRINT:
                return self.get_active_sprint(**kwargs)
            case JiraActions.CREATE_SPRINT:
                return self.create_sprint(**kwargs)
            case JiraActions.GET_ISSUE:
                return self.get_issue(**kwargs)
            case JiraActions.ADD_ISSUE_TO_SPRINT:
                return self.add_issue_to_sprint(**kwargs)
            case JiraActions.MOVE_TO_BACKLOG:
                return self.move_to_backlog(**kwargs)
            case JiraActions.ADD_COMMENT:
                return self.add_comment_for_issue(**kwargs)
            case JiraActions.CREATE_ISSUE:
                raise NotImplementedError
            case JiraActions.ASSIGN_ISSUE:
                raise NotImplementedError
            case _:
                message = f'Invalid Jira action {action}!'
                logger.error(message)
                raise InvalidAction(message)

    def get_list_projects(self):
        try:
            return self._connection.projects()
        except Exception as ex:
            message = f"Projects Getting Error! {ex}"
            logger.error(message)
            raise ProjectException(message)

    def get_active_sprint(
            self,
            *,
            board_id: int,
            start: int | None = 0,
            size: int | None = 1,
            state: str | None = 'active'
    ):
        """
           params:
               board_id(int):The board to get sprints from.
               start(int):The index of the first sprint to return (0 based).
               size(int):The maximum number of sprints to return.
               state(int):Filters results to sprints in specified states. Valid values: `future`, `active`, `closed`.
              You can define multiple states separated by commas.
        """

        try:
            return self._connection.sprints(
                board_id=board_id,
                startAt=start,
                maxResults=size,
                state=state
            )
        except Exception as ex:
            message = f"Active Sprint Not Found! {ex}"
            logger.error(message)
            raise SprintException(message)

    def create_sprint(
            self,
            *,
            name: str,
            board_id: int,
            start_date: Any | None = None,
            end_date: Any | None = None,
            description: str | None = None
    ):
        """
            params:
            name(str):The name to update your sprint to.
            board_id(int):The board to get sprints from.
            start_date(Optional[Any]):The start date for the sprint
            end_date(Optional[Any]):The start date for the sprint
            description(str):The goal of the sprint

        """

        try:
            return self._connection.create_sprint(
                name=name,
                board_id=board_id,
                startDate=start_date,
                endDate=end_date,
                goal=description
            )
        except Exception as ex:
            message = f"Sprint Creation Failed! {ex}"
            logger.error(message)
            raise SprintException(message)

    def get_issue(
            self,
            *,
            issue_id: str
    ):
        """
            params:
                issue_id(str):ID or key of the issue to get.
        """
        try:
            return self._connection.issue(id=issue_id).raw
        except Exception as ex:
            message = f"Issue Not Found! {ex}"
            logger.error(message)
            raise SprintException(message)

    def add_issue_to_sprint(
            self,
            *,
            board_id: int,
            issue_keys: list[str]
    ):
        """
            params:
                board_id(int):The board to get sprints from.
                issue_keys(List[str]):The issues to add to the sprint.
        """

        try:
            current_sprint = self.get_active_sprint(
                board_id=board_id
            )
            for sprint in current_sprint:
                return self._connection.add_issues_to_sprint(
                    sprint_id=sprint.id,
                    issue_keys=issue_keys
                )
        except Exception as ex:
            message = f"Failed to add issue! {ex}"
            logger.error(message)
            raise TaskException(message)

    def move_to_backlog(
            self,
            *,
            issue_keys: list[str]
    ):
        """
            params:
                issue_keys(list[str]):The issues to add to the sprint.
        """
        try:
            return self._connection.move_to_backlog(
                issue_keys=issue_keys
            )
        except Exception as ex:
            message = f"Failed to move backlog! {ex}"
            logger.error(message)
            raise TaskException(message)

    def add_comment_for_issue(
            self,
            *,
            issue_key: str,
            comments: str
    ):
        """
            params:
                issue_keys(str):The issues to add to the sprint.
                comments(str): Text of the comment to add.
        """
        try:
            return self._connection.add_comment(
                issue=issue_key,
                body=comments
            )
        except Exception as ex:
            message = f"Comments added failed! {ex}"
            logger.error(message)
            raise TaskException(message)

    async def ahandle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:

        """
            params:
                action(str): Give an action what has given in the Enum.
        """

        if isinstance(action, str):
            action = action.lower()
        match action:
            case JiraActions.PROJECT:
                return await sync_to_async(self.get_list_projects)
            case JiraActions.ACTIVE_SPRINT:
                return await sync_to_async(self.get_active_sprint, **kwargs)
            case JiraActions.CREATE_SPRINT:
                return await sync_to_async(self.create_sprint, **kwargs)
            case JiraActions.GET_ISSUE:
                return await sync_to_async(self.get_issue, **kwargs)
            case JiraActions.ADD_ISSUE_TO_SPRINT:
                return await sync_to_async(self.add_issue_to_sprint, **kwargs)
            case JiraActions.MOVE_TO_BACKLOG:
                return await sync_to_async(self.move_to_backlog, **kwargs)
            case JiraActions.ADD_COMMENT:
                return await sync_to_async(self.add_comment_for_issue, **kwargs)
            case JiraActions.CREATE_ISSUE:
                raise NotImplementedError
            case JiraActions.ASSIGN_ISSUE:
                raise NotImplementedError
            case _:
                message = f'Invalid Jira action {action}!'
                logger.error(message)
                raise InvalidAction(message)
