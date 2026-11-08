# AXINUS ADDON 4b - India map: population + state news + weather (Leaflet + Open-Meteo + Google News RSS)
import json, time, re, urllib.parse
ST = {
"Maharashtra": (19.08, 72.88, "Mumbai", 112374333), "Uttar Pradesh": (26.85, 80.95, "Lucknow", 199812341), "Bihar": (25.60, 85.14, "Patna", 104099452),
"West Bengal": (22.57, 88.36, "Kolkata", 91276115), "Madhya Pradesh": (23.26, 77.41, "Bhopal", 72626809), "Tamil Nadu": (13.08, 80.27, "Chennai", 72147030),
"Rajasthan": (26.91, 75.79, "Jaipur", 68548437), "Karnataka": (12.97, 77.59, "Bengaluru", 61095297), "Gujarat": (23.22, 72.65, "Gandhinagar", 60439692),
"Andhra Pradesh": (16.51, 80.65, "Amaravati", 49577103), "Odisha": (20.30, 85.82, "Bhubaneswar", 41974218), "Telangana": (17.39, 78.49, "Hyderabad", 35003674),
"Kerala": (8.52, 76.94, "Thiruvananthapuram", 33406061), "Jharkhand": (23.34, 85.31, "Ranchi", 32988134), "Assam": (26.14, 91.74, "Dispur", 31205576),
"Punjab": (30.73, 76.78, "Chandigarh", 27743338), "Chhattisgarh": (21.25, 81.63, "Raipur", 25545198), "Haryana": (30.73, 76.78, "Chandigarh", 25351462),
"Delhi": (28.61, 77.21, "New Delhi", 16787941), "Jammu and Kashmir": (34.08, 74.80, "Srinagar", 12267032), "Uttarakhand": (30.32, 78.03, "Dehradun", 10086292),
"Himachal Pradesh": (31.10, 77.17, "Shimla", 6864602), "Tripura": (23.83, 91.28, "Agartala", 3673917), "Meghalaya": (25.58, 91.89, "Shillong", 2966889),
"Manipur": (24.82, 93.94, "Imphal", 2855794), "Nagaland": (25.67, 94.11, "Kohima", 1978502), "Goa": (15.50, 73.83, "Panaji", 1458545),
"Arunachal Pradesh": (27.08, 93.61, "Itanagar", 1383727), "Puducherry": (11.93, 79.83, "Puducherry", 1247953), "Mizoram": (23.73, 92.72, "Aizawl", 1097206),
"Chandigarh": (30.73, 76.78, "Chandigarh", 1055450), "Sikkim": (27.33, 88.61, "Gangtok", 610577), "Andaman and Nicobar": (11.62, 92.73, "Port Blair", 380581),
"Ladakh": (34.15, 77.58, "Leh", 274289), "Dadra Nagar Haveli and Daman Diu": (20.27, 73.02, "Daman", 585764), "Lakshadweep": (10.57, 72.64, "Kavaratti", 64473)}
CITY2ST = {"mumbai": "Maharashtra", "pune": "Maharashtra", "nagpur": "Maharashtra", "nashik": "Maharashtra", "thane": "Maharashtra", "aurangabad": "Maharashtra", "bangalore": "Karnataka", "bengaluru": "Karnataka", "chennai": "Tamil Nadu", "kolkata": "West Bengal", "hyderabad": "Telangana", "lucknow": "Uttar Pradesh", "jaipur": "Rajasthan", "ahmedabad": "Gujarat", "bhopal": "Madhya Pradesh", "patna": "Bihar", "new delhi": "Delhi", "j&k": "Jammu and Kashmir", "kashmir": "Jammu and Kashmir", "tn": "Tamil Nadu", "up": "Uttar Pradesh", "mp": "Madhya Pradesh"}
WMO = {0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Cloudy", 45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Showers", 81: "Showers", 82: "Heavy showers", 95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"}
MAPC = globals().get("MAPC") or {}
def _state(q):
    q = (q or "").strip().lower()
    if not q: return None
    if q in CITY2ST: return CITY2ST[q]
    for k in ST:
        if k.lower() == q: return k
    for k in ST:
        if q in k.lower() or k.lower() in q: return k
    for c, s in CITY2ST.items():
        if c in q: return s
    return None
def _weather(lat, lon):
    u = "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&timezone=Asia%%2FKolkata&forecast_days=3" % (lat, lon)
    d = requests.get(u, timeout=10).json(); c = d["current"]; dl = d["daily"]
    return {"temp": c["temperature_2m"], "hum": c["relative_humidity_2m"], "wind": c["wind_speed_10m"], "desc": WMO.get(c["weather_code"], "—"),
            "days": [{"d": dl["time"][i], "max": dl["temperature_2m_max"][i], "min": dl["temperature_2m_min"][i], "rain": dl["precipitation_probability_max"][i], "desc": WMO.get(dl["weather_code"][i], "—")} for i in range(len(dl["time"]))]}
def _snews(name):
    q = urllib.parse.quote(name + " when:2d")
    return fetch_feed("https://news.google.com/rss/search?q=" + q + "&hl=en-IN&gl=IN&ceid=IN:en", "Google News")[:6]
def map_data(name):
    s = _state(name)
    if not s: return {"error": "State nahi mila: " + str(name)}
    c = MAPC.get(s)
    if c and time.time() - c["t"] < 900: return c["d"]
    lat, lon, cap, pop = ST[s]; out = {"state": s, "capital": cap, "pop": pop, "pop_note": "Census 2011", "weather": None, "news": [], "errors": []}
    with Stage("research", "Map data: " + s, "open-meteo + rss") as st:
        try: out["weather"] = _weather(lat, lon)
        except Exception as e: out["errors"].append("weather: " + str(e)[:60])
        try: out["news"] = _snews(s)
        except Exception as e: out["errors"].append("news: " + str(e)[:60])
        if not out["weather"] and not out["news"]: st.fail = True; return {"error": "Internet/API issue: " + "; ".join(out["errors"])}
    MAPC[s] = {"t": time.time(), "d": out}
    return out
def map_states(): return J({"states": [{"n": k, "lat": v[0], "lon": v[1], "cap": v[2], "pop": v[3]} for k, v in ST.items()]})
def map_info(state): return J(map_data(state))
def state_info(state: str):
    d = map_data(state)
    if d.get("error"): return "Error: " + d["error"]
    w = d["weather"]; t = "%s (capital %s) - population %s (Census 2011)." % (d["state"], d["capital"], format(d["pop"], ","))
    if w: t += "\nWeather now: %s, %s°C, humidity %s%%, wind %s km/h. Next days: %s" % (w["desc"], w["temp"], w["hum"], w["wind"], "; ".join("%s %s-%s°C rain %s%%" % (x["d"][5:], x["min"], x["max"], x["rain"]) for x in w["days"][1:]))
    if d["news"]: t += "\nTop news:\n" + "\n".join("%d. %s (%s)" % (i + 1, n["title"], n["source"]) for i, n in enumerate(d["news"][:5]))
    return t
reg_tool(state_info, "Population, current weather + forecast and latest news for an Indian state or major city (state)", "research")
ADDON_API.update({"map_states": map_states, "map_info": map_info})

MAP_SECTION = '''<section class="pn" id="pMap"><div class="hd">INDIA MAP<em id="mst">tap a state</em></div><select id="msel" style="width:100%;background:#08131c;border:1px solid #16364a;border-radius:8px;color:#fff;padding:9px;font:14px system-ui;margin-bottom:8px"><option value="">Select state...</option></select><div id="lf" style="height:300px;border-radius:10px;border:1px solid #0f2433;background:#07111a"></div><div id="minfo" style="margin-top:8px;font-size:13px;line-height:1.5"></div><canvas id="map" width="4" height="4" style="display:none"></canvas></section>'''
MAP_JS = r'''
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>.axdark{filter:invert(1) hue-rotate(180deg) brightness(.82) contrast(.92) saturate(.55)}.leaflet-container{background:#07111a;font:12px system-ui}.mw{display:flex;gap:6px;margin:6px 0}.mw div{flex:1;background:#08131c;border:1px solid #0f2433;border-radius:8px;padding:6px;text-align:center;font:11px ui-monospace,monospace;color:#9fc3d3}.mw b{display:block;color:#e6f4fa;font-size:13px}.mn{padding:6px 0;border-top:1px solid #0f2433}.mn a{color:#e6f4fa;text-decoration:none;font-size:13px}.mn small{display:block;color:#6d8a99;font:10.5px ui-monospace,monospace}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
(function(){
const $=id=>document.getElementById(id),E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const api=async(n,a)=>{try{const r=await fetch('/api/'+n,{method:'POST',headers:{'Content-Type':'application/json','X-Pin':localStorage.getItem('pin')||''},body:JSON.stringify({args:a||[]})});return await r.json();}catch(e){return{error:String(e)};}};
let M=null,MK={},cur='';
async function show(s){cur=s;$('msel').value=s;$('mst').textContent=s;$('minfo').innerHTML='<div class="sk"></div><div class="sk"></div>';
const d=await api('map_info',[s]);if(!d||d.error){$('minfo').innerHTML='<div class="emp">'+E((d&&d.error)||'Data nahi mila')+'</div>';return;}
const w=d.weather;let h='<b>'+E(d.state)+'</b> · '+E(d.capital)+'<br><span style="color:#9fc3d3">Population: '+Number(d.pop).toLocaleString('en-IN')+' <small>(Census 2011)</small></span>';
if(w)h+='<div class="mw"><div><b>'+w.temp+'°C</b>'+E(w.desc)+'</div><div><b>'+w.hum+'%</b>humidity</div><div><b>'+w.wind+'</b>km/h wind</div></div>'+w.days.map(x=>'<div style="font:11.5px ui-monospace,monospace;color:#9fc3d3">'+x.d.slice(5)+' · '+x.min+'–'+x.max+'°C · rain '+x.rain+'% · '+E(x.desc)+'</div>').join('');
else h+='<div class="emp">Weather abhi nahi mila</div>';
h+=(d.news||[]).map(n=>'<div class="mn"><a href="'+E(n.link)+'" target="_blank" rel="noopener">'+E(n.title)+'</a><small>'+E(n.source)+(n.date?' · '+E(n.date):'')+'</small></div>').join('')||'<div class="emp">News nahi mili</div>';
h+='<button class="btn" id="mask" style="margin-top:8px">Ask Axinus about '+E(d.state)+'</button>';$('minfo').innerHTML=h;
$('mask').onclick=()=>{$('tx').value=d.state+' ka weather aur latest news batao';$('bsend').click();};}
$('msel').onchange=()=>{const s=$('msel').value;if(s){show(s);if(M&&MK[s]){M.setView(MK[s].getLatLng(),s==='Maharashtra'?7:6);}}};
(async()=>{const r=await api('map_states');if(!r||!r.states)return;
r.states.forEach(s=>{const o=document.createElement('option');o.textContent=s.n;$('msel').appendChild(o);});
if(!window.L){$('lf').innerHTML='<div class="emp" style="padding:20px">Map load nahi hua (internet). Dropdown se state chuno.</div>';return;}
M=L.map('lf',{zoomControl:true,attributionControl:true}).setView([22.5,80],4);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:10,minZoom:3,className:'axdark',attribution:'© OpenStreetMap contributors'}).addTo(M);
r.states.forEach(s=>{const rad=Math.max(5,Math.min(20,Math.sqrt(s.pop/1e5)*1.3));
const m=L.circleMarker([s.lat,s.lon],{radius:rad,color:'#22d3ee',weight:1.5,fillColor:'#22d3ee',fillOpacity:.28}).addTo(M);
m.bindTooltip(s.n+' · '+(s.pop/1e6).toFixed(1)+'M');m.on('click',()=>show(s.n));MK[s.n]=m;});
setTimeout(()=>M.invalidateSize(),400);window.addEventListener('resize',()=>M.invalidateSize());})();
})();
</script>
'''
_old_sec = re.search(r'<section class="pn" id="pMap">.*?</section>', UI_BODY, re.S)
if _old_sec and "INDIA MAP" not in UI_BODY:
    UI_BODY = UI_BODY.replace(_old_sec.group(0), MAP_SECTION) + MAP_JS
else: print("⚠️ map UI patch skipped")
print("✅ ax4b map OK | 36 states, weather + news + population")
if "API" in globals() and "build_old_js" in globals() and "INDIA MAP" in UI_BODY:
    API.update(ADDON_API)
    _oj, _w = build_old_js(PAGE)
    UI_HTML = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>AXINUS</title></head><body>' + UI_BODY.replace("__OLD__", _oj) + '</body></html>'
    print("✅ map live - page refresh karo")
