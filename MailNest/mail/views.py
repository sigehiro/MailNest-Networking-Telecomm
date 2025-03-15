import aiosqlite
import asyncio
import smtplib
import re
from .models import Email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # success to authenticate
            login(request, user)
            return redirect('home')  
        else:
            # Failed to authenticate
            error_message = "Incorrect user name or password."
            print(f"Authentication failed for username: {username}")
            return render(request, 'login.html', {'error_message': error_message})
    
    return render(request, 'login.html')


def home_view(request):
    return render(request, 'home.html')


def is_valid_email(email):
    """メールアドレスのバリデーションを行う関数"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None


def send_email_view(request):
    if request.method == "POST":
        subject = request.POST['subject']
        message = request.POST['message']
        recipient_list = request.POST['recipient']  # To
        cc_list = request.POST.get('cc', '')  # CC (optional)
        bcc_list = request.POST.get('bcc', '')  # BCC (optional)
        from_address = 'tebu826@f5.si'  # From email address

        # Validate recipient list
        recipients = [email.strip() for email in recipient_list.split(',')]
        invalid_recipients = [recipient for recipient in recipients if not is_valid_email(recipient)]

        error_messages = []
        
        if invalid_recipients:
            error_messages.append(f"Invalid recipient email addresses: {', '.join(invalid_recipients)}")

        # CC list validation (only if input is present)
        if cc_list:
            cc_recipients = [email.strip() for email in cc_list.split(',')]
            invalid_cc_recipients = [recipient for recipient in cc_recipients if not is_valid_email(recipient)]
            if invalid_cc_recipients:
                error_messages.append(f"Invalid CC email addresses: {', '.join(invalid_cc_recipients)}")
        else:
            cc_recipients = []

        # BCC list validation (only if input is present)
        if bcc_list:
            bcc_recipients = [email.strip() for email in bcc_list.split(',')]
            invalid_bcc_recipients = [recipient for recipient in bcc_recipients if not is_valid_email(recipient)]
            if invalid_bcc_recipients:
                error_messages.append(f"Invalid BCC email addresses: {', '.join(invalid_bcc_recipients)}")
        else:
            bcc_recipients = []

        # Display error messages if present
        if error_messages:
            return render(request, 'send_email.html', {'error_message': ' '.join(error_messages)})


        # Create email message
        msg = MIMEMultipart()
        msg['From'] = from_address
        msg['To'] = ', '.join(recipients)  # Display recipient list as comma-separated
        msg['Cc'] = ', '.join(cc_recipients)  
        msg['Subject'] = subject  

        # Attach email body
        msg.attach(MIMEText(message, 'plain'))

        try:
            # Connect to SMTP server and send email
            with smtplib.SMTP('localhost', 2525) as server:
                # Add CC and BCC to recipient list
                all_recipients = recipients + cc_recipients + bcc_recipients
                server.send_message(msg, to_addrs=all_recipients)

            email_record = Email(
                sender=from_address,
                recipients=', '.join(recipients),
                cc=', '.join(cc_recipients),
                bcc=', '.join(bcc_recipients),
                subject=subject,
                body=message,
                is_sent=True
            )
            email_record.save()  

            success_message = "Email sent successfully."
            return render(request, 'send_email.html', {'success_message': success_message})
        except Exception as e:
            error_message = f"Failed to send email: {str(e)}"
            return render(request, 'send_email.html', {'error_message': error_message})

    return render(request, 'send_email.html')



async def fetch_emails():
    async with aiosqlite.connect('db.sqlite3') as db:
        async with db.execute("SELECT * FROM mail_email WHERE is_sent = 1 ORDER BY timestamp DESC") as cursor:
            rows = await cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]


def inbox_view(request):
    emails = asyncio.run(fetch_emails())
    return render(request, 'inbox.html', {'emails': emails})
