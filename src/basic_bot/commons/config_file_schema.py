"""
This module contains the schema for the configuration file that bb_start reads.

It can be used with jsonvalidate to validate the configuration file.
"""

#
#  Development Note:  If you change the name of this file, or
#   it's relative path, you will need to update the /build_docs.py script
#

config_file_schema = {
    "type": "object",
    "required": ["bot_name", "version", "services"],
    "properties": {
        #
        # The name of the bot.  This is used for config data and made available
        # via the central hub to all services. TODO: not done yet
        "bot_name": {"type": "string"},
        #
        # Version of basic_bot that the configuration file is compatible with.
        "version": {"type": "string"},
        #
        # Environment variables that are set for all services started unless
        # overridden by the service `env' property.
        "env": {"type": "object", "additionalProperties": {"type": "string"}},
        #
        # Environment variables for all services that are set when the BB_ENV matches
        # the text preceeding`_env`. These are merged with the `env` property and take
        # precedence over it.
        "test_env": {"type": "object", "additionalProperties": {"type": "string"}},
        "development_env": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "production_env": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        #
        # List of services to start.  Each service is started in the background
        # as a detached process.
        "services": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name", "run"],
                "properties": {
                    #
                    # Must have unique name for each service.  `name`` is also
                    # used to create the pid file and log file.
                    "name": {"type": "string"},
                    #
                    # The command to run to start the service.  This command can be
                    # any valid shell command.  The command is run in the current
                    # working directory.
                    "run": {"type": "string"},
                    #
                    # log_file and pid_file are optional file paths to write the
                    # logs and pid for this service.  `bb_stop` uses the pid file
                    # to stop the service. If not provided, the log and pid are
                    # written to the logs and pids directories with the name of the
                    # service.
                    "log_file": {"type": "string"},
                    "pid_file": {"type": "string"},
                    #
                    # Environment variables that are set for this service.
                    "env": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                    #
                    # Environment variables that are set for this service in the
                    # test, production and development  environments.
                    # These are merged with the `env`s above and take precedence
                    # over them.
                    "test_env": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                    "production_env": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                    "development_env": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                },
            },
        },
        #
        # Most central_hub clients connect to the websocket served by central_hub.
        # For some applications, such as connecting to and controlling robots behind
        # a firewall / restrictive router, it may be neccessary to have the bot
        # connect outbound to a public facing host.
        "outbound_clients": {
            "type": "array",
            "minItems": 0,
            "items": {
                "type": "object",
                "required": ["name", "uri", "identity"],
                "properties": {
                    #
                    # Must have unique name for each host.
                    "name": {"type": "string"},
                    #
                    # This is the websocket uri of the host to connect to.
                    # Example: "wss://mypublichost.com:5001"
                    "uri": {"type": "string"},
                    #
                    # This is the name that central_hub expect the bot to use
                    # when it sends the identity after first connecting.
                    # It must match the identity configured in basic_bot.yml
                    "identity": {"type": "string"},
                    #
                    # This is an optional file path pointing to a file that
                    # contains a shared secret token that central_hub sends
                    # to the outbound connection when it first connects.
                    #
                    # This can be used to authenticate the bot by the public
                    # facing host.  The token must match the token configured
                    # via secrets on the public host.
                    "shared_token_file": {"type": "string"},
                },
            },
        },
    },
}
