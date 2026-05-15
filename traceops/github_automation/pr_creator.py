from traceops.core.schemas import (
    GeneratedTest,
    PRResult,
)

from traceops.github_automation.client import (
    get_test_repo,
)

from github import GithubException

import logging
import time

logger = logging.getLogger(__name__)


def create_pr(
    test: GeneratedTest,
) -> PRResult:
    """
    Create a GitHub PR containing the
    generated regression test.

    Flow:
    1. Get default branch SHA
    2. Create branch
    3. Commit generated test file
    4. Open pull request
    """

    repo = get_test_repo()

    branch_name = (
        f"regression/"
        f"{test.failure_type.value}/"
        f"{test.test_id}"
    )

    pr_title = (
        "Regression Test: "
        f"{test.failure_type.value.replace('_', ' ').title()} "
        f"[{test.test_id}]"
    )

    pr_body = _build_pr_body(test)

    # ---- Step 1: get source SHA -------------------------

    default_branch = repo.default_branch

    source_sha = (
        repo.get_branch(default_branch)
        .commit.sha
    )

    logger.info(
        f"Creating branch "
        f"{branch_name} "
        f"from "
        f"{default_branch}@{source_sha[:7]}"
    )

    # ---- Step 2: create branch --------------------------

    try:
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=source_sha,
        )

    except GithubException as e:
        if e.status == 422:
            logger.warning(
                f"Branch already exists: "
                f"{branch_name}"
            )
        else:
            raise

    # ---- Step 3: commit generated test ------------------

    file_path = (
        f"tests/{test.test_file_name}"
    )

    commit_result = repo.create_file(
        path=file_path,
        message=(
            "auto: add regression test "
            f"for trace {test.trace_id[:8]}"
        ),
        content=test.test_file_content,
        branch=branch_name,
    )

    commit_sha = (
        commit_result["commit"]
        .sha
    )

    logger.info(
        f"Committed "
        f"{file_path} "
        f"→ "
        f"{commit_sha[:7]}"
    )

    # Small delay avoids occasional GitHub race conditions
    time.sleep(1)

    # ---- Step 4: open PR --------------------------------

    pr = repo.create_pull(
        title=pr_title,
        body=pr_body,
        head=branch_name,
        base=default_branch,
    )

    logger.info(
        f"Opened PR: {pr.html_url}"
    )

    return PRResult(
        pr_url=pr.html_url,
        pr_number=pr.number,
        branch_name=branch_name,
        commit_sha=commit_sha,
        test_file=file_path,
    )


def _build_pr_body(
    test: GeneratedTest,
) -> str:
    """
    Generate markdown PR description.
    """

    return f"""
## Auto-generated Regression Test

### Source Information

- **Trace ID:** `{test.trace_id}`
- **Failure Type:** `{test.failure_type.value}`
- **Generated At:** `{test.generated_at.isoformat()}`

---

## What Happened

A user flagged a problematic response in production.

TraceOps captured the execution trace,
classified the failure,
and automatically generated this
DeepEval regression test.

---

## What This Test Does

This regression test reproduces the
original production interaction using:

- original query
- retrieved RAG context
- semantic evaluation metrics

If the same issue appears again in future
deployments, CI will fail before the
bug reaches users.

---

## Review Checklist

- [ ] Validate the query/output pair
- [ ] Confirm retrieved context is relevant
- [ ] Verify selected evaluation metric
- [ ] Merge if valid

---

Generated automatically by TraceOps Lite.
"""