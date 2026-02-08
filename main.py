import os
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "movies_full_system_key"

# --- MongoDB Connection ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['webseries_db']
series_collection = db['series']
settings_collection = db['settings']

# --- ডাইনামিক সেটিংস লোড করার ফাংশন ---
def get_site_settings():
    default_config = {
        "site_name": "WebSeries BD",
        "primary_color": "#E50914",
        "bg_color": "#0b0b0b",
        "card_bg_color": "#1a1a1a",
        "text_color": "#ffffff",
        "badge_color": "#E50914",
        "lang_color": "#aaaaaa",
        "ads": []
    }
    config = settings_collection.find_one({"type": "site_config"})
    if not config:
        settings_collection.insert_one({"type": "site_config", **default_config})
        return default_config
    return config

# --- রেসপন্সিভ এবং ডাইনামিক CSS (মোবাইল ও ডেক্সটপ অটো মোড) ---
def get_dynamic_style(s):
    return f"""
<style>
    :root {{ 
        --primary: {s['primary_color']}; 
        --bg: {s['bg_color']}; 
        --card-bg: {s['card_bg_color']}; 
        --text: {s['text_color']}; 
        --badge: {s['badge_color']};
        --lang: {s['lang_color']};
        --border: #333; 
    }}
    body {{ background-color: var(--bg); color: var(--text); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; overflow-x: hidden; }}
    
    /* Header (Auto Responsive) */
    header {{ background: #000; padding: 15px 5%; display: flex; flex-direction: column; align-items: center; border-bottom: 2px solid var(--primary); position: sticky; top: 0; z-index: 1000; }}
    @media (min-width: 768px) {{ header {{ flex-direction: row; justify-content: space-between; }} }}
    
    .logo {{ color: var(--primary); font-size: 26px; font-weight: bold; text-decoration: none; text-transform: uppercase; margin-bottom: 10px; }}
    @media (min-width: 768px) {{ .logo {{ margin-bottom: 0; }} }}

    .search-container {{ width: 100%; max-width: 500px; display: flex; background: #222; border-radius: 5px; overflow: hidden; border: 1px solid var(--border); }}
    .search-container input {{ border: none; background: transparent; color: white; padding: 10px; width: 100%; outline: none; }}
    .search-container button {{ background: var(--primary); border: none; color: white; padding: 0 20px; cursor: pointer; font-weight: bold; }}

    .nav-links {{ margin-top: 10px; font-size: 14px; display: flex; gap: 15px; }}
    .nav-links a {{ color: #aaa; text-decoration: none; transition: 0.3s; }}
    .nav-links a:hover {{ color: var(--primary); }}

    /* Main Grid (Mobile 2 Columns, Desktop 5+ Columns) */
    .container {{ padding: 20px 5%; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
    @media (min-width: 480px) {{ .grid {{ grid-template-columns: repeat(3, 1fr); }} }}
    @media (min-width: 768px) {{ .grid {{ grid-template-columns: repeat(4, 1fr); }} }}
    @media (min-width: 1024px) {{ .grid {{ grid-template-columns: repeat(5, 1fr); gap: 20px; }} }}

    .card {{ background: var(--card-bg); border-radius: 10px; overflow: hidden; position: relative; text-decoration: none; color: white; transition: 0.4s; border: 1px solid var(--border); display: block; }}
    .card:hover {{ transform: translateY(-8px); border-color: var(--primary); }}
    .card img {{ width: 100%; aspect-ratio: 2/3; object-fit: cover; }}
    .badge {{ position: absolute; top: 8px; left: 8px; background: var(--badge); color: white; padding: 3px 10px; font-size: 11px; border-radius: 4px; font-weight: bold; }}
    .card-info {{ padding: 10px; text-align: center; font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

    /* Detail View */
    .detail-flex {{ display: flex; flex-direction: column; gap: 30px; }}
    @media (min-width: 768px) {{ .detail-flex {{ flex-direction: row; }} }}
    .poster-img {{ width: 100%; max-width: 300px; border-radius: 15px; border: 2px solid var(--border); align-self: center; }}
    .info-content {{ flex: 1; }}
    .info-content h1 {{ margin-top: 0; font-size: 32px; color: var(--primary); }}
    .lang-label {{ color: var(--lang); font-weight: bold; }}
    .story {{ color: #ccc; line-height: 1.6; background: #1a1a1a; padding: 15px; border-radius: 8px; border-left: 4px solid var(--primary); margin-top: 15px; }}

    .ep-box {{ background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid var(--border); }}
    .ep-btns {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }}
    .btn {{ padding: 10px 15px; border-radius: 5px; text-decoration: none; color: white; font-size: 12px; font-weight: bold; text-align: center; flex: 1; min-width: 100px; }}
    .btn-dl {{ background: #27ae60; }} .btn-st {{ background: #2980b9; }} .btn-tg {{ background: #0088cc; }}

    /* Admin UI */
    .admin-table-container {{ overflow-x: auto; margin-top: 20px; }}
    .admin-table {{ width: 100%; border-collapse: collapse; min-width: 600px; color: white; }}
    .admin-table td, .admin-table th {{ padding: 12px; border: 1px solid var(--border); }}
    .form-card {{ max-width: 800px; margin: auto; background: #1a1a1a; padding: 25px; border-radius: 15px; border: 1px solid var(--border); }}
    label {{ display: block; margin-top: 10px; font-size: 14px; color: #aaa; }}
    input, textarea {{ width: 100%; padding: 12px; background: #222; color: white; border: 1px solid var(--border); border-radius: 6px; margin-top: 5px; box-sizing: border-box; }}
    .submit-btn {{ width: 100%; padding: 15px; background: var(--primary); border: none; color: white; font-weight: bold; cursor: pointer; border-radius: 8px; margin-top: 20px; }}
    .ep-input-group {{ background: #262626; padding: 10px; border-radius: 8px; margin-bottom: 10px; border: 1px dashed #555; }}
    
    .ad-container {{ margin: 20px 0; text-align: center; }}
</style>
"""

# --- Header Helper ---
def get_header(s, is_admin=False):
    target = "/admin" if is_admin else "/"
    return f"""
    <header>
        <a href="/" class="logo">{s['site_name']}</a>
        <form action="{target}" method="GET" class="search-container">
            <input type="text" name="q" placeholder="মুভি বা সিরিজ খুঁজুন..." value="{request.args.get('q', '')}">
            <button type="submit">Search</button>
        </form>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="/admin">Admin View</a>
            <a href="/admin/settings" style="color: #f1c40f;">Site Settings</a>
            { '<a href="/admin/add" style="background:var(--primary); color:white; padding:5px 10px; border-radius:5px;">+ Add New</a>' if is_admin else '' }
        </div>
    </header>
    """

# --- Routes ---

@app.route('/')
def home():
    s = get_site_settings()
    q = request.args.get('q', '')
    filt = {"title": {"$regex": q, "$options": "i"}} if q else {}
    movies = list(series_collection.find(filt).sort("_id", -1))
    
    html = f"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{get_dynamic_style(s)}</head><body>{get_header(s)}"
    html += '<div class="container">'
    # বিজ্ঞাপনের জন্য লুপ (প্রথম ২টা অ্যাড উপরে দেখাবে)
    for ad in s['ads'][:2]: html += f'<div class="ad-container">{ad}</div>'
    
    html += f'<h3>{"সার্চ রেজাল্ট: " + q if q else "সব মুভি এবং ওয়েব সিরিজ"}</h3><div class="grid">'
    for m in movies:
        html += f"""<a href="/series/{m['_id']}" class="card">
            {f'<div class="badge">{m["poster_text"]}</div>' if m.get("poster_text") else ''}
            <img src="{m['poster']}"><div class="card-info">{m['title']} ({m['year']})</div></a>"""
    html += '</div>'
    
    # বাকি অ্যাডগুলো নিচে দেখাবে
    for ad in s['ads'][2:]: html += f'<div class="ad-container">{ad}</div>'
    html += '</div></body></html>'
    return render_template_string(html)

@app.route('/series/<id>')
def detail(id):
    s = get_site_settings()
    m = series_collection.find_one({"_id": ObjectId(id)})
    if not m: return "Not Found", 404
    
    html = f"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{get_dynamic_style(s)}</head><body>{get_header(s)}"
    html += '<div class="container">'
    if s['ads']: html += f'<div class="ad-container">{s["ads"][0]}</div>'

    html += f"""<div class="detail-flex"><img src="{m['poster']}" class="poster-img">
            <div class="info-content"><h1>{m['title']} ({m['year']})</h1>
                <p><span class="lang-label">ভাষা: {m['language']}</span> | <b>সাল:</b> {m['year']}</p>
                <div class="story"><b>গল্প:</b><br>{m['description']}</div></div></div><hr style="border:0.5px solid #333; margin:30px 0">"""
    
    for ep in m.get('episodes', []):
        html += f"""<div class="ep-box"><strong>Episode No: {ep['ep_no']}</strong><div class="ep-btns">
                {f'<a href="{ep["dl_link"]}" class="btn btn-dl" target="_blank">Download</a>' if ep['dl_link'] else ''}
                {f'<a href="{ep["st_link"]}" class="btn btn-st" target="_blank">Stream</a>' if ep['st_link'] else ''}
                {f'<a href="{ep["tg_link"]}" class="btn btn-tg" target="_blank">Telegram</a>' if ep['tg_link'] else ''}
                </div></div>"""
    
    for ad in s['ads'][1:]: html += f'<div class="ad-container">{ad}</div>'
    html += '</div></body></html>'
    return render_template_string(html)

@app.route('/admin')
def admin_panel():
    s = get_site_settings()
    q = request.args.get('q', '')
    filt = {"title": {"$regex": q, "$options": "i"}} if q else {}
    movies = list(series_collection.find(filt).sort("_id", -1))
    html = f"<!DOCTYPE html><html><head>{get_dynamic_style(s)}</head><body>{get_header(s, True)}"
    html += '<div class="container"><h2>মুভি ম্যানেজমেন্ট</h2><div class="admin-table-container"><table class="admin-table"><thead><tr><th>Poster</th><th>Name</th><th>Year</th><th>Action</th></tr></thead><tbody>'
    for m in movies:
        html += f"<tr><td><img src='{m['poster']}' width='40'></td><td>{m['title']}</td><td>{m['year']}</td><td><a href='/admin/edit/{m['_id']}' style='color:orange'>Edit</a> | <form action='/admin/delete/{m['_id']}' method='POST' style='display:inline'><button type='submit' style='color:red; background:none; border:none; cursor:pointer'>Delete</button></form></td></tr>"
    html += '</tbody></table></div></div></body></html>'
    return render_template_string(html)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    s = get_site_settings()
    if request.method == 'POST':
        new_data = {
            "site_name": request.form.get('site_name'),
            "primary_color": request.form.get('p_color'),
            "bg_color": request.form.get('b_color'),
            "card_bg_color": request.form.get('c_color'),
            "text_color": request.form.get('t_color'),
            "badge_color": request.form.get('badge_color'),
            "lang_color": request.form.get('lang_color'),
            "ads": [ad for ad in request.form.getlist('ads[]') if ad.strip()]
        }
        settings_collection.update_one({"type": "site_config"}, {"$set": new_data})
        return redirect(url_for('admin_settings'))

    html = f"<!DOCTYPE html><html><head>{get_dynamic_style(s)}</head><body>{get_header(s, True)}"
    html += f"""<div class="container"><div class="form-card"><h2>সাইট সেটিংস ও বিজ্ঞাপন</h2>
        <form method="POST">
            <label>সাইটের নাম:</label><input name="site_name" value="{s['site_name']}">
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                <div><label>থিম কালার:</label><input type="color" name="p_color" value="{s['primary_color']}"></div>
                <div><label>ব্যাকগ্রাউন্ড কালার:</label><input type="color" name="b_color" value="{s['bg_color']}"></div>
                <div><label>কার্ড কালার:</label><input type="color" name="c_color" value="{s['card_bg_color']}"></div>
                <div><label>টেক্সট কালার:</label><input type="color" name="t_color" value="{s['text_color']}"></div>
                <div><label>ব্যাজ (Badge) কালার:</label><input type="color" name="badge_color" value="{s['badge_color']}"></div>
                <div><label>ভাষা টেক্সট কালার:</label><input type="color" name="lang_color" value="{s['lang_color']}"></div>
            </div>
            <hr><h3>আনলিমিটেড বিজ্ঞাপন (Ad Codes):</h3>
            <div id="ad-slots">
                {"".join([f'<div><textarea name="ads[]" rows="3" placeholder="Paste Ad Code Here">{ad}</textarea></div>' for ad in s['ads']])}
            </div>
            <button type="button" onclick="addAdSlot()" style="width:100%; margin-top:10px;">+ Add New Ad Slot</button>
            <button type="submit" class="submit-btn">Save Settings</button>
        </form></div></div>
        <script>function addAdSlot(){{ document.getElementById('ad-slots').innerHTML += '<div><textarea name="ads[]" rows="3" placeholder="Paste Ad Code Here"></textarea></div>'; }}</script></body></html>"""
    return render_template_string(html)

@app.route('/admin/add', methods=['GET', 'POST'])
@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def manage_movie(id=None):
    s = get_site_settings()
    movie = series_collection.find_one({"_id": ObjectId(id)}) if id else None
    if request.method == 'POST':
        sh = request.form.get('shortener', "").strip()
        ep_nos = request.form.getlist('ep_no[]')
        dl_links = request.form.getlist('dl[]')
        st_links = request.form.getlist('st[]')
        tg_links = request.form.getlist('tg[]')
        eps = []
        for i in range(len(ep_nos)):
            def lnk(l): return sh + l.strip() if sh and l.strip() else l.strip()
            eps.append({"ep_no": ep_nos[i], "dl_link": lnk(dl_links[i]), "st_link": lnk(st_links[i]), "tg_link": lnk(tg_links[i])})
        data = {"title": request.form.get('title'), "year": request.form.get('year'), "language": request.form.get('lang'), "poster": request.form.get('poster'), "poster_text": request.form.get('poster_text'), "description": request.form.get('desc'), "episodes": eps}
        if id: series_collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        else: series_collection.insert_one(data)
        return redirect(url_for('admin_panel'))
    
    html = f"<!DOCTYPE html><html><head>{get_dynamic_style(s)}</head><body>{get_header(s, True)}<div class='container'><div class='form-card'><form method='POST'>"
    html += f"<h2>Save Movie</h2><label>মুভির নাম:</label><input name='title' value='{movie['title'] if movie else ''}' required>"
    html += f"<div style='display:flex; gap:10px;'><input name='year' placeholder='Year' value='{movie['year'] if movie else ''}'><input name='lang' placeholder='Language' value='{movie['language'] if movie else ''}'></div>"
    html += f"<label>পোস্টার লিঙ্ক:</label><input name='poster' value='{movie['poster'] if movie else ''}' required>"
    html += f"<label>পোস্টার টেক্স (Badge):</label><input name='poster_text' value='{movie['poster_text'] if movie else ''}'>"
    html += f"<label>গল্প:</label><textarea name='desc' rows='4'>{movie['description'] if movie else ''}</textarea>"
    html += f"<label>লিঙ্ক শর্টনার (Base URL):</label><input name='shortener' placeholder='https://short.com/api?link='>"
    html += "<h3>এপিসোড সমূহ:</h3><div id='ep-list'>"
    if movie:
        for ep in movie['episodes']:
            html += f"<div class='ep-input-group'><input name='ep_no[]' value='{ep['ep_no']}'><input name='dl[]' value='{ep['dl_link']}'><input name='st[]' value='{ep['st_link']}'><input name='tg[]' value='{ep['tg_link']}'></div>"
    else:
        html += "<div class='ep-input-group'><input name='ep_no[]' placeholder='Ep No'><input name='dl[]' placeholder='Download'><input name='st[]' placeholder='Stream'><input name='tg[]' placeholder='Telegram'></div>"
    html += "</div><button type='button' onclick='addEp()'>+ Add More Episode</button><button type='submit' class='submit-btn'>Publish Movie</button></form></div></div>"
    html += "<script>function addEp(){{ document.getElementById('ep-list').innerHTML += '<div class=\"ep-input-group\"><input name=\"ep_no[]\" placeholder=\"Ep No\"><input name=\"dl[]\" placeholder=\"Download\"><input name=\"st[]\" placeholder=\"Stream\"><input name=\"tg[]\" placeholder=\"Telegram\"></div>'; }}</script></body></html>"
    return render_template_string(html)

@app.route('/admin/delete/<id>', methods=['POST'])
def delete_movie(id):
    series_collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
