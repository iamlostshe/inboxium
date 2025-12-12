from __future__ import annotations

from email import policy
from email.header import decode_header, make_header
from email.parser import BytesParser
from typing import TYPE_CHECKING

from aiosmtpd.controller import Controller
from loguru import logger

from .types import InboxMessage, Handler

if TYPE_CHECKING:
    from email.message import Message

    from aiosmtpd.smtp import SMTP, Envelope, Session


def _get_body(msg: Message) -> str:
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


def _prepare_message(envelope: Envelope) -> InboxMessage:
    """Prepare message."""
    logger.debug("Prepairing msg")

    msg = BytesParser(policy=policy.default).parsebytes(envelope.content)
    return InboxMessage(
        by=envelope.rcpt_tos,
        sender=envelope.mail_from or "",
        subject=str(make_header(decode_header(msg.get("Subject", "")))),
        text=_get_body(msg),
        raw=msg.as_string(),
    )


class Inbox:
    """SMTP Inbox handler."""

    def __init__(self, address: str, port: int | str) -> None:
        self.address = address
        self.port = int(port)

        self.handlers = []

    async def handle_RCPT(
        self,
        server: SMTP,
        session: Session,
        envelope: Envelope,
        address: str,
        rcpt_options,
    ) -> str:
        """Handle RCPT command."""
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        """Handle DATA command."""
        try:
            msg = _prepare_message(envelope)

            for h in self.handlers:
                if not any((h.by, h.sender, h.subject, h.text)):
                    await h.func(msg)
                    if h.block:
                        break

                elif any((
                    h.by == msg.by,
                    h.sender == msg.sender,
                    h.subject == msg.subject,
                    h.text == msg.text,
                )):
                    await h.func(msg)
                    if h.block:
                        break

        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            return "500 Internal server error"

        return "250 Message accepted for delivery"

    def message(
        self,
        by: str | None = None,
        sender: str | None = None,
        subject: str | None = None,
        text: str | None = None,
        block: bool | None = True,
    ):
        """Set handler for incoming messages."""
        def decorator(func) -> func | None:
            self.handlers.append(Handler(func, by, sender, subject, text, block))

        return decorator

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
            controller._thread.join()  # noqa: SLF001
        finally:
            controller.stop()
