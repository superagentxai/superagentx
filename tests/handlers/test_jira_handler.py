import logging

import pytest
from jira.client import ResultList
from jira.resources import Sprint, Comment
from requests.models import Response

from agentx.handler.jira import JiraHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_get_all_projects
   2.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_get_active_sprint
   3.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_create_sprint//
   4.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_get_issue
   5.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_add_issue_to_active_sprint//
   6.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_move_issue_to_backlog//
   7.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_add_comment_issue
   8.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_active_sprint_get_all_issues
   9.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_active_sprint_issues_by_assignee
   10.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_active_sprint_filter_issues_by_status


'''


@pytest.fixture
def jira_client_init() -> JiraHandler:
    jira_handler = JiraHandler(
        email='',
        token='',
        organization=""
    )
    return jira_handler


class TestJira:

    async def test_get_all_projects(self, jira_client_init: JiraHandler):
        res = await jira_client_init.get_list_projects()
        logger.info(f"Projects: {res}")
        assert isinstance(res, list)
        assert len(res) > 0

    async def test_get_active_sprint(self, jira_client_init: JiraHandler):
        # get active Sprint
        res = await jira_client_init.get_active_sprint(
            board_id=1,
            start=0,
            end=50
        )
        logger.info(f"Active Sprint: {res}")
        assert isinstance(res, ResultList)
        assert len(res) > 0
        assert "DFPS Sprint" in res[0].name

    async def test_create_sprint(self, jira_client_init: JiraHandler):
        # create Sprint
        res = await jira_client_init.create_sprint(
            board_id=1,
            name='DFPS Sprint Testing',
            description='Description of the sprint'
        )

        assert isinstance(res, Sprint)

    async def test_get_issue(self, jira_client_init: JiraHandler):
        # get issue
        res = await jira_client_init.get_issue(issue_id='DFPS-680')
        logger.info(f"Get Issue: {res}")
        assert isinstance(res, dict)
        assert len(res) > 0

    async def test_add_issue_to_active_sprint(self, jira_client_init: JiraHandler):
        # create Sprint
        res = await jira_client_init.add_issue_to_sprint(
            board_id=1,
            issue_keys=['DFPS-520']
        )

        assert isinstance(res, Response)

    async def test_move_issue_to_backlog(self, jira_client_init: JiraHandler):
        # move issue to backlog
        res = await jira_client_init.move_to_backlog(
            issue_keys=['DFPS-520']
        )

        assert isinstance(res, Response)

    async def test_add_comment_issue(self, jira_client_init: JiraHandler):
        # move issue to backlog
        res = await jira_client_init.add_comment_for_issue(
            issue_key='DFPS-520',
            comments="K8s auto restart"
        )

        logger.info(f"Add Comment Issue: {res}")
        assert isinstance(res, Comment)

    async def test_active_sprint_get_all_issues(self, jira_client_init: JiraHandler):
        res = await jira_client_init.active_sprint_get_all_issues(
            board_id=1,
            start=0,
            end=10
        )
        logger.info(f"Issues: {res}")
        assert isinstance(res, list)
        assert len(res) > 0

    async def test_active_sprint_issues_by_assignee(self, jira_client_init: JiraHandler):
        res = await jira_client_init.active_sprint_issues_by_assignee(
            board_id=1,
            assignee_name="Arul",
            start=0,
            end=10
        )
        logger.info(f"Issue: {res}")
        assert isinstance(res, list)
        assert len(res) > 0

    async def test_active_sprint_filter_issues_by_status(self, jira_client_init: JiraHandler):
        res = await jira_client_init.active_sprint_filter_issues_by_status(
            board_id=1,
            filter_by="Done"
        )
        logger.info(f"Issue: {res}")
        assert isinstance(res, list)
        assert len(res) > 0
