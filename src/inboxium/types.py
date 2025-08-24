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
