import os
from pathlib import Path

def main():
    print("=== بدء تحديث ملفات المشروع ===")

    files_to_update = {}

    # 1. تحديث نموذج قاعدة البيانات (إضافة حقل الدولة)
    files_to_update["myapp/models.py"] = """from django.db import models
from django.utils import timezone

class VisitorLog(models.Model):
    ip_address = models.GenericIPAddressField(verbose_name="عنوان IP")
    country = models.CharField(max_length=100, verbose_name="الدولة", default="اليمن")
    governorate = models.CharField(max_length=100, verbose_name="المحافظة")
    visit_time = models.DateTimeField(default=timezone.now, verbose_name="وقت الزيارة")

    class Meta:
        verbose_name = "سجل الزيارة"
        verbose_name_plural = "سجلات الزوار"
        
    def __str__(self):
        return f"{self.country} - {self.governorate} - {self.ip_address}"
"""

    # 2. تحديث لوحة الإدارة
    files_to_update["myapp/admin.py"] = """from django.contrib import admin
from .models import VisitorLog

@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'country', 'governorate', 'visit_time')
    list_filter = ('country', 'governorate', 'visit_time')
    search_fields = ('ip_address', 'governorate', 'country')
"""

    # 3. تحديث واجهة العرض (بدون فورم دخول، عرض ترحيب فقط)
    files_to_update["myapp/views.py"] = """import requests
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

def public_welcome_view(request):
    user_ip = get_client_ip(request)
    api_key = "YOUR_API_KEY_HERE"
    user_governorate = "غير محدد"
    user_country = "اليمن"

    if user_ip != '127.0.0.1':
        api_url = f"https://proxycheck.io/v2/{user_ip}?key={api_key}&vpn=1"
        try:
            response = requests.get(api_url, timeout=5).json()
            if user_ip in response:
                data = response[user_ip]
                is_vpn = data.get('proxy', 'no')
                country_code = data.get('isocode', '')
                user_country = data.get('country', 'غير محدد')

                if is_vpn == 'yes':
                    return HttpResponseForbidden("<h2 style='color:red; text-align:center; margin-top:50px;'>عذراً، يُمنع استخدام شبكات VPN.</h2>")
                
                if country_code != 'YE':
                    return HttpResponseForbidden("<h2 style='color:red; text-align:center; margin-top:50px;'>هذا الموقع متاح من داخل اليمن فقط.</h2>")
                
                user_governorate = data.get('region', 'غير محدد')
        except requests.exceptions.RequestException:
            pass 

    VisitorLog.objects.create(ip_address=user_ip, country=user_country, governorate=user_governorate)
    context = {'governorate': user_governorate}
    return render(request, 'welcome.html', context)
"""

    # 4. تحديث الروابط
    files_to_update["myapp/urls.py"] = """from django.urls import path
from . import views

urlpatterns = [
    path('', views.public_welcome_view, name='welcome_page'),
]
"""

    # 5. قالب صفحة الترحيب (welcome.html)
    templates_dir = Path("myapp/templates")
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    files_to_update["myapp/templates/welcome.html"] = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مرحباً بك في موقعنا</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .welcome-container { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 80%; max-width: 600px; text-align: center; }
        .ads-container { background: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: center; border: 1px solid #ffeeba; }
        h1 { color: #28a745; margin-bottom: 10px; }
        p { font-size: 18px; color: #555; }
    </style>
</head>
<body>
    <div class="welcome-container">
        <h1>مرحباً بك في موقعنا!</h1>
        <p>نحن سعداء بزيارتك، ونتمنى لك تصفحاً ممتعاً.</p>

        <div class="ads-container">
            {% if governorate == "Amanat Al Asimah" or governorate == "Sana'a" %}
                <p>إعلان خاص: عروض مميزة لزوارنا من <b>صنعاء</b>!</p>
            {% elif governorate == "Aden" %}
                <p>إعلان خاص: تخفيضات حصرية لسكان <b>عدن</b>!</p>
            {% elif governorate == "Ta'izz" %}
                <p>إعلان خاص: خصم 20% لفترة محدودة لسكان <b>تعز</b>!</p>
            {% else %}
                <p>أهلاً بك! أنت تتصفح من: <b>{{ governorate }}</b></p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

    # كتابة وتحديث الملفات
    for filepath, content in files_to_update.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"تم تحديث: {filepath}")

    print("\n=== تم تحديث جميع الملفات بنجاح! ===")
    print("الآن قم بتنفيذ الأوامر التالية لتطبيق التغييرات على قاعدة البيانات:")
    print("1. python manage.py makemigrations")
    print("2. python manage.py migrate")
    print("3. python manage.py runserver")

if __name__ == "__main__":
    main()