import smtplib, ssl
from os import environ
from oslash import Right
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from dotenv import load_dotenv

load_dotenv()

def send_email(receiver: str, file_name: str, pharmacy_id: int) -> bool:
  receiver = receiver
  msg = MIMEMultipart()
  password = environ["EMAIL_PASSWORD"]
  sender = environ["EMAIL_USER"]
  subject = f'UTEKA PARSING FOR ID: {pharmacy_id}'
  
  msg['From'] = sender
  msg['To'] = receiver
  msg['Subject'] = subject
  
  with open(file_name,'rb') as file:
    msg.attach(MIMEApplication(file.read(), Name=file_name))
  
  context = ssl.create_default_context()
  
  with smtplib.SMTP_SSL('smtp.gmail.com', port=465, context=context) as smtp:
    smtp.login(sender, password)
    smtp.sendmail(sender, receiver, msg.as_string())
  return Right(True)