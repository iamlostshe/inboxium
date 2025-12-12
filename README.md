# inboxium

This is the elegant, asynchronous and simplest SMTP server you'll ever see.

One instance should handle over one thousand emails per second.

## Installation

Installing inboxium is simple::

``` sh
# Use pip
pip install git+https://github.com/iamlostshe/inboxium

# Use uv
uv add git+https://github.com/iamlostshe/inboxium

# Use poetry
poetry add git+https://github.com/iamlostshe/inboxium
```

## Usage

That's all, what you need to start your own mail server:

``` python
from inboxium import Inbox
from inboxium.types import InboxMessage

inbox = Inbox(address="0.0.0.0", port=25)  # noqa: S104


@inbox.message()
async def handle(message: InboxMessage) -> None:
    """Handle any messages."""
    print(  # noqa: T201
        message.by,
        message.sender,
        message.subject,
        message.text,
        message.raw,
        sep="\n",
    )

if __name__ == "__main__":
    inbox.serve()
```

Also, you can use simple, aiogram-like handles system, like that:

``` python
TARGET_BY = ["example@example.com"]
TARGET_SENDER = example@example.com
TARGET_SUBJECT = "target subject"
TARGET_TEXT = "target text"

@inbox.message(by=TARGET_BY, sender=TARGET_SENDER, subject=TARGET_SUBJECT, text=TARGET_TEXT, block=False)
async def handle(message: InboxMessage) -> None:
```

`block` - stoping handling next functions if handler has been activated (by default is True).

For example you can use it for logs:

``` python
@inbox.message(block=False)
async def show_logs(message: InboxMessage) -> None:
    logger.debug(
        message.sender,
        message.subject,
    )
```

You can test sever by this script:

``` python
import smtplib
from email.message import EmailMessage

SMTP_HOST = "0.0.0.0"
SMTP_PORT = 4467


def send_one(from_addr, to_addrs, subject, body):
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs) if isinstance(to_addrs, (list, tuple)) else to_addrs
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT, timeout=10) as smtp:
        smtp.send_message(msg)
        print(f"Sent: {subject} -> {to_addrs}")


if __name__ == "__main__":
    send_one(
        from_addr="sender@example.com",
        to_addrs=["recipient@example.com"],
        subject="Test message",
        body="Hello, thats test message.",
    )
```
