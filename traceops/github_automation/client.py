from github import Github
from github import GithubException

from traceops.core.config import settings

import logging

logger = logging.getLogger(__name__)

_gh_client = None


def get_github_client() -> Github:
    """
    Singleton GitHub client.
    """

    global _gh_client

    if _gh_client is None:
        _gh_client = Github(
            settings.github_token
        )

    return _gh_client


def get_test_repo():
    """
    Returns the GitHub repository object.

    Expected format:
    username/repo-name
    """

    gh = get_github_client()

    repo_name = (
        settings.github_test_repo
        .replace("https://github.com/", "")
        .replace(".git", "")
        .strip("/")
    )

    try:
        repo = gh.get_repo(repo_name)

        logger.info(
            f"Connected to GitHub repo: "
            f"{repo.full_name}"
        )

        return repo

    except GithubException as e:
        logger.error(
            f"Cannot connect to GitHub repo "
            f"{repo_name}: {e}"
        )

        raise