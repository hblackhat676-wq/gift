import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    print(f"جاري تنفيذ: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    print("=== بدء إنشاء المشروع والبيئة ===")

    # 1. إنشاء البيئة الوهمية (Virtual Environment)
    run_command(f'"{sys.executable}" -m venv venv')

    # تحديد مسارات التشغيل بناءً على نظام التشغيل (ويندوز أو لينكس/ماك)
    if os.name == 'nt':
        pip_cmd = r"venv\Scripts\pip"
        python_cmd = r"venv\Scripts\python"
        django_admin_cmd = r"venv\Scripts\django-admin"
    else:
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
        django_admin_cmd = "venv/bin/django-admin"

    # 2. إنشاء ملف المتطلبات وتثبيتها
    requirements_content = """Django==5.0.3\nrequests==2.31.0\ngunicorn==21.2.0\n"""
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)
    
    run_command(f'"{pip_cmd}" install -r requirements.txt')

    # 3. إنشاء مشروع وتطبيق ديجانقو
    run_command(f'"{django_admin_cmd}" startproject myproject .')
    run_command(f'"{python_cmd}" manage.py startapp myapp')

    # 4. إعداد الملفات والمجلدات
    files_to_create = {}

    # ملف التجهيز لـ Render
    files_to_create["build.sh"] = """#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
"""

    # ملف myapp/models.py
    files_to_create["myapp/models.py"] = """from django.db import models
from django.utils import timezone

class VisitorLog(models.Model):
    ip_address = models.GenericIPAddressField(verbose_name="عنوان IP")
    governorate = models.CharField(max_length=100, verbose_name="المحافظة")
    visit_time = models.DateTimeField(default=timezone.now, verbose_name="وقت الزيارة")

    class Meta:
        verbose_name = "سجل الزيارة"
        verbose_name_plural = "سجلات الزوار"
        
    def __str__(self):
        return f"{self.governorate} - {self.ip_address}"
"""

    # ملف myapp/admin.py
    files_to_create["myapp/admin.py"] = """from django.contrib import admin
from .models import VisitorLog

@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'governorate', 'visit_time')
    list_filter = ('governorate', 'visit_time')
    search_fields = ('ip_address', 'governorate')
"""

    # ملف myapp/views.py
    files_to_create["myapp/views.py"] = """import requests
from django.shortcuts import render
from django.http import HttpResponseForbidden
from .models import VisitorLog

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def secure_login_view(request):
    user_ip = get_client_ip(request)
    api_key = "YOUR_API_KEY_HERE"
    user_governorate = "غير محدد"

    if user_ip != '127.0.0.1':
        api_url = f"https://proxycheck.io/v2/{user_ip}?key={api_key}&vpn=1"
        try:
            response = requests.get(api_url, timeout=5).json()
            if user_ip in response:
                data = response[user_ip]
                is_vpn = data.get('proxy', 'no')
                country = data.get('isocode', '')

                if is_vpn == 'yes':
                    return HttpResponseForbidden("<h2 style='color:red; text-align:center; font-family:sans-serif; margin-top:50px;'>تم حظر الوصول: يُمنع استخدام شبكات VPN.</h2>")
                
                if country != 'YE':
                    return HttpResponseForbidden("<h2 style='color:red; text-align:center; font-family:sans-serif; margin-top:50px;'>الوصول متاح من داخل اليمن فقط.</h2>")
                
                user_governorate = data.get('region', 'غير محدد')
        except requests.exceptions.RequestException:
            pass 

    VisitorLog.objects.create(ip_address=user_ip, governorate=user_governorate)
    context = {'governorate': user_governorate}
    return render(request, 'login.html', context)
"""

    # ملف myapp/urls.py
    files_to_create["myapp/urls.py"] = """from django.urls import path
from . import views

urlpatterns = [
    path('', views.secure_login_view, name='login_page'),
]
"""

    # ملف myproject/urls.py (تحديث الملف الافتراضي)
    files_to_create["myproject/urls.py"] = """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),
]
"""

    # قالب HTML
    templates_dir = Path("myapp/templates")
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    files_to_create["myapp/templates/login.html"] = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .ads-container { background: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; margin-bottom: 20px; width: 320px; text-align: center; border: 1px solid #ffeeba; }
        .login-container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 320px; text-align: center; }
        input[type="text"], input[type="password"] { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;}
        input[type="submit"] { background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; width: 90%; font-size: 16px; margin-top: 10px;}
    </style>
</head>
<body>
    <div class="ads-container">
        {% if governorate == "Amanat Al Asimah" or governorate == "Sana'a" %}
            <p>إعلان: عروض خاصة لزوارنا من <b>صنعاء</b>!</p>
        {% elif governorate == "Aden" %}
            <p>إعلان: تخفيضات حصرية لسكان <b>عدن</b>!</p>
        {% elif governorate == "Ta'izz" %}
            <p>إعلان: خصم 20% لفترة محدودة لسكان <b>تعز</b>!</p>
        {% else %}
            <p>أهلاً بك! أنت تتصفح من: <b>{{ governorate }}</b></p>
        {% endif %}
    </div>

    <div class="login-container">
        <h2>تسجيل الدخول</h2>
        <form method="POST">
            {% csrf_token %}
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <input type="submit" value="دخول">
        </form>
    </div>
</body>
</html>
"""

    # كتابة جميع الملفات
    for filepath, content in files_to_create.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"تم إنشاء وتعبئة: {filepath}")

    # 5. تعديل ملف myproject/settings.py
    settings_path = "myproject/settings.py"
    with open(settings_path, "a", encoding="utf-8") as f:
        f.write("\n# --- الإعدادات المضافة تلقائياً ---")
        f.write("\nimport os")
        f.write("\nALLOWED_HOSTS = ['*']")
        f.write("\nSECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')")
        f.write("\nINSTALLED_APPS.append('myapp')")
        f.write("\nTEMPLATES[0]['DIRS'] = [BASE_DIR / 'myapp' / 'templates']")
        f.write("\nSTATIC_URL = 'static/'")
        f.write("\nSTATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')\n")
    print(f"تم تعديل: {settings_path}")

    print("\n=== اكتمل إنشاء المشروع بنجاح! ===")
    print("الخطوات التالية:")
    print("1. لا تنسَ وضع الـ API Key في ملف myapp/views.py")
    if os.name == 'nt':
        print(r"2. لتفعيل البيئة: venv\Scripts\activate")
    else:
        print("2. لتفعيل البيئة: source venv/bin/activate")
    print("3. لتجهيز قاعدة البيانات: python manage.py migrate")
    print("4. لتشغيل السيرفر: python manage.py runserver")

if __name__ == "__main__":
    main()