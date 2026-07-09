"""
EarthView v3 — 地球观测与天文探索系统
本地化GeoJSON + Open-Meteo天气 + NASA影像
"""
import json, os, socket, webbrowser, threading, time
from flask import Flask, render_template, jsonify, send_file, Response
import requests

app = Flask(__name__)

# ==================== 本地世界地图GeoJSON ====================
@app.route('/api/world-geo')
def api_world_geo():
    geo_path = os.path.join(os.path.dirname(__file__), 'static', 'world.json')
    if os.path.exists(geo_path):
        return send_file(geo_path, mimetype='application/json')
    return Response('{}', mimetype='application/json')

# ==================== 台风数据接口 ====================
@app.route('/api/typhoon-live')
def api_typhoon_live():
    """获取实时活跃热带气旋（GDACS）"""
    typhoons = []
    try:
        resp = requests.get(
            'https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEVENT',
            timeout=15,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data[:30]:
                etype = item.get('eventtype', '')
                if 'TC' in etype or 'TROPICAL' in etype.upper():
                    typhoons.append({
                        'id': item.get('eventid', ''),
                        'name': item.get('eventname', 'Unknown'),
                        'lat': item.get('latitude', 0),
                        'lon': item.get('longitude', 0),
                        'severity': item.get('severity', 'Unknown'),
                        'country': item.get('country', ''),
                        'date': item.get('fromdate', ''),
                        'description': item.get('description', '')[:200] if item.get('description') else '',
                        'source': 'GDACS',
                    })
        return jsonify({'typhoons': typhoons, 'source': 'GDACS', 'count': len(typhoons)})
    except Exception as e:
        return jsonify({'typhoons': [], 'source': 'GDACS', 'error': str(e)})

# ==================== Open-Meteo 全球天气 ====================
CITIES = [
    [35.7,139.7,'东京','日本'],[37.6,127.0,'首尔','韩国'],[1.3,103.8,'新加坡','新加坡'],
    [19.1,72.9,'孟买','印度'],[-33.9,151.2,'悉尼','澳大利亚'],[-36.8,174.8,'奥克兰','新西兰'],
    [51.5,-0.1,'伦敦','英国'],[48.9,2.3,'巴黎','法国'],[52.5,13.4,'柏林','德国'],
    [40.4,-3.7,'马德里','西班牙'],[55.8,37.6,'莫斯科','俄罗斯'],[40.7,-74.0,'纽约','美国'],
    [34.1,-118.2,'洛杉矶','美国'],[43.7,-79.4,'多伦多','加拿大'],[-22.9,-43.2,'里约热内卢','巴西'],
    [-34.6,-58.4,'布宜诺斯艾利斯','阿根廷'],[30.0,31.2,'开罗','埃及'],[-26.2,28.0,'约翰内斯堡','南非'],
    [25.2,55.3,'迪拜','阿联酋'],[14.6,121.0,'马尼拉','菲律宾'],
]

@app.route('/api/weather')
def api_weather():
    results = []
    for lat, lon, name, country in CITIES:
        try:
            url = (f"https://api.open-meteo.com/v1/forecast?"
                   f"latitude={lat}&longitude={lon}&current=temperature_2m,"
                   f"relative_humidity_2m,wind_speed_10m,pressure_msl,weather_code"
                   f"&timezone=auto")
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                d = resp.json()['current']
                results.append({
                    'name':name,'country':country,'temp':d['temperature_2m'],
                    'humidity':d['relative_humidity_2m'],'wind':d['wind_speed_10m'],
                    'pressure':d['pressure_msl'],'code':d['weather_code']
                })
                continue
        except: pass
        results.append({'name':name,'country':country,'temp':None,'humidity':None,'wind':None,'pressure':None,'code':None})
    return jsonify({'cities':results})

# ==================== ISS ====================
@app.route('/api/iss')
def api_iss():
    try:
        resp = requests.get("http://api.open-notify.org/iss-now.json", timeout=5)
        if resp.status_code == 200:
            d = resp.json()
            return jsonify({'lat':float(d['iss_position']['latitude']),'lon':float(d['iss_position']['longitude'])})
    except: pass
    return jsonify({'lat':0,'lon':0})

# ==================== 页面 ====================
@app.route('/')
def index():
    return render_template('index.html')

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return '127.0.0.1'

def open_browser():
    time.sleep(1.5)
    edge_paths = [
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    ]
    for p in edge_paths:
        if os.path.exists(p):
            webbrowser.register('edge',None,webbrowser.BackgroundBrowser(p))
            webbrowser.get('edge').open('http://127.0.0.1:8080')
            return
    webbrowser.open('http://127.0.0.1:8080')

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("\n" + "="*60)
    print("  EarthView v3 — 地球观测与天文探索系统")
    print("="*60)
    print(f"  电脑访问: http://127.0.0.1:8080")
    print(f"  手机访问: http://{local_ip}:8080  (同一WiFi)")
    print("="*60+"\n")
    threading.Thread(target=open_browser,daemon=True).start()
    app.run(host='0.0.0.0',port=8080,debug=False)
