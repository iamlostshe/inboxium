import inspect
from email import policy
from email.header import decode_header, make_header
from email.parser import BytesParser

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, Envelope, Session
from loguru import logger


class Inbox:
    """SMTP Inbox server with decoding of headers and body."""

    def __init__(self, address: str, port: int | str) -> None:
        self.address = address
        self.port = int(port)
        self.collator = None

    def collate(self, collator):
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
        mailfrom = envelope.mail_from
        rcpttos = envelope.rcpt_tos
        raw_data = envelope.content

        # Парсим письмо с учетом MIME-политик
        msg = BytesParser(policy=policy.default).parsebytes(raw_data)

        # Декодируем заголовки
        subject = str(make_header(decode_header(msg.get("Subject", "No Subject"))))
        sender = str(make_header(decode_header(msg.get("From", mailfrom))))
        recipients = str(make_header(decode_header(msg.get("To", ", ".join(rcpttos)))))

        # Извлекаем тело (text/plain, либо fallback)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(
                        part.get_content_charset("utf-8"), errors="replace",
                    )
                    break
        else:
            body = msg.get_payload(decode=True).decode(
                msg.get_content_charset("utf-8"), errors="replace",
            )

        if self.collator:
            try:
                if inspect.iscoroutinefunction(self.collator):
                    await self.collator(
                        to=recipients,
                        sender=sender,
                        subject=subject,
                        body=body,
                    )
                else:
                    await server.loop.run_in_executor(
                        None,
                        self.collator,
                        recipients,
                        sender,
                        subject,
                        body,
                    )
            except Exception as e:  # noqa: BLE001
                logger.exception(e)
                return "500 Internal server error"

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
