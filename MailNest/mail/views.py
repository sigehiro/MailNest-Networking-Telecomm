import aiosqlite
import asyncio
import smtplib
import re
import os
import mimetypes
from .models import Email, Attachment
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse 

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']  
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # success to authenticate
            login(request, user)
            
            # Update email address
            user.email = email
            user.save()  
            
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

        # CC and BCC list validation
        cc_recipients = [email.strip() for email in cc_list.split(',')] if cc_list else []
        bcc_recipients = [email.strip() for email in bcc_list.split(',')] if bcc_list else []

        # Display error messages if present
        if error_messages:
            return render(request, 'send_email.html', {'error_message': ' '.join(error_messages)})

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = from_address
        msg['To'] = ', '.join(recipients)  
        msg['Cc'] = ', '.join(cc_recipients)  
        msg['Subject'] = subject  

        # Attach email body
        msg.attach(MIMEText(message, 'plain'))
        
        # Attachments file handling
        if request.FILES:
            for uploaded_file in request.FILES.getlist('attachments'):
                try:
                    part = MIMEBase('application', 'octet-stream')
                    content = uploaded_file.read()
                    if not content:
                        print(f"Failed to read content from {uploaded_file.name}. It might be empty.")
                        continue
                    
                    part.set_payload(content)

                    # Determine the MIME type of the file
                    mime_type, _ = mimetypes.guess_type(uploaded_file.name)
                    if mime_type:
                        part.set_type(mime_type)
                    else:
                        part.set_type('application/octet-stream')  # Default to binary
                    
                    encoders.encode_base64(part)  # Base64でエンコード
                    part.add_header('Content-Disposition', f'attachment; filename="{uploaded_file.name}"')
                    msg.attach(part)

                    print(f"Attached file: {uploaded_file.name} with MIME type: {mime_type}")

                except Exception as e:
                    print(f"Error processing file {uploaded_file.name}: {str(e)}")


        # Check for any errors after processing attachments
        if error_messages:
            return render(request, 'send_email.html', {'error_message': ' '.join(error_messages)})

        try:
            # Connect to SMTP server and send email
            with smtplib.SMTP('localhost', 2525) as server:
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
            error_message = f"An error occurred while sending the email: {str(e)}"
            return render(request, 'send_email.html', {'error_message': error_message})

    return render(request, 'send_email.html')


# async def fetch_emails():
#     async with aiosqlite.connect('db.sqlite3') as db:
#         async with db.execute("SELECT * FROM mail_email WHERE is_sent = 1 ORDER BY timestamp DESC") as cursor:
#             rows = await cursor.fetchall()
#             columns = [column[0] for column in cursor.description]
#             return [dict(zip(columns, row)) for row in rows]
async def fetch_emails():
    async with aiosqlite.connect('db.sqlite3') as db:
        async with db.execute("SELECT * FROM mail_email WHERE is_sent = 1 ORDER BY timestamp DESC") as cursor:
            rows = await cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            emails = [dict(zip(columns, row)) for row in rows]
            
            # 添付ファイル情報を取得
            for email in emails:
                email['attachments'] = await fetch_attachments(email['id'])  # この関数を実装する必要があります

            return emails

async def fetch_attachments(email_id):
    async with aiosqlite.connect('db.sqlite3') as db:
        async with db.execute("SELECT * FROM mail_attachment WHERE email_id = ?", (email_id,)) as cursor:
            rows = await cursor.fetchall()
            return [{'name': row[2], 'url': row[3]} for row in rows]  # filenameとfile_pathを返す


def inbox_view(request):
    emails = asyncio.run(fetch_emails())
    return render(request, 'inbox.html', {'emails': emails})


class UploadAttachmentView(View):
    def post(self, request):
        email_id = request.POST.get('email_id')
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.url(filename)

        attachment = Attachment(email_id=email_id, file_name=uploaded_file.name, file_path=file_path)
        attachment.save()

        return JsonResponse({'success': True, 'file_path': file_path})

# class DownloadAttachmentView(View):
#     def get(self, request, id):
#         try:
#             attachment = Attachment.objects.get(id=id)
#             file_path = attachment.file_path
#             # ファイルを返す処理（例: HttpResponse、FileResponseなどを使用）
#             return JsonResponse({'file_path': file_path})
#         except Attachment.DoesNotExist:
#             return JsonResponse({'success': False, 'error': 'File not found'}, status=404)



class DownloadAttachmentView(View):
    def get(self, request, id):
        try:
            attachment = Attachment.objects.get(id=id)
            file_path = attachment.file_path
            
            # ファイルを返す処理（HttpResponseを使用）
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
                return response
        except Attachment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'File not found'}, status=404)

