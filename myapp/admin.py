from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import VisitorLog

@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = (
        'visit_time_formatted',
        'ip_address',
        'isp_and_asn',
        'location_summary',
        'positioning_badge',
        'vpn_status_badge',
        'device_summary',
        'google_maps_button'
    )
    list_filter = (
        'positioning_method',
        'is_vpn_or_proxy',
        'country',
        'governorate',
        'os',
        'browser',
        'visit_time'
    )
    search_fields = (
        'ip_address',
        'webrtc_local_ip',
        'webrtc_public_ip',
        'governorate',
        'city',
        'full_address',
        'isp',
        'asn',
        'user_agent'
    )
    readonly_fields = (
        'visit_time',
        'google_maps_display',
        'vpn_analysis_display',
        'accuracy_display'
    )

    fieldsets = (
        ("🌐 الاستخبارات الشبكية وهوية الاتصال", {
            'fields': (
                'ip_address',
                'isp',
                'asn',
                'is_vpn_or_proxy',
                'vpn_analysis_display',
                'webrtc_local_ip',
                'webrtc_public_ip',
            )
        }),
        ("📍 الموقع الجغرافي والإحداثيات (GPS / Geolocation)", {
            'fields': (
                'positioning_method',
                'google_maps_display',
                'accuracy_display',
                ('latitude', 'longitude'),
                ('altitude', 'altitude_accuracy'),
                ('heading', 'speed'),
                'full_address',
                ('city', 'governorate', 'country'),
            )
        }),
        ("💻 بصمة الجهاز والعتاد (Hardware & Device Fingerprint)", {
            'fields': (
                ('device_type', 'os', 'browser'),
                ('screen_resolution', 'cpu_cores', 'device_memory_gb'),
                ('battery_level', 'is_charging'),
                ('language', 'timezone_browser', 'timezone_ip'),
            )
        }),
        ("📋 البيانات الفنية الأولية (Metadata)", {
            'classes': ('collapse',),
            'fields': (
                'visit_time',
                'referrer',
                'user_agent',
            )
        }),
    )

    def visit_time_formatted(self, obj):
        return obj.visit_time.strftime('%Y-%m-%d %H:%M:%S')
    visit_time_formatted.short_description = "وقت الالتقاط"
    visit_time_formatted.admin_order_field = 'visit_time'

    def isp_and_asn(self, obj):
        if obj.isp and obj.asn:
            return f"{obj.isp} ({obj.asn})"
        return obj.isp or obj.asn or "-"
    isp_and_asn.short_description = "مزود الخدمة (ISP)"

    def location_summary(self, obj):
        city = obj.city or ""
        gov = obj.governorate or ""
        if city and gov and city != gov:
            return f"{city} - {gov}"
        return city or gov or obj.country or "غير محدد"
    location_summary.short_description = "المنطقة / المدينة"

    def positioning_badge(self, obj):
        method = obj.positioning_method or ""
        if "GPS" in method or (obj.accuracy > 0 and obj.accuracy <= 50):
            return format_html(
                '<span style="background:#16a34a; color:white; padding:4px 8px; border-radius:6px; font-weight:bold; font-size:12px;">🛰️ GPS دقيق (±{}m)</span>',
                int(obj.accuracy) if obj.accuracy else 0
            )
        elif "Wi-Fi" in method or (obj.accuracy > 0 and obj.accuracy <= 500):
            return format_html(
                '<span style="background:#2563eb; color:white; padding:4px 8px; border-radius:6px; font-size:12px;">📶 Wi-Fi (±{}m)</span>',
                int(obj.accuracy) if obj.accuracy else 0
            )
        elif obj.accuracy > 0:
            return format_html(
                '<span style="background:#d97706; color:white; padding:4px 8px; border-radius:6px; font-size:12px;">📡 شبكي (±{}m)</span>',
                int(obj.accuracy)
            )
        return mark_safe('<span style="color:#64748b; font-size:12px;">🌐 تقريب IP</span>')
    positioning_badge.short_description = "وسيلة ودقة التحديد"

    def vpn_status_badge(self, obj):
        if obj.is_vpn_or_proxy:
            return mark_safe(
                '<span style="background:#dc2626; color:white; padding:3px 7px; border-radius:5px; font-weight:bold; font-size:11px;">⚠️ اشتباه VPN/Proxy</span>'
            )
        return mark_safe(
            '<span style="color:#16a34a; font-weight:bold; font-size:12px;">✓ اتصال مباشر</span>'
        )
    vpn_status_badge.short_description = "فحص الـ VPN"

    def device_summary(self, obj):
        parts = [p for p in [obj.device_type, obj.os, obj.browser] if p and p != 'Unknown']
        return " | ".join(parts) if parts else "غير محدد"
    device_summary.short_description = "الجهاز والنظام"

    def google_maps_button(self, obj):
        url = obj.google_maps_url
        if url:
            return format_html(
                '<a href="{}" target="_blank" style="background:#0284c7; color:white; padding:5px 10px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:12px; display:inline-block;">🗺️ عرض الخريطة</a>',
                url
            )
        return "-"
    google_maps_button.short_description = "الخريطة"

    def google_maps_display(self, obj):
        url = obj.google_maps_url
        if url:
            return format_html(
                '<div style="margin:10px 0;"><a href="{}" target="_blank" style="background:#0284c7; color:white; padding:8px 16px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:14px; display:inline-flex; align-items:center; gap:8px;">📍 فتح الموقع الدقيق على Google Maps (إحداثيات: {}, {})</a></div>',
                url, obj.latitude, obj.longitude
            )
        return "لا تتوفر إحداثيات صالحة للخريطة"
    google_maps_display.short_description = "رابط الخريطة المباشر"

    def accuracy_display(self, obj):
        if obj.accuracy > 0:
            return f"± {obj.accuracy:.1f} متر ({obj.positioning_method})"
        return "غير محددة بدقة الأمتار (تقريب مزود الخدمة)"
    accuracy_display.short_description = "هامش دقة الموقع"

    def vpn_analysis_display(self, obj):
        reasons = []
        if obj.is_vpn_or_proxy:
            reasons.append("تم اكتشاف وجود Proxy/Datacenter في بيانات مزود الخدمة.")
        if obj.webrtc_public_ip and obj.ip_address and obj.webrtc_public_ip != obj.ip_address:
            reasons.append(f"تسريب WebRTC: الـ IP المسرب ({obj.webrtc_public_ip}) يختلف عن الـ IP المتصل ({obj.ip_address})!")
        if obj.timezone_browser and obj.timezone_ip and obj.timezone_browser != obj.timezone_ip:
            reasons.append(f"اختلاف النطاق الزمني: توقيت المتصفح ({obj.timezone_browser}) يختلف عن توقيت الـ IP ({obj.timezone_ip})!")
        
        if reasons:
            return format_html('<div style="color:#b91c1c; font-weight:bold; line-height:1.6;">⚠️ تنبيهات أمنية:<br>• {}</div>', mark_safe("<br>• ".join(reasons)))
        return mark_safe('<span style="color:#16a34a; font-weight:bold;">لا توجد مؤشرات تزييف أو تسريب مسجلة.</span>')
    vpn_analysis_display.short_description = "تقرير تحليل التزييف"

