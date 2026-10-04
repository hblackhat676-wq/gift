from django.db import models
from django.utils import timezone

class VisitorLog(models.Model):
    # بيانات الشبكة وعنوان الاتصال
    ip_address = models.GenericIPAddressField(verbose_name="عنوان IP", blank=True, null=True)
    country = models.CharField(max_length=100, verbose_name="الدولة", default="غير محدد")
    governorate = models.CharField(max_length=200, verbose_name="المحافظة / المنطقة", blank=True, null=True)
    city = models.CharField(max_length=100, verbose_name="المدينة", blank=True, null=True)
    full_address = models.TextField(verbose_name="العنوان التفصيلي (الشارع/الحي)", blank=True, null=True)
    
    # الاستخبارات الشبكية (Forensic Network Intelligence)
    isp = models.CharField(max_length=150, verbose_name="مزود خدمة الإنترنت (ISP)", blank=True, null=True)
    asn = models.CharField(max_length=50, verbose_name="رقم النظام المستقل (ASN)", blank=True, null=True)
    is_vpn_or_proxy = models.BooleanField(verbose_name="اشتباه VPN أو Proxy", default=False)
    webrtc_local_ip = models.CharField(max_length=100, verbose_name="الـ IP المحلي الداخلي (WebRTC)", blank=True, null=True)
    webrtc_public_ip = models.CharField(max_length=100, verbose_name="الـ IP العام المسرب (WebRTC)", blank=True, null=True)
    
    # الإحداثيات الجغرافية وتحديد الموقع بدقة
    latitude = models.FloatField(verbose_name="خط العرض (Latitude)", default=0.0)
    longitude = models.FloatField(verbose_name="خط الطول (Longitude)", default=0.0)
    accuracy = models.FloatField(verbose_name="دقة الموقع بالأمتار (Accuracy)", default=0.0)
    altitude = models.FloatField(verbose_name="الارتفاع بالمتر (Altitude)", blank=True, null=True)
    altitude_accuracy = models.FloatField(verbose_name="دقة الارتفاع بالمتر", blank=True, null=True)
    heading = models.FloatField(verbose_name="اتجاه الحركة (درجة)", blank=True, null=True)
    speed = models.FloatField(verbose_name="السرعة (متر/ثانية)", blank=True, null=True)
    positioning_method = models.CharField(max_length=50, verbose_name="وسيلة التحديد", default="IP Geolocation")
    
    # بيانات الجهاز والعتاد (Device & Hardware Fingerprinting)
    device_type = models.CharField(max_length=50, verbose_name="نوع الجهاز", blank=True, null=True)
    browser = models.CharField(max_length=100, verbose_name="المتصفح", blank=True, null=True)
    os = models.CharField(max_length=100, verbose_name="نظام التشغيل", blank=True, null=True)
    screen_resolution = models.CharField(max_length=50, verbose_name="دقة الشاشة", blank=True, null=True)
    cpu_cores = models.IntegerField(verbose_name="عدد أنوية المعالج", blank=True, null=True)
    device_memory_gb = models.FloatField(verbose_name="الذاكرة RAM (GB تقريبية)", blank=True, null=True)
    battery_level = models.CharField(max_length=20, verbose_name="نسبة البطارية", blank=True, null=True)
    is_charging = models.BooleanField(verbose_name="متصل بالشاحن", default=False)
    
    # التحليل الزمني واللغوي
    timezone_browser = models.CharField(max_length=100, verbose_name="منطقة توقيت الجهاز", blank=True, null=True)
    timezone_ip = models.CharField(max_length=100, verbose_name="منطقة توقيت الـ IP", blank=True, null=True)
    language = models.CharField(max_length=50, verbose_name="لغة الجهاز", blank=True, null=True)
    
    # بيانات إضافية
    user_agent = models.TextField(verbose_name="User Agent الكامل", blank=True, null=True)
    referrer = models.URLField(verbose_name="الصفحة السابقة", blank=True, null=True)
    visit_time = models.DateTimeField(default=timezone.now, verbose_name="وقت الزيارة والالتقاط")

    class Meta:
        verbose_name = "سجل الزيارة الجنائي"
        verbose_name_plural = "سجلات التحقيق والزوار"
        ordering = ['-visit_time']

    @property
    def google_maps_url(self):
        if self.latitude and self.longitude and (self.latitude != 0.0 or self.longitude != 0.0):
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None

    def __str__(self):
        acc = f"(±{int(self.accuracy)}m)" if self.accuracy > 0 else ""
        return f"[{self.positioning_method}] {self.ip_address or 'Unknown'} - {self.city or self.governorate or 'Unknown'} {acc}"
