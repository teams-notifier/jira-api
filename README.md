# jira-api

Teams Notifier's jira-api component.


This component enables notification from Jira Automation to MS Teams card.

Here's an example of an Issue message:
![Issue message collapsed](https://teams-notifier.github.io/docs/deployment/addons/jira-api/jira-card-example-original.png)
![Issue message with details](https://teams-notifier.github.io/docs/deployment/addons/jira-api/jira-card-example-level1.png)
![Issue message fully expanded](https://teams-notifier.github.io/docs/deployment/addons/jira-api/jira-card-example-full.png)

# Config

Environment variables or `.env`:

* `PORT`: port to listen to (def: `8080`)
* `ACTIVITY_API`: `activity-api` base URL (ex: `https://activity-api:3981/`)
* `VALID_X_SHARED_SECRET_TOKEN`: comma separated list of Gitlab's Secret token (sent as `X-Shared-Secret-Token` header). A UUIDv4 generated token is recommended.

# Web hook config

You'll need:
- one or more conversation tokens
- one of the `VALID_X_SHARED_SECRET_TOKEN` you generated

On your Jira Automation, in a "Send web request" action:

* **Web request URL**: https://hostname-of-this-api.example.org/api/v1/issue
* **HTTP method**: POST
* **Web request body**: Either *Issue data (Jira format)* or *Issue data (Automation format)*
* **Headers (optional)**: add two headers
  * **X-Shared-Secret-Token**: One of the `VALID_X_SHARED_SECRET_TOKEN` you generated
  * **X-Conversation-Token**: comma separated list of conversation tokens you want the Issue sent to
