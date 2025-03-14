from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        # ユーザー認証
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 認証成功
            login(request, user)
            return redirect('home')  
        else:
            # 認証失敗
            error_message = "ユーザー名またはパスワードが間違っています。"
            print(f"Authentication failed for username: {username}")
            return render(request, 'login.html', {'error_message': error_message})
    
    return render(request, 'login.html')


def home_view(request):
    return render(request, 'home.html')