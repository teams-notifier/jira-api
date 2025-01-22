#!/usr/bin/env python3
import datetime
from typing import Optional

from jira2markdown import convert
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic_core import PydanticUseDefault


class IssueType(BaseModel, extra="allow"):
    name: str
    iconUrl: str


class LinkType(BaseModel, extra="allow"):
    name: str
    inward: str
    outward: str


class StatusCategory(BaseModel, extra="allow"):
    id: int
    key: str
    colorName: str
    name: str


class IssueStatus(BaseModel, extra="allow"):
    name: str
    statusCategory: StatusCategory


class IssueLink(BaseModel, extra="allow"):
    id: int
    type: LinkType
    outwardIssue: Optional["JiraIssue"] = None
    inwardIssue: Optional["JiraIssue"] = None

    @property
    def issue(self) -> Optional["JiraIssue"]:
        return self.outwardIssue or self.inwardIssue

    @property
    def relation(self) -> str:
        return self.type.outward if self.outwardIssue else self.type.inward


class AvatarUrls(BaseModel, extra="allow"):
    thumb_16: str = Field(alias="16x16")
    thumb_24: str = Field(alias="24x24")
    thumb_32: str = Field(alias="32x32")
    thumb_48: str = Field(alias="48x48")


class User(BaseModel, extra="allow"):
    emailAddress: str
    displayName: str
    avatarUrls: AvatarUrls


class IssueComponent(BaseModel, extra="allow"):
    id: str
    name: str


class IssueFields(BaseModel, extra="allow"):
    issuelinks: list[IssueLink] = []
    components: list[IssueComponent] = []
    status: IssueStatus
    assignee: User | None = None
    reporter: User | None = None
    summary: str
    resolutiondate: int | str | None = ""
    updated: int | str = 0
    description: str = ""

    @field_validator("description", mode="before")
    @classmethod
    def none_to_default(cls, v):
        if v is None:
            raise PydanticUseDefault()
        return v

    @property
    def description_md(self) -> str:
        try:
            md_formated: str = convert(self.description)
            return md_formated
        except Exception:
            return self.description

    @property
    def sensible_date(self) -> str:
        date = self.resolutiondate or self.updated
        if type(date) is int:
            return (
                datetime.datetime.fromtimestamp(date / 1000)
                .astimezone(datetime.timezone.utc)
                .strftime("%Y-%m-%d %H:%M:%S %z")
            )
        if type(date) is str:
            return date[:-5].replace("T", " ") + " " + date[-5:]
        return "unknown"


class JiraIssue(BaseModel, extra="allow"):
    self_url: str = Field(alias="self")
    id: int
    key: str
    fields: IssueFields

    @property
    def baseUrl(self):
        return "/".join(self.self_url.split("/")[:3])


class JiraIssueEnvelope(BaseModel, extra="allow"):
    issue: JiraIssue
