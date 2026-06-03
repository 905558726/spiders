import smtplib
import os
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from imap_tools import MailBox, AND

def sender_email(send_info, receiver_email, file_path):
    msg = MIMEMultipart()

    msg['From'] = send_info['sender_email']
    msg['To'] = receiver_email
    msg['Subject'] = Header("【系统自动发送】", 'utf-8')

    body = "请查收附件中详细数据。如有疑问请回复本邮件。"
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with open(file_path, 'rb') as f:
            # 提取纯文件名，避免路径中包含反斜杠导致附件名错误
            file_name = os.path.basename(file_path)
            part = MIMEApplication(f.read())
            # 这里的 filename 建议处理一下编码
            part.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', file_name))
            msg.attach(part)
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return

    try:
        server = smtplib.SMTP_SSL(send_info['smtp_server'], 465)
        server.login(send_info['sender_email'], send_info['password'])
        server.sendmail(send_info['sender_email'], [receiver_email], msg.as_string())
        server.quit()
        print(f"成功发送至: {receiver_email}")
    except Exception as e:
        print(f"发送给 {receiver_email} 失败: {e}")

def read_email(email_user, email_pass, imap_server, save_path):
    today = datetime.date.today()
    full_path = None
    with MailBox(imap_server).login(email_user, email_pass, 'INBOX') as mailbox:
        criteria = AND(seen=False, date=today, subject='密文订单')
        for msg in mailbox.fetch(criteria, reverse=True, charset='utf-8'):
            print(f"【新邮件】")
            print(f"时间: {msg.date}")
            print(f"主题: {msg.subject}")
            print(f"发件人: {msg.from_}")
            for att in msg.attachments:
                if att.filename.endswith(('.xlsx', '.xls')):
                    full_path = os.path.join(save_path, att.filename)
                    with open(full_path, 'wb') as f:
                        f.write(att.payload)
                    print(f"[已保存] -> {full_path}")
            print("-" * 30)
    return True, full_path

