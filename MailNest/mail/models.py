from django.db import models

class User(models.Model):
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=12)

class Email(models.Model):
    sender = models.CharField(max_length=64)
    recipients = models.TextField()
    cc = models.TextField(blank=True, null=True)
    bcc = models.TextField(blank=True, null=True)
    subject = models.CharField(max_length=25)
    body = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)

class Attachment(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_path = models.TextField()
