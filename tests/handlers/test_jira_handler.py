import pytest
import logging
from jira.client import ResultList
from jira.resources import Sprint, Comment
from requests.models import Response

from agentx.handler.jira import JiraHandler, JiraActions

logger = logging.getLogger(__name__)

'''
 Run Pytest:  
 
   # sync 
   1.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_get_all_projects
   2.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_get_active_sprint
   3.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_create_sprint
   4.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_get_issue
   5.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_add_issue_to_active_sprint
   6.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_move_issue_to_backlog
   7.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_add_comment_issue
   
   # async
   1.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_aget_all_projects
   2.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_aget_active_sprint
   3.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_acreate_sprint//
   4.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_aget_issue
   5.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_aadd_issue_to_active_sprint//
   6.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_amove_issue_to_backlog//
   7.pytest --log-cli-level=INFO tests/handlers/test_jira_handler.py::TestJira::test_aadd_comment_issue
   
   
'''

@pytest.fixture
def jira_client_init() -> JiraHandler:
    jira_handler = JiraHandler(
    email='arul@decisionforce.io',
    token='ATATT3xFfGF0wsUTluleaFMNfR3phlGq-icNuTHgw5bD5jtehm10x1TJHmn3EiOh0YJSqY3N3Is4jnwmDbq1X3uo4ZaI8pwcWoBo3Uekb2ASB3GCkfwLkgF7dFVK8WGuUxd6l9B_USPb1aX3YjXqdqPxmnIdvQP0686ke6QMpi5HL6RHJG3QUlw=69A06FF3',
    organization="decisionforce"
)
    return jira_handler

class TestJira:

    def test_get_all_projects(self, jira_client_init:JiraHandler):
        res = jira_client_init.handle(
            action=JiraActions.PROJECT
        )
        logger.info(f"Projects: {res}")
        assert isinstance(res, list)
        assert len(res) > 0


    def test_get_active_sprint(self, jira_client_init:JiraHandler):
        # get active Sprint
        res = jira_client_init.handle(
            action=JiraActions.ACTIVE_SPRINT,
            board_id=1,
            start=0,
            size=50,
            state="active"
        )
        logger.info(f"Active Sprint: {res}")
        assert isinstance(res, ResultList)
        assert len(res) > 0
        assert "DFPS Sprint" in res[0].name



    def test_create_sprint(self, jira_client_init:JiraHandler):
        # create Sprint
        res = jira_client_init.handle(
            action=JiraActions.CREATE_SPRINT,
            board_id=1,
            name='DFPS Sprint Testing',
            description='Description of the sprint'
        )
        assert isinstance(res, Sprint)


    def test_get_issue(self, jira_client_init:JiraHandler):
        # get issue
        res = jira_client_init.handle(
            action=JiraActions.GET_ISSUE,
            issue_id='DFPS-520'
        )
        logger.info(f"Get Issue: {res}")
        assert isinstance(res, dict)
        assert len(res) > 0


    def test_add_issue_to_active_sprint(self, jira_client_init:JiraHandler):
        # create Sprint
        res = jira_client_init.handle(
            action=JiraActions.ADD_ISSUE_TO_SPRINT,
            board_id=1,
            issue_keys=['DFPS-520']
        )
        assert isinstance(res, Response)


    def test_move_issue_to_backlog(self, jira_client_init:JiraHandler):
        # move issue to backlog
        res = jira_client_init.handle(
            action=JiraActions.MOVE_TO_BACKLOG,
            issue_keys=['DFPS-520']
        )
        assert isinstance(res, Response)

    def test_add_comment_issue(self, jira_client_init:JiraHandler):
        # move issue to backlog
        res = jira_client_init.handle(
            action=JiraActions.ADD_COMMENT,
            issue_key='DFPS-520',
            comments="K8s auto restart"
        )
        logger.info(f"Add Comment Issue: {res}")
        assert isinstance(res, Comment)


    # async

    async def test_aget_all_projects(self, jira_client_init:JiraHandler):
        res = await jira_client_init.ahandle(
            action=JiraActions.PROJECT
        )
        logger.info(f"Projects: {res}")
        assert isinstance(res, list)
        assert len(res) > 0


    async def test_aget_active_sprint(self, jira_client_init:JiraHandler):
        # get active Sprint
        res = await jira_client_init.ahandle(
            action=JiraActions.ACTIVE_SPRINT,
            board_id=1,
            start=0,
            size=50
        )
        logger.info(f"Active Sprint: {res}")
        assert isinstance(res, ResultList)
        assert len(res) > 0
        assert "DFPS Sprint" in res[0].name


    async def test_acreate_sprint(self, jira_client_init:JiraHandler):
        # create Sprint
        res = await jira_client_init.ahandle(
            action=JiraActions.CREATE_SPRINT,
            board_id=1,
            name='DFPS Sprint Testing',
            description='Description of the sprint'
        )
        assert isinstance(res, Sprint)


    async def test_aget_issue(self, jira_client_init:JiraHandler):
        # get issue
        res = await jira_client_init.ahandle(
            action=JiraActions.GET_ISSUE,
            issue_id='DFPS-520'
        )
        logger.info(f"Get Issue: {res}")
        assert isinstance(res, dict)
        assert len(res) > 0


    async def test_aadd_issue_to_active_sprint(self, jira_client_init:JiraHandler):
        # create Sprint
        res = await jira_client_init.ahandle(
            action=JiraActions.ADD_ISSUE_TO_SPRINT,
            board_id=1,
            issue_keys=['DFPS-520']
        )
        assert isinstance(res, Response)


    async def test_amove_issue_to_backlog(self, jira_client_init:JiraHandler):
        # move issue to backlog
        res = await jira_client_init.ahandle(
            action=JiraActions.MOVE_TO_BACKLOG,
            issue_keys=['DFPS-520']
        )
        assert isinstance(res, Response)


    async def test_aadd_comment_issue(self, jira_client_init:JiraHandler):
        # move issue to backlog
        res = await jira_client_init.ahandle(
            action=JiraActions.ADD_COMMENT,
            issue_key='DFPS-520',
            comments="K8s auto restart"
        )
        logger.info(f"Add Comment Issue: {res}")
        assert isinstance(res, Comment)
