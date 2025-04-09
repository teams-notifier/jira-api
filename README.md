# jira-api

Teams Notifier's jira-api component.


This component enables notification from Jira webhooks or Jira Automation to MS Teams card.

Here's an example of an Issue message:
![Issue message collapsed](https://teams-notifier.github.io/docs/deployment/addons/jira-api/jira-card-example-original.png)
![Issue message with details](https://teams-notifier.github.io/docs/deployment/addons/jira-api/jira-card-example-level1.png)
![Issue message fully expanded](https://teams-notifier.github.io/docs/deployment/addons/jira-api/jira-card-example-full.png)

# Config

Environment variables or `.env`:

* `PORT`: port to listen to (def: `8080`)
* `ACTIVITY_API`: `activity-api` base URL (ex: `https://activity-api:3981/`)
* `VALID_X_SHARED_SECRET_TOKEN`: comma separated list of Gitlab's Secret token (sent as `X-Shared-Secret-Token` header). A UUIDv4 generated token is recommended.
* `HMAC_KEYS`: a json dict mapping keys to secrets for webhook ex: `HMAC_KEYS='{"key1":"aaaaaa","key2":"bbbbbb"}'`
* `PARTICIPANTS_CUSTOM_FIELD`: custom field id of type *User picker (multiple)* to be credited in the card ex: `customfield_12345`


# Jira Automation workflow

You'll need:
- one or more conversation tokens
- one of the `VALID_X_SHARED_SECRET_TOKEN` you generated

Go to *System* > *Automation* > *Global automation*, open your rule and in a "Send web request" action:

* **Web request URL**: https://hostname-of-this-api.example.org/api/v1/issue
* **HTTP method**: POST
* **Web request body**: Either *Issue data (Jira format)* or *Issue data (Automation format)*
* **Headers (optional)**: add two headers
  * **X-Shared-Secret-Token**: One of the `VALID_X_SHARED_SECRET_TOKEN` you generated
  * **X-Conversation-Token**: comma separated list of conversation tokens you want the Issue sent to

# Web hook config

You'll need:
- one or more conversation tokens
- define a key to identify the secret (or use the `VALID_X_SHARED_SECRET_TOKEN`)

As call authentication is HMAC based, a shared secret has to be defined and properly configured both locally and on Jira's side.
To avoid recycling keys, you can configure several keys, identified by a name, in `HMAC_KEYS`.

Go to *System* > *Advanced* > *WebHooks*, create or edit your webhook.

* **URL**: https://hostname-of-this-api.example.org/api/v1/webhook?conversation_token=xxx&key_name=xxx where
  * **conversation_token** is a comma separated list of conversation token
  * **key_name** is the reference in the `HMAC_KEYS` env var of the key used to validate HMAC signature
* **Secret**: define or generate a secret and register it in the `HMAC_KEYS` according to ``key_name``
* **Events**: in *Issue related events*, define your JQL and the *Issue* event type you want ex: `project = "FP" and status = Done` and check *Issue* > *updated*
