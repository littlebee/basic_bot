# basic_bot services

These are the services that come with basic_bot.  Many are hardware dependent.  Some require additional drivers installed.  See documentation for each service to learn more about what it requires and provides.

[central_hub](https://littlebee.github.io/basic_bot/Api%20Docs/services/central_hub/) is the only service that must be started.  It provides an under 5ms roundtrip latency pub/sub service that the other services communicate state through.

[web_server](https://littlebee.github.io/basic_bot/Api%20Docs/services/web_server/) is an optional service that serves a web UI from your robot.

[vision](https://littlebee.github.io/basic_bot/Api%20Docs/services/vision/) provides live video streaming and in-frame object detection and classification.

[motor_control_2w](https://littlebee.github.io/basic_bot/Api%20Docs/services/motor_control_2w/) provides motor control of a 2 wheel or track drive mobile robot.

