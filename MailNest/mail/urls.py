from django.urls import path
from .views import (
    login_view,
    home_view,
    send_email_view,
    inbox_view,
    UploadAttachmentView,
    DownloadAttachmentView,
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('home/', home_view, name='home'), 
    path('send_email/', send_email_view, name='send_email'),
    path('inbox/', inbox_view, name='inbox'),
    path('upload_attachment/', UploadAttachmentView.as_view(), name='upload_attachment'),
    path('download_attachment/<int:id>/', DownloadAttachmentView.as_view(), name='download_attachment'),
]
