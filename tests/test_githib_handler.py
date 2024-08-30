from agentx.handler.github import GitHubHandler

github_handler = GitHubHandler(
    access_token = '',
    organization_name =  '',
)

def test_get_pull_request():
    res = github_handler.handle(
        action="pull_request",
        state="open")
    assert len(res) > 0

def test_get_issues():
    res = github_handler.handle(
        action="issues",
        state="open",
        assignee="Elangovan1988",
    )
    assert len(res) > 0