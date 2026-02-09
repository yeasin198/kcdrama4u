import os
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- কনফিগারেশন (Error এড়াতে ডিফল্ট ভ্যালু দেওয়া হয়েছে) ---
app.secret_key = os.environ.get("SESSION_SECRET", "hardcoded_secret_key_v5")
RECOVERY_KEY = os.environ.get("RECOVERY_KEY", "admin@123")

# --- MongoDB কানেকশন (Timeout এবং Error হ্যান্ডেলিং সহ) ---
try:
    MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster"
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['app_directory_final_pro']
    apps_col = db['apps']
    users_col = db['users']
    ads_col = db['ads']
    settings_col = db['settings']
except Exception as e:
    print(f"Database Error: {e}")

# সাইট ইনফো ডাইনামিক ফাংশন
def get_site_info():
    try:
        info = settings_col.find_one({"type": "site_info"})
        if info: return info
    except: pass
    return {"name": "APPHUB", "title": "Ultimate App Store", "logo": "https://cdn-icons-png.flaticon.com/512/2589/2589127.png"}

# --- সম্পূর্ণ UI ডিজাইন ---
UI_STYLE = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.css" />
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800&display=swap');
    body { font-family: 'Plus Jakarta Sans', sans-serif; background: #f8fafc; }
    .swiper { width: 100%; height: 350px; border-radius: 2rem; overflow: hidden; margin-bottom: 2rem; }
    .sidebar-active { background: #4f46e5; color: white !important; border-radius: 12px; }
    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
"""

def render_layout(content, site, is_admin=False, active=""):
    nav = ""
    if not is_admin:
        nav = f'''<nav class="bg-white border-b sticky top-0 z-50 h-16 flex items-center shadow-sm">
            <div class="container mx-auto px-4 flex items-center justify-between">
                <a href="/" class="text-2xl font-black text-indigo-600 uppercase">{site['name']}</a>
                <form action="/" method="GET" class="hidden md:flex bg-gray-100 rounded-full px-4 py-1.5 items-center">
                    <input type="text" name="q" placeholder="Search apps..." class="bg-transparent outline-none text-sm w-64">
                    <button type="submit"><i class="fas fa-search text-gray-400"></i></button>
                </form>
                <div class="text-[10px] font-bold text-gray-400">PRO v5</div>
            </div></nav>'''
    
    return f"""
    <!DOCTYPE html><html><head><title>{site['name']}</title>{UI_STYLE}</head>
    <body class="bg-slate-50">
        {nav}
        <div class="{'flex min-h-screen' if is_admin else 'container mx-auto px-4 py-8'}">
            {content}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
        <script>const swiper = new Swiper('.swiper', {{ loop: true, autoplay: {{ delay: 3000 }}, pagination: {{ el: '.swiper-pagination', clickable: true }} }});</script>
    </body></html>
    """

# --- ইউজার রাউটস ---

@app.route('/')
def home():
    site = get_site_info()
    q = request.args.get('q', '')
    query = {"name": {"$regex": q, "$options": "i"}} if q else {}
    apps = list(apps_col.find(query).sort('_id', -1))
    featured = [] if q else list(apps_col.find({"featured": "on"}).limit(5))
    ads = list(ads_col.find())
    
    ads_html = "".join([f'<div class="bg-white p-2 rounded-xl shadow-sm border flex justify-center mb-4">{ad["code"]}</div>' for ad in ads])
    
    slides = "".join([f'''<div class="swiper-slide bg-indigo-900 flex items-center p-10 text-white relative">
        <div class="z-10">
            <h2 class="text-4xl font-black mb-4">{f['name']}</h2>
            <a href="/app/{f['_id']}" class="bg-white text-indigo-900 px-6 py-2 rounded-full font-bold">Details</a>
        </div>
        <img src="{f['logo']}" class="absolute right-10 w-40 h-40 rounded-3xl opacity-40">
    </div>''' for f in featured])
    
    featured_html = f'<div class="swiper"><div class="swiper-wrapper">{slides}</div><div class="swiper-pagination"></div></div>' if slides else ""

    apps_html = "".join([f'''<a href="/app/{a['_id']}" class="bg-white p-6 rounded-[2rem] border hover:shadow-xl transition text-center group">
        <img src="{a['logo']}" class="w-20 h-20 rounded-2xl mx-auto mb-3 shadow group-hover:scale-110 transition">
        <h3 class="font-bold text-gray-800">{a['name']}</h3>
        <p class="text-[10px] font-bold text-indigo-600 uppercase mb-4">{a['category']} • v{a['version']}</p>
        <div class="bg-indigo-600 text-white py-2 rounded-xl font-bold">Download</div>
    </a>''' for a in apps])

    content = f"""{featured_html}<div class="mb-8">{ads_html}</div>
    <h2 class="text-xl font-black mb-6 text-gray-800 uppercase italic border-l-4 border-indigo-600 pl-3">{'Results' if q else 'Latest Uploads'}</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">{apps_html}</div>"""
    
    return render_layout(content, site)

@app.route('/app/<id>')
def details(id):
    site = get_site_info()
    try:
        app_data = apps_col.find_one({"_id": ObjectId(id)})
        if not app_data: return redirect('/')
    except: return redirect('/')
    
    content = f"""
    <div class="max-w-4xl mx-auto bg-white rounded-[3rem] shadow-2xl p-10 flex flex-col md:flex-row gap-10 items-center border">
        <img src="{app_data['logo']}" class="w-48 h-48 rounded-[2.5rem] shadow-lg">
        <div class="flex-1 text-center md:text-left">
            <h1 class="text-4xl font-black mb-4">{app_data['name']}</h1>
            <p class="text-gray-500 mb-8 leading-relaxed">{app_data['info']}</p>
            <a href="/get/{id}" class="bg-indigo-600 text-white px-10 py-4 rounded-full font-black text-xl shadow-lg hover:bg-indigo-700 transition">DOWNLOAD NOW</a>
        </div>
    </div>
    """
    return render_layout(content, site)

@app.route('/get/<id>')
def download(id):
    try:
        app_data = apps_col.find_one({"_id": ObjectId(id)})
        if not app_data: return redirect('/')
        cfg = settings_col.find_one({"type": "shortener"})
        url = app_data['download_link']
        if cfg and cfg.get('url') and cfg.get('api'):
            try:
                res = requests.get(f"https://{cfg['url']}/api?api={cfg['api']}&url={url}", timeout=10).json()
                short = res.get('shortenedUrl') or res.get('shortedUrl')
                if short: return redirect(short)
            except: pass
        return redirect(url)
    except: return redirect('/')

# --- এডমিন প্যানেল ---

@app.route('/admin-gate', methods=['GET', 'POST'])
def login():
    site = get_site_info()
    admin_u = users_col.find_one({"username": "admin"})
    if request.method == 'POST':
        pw = request.form.get('password')
        if not admin_u:
            users_col.insert_one({"username": "admin", "password": generate_password_hash(pw)})
            session['logged_in'] = True
            return redirect('/admin/dashboard')
        if check_password_hash(admin_u['password'], pw):
            session['logged_in'] = True
            return redirect('/admin/dashboard')
        flash("Wrong Password!")
    content = f"""<div class="max-w-sm mx-auto mt-20 bg-white p-10 rounded-[2.5rem] shadow-2xl border text-center">
        <h2 class="text-2xl font-black mb-6">ADMIN LOGIN</h2>
        <form method="POST"><input type="password" name="password" class="w-full border p-4 rounded-xl mb-4 text-center outline-none" placeholder="Passcode" required>
        <button class="w-full bg-indigo-600 text-white py-3 rounded-xl font-bold">LOGIN</button></form>
        <a href="/forgot" class="text-xs text-gray-400 block mt-4">Forgot?</a>
    </div>"""
    return render_layout(content, site)

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    stats = {"apps": apps_col.count_documents({}), "ads": ads_col.count_documents({})}
    content = f"""{get_admin_nav(site, 'dashboard')}
    <div class="flex-1 p-10">
        <h1 class="text-3xl font-black mb-6">System Statistics</h1>
        <div class="grid grid-cols-2 gap-6">
            <div class="bg-indigo-600 text-white p-10 rounded-3xl shadow-lg">
                <div class="text-5xl font-black">{stats['apps']}</div><div class="font-bold text-xs uppercase opacity-70">Total Apps</div>
            </div>
            <div class="bg-gray-900 text-white p-10 rounded-3xl shadow-lg">
                <div class="text-5xl font-black">{stats['ads']}</div><div class="font-bold text-xs uppercase opacity-70">Ad Units</div>
            </div>
        </div>
    </div>"""
    return render_layout(content, site, True)

@app.route('/admin/apps', methods=['GET', 'POST'])
def admin_apps():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        apps_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo'), "category": request.form.get('category'), "version": request.form.get('version'), "info": request.form.get('info'), "download_link": request.form.get('download_link'), "featured": request.form.get('featured')})
        flash("App Added")
    
    apps = list(apps_col.find().sort('_id', -1))
    apps_list = "".join([f'<tr class="border-b"><td class="p-3">{a["name"]}</td><td class="p-3 text-right"><a href="/del/app/{a["_id"]}" class="text-red-500 font-bold px-3 py-1 bg-red-50 rounded">Delete</a></td></tr>' for a in apps])
    
    content = f"""{get_admin_nav(site, 'apps')}
    <div class="flex-1 p-10">
        <div class="grid lg:grid-cols-3 gap-10">
            <form method="POST" class="bg-white p-6 rounded-3xl border shadow-sm space-y-3">
                <h2 class="font-bold mb-2">New Upload</h2>
                <input name="name" placeholder="App Name" class="w-full p-2 border rounded-xl" required>
                <input name="logo" placeholder="Logo URL" class="w-full p-2 border rounded-xl" required>
                <select name="category" class="w-full p-2 border rounded-xl"><option>Mobile</option><option>PC</option></select>
                <input name="version" placeholder="v1.0" class="w-full p-2 border rounded-xl" required>
                <textarea name="info" placeholder="Info" class="w-full p-2 border rounded-xl h-24" required></textarea>
                <input name="download_link" placeholder="Download Link" class="w-full p-2 border rounded-xl" required>
                <label class="flex items-center gap-2 font-bold"><input type="checkbox" name="featured"> Slider App</label>
                <button class="w-full bg-indigo-600 text-white py-3 rounded-xl font-bold">PUBLISH</button>
            </form>
            <div class="lg:col-span-2 bg-white rounded-3xl border overflow-hidden shadow-sm"><table class="w-full text-left"><tbody>{apps_list}</tbody></table></div>
        </div>
    </div>"""
    return render_layout(content, site, True)

@app.route('/admin/ads', methods=['GET', 'POST'])
def admin_ads():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST': ads_col.insert_one({"name": request.form.get('name'), "code": request.form.get('code')})
    
    ads_list = "".join([f'<div class="flex justify-between p-3 border-b"><span>{ad["name"]}</span><a href="/del/ad/{ad["_id"]}" class="text-red-500 font-bold">Remove</a></div>' for ad in ads_col.find()])
    
    content = f"""{get_admin_nav(site, 'ads')}
    <div class="flex-1 p-10">
        <form method="POST" class="bg-white p-10 rounded-[2.5rem] border mb-10 space-y-4 shadow-sm">
            <input name="name" placeholder="Ad Spot Label" class="w-full p-4 border rounded-xl">
            <textarea name="code" placeholder="Ad Script" class="w-full p-4 border rounded-xl h-40"></textarea>
            <button class="bg-indigo-600 text-white px-10 py-3 rounded-xl font-bold">Save Ad</button>
        </form>
        <div class="bg-white p-4 rounded-3xl border">{ads_list}</div>
    </div>"""
    return render_layout(content, site, True)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        if request.form.get('type') == 'site':
            settings_col.update_one({"type": "site_info"}, {"$set": {"name": request.form.get('name'), "title": request.form.get('title')}}, upsert=True)
        else:
            settings_col.update_one({"type": "shortener"}, {"$set": {"url": request.form.get('url'), "api": request.form.get('api')}}, upsert=True)
        flash("Settings Updated")
        return redirect('/admin/settings')

    curr = settings_col.find_one({"type": "shortener"}) or {}
    content = f"""{get_admin_nav(site, 'settings')}
    <div class="flex-1 p-10 space-y-10">
        <form method="POST" class="bg-white p-10 rounded-[2.5rem] border shadow-sm space-y-4">
            <h2 class="font-bold">Site Branding</h2>
            <input type="hidden" name="type" value="site">
            <input name="name" value="{site['name']}" class="w-full p-4 border rounded-xl">
            <input name="title" value="{site['title']}" class="w-full p-4 border rounded-xl">
            <button class="bg-indigo-600 text-white px-10 py-3 rounded-xl">Update Name</button>
        </form>
        <form method="POST" class="bg-white p-10 rounded-[2.5rem] border shadow-sm space-y-4">
            <h2 class="font-bold">Shortener API</h2>
            <input type="hidden" name="type" value="short">
            <input name="url" value="{curr.get('url','')}" class="w-full p-4 border rounded-xl">
            <input name="api" value="{curr.get('api','')}" class="w-full p-4 border rounded-xl">
            <button class="bg-gray-900 text-white px-10 py-3 rounded-xl">Update API</button>
        </form>
    </div>"""
    return render_layout(content, site, True)

def get_admin_nav(site, active):
    return f"""
    <div class="w-64 bg-gray-900 text-gray-400 p-6 space-y-2 flex flex-col h-screen sticky top-0 shadow-2xl">
        <div class="text-xl font-black text-white mb-10 italic uppercase tracking-tighter">{site['name']}</div>
        <a href="/admin/dashboard" class="p-4 rounded-xl flex items-center gap-3 {'sidebar-active' if active=='dashboard' else 'hover:bg-gray-800'}"><i class="fas fa-home"></i> Home</a>
        <a href="/admin/apps" class="p-4 rounded-xl flex items-center gap-3 {'sidebar-active' if active=='apps' else 'hover:bg-gray-800'}"><i class="fas fa-box"></i> Apps</a>
        <a href="/admin/ads" class="p-4 rounded-xl flex items-center gap-3 {'sidebar-active' if active=='ads' else 'hover:bg-gray-800'}"><i class="fas fa-ad"></i> Ads</a>
        <a href="/admin/settings" class="p-4 rounded-xl flex items-center gap-3 {'sidebar-active' if active=='settings' else 'hover:bg-gray-800'}"><i class="fas fa-cog"></i> Settings</a>
        <div class="flex-1"></div>
        <a href="/logout" class="text-red-400 font-bold p-4"><i class="fas fa-sign-out-alt"></i> Logout</a>
    </div>"""

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        if request.form.get('key') == RECOVERY_KEY:
            users_col.update_one({"username": "admin"}, {"$set": {"password": generate_password_hash(request.form.get('pw'))}}, upsert=True)
            flash("System Reset Done")
            return redirect('/admin-gate')
        flash("Incorrect Key")
    return render_template_string(f'<form method="POST" style="max-width:300px;margin:100px auto;display:flex;flex-direction:column;gap:10px;"><input name="key" placeholder="System Key"><input name="pw" placeholder="New Pass"><button>Reset</button></form>')

@app.route('/del/<type>/<id>')
def delete(type, id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    if type == 'app': apps_col.delete_one({"_id": ObjectId(id)})
    elif type == 'ad': ads_col.delete_one({"_id": ObjectId(id)})
    return redirect(request.referrer)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Vercel Handler
handler = app
