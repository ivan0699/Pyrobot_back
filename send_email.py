import smtplib

from constants import *


def send_validation_code(to_email: str, code: str, name: str) -> bool:
    msg = (
        f'From: {EMAIL_FROM}\n'
        f'To: {to_email}\n'
        f'Subject: {EMAIL_VALIDATION_SUBJECT}\n'
        f'\n'
        f'This is your validation code:\n'
        f'\t{code}\n\n'
        f'Go to: {FRONTEND_URL}/validation/{name}\n'
        f'\n\n'
        f'Cheers'
    )

    return send_email(to_email, msg)


def send_recover_code(to_email: str, code: str, name: str) -> bool:
    msg = (
        f'From: {EMAIL_FROM}\n'
        f'To: {to_email}\n'
        f'Subject: {EMAIL_RECOVER_SUBJECT}\n'
        f'\n'
        f'This is your password recover link:\n'
        f'{FRONTEND_URL}/recover/{name}/{code}\n'
        f'\n\n'
        f'Cheers'
    )

    return send_email(to_email, msg)


def send_email(to_email: str, msg: str) -> bool:
    has_sent = True

    with smtplib.SMTP_SSL(EMAIL_SERVER, EMAIL_PORT) as server:
        server.ehlo()
        server.login(EMAIL_USER, EMAIL_PASSWORD)

        try:
            server.sendmail(EMAIL_USER, to_email, msg)
        except smtplib.SMTPRecipientsRefused:
            has_sent = False

    return has_sent
