import os
from typing import List
from requests import Response, post

FAILED_LOAD_API_KEY = "Failed to load Mailgun API key."
ERROR_LOAD_DOMAIN = "Failed to load Mailgun domain."
ERROR_SENDING_EMAIL = "Error in sending confirmation email, user registration failed."


class MailgunException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Mailgun:
    MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")    # can be None
    MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")  # can be None
    FROM_TITLE = "Stores REST API"
    FROM_EMAIL = "postmaster@sandbox53dc3f08891e474fb07e1a3a88a256a6.mailgun.org"

    @classmethod
    def send_email(cls, email: List[str], subject: str, text: str, html: str) -> Response:
        if cls.MAILGUN_API_KEY is None:
            raise MailgunException(FAILED_LOAD_API_KEY)

        if cls.MAILGUN_DOMAIN is None:
            raise MailgunException(ERROR_LOAD_DOMAIN)

        response = post(
            f"https://api.mailgun.net/v3/{cls.MAILGUN_DOMAIN}/messages",
            auth=("api", cls.MAILGUN_API_KEY),
            data={
                "from": f"{cls.FROM_TITLE} <{cls.FROM_EMAIL}>",
                "to": [email],
                "subject": subject,
                "text": text,
                "html": html
            },
        )

        if response.status_code != 200:
            raise MailgunException(ERROR_SENDING_EMAIL)

        return response
