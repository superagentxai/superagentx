from enum import Enum
from typing import Any, Optional

from github import Github

from agentx.handler.base import BaseHandler
from agentx.handler.github.exceptions import InvalidType

class GitHubAction(str, Enum):
    PULL_REQUEST = 'pull_request'
    ISSUES = 'issues'
    ALL = 'all'


class GitHubHandler(BaseHandler):

    def __init__(
            self,
            access_token: str,
            organization_name: str,
    ):
        self.access_token = access_token
        self.organization_name = organization_name


    def handle(
            self,
            *,
            action: str | Enum,
            **kwargs
    ) -> Any:
        match action:
            case GitHubAction.PULL_REQUEST:
                return self.get_pull_requests(**kwargs)
            case GitHubAction.ISSUES:
                return self.get_issues(**kwargs)
            case _:
                raise InvalidType(f"{action} is not supported")

    def config(self):
        client = Github(self.access_token)
        return client.get_organization(self.organization_name)

    def get_pull_requests(self, state: str):
        results = []
        org = self.config()
        for repo in org.get_repos():
            prs = org.get_repo(repo.name)
            pulls = prs.get_pulls(state=state)
            for pull in pulls:
                result = {
                    "repo_name": repo.name,
                    "title": pull.title,
                    "created_by": pull.user.login,
                    "state": pull.state,
                    "base": pull.base.ref,
                    "head": pull.head.ref,
                    "created_at": pull.created_at
                }
                results.append(result)
        return results

    def get_issues(self, state: str, assignee: str):
        results = []
        org = self.config()
        for repo in org.get_repos():
            issues = repo.get_issues(
                state=state,
                assignee=assignee,
            )
            for issue in issues:
                if issue.pull_request is None:
                    result = {
                        "repo_name": repo.name,
                        "title": issue.title,
                        "created_by": issue.user.login,
                        "state": issue.state,
                        "created_at": issue.created_at
                    }
                    results.append(result)
        return results
