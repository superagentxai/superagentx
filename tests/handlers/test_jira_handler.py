from agentx.handler.jira import JiraHandler, JiraActions


jira_handler = JiraHandler(
    '',
    '',
    ""
)


def test_get_all_projects():
    res = jira_handler.handle(
        action=JiraActions.PROJECT
    )
    for project in res:
        print(f'Project Name => {project.name}')


def test_get_active_sprint():
    # get active Sprint
    res = jira_handler.handle(
        action=JiraActions.ACTIVE_SPRINT,
        board_id=1,
        start=0,
        size=50,
        status="active"
    )
    for project in res:
        print(f'Active Sprint => {project.name}')


def test_create_sprint():
    # create Sprint
    res = jira_handler.handle(
        action=JiraActions.CREATE_SPRINT,
        board_id=1,
        name='DFPS Sprint Testing',
        description='Description of the sprint'
    )
    print(res)


def test_get_issue():
    # get issue
    res = jira_handler.handle(
        action=JiraActions.GET_ISSUE,
        issue_id='DFPS-520'
    )
    print(f'Issue key => {res['key']}')
    print(f'Issue id => {res['id']}')
    print(f'Issue info => {res.get('fields', {}).get('summary')}')


def test_add_issue_to_active_sprint():
    # create Sprint
    res = jira_handler.handle(
        action=JiraActions.ADD_ISSUE_TO_SPRINT,
        board_id=1,
        issue_keys=['DFPS-520']
    )
    print(res)


def test_move_issue_to_backlog():
    # move issue to backlog
    res = jira_handler.handle(
        action=JiraActions.MOVE_TO_BACKLOG,
        issue_keys=['DFPS-520']
    )
    print(res)


def test_add_comment_issue():
    # move issue to backlog
    res = jira_handler.handle(
        action=JiraActions.ADD_COMMENT,
        issue_keys='DFPS-520',
        comments="K8s auto restart"
    )
    print(res)
