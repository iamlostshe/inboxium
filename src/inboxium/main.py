import argparse
from email.parser import Parser

import asyncore
import smtpd
from logbook import Logger

log = Logger(__name__)


class InboxServer(smtpd.SMTPServer):
    """Logging-enabled SMTPServer instance with handler support."""

    def __init__(self, handler, *args, **kwargs):
        """Init the inbox server class."""
        super(InboxServer, self).__init__(*args, **kwargs)
        self._handler = handler

    def process_message(self, peer, mailfrom, rcpttos, data):
        """Work with message."""
        log.info("Collating message from {}", mailfrom)
        subject = Parser().parsestr(data)["subject"]
        log.debug(dict(to=rcpttos, sender=mailfrom, subject=subject, body=data))
        return self._handler(to=rcpttos, sender=mailfrom, subject=subject, body=data)


class Inbox:
    """A simple SMTP Inbox."""

    def __init__(
        self, port: str | int | None = None, address: str | None = None,
    ) -> None:
        """Init the inbox class."""
        self.port = port
        self.address = address
        self.collator = None

    def collate(self, collator):
        """Func decorator. Used to specify inbox handler."""
        self.collator = collator
        print(type(collator))
        return collator

    def serve(
        self,
        port: str | int | None = None,
        address: str | None = None,
    ) -> None:
        """Serve the SMTP server on the given port and address."""
        port = port or self.port
        address = address or self.address

        log.info("Starting SMTP server at {}:{}", address, port)

        InboxServer(self.collator, (address, port), None)

        try:
            asyncore.loop()
        except KeyboardInterrupt:
            log.info("Cleaning up")

    def dispatch(self) -> None:
        """Command-line dispatch."""
        parser = argparse.ArgumentParser(description="Run an Inbox server.")

        parser.add_argument("addr", metavar="addr", type=str, help="addr to bind to")
        parser.add_argument("port", metavar="port", type=int, help="port to bind to")

        args = parser.parse_args()

        self.serve(port=args.port, address=args.addr)
