# Inboxium: SMTP Server for Humans

This is the simplest SMTP server you'll ever see. It's asynchronous.

One instance should handle over one thousand emails per second.

## Usage

Give your app an inbox easily:

``` python
from inboxium import Inbox

inbox = Inbox("127.0.0.1", 4470)


@inbox.collate
def handle(to: list[str], sender: str, subject: str, body: str) -> None:
    print(to)
    print(sender)
    print(subject)
    print(body)


if __name__ == "__main__":
    inbox.serve()
```

``` sh
python3 filename.py
```

```
Starting SMTP server at 127.0.0.1:4470

deepcyan@127.0.0.1
sender@127.0.0.1
Test mail
Thats test mail for local SMTP-server
```

## Installation

Installing inboxium is simple::

``` sh
pip install inboxium
```
