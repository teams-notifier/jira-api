#!/usr/bin/env python3
import hashlib
import hmac
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

import blibs
import httpx
import yaml
from asgi_logger.middleware import AccessLoggerMiddleware
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import Template

from config import DefaultConfig
from jira_model import JiraIssue
from jira_model import JiraIssueEnvelope

# from fastapi.middleware.cors import CORSMiddleware

config = DefaultConfig()

# Configure logging
blibs.init_root_logger()
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("msrest").setLevel(logging.ERROR)
logging.getLogger("msal").setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting app version %s", app.version)

    yield


app: FastAPI = FastAPI(
    title="Teams Notifier jira-api",
    version=os.environ.get("VERSION", "v0.0.0-dev"),
    lifespan=lifespan,
    middleware=[
        Middleware(
            AccessLoggerMiddleware,  # type: ignore
            format='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)ss',  # noqa # type: ignore
        )
    ],
)

env = Environment(loader=FileSystemLoader("./cards/"))
templ: Template = env.get_template("changes.yaml.j2")
client: httpx.AsyncClient = httpx.AsyncClient()


# For 422 debugging purpose :)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    with open("OUT_error.json", "w") as fp:
        json.dump(exc.args, fp, indent=2)
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.get("/", response_class=RedirectResponse, status_code=302)
async def root():
    return "/docs"


def validate_shared_secret_token(token: str) -> None:
    if not config.is_valid_token(token):
        raise HTTPException(status_code=403, detail=f"Invalid shared secret token {token}")


def validate_uuid(val: str) -> str | None:
    try:
        return str(uuid.UUID(str(val)))
    except ValueError:
        return None


@app.post("/api/v1/issue")
async def api_v1_issue(
    payload: JiraIssue | JiraIssueEnvelope,
    x_shared_secret_token: Annotated[str, Header()],
    x_conversation_token: Annotated[str, Header()],
):
    validate_shared_secret_token(x_shared_secret_token)

    issue: JiraIssue
    if isinstance(payload, JiraIssueEnvelope):
        issue = payload.issue
    else:
        issue = payload

    conversation_tokens = list(
        filter(
            None,
            [validate_uuid(ct.strip()) for ct in x_conversation_token.split(",")],
        )
    )

    return await send_issue_to_conversations(issue, conversation_tokens)


async def send_issue_to_conversations(
    issue: JiraIssue,
    conversation_tokens: list[str],
):
    try:
        fallback = f"{issue.fields.summary} [{issue.key}]"

        output = templ.render(
            fallback=fallback,
            issue=issue,
        )

        # with open("OUT_changes.yaml", "w") as fp:
        #     fp.write(output)
        # with open("OUT_issue.json", "w") as fp:
        #     fp.write(json.dumps(issue.model_dump(), indent=2))

        for conversation_token in conversation_tokens:
            response = await client.post(
                config.ACTIVITY_API + "api/v1/message",
                json={
                    "conversation_token": conversation_token,
                    "card": yaml.safe_load(
                        output,
                    ),
                    "summary": fallback,
                },
            )
            response.raise_for_status()
        return {"status": "ok"}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.json(),
        )


async def get_body(request: Request):
    return await request.body()


@app.post("/api/v1/webhook/issue")
async def api_v1_webhook_issue(
    request: Request,
    x_hub_signature: Annotated[str, Header()],
    conversation_token: str,
    key_name: str = "",
):
    algo, signature = x_hub_signature.split("=")
    body: bytes = await request.body()
    computed_sig = hmac.new(
        config.get_key_by_name(key_name),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if computed_sig != signature:
        raise HTTPException(
            403,
            detail="invalid signature",
        )

    conversation_tokens = list(
        filter(
            None,
            [validate_uuid(ct.strip()) for ct in conversation_token.split(",")],
        )
    )

    return await send_issue_to_conversations(
        JiraIssueEnvelope(**json.loads(body)).issue,
        conversation_tokens=conversation_tokens,
    )


@app.get("/healthz", include_in_schema=False)
async def healthcheck():
    return {"ok": True}


if __name__ == "__main__":
    # fmt: off
    print(
        "use fastapi cli to run this app\n"
        "- fastapi run # for prod\n"
        "- fastapi dev # for dev :)\n"
    )
    # fmt: on

    # for debug entry point
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
