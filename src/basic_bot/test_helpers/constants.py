import os

# run central hub on different port for test
CENTRAL_HUB_TEST_PORT = 5100

# Default timeout for web socket message recv
DEFAULT_TIMEOUT = 10

IS_HEADLESS = (
    os.getenv("GITHUB_ACTIONS")
    or os.getenv("TRAVIS")
    or os.getenv("CIRCLECI")
    or os.getenv("GITLAB_CI")
)
