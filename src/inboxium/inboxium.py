from __future__ import annotations

from email import policy
from email.header import decode_header, make_header
from email.parser import BytesParser
from typing import TYPE_CHECKING

from aiosmtpd.controller import Controller
from loguru import logger

from .types import InboxMessage

if TYPE_CHECKING:
    from email.message import Message

    from aiosmtpd.smtp import SMTP, Envelope, Session


def prepare_message(envelope: Envelope) -> InboxMessage:
    """Prepare message."""
    mailfrom = envelope.mail_from or ""
    rcpttos = envelope.rcpt_tos
    raw_data: bytes = envelope.content

    # Парсим письмо с учетом MIME-политик
    msg = BytesParser(policy=policy.default).parsebytes(raw_data)

    return InboxMessage(
        by=str(make_header(decode_header(msg.get("To", ", ".join(rcpttos))))),
        sender=str(make_header(decode_header(msg.get("From", mailfrom)))),
        subject=str(make_header(decode_header(msg.get("Subject", "No Subject")))),
        text=get_body(msg),
        raw=msg.as_string(),
    )


def get_body(msg: Message) -> str:
    """Get message body (text)."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(
                    part.get_content_charset("utf-8"),
                    errors="replace",
                )
    else:
        return msg.get_payload(decode=True).decode(
            msg.get_content_charset("utf-8"),
            errors="replace",
        )

    return ""


class Inbox:
    """SMTP Inbox server with decoding of headers and text."""

    def __init__(self, address: str, port: int | str) -> None:
        self.address = address
        self.port = int(port)
        self.collator = None

    def message(self, collator):
        """Decorator to set handler for incoming messages."""
        self.collator = collator
        return collator

    async def handle_RCPT(
        self,
        server: SMTP,
        session: Session,
        envelope: Envelope,
        address: str,
        rcpt_options,
    ):
        """Handle RCPT command."""
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        """Handle DATA command."""
        try:
            if self.collator:
                message = prepare_message(envelope)
                await self.collator(message)

        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            return "500 Internal server error"

        else:
            return "250 Message accepted for delivery"

    def serve(self) -> None:
        """Run the SMTP server."""
        logger.info("Starting SMTP server at {}:{}", self.address, self.port)
        controller = Controller(
            self,
            hostname=self.address,
            port=self.port,
        )
        try:
            controller.start()
            controller._thread.join()
        finally:
            controller.stop()
