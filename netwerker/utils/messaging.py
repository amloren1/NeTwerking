import enum
import logging
import pathlib
from dataclasses import dataclass

import boto3
import idna
from botocore.exceptions import ClientError
from flask import current_app, render_template
from flask.json import dumps
from marshmallow import ValidationError
from werkzeug.exceptions import BadRequest


def email_domain_blacklisted(email_address: str):
    """Check whether the domain of an email address is blacklisted.

    Loads a list with blacklisted domain names and checks whether or not the
    provided email address is blacklisted or not. Email address may be
    given in any character set. IDNA (International Domain Names in
    Applications) is supported. Note that there is no return statement
    and this function is meant only to raise a BadRequest exception if needed.

    Parameters
    ----------
    email_address : str
        The email address as provided by the user.

    Raises
    ------
    BadRequest
        If the email address is not valid or if it is blacklisted.
    """
    global _blacklisted_email_domains

    if not _blacklisted_email_domains:
        blacklist_file = (
            pathlib.Path(current_app.static_folder) / "email-domain-blacklist.txt"
        )
        _blacklisted_email_domains = blacklist_file.read_text().split("\n")

    parts = email_address.split("@")
    if len(parts) != 2:
        raise BadRequest("Not a valid email address.")

    # Domain names must always be lowercase.
    # Unicode Technical Standard #46 (a.k.a. Unicode IDNA Compatibility
    # Processing) defines lower case mapping in IDNA.
    try:
        domain = idna.encode(parts[1], uts46=True).decode("utf-8")
    except idna.IDNAError:
        raise BadRequest("Not a valid email address.")

    if domain in _blacklisted_email_domains:
        raise BadRequest(f'Email addresses from "{parts[1]}" are not allowed.')


def send_email(
    template: str,
    to: str,
    sender: str = "NeTwerker No Reply <no-reply@netwerker.com>",
    _internal: str = None,
    **kwargs,
):
    """Send an email.

    Send an email using Amazon SES service. The body text is based on 3 email
    templates in '/templates': template.html for HTML formatted emails,
    template.txt for plain text formatted emails, and template-subject.txt for
    the subject line. Any additional keyword arguments passed in here are
    used as replacement values when rendering the templates.

    Parameters
    ----------
    template : str
        The filename (without extension) of the template to use for the email body.
        "template.html", "template.txt", and "template-subject.txt" are expected
        to exist in /templates.

    to : str
        The email address of the recipient.

    sender : str (optional)
        The email address of the sender, no-reply@modobio.com by default.

    _internal : str (optional, testing only)
        Use an internal SES email address to send the email to. Must be one of
        'success', 'bounce', or 'complaint'. This is intended to be used by
        the /client/testemail/ endpoint only.

    **kwargs
        Any other keyword=value pairs will be used as replacement parameters
        when rendering the template.

    Raises
    ------
    :class:`~werkzeug.exceptions.BadRequest`
        Raised when email address is invalid or when email failed to send through
        Amazon SES.
    """
    if _internal:
        if _internal not in ("success", "bounce", "complaint"):
            raise BadRequest("Invalid internal address.")

        to = f"{_internal}@simulator.amazonses.com"

    domain = to.split("@")
    if len(domain) != 2:
        raise BadRequest(f"Email address {to} invalid.")

    # Route emails to AWS mailbox simulator when in DEV environment,
    # unless domain is in the accepted domains list.
    if current_app.debug and domain[1] not in ("gmail.com", "netwerker.com"):
        to = "success@simulator.amazonses.com"

    if template.endswith(".html"):
        template = template[:-5]
    elif template.endswith(".txt"):
        template = template[:-4]

    body_html = render_template(f"{template}.html", **kwargs)
    body_text = render_template(f"{template}.txt", **kwargs)
    subject = render_template(f"{template}-subject.txt", **kwargs)

    destination = {"ToAddresses": [to]}
    message = {
        "Subject": {"Charset": "utf-8", "Data": subject},
        "Body": {
            "Html": {"Charset": "utf-8", "Data": body_html},
            "Text": {"Charset": "utf-8", "Data": body_text},
        },
    }

    # Create a new SES resource; use default region.
    client = boto3.client("ses")
    try:
        response = client.send_email(
            Destination=destination, Message=message, Source=sender
        )
    except ClientError as err:
        # Log extra info to error log, info we don't want in message to end user.
        msg = err.response["Error"]["Message"]
        current_app.logger.error(
            f'Email based on template "{template}" to "{to}" failed with'
            f" error: {msg}"
        )
        raise BadRequest("Email failed to send.")
    else:
        mid = response["MessageId"]
        current_app.logger.info(
            f'Email based on template "{template}" sent to "{to}", message ID:'
            f" {mid}"
        )
