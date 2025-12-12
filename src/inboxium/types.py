"""Typing."""

from dataclasses import dataclass


@dataclass
class InboxMessage:
    """Message class."""

    by: str
    sender: str
    subject: str
    text: str
    raw: str


@dataclass
class Handler:
    """Обработчик."""

    func: any
    by: str | None = None
    sender: str | None = None
    subject: str | None = None
    text: str | None = None
    block: bool | None = True
