from django.urls import path
from .views import login_view, home_view, send_email_view, inbox_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('home/', home_view, name='home'), 
    path('send_email/', send_email_view, name='send_email'),
    path('inbox/', inbox_view, name='inbox'),
]
