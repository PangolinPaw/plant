from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import base64
from mimetypes import MimeTypes
import os

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEImage import MIMEImage
from email.MIMEAudio import MIMEAudio
from email import encoders

def sendSMTP(account, password, recipient, subject, body, attachment=None):
    msg = MIMEMultipart()
    msg['From'] = account
    msg['To'] = recipient
    msg['Subject'] = subject
    msg = MIMEMultipart()
    msg['From'] = account
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment != None:
        attachment = open(attachment, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= {}".format(attachment))
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(account, password)
    text = msg.as_string()
    server.sendmail(account, recipient, text)
    server.quit()

def authAPI():
    # Setup the Gmail API
    SCOPES = 'https://www.googleapis.com/auth/gmail.compose'
    store = file.Storage('/home/pi/plant/credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('/home/pi/plant/client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('gmail', 'v1', http=creds.authorize(Http()))
    return service

def sendAPI(sender, to, subject, body, attachment=None):
    try:
        service = authAPI()

        message = MIMEMultipart()
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject

        msg = MIMEText(body, 'html')
        message.attach(msg)

        if attachment != None:
            mime = MimeTypes()
            content_type, encoding = mime.guess_type(attachment)

            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            main_type, sub_type = content_type.split('/', 1)

            if main_type == 'text':
                fp = open(attachment, 'rb')
                msg = MIMEText(fp.read(), _subtype=sub_type)
                fp.close()
            elif main_type == 'image':
                fp = open(attachment, 'rb')
                msg = MIMEImage(fp.read(), _subtype=sub_type)
                fp.close()
            elif main_type == 'audio':
                fp = open(attachment, 'rb')
                msg = MIMEAudio(fp.read(), _subtype=sub_type)
                fp.close()
            else:
                fp = open(attachment, 'rb')
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(fp.read())
                fp.close()
            filename = os.path.basename(attachment)
            msg.add_header('Content-Disposition', 'attachment', filename=filename)
        
        message.attach(msg)
        message = {'raw': base64.urlsafe_b64encode(message.as_string()), 'payload': {'mimeType': 'text/html'}}
        message = (service.users().messages().send(userId=sender, body=message)
                    .execute())
        return True, ''
    
    except Exception, error:
        return False, error


