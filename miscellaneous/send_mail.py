import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def send_mail(  # pylint: disable=too-many-arguments
    icloud_id: str,
    icloud_pass: str,
    to_address: str,
    subject: str,
    message: str,
    files: list[Path],
):
    msg = MIMEMultipart()
    msg["From"] = icloud_id
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(message + "\n\n"))

    for path in files:
        part = MIMEBase("application", "octet-stream")
        with open(path, "rb") as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", "attachment; filename={}".format(path.name)
        )
        msg.attach(part)

    mailserver = smtplib.SMTP("smtp.mail.me.com", 587)
    # identify ourselves
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login(icloud_id, icloud_pass)
    mailserver.sendmail(icloud_id, to_address, msg.as_string())

    mailserver.quit()
