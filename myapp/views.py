import json
import urllib.request
import urllib.error
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.utils import timezone
from .models import VisitorLog

def get_client_ip(request):
    """
    استخراج عنوان الـ IP الحقيقي للمتصل بدقة، مع مراعاة السيرفرات السحابية
    وخدمات البروكسي العكسي (Render, Cloudflare, AWS, Heroku, Nginx)
    """
    # 1. ترويسة X-Forwarded-For (الأولوية القصوى لخوادم Render و AWS حيث يكون أول IP هو جهاز العميل الحقيقي)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ips = [ip.strip() for ip in x_forwarded_for.split(',')]
        # استبعاد عناوين الشبكات الداخلية واستخراج أول IP عام حقيقي للزائر
        for ip in ips:
            if not is_private_ip(ip):
                return ip
        if ips:
            return ips[0]

    # 2. ترويسة Cloudflare (الأعلى موثوقية إن وجدت)
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip and not is_private_ip(cf_ip.strip()):
        return cf_ip.strip()

    # 3. ترويسة Nginx / Apache (تستخدم فقط إن لم تكن شبكة داخلية)
    real_ip = request.META.get('HTTP_X_REAL_IP')
    if real_ip and not is_private_ip(real_ip.strip()):
        return real_ip.strip()

    # 4. العنوان الافتراضي للمتصل المباشر
    return request.META.get('REMOTE_ADDR', '127.0.0.1')

def is_private_ip(ip):
    """فحص ما إذا كان الـ IP شبكة داخلية (LAN) أو Loopback"""
    if not ip or ip in ['127.0.0.1', '::1', 'localhost', 'unknown']:
        return True
    if ip.startswith(('10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.',
                      '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                      '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
                      '169.254.', 'fc00:', 'fe80:')):
        return True
    return False

def get_ip_intelligence(ip_address):
    """
    محرك استخباراتي لفحص الـ IP بدقة، كشف مزود الخدمة ISP،
    رقم النظام المستقل ASN، فحص استخدام الـ VPN/Proxy، والموقع التقريبي بدون أي قيم وهمية.
    """
    if is_private_ip(ip_address):
        return {
            'status': 'local',
            'ip': ip_address,
            'country': 'شبكة محلية / سيرفر محلي',
            'region': 'Localhost',
            'city': 'Localhost',
            'lat': 0.0,
            'lon': 0.0,
            'isp': 'Loopback / LAN',
            'asn': 'N/A',
            'is_vpn_proxy': False,
            'timezone': 'UTC'
        }

    # المحاولة الأولى: عبر ip-api.com (شامل وسريع جداً للـ ISP و ASN وفحص البروكسي)
    try:
        url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,regionName,city,district,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting,query"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (ForensicTool/2.0)'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('status') == 'success':
                is_proxy = data.get('proxy', False) or data.get('hosting', False)
                return {
                    'status': 'success',
                    'ip': ip_address,
                    'country': data.get('country', 'غير محدد'),
                    'region': data.get('regionName', ''),
                    'city': data.get('city', ''),
                    'district': data.get('district', ''),
                    'lat': float(data.get('lat', 0.0)),
                    'lon': float(data.get('lon', 0.0)),
                    'isp': data.get('isp', data.get('org', 'غير معروف')),
                    'asn': data.get('as', ''),
                    'is_vpn_proxy': is_proxy,
                    'timezone': data.get('timezone', '')
                }
    except Exception:
        pass

    # المحاولة الثانية كخيار احتياطي: ipwho.is
    try:
        url = f"https://ipwho.is/{ip_address}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (ForensicTool/2.0)'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('success'):
                sec = data.get('security', {})
                conn = data.get('connection', {})
                is_proxy = sec.get('vpn', False) or sec.get('proxy', False) or sec.get('tor', False) or sec.get('hosting', False)
                return {
                    'status': 'success',
                    'ip': ip_address,
                    'country': data.get('country', 'غير محدد'),
                    'region': data.get('region', ''),
                    'city': data.get('city', ''),
                    'district': '',
                    'lat': float(data.get('latitude', 0.0)),
                    'lon': float(data.get('longitude', 0.0)),
                    'isp': conn.get('isp', conn.get('org', 'غير معروف')),
                    'asn': f"AS{conn.get('asn', '')}",
                    'is_vpn_proxy': is_proxy,
                    'timezone': data.get('timezone', {}).get('id', '')
                }
    except Exception:
        pass

    # في حال انقطاع خدمة الـ APIs
    return {
        'status': 'error',
        'ip': ip_address,
        'country': 'غير محدد',
        'region': '',
        'city': '',
        'district': '',
        'lat': 0.0,
        'lon': 0.0,
        'isp': 'تعذر الاستعلام',
        'asn': '',
        'is_vpn_proxy': False,
        'timezone': ''
    }

def get_exact_address_from_coords(lat, lon):
    """
    تحويل الإحداثيات الجغرافية المباشرة (GPS) بدقة متناهية إلى عنوان تفصيلي
    باستخدام OpenStreetMap مع ترويسة احترافية تمنع الحظر.
    """
    if not lat or not lon or (lat == 0.0 and lon == 0.0):
        return "", {}

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'ForensicInvestigationToolkit/2.5 (Security Incident Response Unit; contact: security@local.dev)',
            'Accept': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode('utf-8'))
            address = data.get('address', {})
            
            parts = []
            # المكونات التفصيلية: مبنى، شارع، حي، منطقة، مدينة
            building = address.get('building') or address.get('house_number')
            road = address.get('road') or address.get('pedestrian')
            suburb = address.get('suburb') or address.get('neighbourhood') or address.get('residential')
            district = address.get('city_district') or address.get('district')
            city = address.get('city') or address.get('town') or address.get('village') or address.get('county')
            state = address.get('state')
            country = address.get('country')

            if road:
                parts.append(f"شارع {road}" if building is None else f"{road} {building}")
            if suburb:
                parts.append(f"حي {suburb}")
            if district and district != suburb:
                parts.append(district)
            if city:
                parts.append(city)
            if state and state != city:
                parts.append(state)
            if country:
                parts.append(country)

            full_addr = "، ".join(parts) if parts else data.get('display_name', f"إحداثيات: {lat:.6f}, {lon:.6f}")
            return full_addr, address
    except Exception as e:
        return f"الإحداثيات: {lat:.6f}, {lon:.6f}", {}

def get_device_info(request):
    """استخراج معلومات الجهاز من ترويسة الـ User-Agent كمعاينة أولية"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    device_type = 'Desktop'
    if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
        device_type = 'Mobile'
    elif 'iPad' in user_agent or 'Tablet' in user_agent:
        device_type = 'Tablet'
    
    browser = 'Unknown'
    if 'Edg' in user_agent:
        browser = 'Edge'
    elif 'Chrome' in user_agent and 'OPR' not in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
        browser = 'Safari'
    elif 'OPR' in user_agent:
        browser = 'Opera'
    
    os_name = 'Unknown'
    if 'Windows NT 10.0' in user_agent:
        os_name = 'Windows 10/11'
    elif 'Windows' in user_agent:
        os_name = 'Windows'
    elif 'Android' in user_agent:
        os_name = 'Android'
    elif 'iPhone' in user_agent:
        os_name = 'iOS (iPhone)'
    elif 'iPad' in user_agent:
        os_name = 'iPadOS'
    elif 'Mac OS X' in user_agent:
        os_name = 'macOS'
    elif 'Linux' in user_agent:
        os_name = 'Linux'
    
    return {
        'device_type': device_type,
        'browser': browser,
        'os': os_name,
        'user_agent': user_agent
    }

@never_cache
def public_welcome_view(request):
    """
    واجهة العرض الأولى - تسجيل البصمة المبدئية للزائر فور الدخول،
    وتجهيز الصفحة لإطلاق طلبات الموقع الدقيقة (GPS) و WebRTC Leak
    مع ضمان عدم تكرار السجلات نهائياً (سجل واحد فقط لكل زائر / IP).
    """
    user_ip = get_client_ip(request)
    device_info = get_device_info(request)
    
    # فحص ما إذا كان الزائر مسجلاً مسبقاً بنفس الـ IP
    last_log = VisitorLog.objects.filter(ip_address=user_ip).first()
    
    if last_log:
        # تحديث توقيت الزيارة وبيانات الجهاز للسجل نفسه لمنع تكرار البيانات
        last_log.visit_time = timezone.now()
        last_log.device_type = device_info['device_type']
        last_log.browser = device_info['browser']
        last_log.os = device_info['os']
        last_log.user_agent = device_info['user_agent']
        if request.META.get('HTTP_REFERER'):
            last_log.referrer = request.META.get('HTTP_REFERER')
        last_log.evidence_hash = last_log.compute_evidence_hash()
        last_log.save()
    else:
        # إنشاء السجل الأول لهذا الـ IP مع استعلام الاستخبارات الجغرافية
        intel = get_ip_intelligence(user_ip)
        initial_address = ""
        if intel.get('lat') and intel.get('lon') and intel['lat'] != 0.0:
            initial_address, _ = get_exact_address_from_coords(intel['lat'], intel['lon'])
            
        last_log = VisitorLog.objects.create(
            ip_address=user_ip,
            country=intel.get('country', 'غير محدد'),
            governorate=intel.get('region') or intel.get('city') or 'غير محدد',
            city=intel.get('city', ''),
            full_address=initial_address or f"{intel.get('city', '')} - {intel.get('region', '')}",
            isp=intel.get('isp', ''),
            asn=intel.get('asn', ''),
            is_vpn_or_proxy=intel.get('is_vpn_proxy', False),
            timezone_ip=intel.get('timezone', ''),
            device_type=device_info['device_type'],
            browser=device_info['browser'],
            os=device_info['os'],
            latitude=intel.get('lat', 0.0),
            longitude=intel.get('lon', 0.0),
            accuracy=5000.0 if (intel.get('lat') and intel['lat'] != 0.0) else 0.0,
            positioning_method="IP Geolocation",
            user_agent=device_info['user_agent'],
            referrer=request.META.get('HTTP_REFERER', '')
        )
        last_log.evidence_hash = last_log.compute_evidence_hash()
        last_log.save(update_fields=['evidence_hash'])
    
    context = {
        'log_id': last_log.id,
        'user_ip': user_ip,
        'governorate': last_log.governorate or last_log.city or 'جاري التحديد...',
        'city': last_log.city or '',
        'country': last_log.country or '',
        'isp': last_log.isp or '',
        'device_info': device_info,
        'is_vpn': last_log.is_vpn_or_proxy
    }
    return render(request, 'welcome.html', context)

@csrf_exempt
@never_cache
def report_forensic_data_view(request):
    """
    نقطة النهاية المركزية (Central Forensic Ingestion API):
    تستقبل الحزمة الجنائية الكاملة من المتصفح:
    - إحداثيات GPS الدقيقة جداً، نسبة الخطأ بالأمتار، الارتفاع، والسرعة
    - تسريب عناوين WebRTC (Local LAN IP و Public IP)
    - بصمة العتاد (المعالج، الذاكرة، دقة الشاشة، شحن البطارية)
    - كشف التزييف عبر مقارنة التوقيت المحلي للمتصفح بتوقيت الـ IP
    مع ضمان عدم تكرار السجلات نهائياً (سجل واحد فقط لكل زائر / IP).
    """
    user_ip = get_client_ip(request)
    
    data = {}
    if request.method == 'POST':
        try:
            if request.body:
                data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST.dict()
    else:
        data = request.GET.dict()
    
    # 1. استخراج بيانات الـ GPS المتقدمة
    gps_data = data.get('gps', {})
    lat = gps_data.get('latitude') or data.get('lat')
    lon = gps_data.get('longitude') or data.get('lon')
    accuracy = gps_data.get('accuracy') or data.get('accuracy')
    altitude = gps_data.get('altitude') or data.get('altitude')
    altitude_accuracy = gps_data.get('altitudeAccuracy') or data.get('altitude_accuracy')
    heading = gps_data.get('heading') or data.get('heading')
    speed = gps_data.get('speed') or data.get('speed')
    
    # تحويل القيم لأرقام عشرية
    lat = float(lat) if lat not in [None, '', 'null'] else 0.0
    lon = float(lon) if lon not in [None, '', 'null'] else 0.0
    accuracy = float(accuracy) if accuracy not in [None, '', 'null'] else 0.0
    altitude = float(altitude) if altitude not in [None, '', 'null'] else None
    altitude_accuracy = float(altitude_accuracy) if altitude_accuracy not in [None, '', 'null'] else None
    heading = float(heading) if heading not in [None, '', 'null'] else None
    speed = float(speed) if speed not in [None, '', 'null'] else None

    # 2. استخراج بيانات الـ WebRTC
    webrtc = data.get('webrtc', {})
    local_ip = webrtc.get('localIp') or data.get('local_ip')
    leaked_public_ip = webrtc.get('publicIp') or data.get('webrtc_public_ip')

    # 3. استخراج بيانات العتاد والنظام
    device = data.get('device', {})
    browser_name = device.get('browser') or data.get('browser')
    os_name = device.get('os') or data.get('os')
    device_type = device.get('deviceType') or data.get('device_type')
    screen_res = device.get('screenResolution') or data.get('screen_resolution')
    cpu_cores = device.get('cpuCores') or data.get('cpu_cores')
    memory_gb = device.get('deviceMemory') or data.get('device_memory_gb')
    battery_level = device.get('batteryLevel') or data.get('battery_level')
    is_charging = bool(device.get('isCharging') or data.get('is_charging', False))
    browser_timezone = device.get('timezone') or data.get('timezone_browser')
    lang = device.get('language') or data.get('language')
    
    # تحديد وسيلة التموضع بدقة بناءً على هامش الخطأ (Accuracy)
    positioning_method = "IP Geolocation"
    exact_address = ""
    if lat != 0.0 and lon != 0.0:
        if accuracy > 0 and accuracy <= 50:
            positioning_method = f"🛰️ GPS دقيق جداً (±{int(accuracy)}m)"
        elif accuracy <= 300:
            positioning_method = f"📶 Wi-Fi Triangulation (±{int(accuracy)}m)"
        elif accuracy <= 3000:
            positioning_method = f"📡 Cell Tower Triangulation (±{int(accuracy)}m)"
        else:
            positioning_method = f"🌐 Network Geolocation (±{int(accuracy)}m)"
            
        exact_address, addr_details = get_exact_address_from_coords(lat, lon)
    else:
        exact_address, addr_details = "", {}
    
    # محاولة جلب السجل المحدد بالـ log_id أولاً، أو بالـ ip_address لضمان عدم تكرار السجلات نهائياً
    log_id = data.get('log_id')
    last_log = None
    if log_id:
        try:
            last_log = VisitorLog.objects.filter(id=int(log_id)).first()
        except Exception:
            pass

    if not last_log:
        last_log = VisitorLog.objects.filter(ip_address=user_ip).first()
    
    if not last_log:
        intel = get_ip_intelligence(user_ip)
        last_log = VisitorLog.objects.create(
            ip_address=user_ip,
            country=intel.get('country', 'غير محدد'),
            governorate=intel.get('region') or 'غير محدد',
            city=intel.get('city', ''),
            isp=intel.get('isp', ''),
            asn=intel.get('asn', ''),
            is_vpn_or_proxy=intel.get('is_vpn_proxy', False),
            timezone_ip=intel.get('timezone', ''),
            positioning_method=positioning_method
        )
    
    # تحديث وقت الزيارة دائماً ليبقى السجل في قمة لوحة التحكم بأحدث وقت
    last_log.visit_time = timezone.now()

    # فحص دقيق للـ VPN / Proxy بدون أي اشتباه خاطئ في الشبكات المحلية
    if is_private_ip(user_ip):
        # الشبكة المحلية (LAN / Hotspot / 192.168.x.x) ليست اتصال VPN
        last_log.is_vpn_or_proxy = False
    else:
        # فحص الـ IP العام الحقيقي عبر قاعدة بيانات الـ Proxy / Hosting
        intel = get_ip_intelligence(user_ip)
        is_vpn = intel.get('is_vpn_proxy', False)
        
        # كشف تسريب WebRTC (فقط في حال كان الـ IP المسرب عنواناً عاماً حقيقياً مختلفاً عن IP الاتصال)
        if leaked_public_ip and not is_private_ip(leaked_public_ip) and leaked_public_ip != user_ip:
            is_vpn = True
            
        last_log.is_vpn_or_proxy = is_vpn

    # تحديث الحقول الجنائية والموقع
    if lat != 0.0 and lon != 0.0:
        # الحفاظ على أفضل دقة تم الحصول عليها
        if last_log.latitude == 0.0 or last_log.accuracy == 0.0 or accuracy <= (last_log.accuracy * 1.5):
            last_log.latitude = lat
            last_log.longitude = lon
            last_log.accuracy = accuracy
            last_log.positioning_method = positioning_method
            if exact_address:
                last_log.full_address = exact_address
            if addr_details.get('country'):
                last_log.country = addr_details['country']
            if addr_details.get('state'):
                last_log.governorate = addr_details['state']
            if addr_details.get('city') or addr_details.get('town') or addr_details.get('village'):
                last_log.city = addr_details.get('city') or addr_details.get('town') or addr_details.get('village')
    elif (last_log.latitude == 0.0 or last_log.longitude == 0.0) and leaked_public_ip and not is_private_ip(leaked_public_ip):
        # في حال لم تتوفر إحداثيات GPS بعد وكان الاتصال محلياً، نستخدم إحداثيات الـ IP العام المسرب احتياطياً ليظهر زر الخريطة
        leaked_intel = get_ip_intelligence(leaked_public_ip)
        if leaked_intel.get('lat') and leaked_intel.get('lon') and leaked_intel['lat'] != 0.0:
            last_log.latitude = leaked_intel['lat']
            last_log.longitude = leaked_intel['lon']
            last_log.accuracy = 10000.0
            last_log.positioning_method = "🌐 تقريب شبكي (IP)"
            if not last_log.city:
                last_log.city = leaked_intel.get('city', '')
            if not last_log.governorate or last_log.governorate in ['Localhost', 'غير محدد']:
                last_log.governorate = leaked_intel.get('region') or leaked_intel.get('city') or 'غير محدد'
            if not last_log.country or last_log.country in ['شبكة محلية / سيرفر محلي', 'غير محدد']:
                last_log.country = leaked_intel.get('country', '')
            if not last_log.isp or last_log.isp in ['Loopback / LAN', '']:
                last_log.isp = leaked_intel.get('isp', '')
            if not last_log.asn:
                last_log.asn = leaked_intel.get('asn', '')

    if altitude is not None:
        last_log.altitude = altitude
    if altitude_accuracy is not None:
        last_log.altitude_accuracy = altitude_accuracy
    if heading is not None:
        last_log.heading = heading
    if speed is not None:
        last_log.speed = speed

    if local_ip:
        last_log.webrtc_local_ip = str(local_ip)[:100]
    if leaked_public_ip:
        last_log.webrtc_public_ip = str(leaked_public_ip)[:100]

    if browser_name:
        last_log.browser = str(browser_name)[:100]
    if os_name:
        last_log.os = str(os_name)[:100]
    if device_type:
        last_log.device_type = str(device_type)[:50]
    if screen_res:
        last_log.screen_resolution = str(screen_res)[:50]
    if cpu_cores:
        try: last_log.cpu_cores = int(cpu_cores)
        except Exception: pass
    if memory_gb:
        try: last_log.device_memory_gb = float(memory_gb)
        except Exception: pass
    if battery_level:
        last_log.battery_level = str(battery_level)[:20]
    last_log.is_charging = is_charging
    if browser_timezone:
        last_log.timezone_browser = str(browser_timezone)[:100]
    if lang:
        last_log.language = str(lang)[:50]

    # استخراج بصمة معالج الرسوميات وكشف الأتمتة
    gpu_renderer = device.get('gpuRenderer') or data.get('gpu_renderer')
    is_bot = bool(device.get('isBot') or data.get('is_bot', False))
    if gpu_renderer:
        last_log.gpu_renderer = str(gpu_renderer)[:200]
    last_log.is_automated_agent = is_bot

    # حساب مؤشر درجة الخطورة والاشتباه الجنائي (0-100)
    risk = 0
    if last_log.is_vpn_or_proxy:
        risk += 35
    if leaked_public_ip and not is_private_ip(leaked_public_ip) and leaked_public_ip != user_ip:
        risk += 30
    if browser_timezone and last_log.timezone_ip and browser_timezone != last_log.timezone_ip:
        risk += 20
    if is_bot:
        risk += 15
    last_log.risk_score = min(risk, 100)

    # حفظ السجل وتوليد الختم الرقمي لسلامة الأدلة (Evidence Integrity SHA-256)
    last_log.save()
    last_log.evidence_hash = last_log.compute_evidence_hash()
    last_log.save(update_fields=['evidence_hash'])
    
    return JsonResponse({
        "status": "success",
        "log_id": last_log.id,
        "method": last_log.positioning_method,
        "latitude": last_log.latitude,
        "longitude": last_log.longitude,
        "accuracy_meters": last_log.accuracy,
        "address": last_log.full_address or last_log.governorate,
        "google_maps_url": last_log.google_maps_url,
        "is_vpn_detected": last_log.is_vpn_or_proxy,
        "webrtc_local_ip": last_log.webrtc_local_ip,
        "webrtc_public_ip": last_log.webrtc_public_ip
    })

# الحفاظ على التوافق التام مع الـ Endpoints السابقة
update_location_view = report_forensic_data_view
collect_device_info_view = report_forensic_data_view
collect_all_device_info_view = report_forensic_data_view