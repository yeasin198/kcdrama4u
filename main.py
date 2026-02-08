import os
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "movies_ultimate_system_key"

# --- MongoDB কানেকশন ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['webseries_db']
series_collection = db['series']
settings_collection = db['settings']

# --- সেটিংস লোড ফাংশন ---
def get_site_config():
    default = {
        "site_name": "WebSeries BD",
        "primary_color": "#E50914",
        "bg_color": "#0b0b0b",
        "card_bg": "#1a1a1a",
        "text_color": "#ffffff",
        "badge_color": "#E50914",
        "lang_color": "#aaaaaa",
        "ads": []
    }
    s = settings_collection.find_one({"type": "config"})
    if not s:
        settings_collection.insert_one({"type": "config", **default})
        return default
    return s

# --- ডাইনামিক রেসপন্সিভ CSS ---
def get_css(s):
    return f"""
<style>
    :root {{ 
        --primary: {s['primary_color']}; 
        --bg: {s['bg_color']}; 
        --card: {s['card_bg']}; 
        --text: {s['text_color']}; 
        --badge: {s['badge_color']};
        --lang: {s['lang_color']};
    }}
    body {{ background: var(--bg); color: var(--text); font-family: sans-serif; margin: 0; padding: 0; }}
    
    /* Header */
    header {{ background: #000; padding: 15px 5%; display: flex; flex-direction: column; align-items: center; border-bottom: 2px solid var(--primary); position: sticky; top: 0; z-index: 1000; }}
    @media (min-width: 768px) {{ header {{ flex-direction: row; justify-content: space-between; }} }}
    .logo {{ color: var(--primary); font-size: 24px; font-weight: bold; text-decoration: none; text-transform: uppercase; }}
    
    /* Search Bar */
    .search-box {{ display: flex; background: #222; border-radius: 5px; overflow: hidden; margin: 10px 0; border: 1px solid #333; width: 100%; max-width: 450px; }}
    .search-box input {{ border: none; background: transparent; color: white; padding: 10px; width: 100%; outline: none; }}
    .search-box button {{ background: var(--primary); border: none; color: white; padding: 0 15px; cursor: pointer; }}

    .container {{ padding: 20px 5%; }}
    
    /* Grid System (Mobile vs Desktop) */
    .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
    @media (min-width: 768px) {{ .grid {{ grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }} }}

    /* Cards */
    .card {{ background: var(--card); border-radius: 8px; overflow: hidden; position: relative; text-decoration: none; color: white; transition: 0.3s; border: 1px solid #333; display: block; }}
    .card:hover {{ transform: translateY(-5px); border-color: var(--primary); }}
    .card img {{ width: 100%; aspect-ratio: 2/3; object-fit: cover; }}
    .badge {{ position: absolute; top: 8px; left: 8px; background: var(--badge); color: white; padding: 3px 8px; font-size: 10px; border-radius: 3px; font-weight: bold; }}
    .card-info {{ padding: 10px; text-align: center; font-size: 14px; font-weight: bold; }}

    /* Detail Page */
    .detail-flex {{ display: flex; flex-direction: column; gap: 20px; }}
    @media (min-width: 768px) {{ .detail-flex {{ flex-direction: row; }} }}
    .detail-img {{ width: 100%; max-width: 280px; border-radius: 10px; border: 1px solid #333; align-self: center; }}
    .story {{ background: #111; padding: 15px; border-radius: 8px; border-left: 4px solid var(--primary); margin: 15px 0; color: #ccc; line-height: 1.6; }}
    .lang-label {{ color: var(--lang); font-weight: bold; }}

    /* Episode Buttons */
    .ep-row {{ background: #1a1a1a; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #333; }}
    .btn-group {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }}
    .btn {{ padding: 10px; border-radius: 5px; text-decoration: none; color: white; font-size: 12px; font-weight: bold; text-align: center; flex: 1; min-width: 100px; }}
    .dl {{ background: #27ae60; }} .st {{ background: #2980b9; }} .tg {{ background: #0088cc; }}

    /* Ads */
    .ad-slot {{ margin: 20px 0; text-align: center; max-width: 100%; overflow: hidden; }}

    /* Admin Management UI */
    .admin-nav {{ display: flex; gap: 10px; margin-top: 10px; }}
    .admin-nav a {{ color: white; text-decoration: none; font-size: 13px; background: #333; padding: 5px 10px; border-radius: 4px; }}
    .admin-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    .admin-table th, .admin-table td {{ padding: 12px; border: 1px solid #333; text-align: left; }}
    .form-card {{ max-width: 700px; margin: auto; background: #1a1a1a; padding: 25px; border-radius: 10px; border: 1px solid #333; }}
    input, textarea {{ width: 100%; padding: 12px; margin: 8px 0; background: #222; color: white; border: 1px solid #444; border-radius: 5px; box-sizing: border-box; }}
    .submit-btn {{ background: var(--primary); color: white; border: none; padding: 15px; width: 100%; cursor: pointer; font-weight: bold; border-radius: 5px; }}
    .ep-group {{ background: #262626; padding: 10px; border-radius: 5px; margin-bottom: 10px; border: 1px dashed #555; }}
</style>
"""

# --- ইউজার প্যানেল (শুধুমাত্র মুভি এবং সার্চ) ---

@app.route('/')
def home():
    s = get_site_config()
    q = request.args.get('q', '')
    movies = list(series_collection.find({"title": {"$regex": q, "$options": "i"}}).sort("_id", -1))
    
    html = f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{get_css(s)}</head><body>"
    # Header with only Logo and User Search
    html += f"<header><a href='/' class='logo'>{s['site_name']}</a>"
    html += f"<form action='/' class='search-box'><input name='q' placeholder='খুঁজুন...' value='{q}'><button>Search</button></form></header>"
    
    html += "<div class='container'>"
    # Ads
    for ad in s['ads']: html += f"<div class='ad-slot'>{ad}</div>"
    
    html += "<div class='grid'>"
    for m in movies:
        html += f"<a href='/series/{m['_id']}' class='card'>{'<div class="badge">'+m["poster_text"]+'</div>' if m.get("poster_text") else ''}<img src='{m['poster']}'><div class='card-info'>{m['title']} ({m['year']})</div></a>"
    html += "</div></div></body></html>"
    return render_template_string(html)

@app.route('/series/<id>')
def detail(id):
    s = get_site_config()
    m = series_collection.find_one({"_id": ObjectId(id)})
    html = f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{get_css(s)}</head><body><header><a href='/' class='logo'>{s['site_name']}</a></header><div class='container'>"
    # Ad
    if s['ads']: html += f"<div class='ad-slot'>{s['ads'][0]}</div>"
    
    html += f"<div class='detail-flex'><img src='{m['poster']}' class='detail-img'><div><h1>{m['title']} ({m['year']})</h1>"
    html += f"<p><span class='lang-label'>ভাষা: {m['language']}</span> | সাল: {m['year']}</p>"
    html += f"<div class='story'><b>গল্প:</b><br>{m['description']}</div></div></div><hr style='border:0.1px solid #333; margin:30px 0'><h3>এপিসোড লিঙ্ক:</h3>"
    
    for ep in m['episodes']:
        html += f"<div class='ep-row'><strong>Ep: {ep['ep_no']}</strong><div class='btn-group'>"
        if ep['dl_link']: html += f"<a href='{ep['dl_link']}' class='btn dl' target='_blank'>Download</a>"
        if ep['st_link']: html += f"<a href='{ep['st_link']}' class='btn st' target='_blank'>Stream</a>"
        if ep['tg_link']: html += f"<a href='{ep['tg_link']}' class='btn tg' target='_blank'>Telegram</a>"
        html += "</div></div>"
    
    html += "</div></body></html>"
    return render_template_string(html)

# --- অ্যাডমিন প্যানেল (ম্যানেজমেন্ট, কালার, সেটিংস, বিজ্ঞাপন) ---

@app.route('/admin')
def admin_dashboard():
    s = get_site_config()
    q = request.args.get('q', '')
    movies = list(series_collection.find({"title": {"$regex": q, "$options": "i"}}).sort("_id", -1))
    
    html = f"<html><head>{get_css(s)}</head><body><header><a href='/' class='logo'>Admin Panel</a>"
    html += f"<form action='/admin' class='search-box'><input name='q' placeholder='অ্যাডমিন সার্চ...' value='{q}'><button>Search</button></form></header>"
    
    html += "<div class='container'><h2>মুভি লিস্ট</h2>"
    html += "<div class='admin-nav'><a href='/admin/add'>+ Add New Movie</a><a href='/admin/settings'>⚙ Site Settings & Ads</a><a href='/' style='background:red'>View Site</a></div>"
    
    html += "<table class='admin-table'><tr><th>Poster</th><th>Title</th><th>Action</th></tr>"
    for m in movies:
        html += f"<tr><td><img src='{m['poster']}' width='40'></td><td>{m['title']}</td>"
        html += f"<td><a href='/admin/edit/{m['_id']}' style='color:orange'>Edit</a> | <form action='/admin/delete/{m['_id']}' method='POST' style='display:inline'><button style='color:red; background:none; border:none; cursor:pointer'>Delete</button></form></td></tr>"
    html += "</table></div></body></html>"
    return render_template_string(html)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    s = get_site_config()
    if request.method == 'POST':
        settings_collection.update_one({"type": "config"}, {"$set": {
            "site_name": request.form.get('site_name'),
            "primary_color": request.form.get('p_color'),
            "bg_color": request.form.get('b_color'),
            "card_bg": request.form.get('c_color'),
            "text_color": request.form.get('t_color'),
            "badge_color": request.form.get('badge_color'),
            "lang_color": request.form.get('lang_color'),
            "ads": [ad for ad in request.form.getlist('ads[]') if ad.strip()]
        }})
        return redirect('/admin/settings')

    html = f"<html><head>{get_css(s)}</head><body><header><a href='/admin' class='logo'>Settings</a></header><div class='container'><div class='form-card'><h2>সাইট সেটিংস ও কালার</h2>"
    html += "<form method='POST'><label>সাইট নেম:</label><input name='site_name' value='"+s['site_name']+"'>"
    html += f"<label>থিম কালার:</label><input type='color' name='p_color' value='{s['primary_color']}'>"
    html += f"<label>ব্যাকগ্রাউন্ড:</label><input type='color' name='b_color' value='{s['bg_color']}'>"
    html += f"<label>কার্ড ব্যাকগ্রাউন্ড:</label><input type='color' name='c_color' value='{s['card_bg']}'>"
    html += f"<label>টেক্সট কালার:</label><input type='color' name='t_color' value='{s['text_color']}'>"
    html += f"<label>ব্যাজ কালার:</label><input type='color' name='badge_color' value='{s['badge_color']}'>"
    html += f"<label>ভাষা কালার:</label><input type='color' name='lang_color' value='{s['lang_color']}'>"
    html += "<hr><h3>আনলিমিটেড বিজ্ঞাপন কোড:</h3><div id='ad-list'>"
    for ad in s['ads']: html += f"<textarea name='ads[]' rows='3'>{ad}</textarea>"
    html += "</div><button type='button' onclick='addAd()' style='width:100%'>+ Add Ad Slot</button><button class='submit-btn' style='margin-top:20px'>Save Settings</button></form></div></div>"
    return render_template_string(html + "<script>function addAd(){document.getElementById('ad-list').insertAdjacentHTML('beforeend', '<textarea name=\"ads[]\" rows=\"3\" placeholder=\"Ad Code\"></textarea>')}</script></body></html>")

@app.route('/admin/add', methods=['GET', 'POST'])
@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def manage_movie(id=None):
    s = get_site_config()
    m = series_collection.find_one({"_id": ObjectId(id)}) if id else None
    if request.method == 'POST':
        sh = request.form.get('shortener', "")
        eps = []
        for i, en in enumerate(request.form.getlist('ep_no[]')):
            def l(f): return sh + request.form.getlist(f)[i].strip() if sh and request.form.getlist(f)[i].strip() else request.form.getlist(f)[i].strip()
            eps.append({"ep_no": en, "dl_link": l('dl[]'), "st_link": l('st[]'), "tg_link": l('tg[]')})
        data = {"title": request.form.get('t'), "year": request.form.get('y'), "language": request.form.get('l'), "poster": request.form.get('p'), "poster_text": request.form.get('pt'), "description": request.form.get('d'), "episodes": eps}
        if id: series_collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        else: series_collection.insert_one(data)
        return redirect('/admin')

    html = f"<html><head>{get_css(s)}</head><body><header><a href='/admin' class='logo'>Manage Movie</a></header><div class='container'><div class='form-card'><form method='POST'>"
    html += f"<input name='t' placeholder='মুভির নাম' value='{m['title'] if m else ''}' required><input name='y' placeholder='সাল' value='{m['year'] if m else ''}'><input name='l' placeholder='ভাষা' value='{m['language'] if m else ''}'>"
    html += f"<input name='p' placeholder='পোস্টার লিঙ্ক' value='{m['poster'] if m else ''}' required><input name='pt' placeholder='ব্যাজ টেক্স (4K/HD)' value='{m['poster_text'] if m else ''}'>"
    html += f"<textarea name='d' placeholder='গল্প'>{m['description'] if m else ''}</textarea><input name='shortener' placeholder='লিঙ্ক শর্টনার বেস লিঙ্ক (ঐচ্ছিক)'>"
    html += "<h3>এপিসোড সমূহ:</h3><div id='ep-area'>"
    if m:
        for e in m['episodes']: html += f"<div class='ep-group'><input name='ep_no[]' value='{e['ep_no']}'><input name='dl[]' value='{e['dl_link']}'><input name='st[]' value='{e['st_link']}'><input name='tg[]' value='{e['tg_link']}'></div>"
    else: html += "<div class='ep-group'><input name='ep_no[]' placeholder='এপিসোড নং'><input name='dl[]' placeholder='DL লিঙ্ক'><input name='st[]' placeholder='Stream লিঙ্ক'><input name='tg[]' placeholder='TG লিঙ্ক'></div>"
    html += "</div><button type='button' onclick='addEp()' style='width:100%'>+ Add More Episode</button><button class='submit-btn' style='margin-top:20px'>Save Movie</button></form></div></div>"
    return render_template_string(html + "<script>function addEp(){document.getElementById('ep-area').insertAdjacentHTML('beforeend', '<div class=\"ep-group\"><input name=\"ep_no[]\" placeholder=\"এপিসোড নং\"><input name=\"dl[]\" placeholder=\"DL\"><input name=\"st[]\" placeholder=\"ST\"><input name=\"tg[]\" placeholder=\"TG\"></div>')}</script></body></html>")

@app.route('/admin/delete/<id>', methods=['POST'])
def delete_movie(id):
    series_collection.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
