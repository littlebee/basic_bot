import os

# Default timeout for web socket message recv
DEFAULT_TIMEOUT = 10

IS_BLIND = (
    os.getenv("GITHUB_ACTIONS")
    or os.getenv("TRAVIS")
    or os.getenv("CIRCLECI")
    or os.getenv("GITLAB_CI")
)
