from django.shortcuts import render,redirect
from django.views.generic.base import View
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth import login,logout,authenticate
from django.db.models import Q
from users.models import UserProfile,EmailVerifyRecord
from .forms import LoginForm,RegisterForm,ForgetPwdForm,ModifyPwdForm
from utils.email_send import send_register_email

# Create your views here.
# 基础ModelBackend类，因为它有authenticate方法
class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 不希望用户存在两个，get只能有一个。两个是get失败的一种原因 Q为使用并集查询
            user = UserProfile.objects.get(Q(username=username)|Q(email=username))

            # django的后台中密码加密：所以不能password==password
            # UserProfile继承的AbstractUser中有def check_password(self, raw_password):
            if user.check_password(password):
                return user
        except Exception as e:
            return None

class IndexView(View):
    def get(self,request):

        return render(request,'html/index.html')

class LoginView(View):
    def get(self,request):
        logout(request)
        return render(request, 'html/login.html')

    def post(self,request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name = request.POST.get('username',None)
            pass_word = request.POST.get('password',None)
            user = authenticate(username=user_name,password=pass_word)
            if user is not None:
                if user.is_active:
                    login(request,user)
                    return redirect('index')
                else:
                    return render(request, 'html/login.html', {'msg': '用户名未激活'})
            else:
                return render(request, 'html/login.html', {'msg': '用户名或密码错误'})
        else:
            return render(request, 'html/login.html', {'login_form':login_form})

class ActiveUserView(View):
    def get(self, request, active_code):
        # 查询邮箱验证记录是否存在
        all_record = EmailVerifyRecord.objects.filter(code = active_code)
        # 如果不为空也就是有用户
        if all_record:
            for record in all_record:
                # 获取到对应的邮箱
                email = record.email
                # 查找到邮箱对应的user
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
                # 激活成功跳转到登录页面
                return render(request, "html/login.html", )
        # 自己瞎输的验证码
        else:
            return render(request, "html/active_fail.html")


class RegisterView(View):
    def get(self,request):
        register_form = RegisterForm()
        return render(request, 'html/register.html',{'register_form':register_form})

    def post(self,request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user_name = request.POST.get('email',None)
            if UserProfile.objects.filter(email = user_name):
                return render(request, 'html/login.html', {'register_form':register_form, 'msg': u'用户名已存在'})

            pass_word = request.POST.get('password',None)
            user_profile = UserProfile()
            user_profile.username = user_name
            user_profile.email = user_name
            user_profile.is_active = False

            user_profile.password = make_password(pass_word)
            user_profile.save()
            send_register_email(user_name,'register')
            return render(request, 'html/login.html', {'msg': u'邮箱已发送验证码，进去邮箱激活'})
        else:
            return render(request, 'html/register.html', {'register_form':register_form})


class ForgetPwdView(View):
    def get(self,request):
        forget_form = ForgetPwdForm()
        return render(request,'html/forgetpwd.html',{'forget_form':forget_form})
    def post(self,request):
        forget_form = ForgetPwdForm(request.POST)
        if forget_form.is_valid():
            email = request.POST.get('email',None)
            send_register_email(email,'forget')
            return render(request, 'html/forgetpwd.html',{'msg': u'邮箱已发送验证码，进去邮箱修改'})
        else:
            return render(request,'html/forgetpwd.html',{'forget_form':forget_form})


class ResetView(View):
    def get(self,request,active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                return render(request,'html/password_reset.html',{'email':email})
        else:
            return render(request,'html/active_fail.html')
        return render(request,'html/login.html')

class ModifyPwdView(View):
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", None)
            pwd2 = request.POST.get("password2", None)
            email = request.POST.get("email", None)
            if pwd1 != pwd2:
                return render(request, "html/password_reset.html", {"email":email, "msg":"密码不一致！"})
            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd2)
            user.save()

            return render(request, "html/login.html")
        else:
            email = request.POST.get("email", "")
            return render(request, "html/password_reset.html", {"email":email, "modify_form":modify_form })
















