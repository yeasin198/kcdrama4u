import os
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- সিকিউরিটি কনফিগারেশন ---
app.secret_key = os.environ.get("SESSION_SECRET", "pro_secure_key_998877")
RECOVERY_KEY = os.environ.get("RECOVERY_KEY", "admin@secret")

# --- MongoDB কানেকশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster"
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client['app_hub_final_v7']
apps_col = db['apps']
users_col = db['users']
ads_col = db['ads']
settings_col = db['settings']

# --- ব্র্যান্ডিং তথ্য ---
def get_site_info():
    info = settings_col.find_one({"type": "site_info"})
    if not info:
        return {"name": "APPHUB", "title": "Ultimate Store", "logo": "https://cdn-icons-png.flaticon.com/512/2589/2589127.png"}
    return info

# --- HTML লেআউট (f-string ব্যবহার করা হয়নি এরর এড়াতে) ---
LAYOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site.name }} - {{ site.title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.css" />
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #f8fafc; }
        .swiper { width: 100%; height: 380px; border-radius: 2.5rem; overflow: hidden; margin-bottom: 3rem; }
        .sidebar-active { background: #4f46e5; color: white !important; border-radius: 1rem; }
        .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    </style>
</head>
<body class="bg-slate-50">
    {% if not is_admin_route %}
    <nav class="bg-white border-b sticky top-0 z-50 h-20 flex items-center shadow-sm">
        <div class="container mx-auto px-6 flex items-center justify-between">
            <a href="/" class="text-3xl font-black text-indigo-600 tracking-tighter uppercase">{{ site.name }}</a>
            <form action="/" method="GET" class="hidden md:flex bg-gray-100 rounded-2xl px-5 py-2 items-center border">
                <input type="text" name="q" placeholder="Search apps..." class="bg-transparent outline-none text-sm w-72" value="{{ q }}">
                <button type="submit"><i class="fas fa-search text-gray-400"></i></button>
            </form>
            <div class="text-[10px] font-black bg-gray-900 text-white px-3 py-1 rounded-full">v7.0 PRO</div>
        </div>
    </nav>
    {% endif %}

    <div class="{% if is_admin_route %}flex min-h-screen{% else %}container mx-auto px-6 py-12{% endif %}">
        {% if is_admin_route %}
        <!-- Sidebar -->
        <div class="w-72 bg-slate-900 text-slate-300 flex flex-col p-8 sticky top-0 h-screen shadow-2xl">
            <div class="text-2xl font-black text-white mb-10 italic border-b border-slate-800 pb-4 uppercase tracking-tighter">{{ site.name }}</div>
            <div class="flex-1 space-y-2">
                <a href="/admin/dashboard" class="flex items-center gap-3 p-4 transition {{ 'sidebar-active' if active_page == 'dashboard' }}"><i class="fas fa-home"></i> Dashboard</a>
                <a href="/admin/apps" class="flex items-center gap-3 p-4 transition {{ 'sidebar-active' if active_page == 'apps' }}"><i class="fas fa-box"></i> Manage Apps</a>
                <a href="/admin/ads" class="flex items-center gap-3 p-4 transition {{ 'sidebar-active' if active_page == 'ads' }}"><i class="fas fa-ad"></i> Ad Manager</a>
                <a href="/admin/settings" class="flex items-center gap-3 p-4 transition {{ 'sidebar-active' if active_page == 'settings' }}"><i class="fas fa-cog"></i> Site Settings</a>
            </div>
            <div class="border-t border-slate-800 pt-6 space-y-4">
                <a href="/" class="block text-emerald-400 font-bold hover:underline"><i class="fas fa-globe mr-2"></i>Live Site</a>
                <a href="/logout" class="block text-red-400 font-bold hover:underline"><i class="fas fa-sign-out-alt mr-2"></i>Logout</a>
            </div>
        </div>
        <div class="flex-1 p-10 bg-white overflow-y-auto">
            {% with messages = get_flashed_messages() %}
                {% for msg in messages %}<div class="bg-indigo-600 text-white p-4 rounded-2xl mb-6 shadow-lg">{{ msg }}</div>{% endfor %}
            {% endwith %}
            {% block admin_content %}{% endblock %}
        </div>
        {% else %}
            {% with messages = get_flashed_messages() %}
                {% for msg in messages %}<div class="bg-indigo-100 text-indigo-700 p-4 rounded-xl mb-6 border-l-4 border-indigo-600 shadow-sm">{{ msg }}</div>{% endfor %}
            {% endwith %}
            {% block content %}{% endblock %}
        {% endif %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
    <script>const swiper = new Swiper('.swiper', { loop: true, autoplay: { delay: 3500 }, pagination: { el: '.swiper-pagination', clickable: true } });</script>
</body>
</html>
"""

# --- রুটস (Routes) ---

@app.route('/')
def home():
    site = get_site_info()
    q = request.args.get('q', '')
    query = {"name": {"$regex": q, "$options": "i"}} if q else {}
    apps = list(apps_col.find(query).sort('_id', -1))
    featured = [] if q else list(apps_col.find({"featured": "on"}).limit(5))
    ads = list(ads_col.find())
    
    content = """
    {% if featured %}
    <div class="swiper mb-12 shadow-2xl">
        <div class="swiper-wrapper">
            {% for f in featured %}
            <div class="swiper-slide bg-indigo-900 flex items-center p-12 text-white relative">
                <div class="z-10 max-w-xl">
                    <span class="bg-indigo-500 text-[10px] font-bold px-3 py-1 rounded-full uppercase mb-4 inline-block tracking-widest text-white">Featured App</span>
                    <h2 class="text-5xl font-black mb-6 leading-none">{{ f.name }}</h2>
                    <p class="text-indigo-200 mb-8 line-clamp-2">{{ f.info }}</p>
                    <a href="/app/{{f._id}}" class="bg-white text-indigo-900 px-10 py-4 rounded-full font-black text-xl shadow-2xl transition hover:bg-indigo-50">Details</a>
                </div>
                <img src="{{f.logo}}" class="absolute right-20 w-56 h-56 rounded-[3.5rem] opacity-60 shadow-2xl hidden md:block rotate-12">
            </div>
            {% endfor %}
        </div>
        <div class="swiper-pagination"></div>
    </div>
    {% endif %}
    <div class="mb-10">
        {% for ad in ads %}<div class="bg-white p-3 rounded-2xl shadow-sm border flex justify-center mb-6 overflow-hidden">{{ ad.code | safe }}</div>{% endfor %}
    </div>
    <div class="flex justify-between items-center mb-10"><h2 class="text-3xl font-black text-gray-800 uppercase italic">{% if q %}Search Results{% else %}Latest Uploads{% endif %}</h2></div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
        {% for a in apps %}
        <a href="/app/{{a._id}}" class="bg-white p-8 rounded-[3rem] border border-gray-100 shadow-sm hover:shadow-2xl transition duration-500 text-center group">
            <img src="{{a.logo}}" class="w-24 h-24 rounded-[2rem] mx-auto mb-5 shadow-lg group-hover:scale-110 transition duration-500">
            <h3 class="font-extrabold text-xl text-gray-800 mb-2 truncate px-2">{{a.name}}</h3>
            <p class="text-xs font-bold text-indigo-500 uppercase mb-5 tracking-tighter">{{a.category}} • V{{a.version}}</p>
            <div class="bg-gray-50 text-indigo-600 py-3 rounded-2xl font-black group-hover:bg-indigo-600 group-hover:text-white transition uppercase">View Details</div>
        </a>
        {% endfor %}
    </div>
    """
    return render_template_string(LAYOUT_TEMPLATE.replace('{% block content %}{% endblock %}', content), site=site, apps=apps, featured=featured, ads=ads, q=q, is_admin_route=False)

@app.route('/app/<id>')
def details(id):
    site = get_site_info()
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    if not app_data: return redirect('/')
    content = """
    <div class="max-w-5xl mx-auto bg-white rounded-[4rem] shadow-2xl p-12 flex flex-col md:flex-row gap-12 items-center border border-gray-100">
        <img src="{{ app.logo }}" class="w-64 h-64 rounded-[4rem] shadow-2xl">
        <div class="flex-1 text-center md:text-left">
            <h1 class="text-5xl font-black text-gray-800 mb-6 tracking-tighter italic">{{ app.name }}</h1>
            <div class="flex flex-wrap gap-2 mb-8 justify-center md:justify-start uppercase font-bold text-xs tracking-widest">
                <span class="bg-indigo-600 text-white px-5 py-2 rounded-full">{{ app.category }}</span>
                <span class="bg-gray-100 text-gray-500 px-5 py-2 rounded-full">Version {{ app.version }}</span>
                <span class="bg-slate-100 text-slate-400 px-5 py-2 rounded-full">Released: {{ app.release_date }}</span>
            </div>
            <p class="text-gray-500 text-lg leading-relaxed mb-10">{{ app.info }}</p>
            <a href="/get/{{ app._id }}" class="inline-block bg-indigo-600 text-white px-16 py-5 rounded-full font-black text-2xl shadow-2xl shadow-indigo-200 hover:scale-105 transition italic uppercase">Get APK Now</a>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_TEMPLATE.replace('{% block content %}{% endblock %}', content), site=site, app=app_data, is_admin_route=False)

@app.route('/get/<id>')
def download_logic(id):
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    cfg = settings_col.find_one({"type": "shortener"})
    url = app_data['download_link']
    if cfg and cfg.get('url') and cfg.get('api'):
        try:
            res = requests.get(f"https://{cfg['url']}/api?api={cfg['api']}&url={url}", timeout=10).json()
            short = res.get('shortenedUrl') or res.get('shortedUrl')
            if short: return redirect(short)
        except: pass
    return redirect(url)

# --- এডমিন সেকশন ---

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
        flash("Access Key Invalid!")
    content = """
    <div class="max-w-sm mx-auto mt-32 bg-white p-16 rounded-[4rem] shadow-2xl border text-center border-slate-100">
        <h2 class="text-3xl font-black mb-10 text-indigo-700 tracking-tighter italic uppercase">Admin Access</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Access Key" class="w-full bg-slate-50 p-4 rounded-2xl text-center mb-6 outline-none border focus:border-indigo-500" required>
            <button class="w-full bg-indigo-600 text-white py-4 rounded-2xl font-black shadow-lg hover:bg-indigo-700 transition uppercase tracking-widest">Authenticate</button>
        </form>
        <div class="mt-8 text-xs text-slate-300"><a href="/forgot">Override Password</a></div>
    </div>
    """
    return render_template_string(LAYOUT_TEMPLATE.replace('{% block content %}{% endblock %}', content), site=site, is_admin_route=False)

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/admin-gate')
    stats = {"apps": apps_col.count_documents({}), "ads": ads_col.count_documents({}), "featured": apps_col.count_documents({"featured": "on"})}
    content = """
    <h1 class="text-4xl font-black mb-10 text-slate-800 tracking-tighter uppercase italic">Dashboard Statistics</h1>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
        <div class="bg-indigo-600 p-12 rounded-[3.5rem] text-white shadow-xl shadow-indigo-100">
            <div class="text-7xl font-black mb-2 tracking-tighter">{{ stats.apps }}</div><div class="font-bold text-xs uppercase opacity-70 tracking-widest">Total Apps Live</div>
        </div>
        <div class="bg-slate-900 p-12 rounded-[3.5rem] text-white shadow-xl shadow-slate-300">
            <div class="text-7xl font-black mb-2 tracking-tighter">{{ stats.ads }}</div><div class="font-bold text-xs uppercase opacity-70 tracking-widest">Active Ads</div>
        </div>
        <div class="bg-orange-500 p-12 rounded-[3.5rem] text-white shadow-xl shadow-orange-100">
            <div class="text-7xl font-black mb-2 tracking-tighter">{{ stats.featured }}</div><div class="font-bold text-xs uppercase opacity-70 tracking-widest">Slider Apps</div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_TEMPLATE.replace('{% block admin_content %}{% endblock %}', content), site=get_site_info(), stats=stats, is_admin_route=True, active_page='dashboard')

@app.route('/admin/apps', methods=['GET', 'POST'])
def admin_apps():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        apps_col.insert_one({
            "name": request.form.get('name'), "logo": request.form.get('logo'), 
            "category": request.form.get('category'), "release_date": request.form.get('release_date'), 
            "version": request.form.get('version'), "info": request.form.get('info'), 
            "download_link": request.form.get('download_link'), "featured": request.form.get('featured')
        })
        flash("Application Uploaded!")
    
    q = request.args.get('q', '')
    query = {"name": {"$regex": q, "$options": "i"}} if q else {}
    apps = list(apps_col.find(query).sort('_id', -1))
    
    content = """
    <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
        <h1 class="text-3xl font-black text-slate-800 tracking-tighter uppercase">Application Control</h1>
        <form class="bg-slate-100 px-6 py-2.5 rounded-full border flex items-center w-full md:w-80">
            <input type="text" name="q" placeholder="Search apps..." class="bg-transparent outline-none text-sm w-full font-bold" value="{{ q }}">
            <button type="submit"><i class="fas fa-search text-indigo-600"></i></button>
        </form>
    </div>
    <div class="grid lg:grid-cols-3 gap-10">
        <form method="POST" class="bg-slate-50 p-8 rounded-[3rem] border space-y-4 shadow-inner">
            <input name="name" placeholder="App Name" class="w-full p-4 rounded-xl border outline-none" required>
            <input name="logo" placeholder="Logo Link" class="w-full p-4 rounded-xl border outline-none" required>
            <select name="category" class="w-full p-4 rounded-xl border outline-none"><option>Mobile (Android)</option><option>PC / Desktop</option><option>iOS (Apple)</option></select>
            <div class="flex gap-2">
                <input type="date" name="release_date" class="w-1/2 p-4 rounded-xl border outline-none" required>
                <input name="version" placeholder="v1.0" class="w-1/2 p-4 rounded-xl border outline-none" required>
            </div>
            <textarea name="info" placeholder="Short Meta Info..." class="w-full p-4 rounded-xl border h-28 outline-none" required></textarea>
            <input name="download_link" placeholder="Download Destination URL" class="w-full p-4 rounded-xl border outline-none" required>
            <label class="flex items-center gap-2 font-bold text-indigo-600 text-sm cursor-pointer"><input type="checkbox" name="featured" class="w-5 h-5 accent-indigo-600"> Show in Slider</label>
            <button class="w-full bg-indigo-600 text-white py-4 rounded-2xl font-black shadow-lg hover:bg-indigo-700">PUBLISH LIVE</button>
        </form>
        <div class="lg:col-span-2 bg-white rounded-[3rem] border overflow-hidden shadow-sm">
            <table class="w-full text-left">
                <thead class="bg-slate-50 border-b"><tr><th class="p-5 font-bold uppercase text-xs">App Name</th><th class="p-5 text-right font-bold uppercase text-xs">Operations</th></tr></thead>
                <tbody>
                    {% for a in apps %}
                    <tr class="border-b last:border-0 hover:bg-slate-50">
                        <td class="p-5 flex items-center gap-4">
                            <img src="{{ a.logo }}" class="w-10 h-10 rounded-lg shadow-sm">
                            <div><p class="font-bold text-slate-800 leading-none">{{ a.name }}</p>
                            {% if a.featured %}<span class="text-[8px] bg-orange-500 text-white px-2 py-0.5 rounded font-black">SLIDER ACTIVE</span>{% endif %}</div>
                        </td>
                        <td class="p-5 text-right"><a href="/del/app/{{ a._id }}" class="text-red-500 font-black text-sm" onclick="return confirm('WARNING: Permanent deletion?')">DELETE</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_TEMPLATE.replace('{% block admin_content %}{% endblock %}', content), site=site, apps=apps, q=q, is_admin_route=True, active_page='apps')

@app.route('/admin/ads', methods=['GET', 'POST'])
def admin_ads():
    if not session.get('logged_in'): return redirect('/admin-gate')
    if request.method == 'POST':
        ads_col.insert_one({"name": request.form.get('name'), "code": request.form.get('code')})
        flash("Ad Script Injected Successfully!")
    ads = list(ads_col.find())
    content = """
    <h1 class="text-3xl font-black mb-10 text-slate-800 tracking-tighter uppercase italic">Monetization Manager</h1>
    <form method="POST" class="max-w-3xl bg-slate-50 p-10 rounded-[3rem] space-y-4 mb-12 border shadow-inner">
        <input name="name" placeholder="Ad Spot Identity (e.g. Header)" class="w-full p-4 rounded-xl border outline-none" required>
        <textarea name="code" placeholder="Paste full HTML/JS Code here..." class="w-full p-4 rounded-xl border h-44 font-mono text-xs outline-none" required></textarea>
        <button class="bg-indigo-600 text-white px-10 py-4 rounded-2xl font-black shadow-lg hover:bg-indigo-700 transition">DEPLOY SCRIPT</button>
    </form>
    <div class="space-y-4">
        {% for ad in ads %}
        <div class="flex justify-between items-center p-6 bg-white border rounded-[2.5rem] shadow-sm hover:shadow-xl transition">
            <span class="font-bold text-slate-800">{{ ad.name }} <br> <small class="text-green-500 font-black uppercase text-[8px]">Status: Active & Live</small></span>
            <a href="/del/ad/{{ ad._id }}" class="text-red-500 font-bold bg-red-50 px-6 py-2 rounded-2xl hover:bg-red-500 hover:text-white transition">DISABLE UNIT</a>
        </div>
        {% endfor %}
    </div>
    """
    return render_template_string(LAYOUT_TEMPLATE.replace('{% block admin_content %}{% endblock %}', content), site=get_site_info(), ads=ads, is_admin_route=True, active_page='ads')

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        f_type = request.form.get('form_type')
        if f_type == "site_info":
            settings_col.update_one({"type": "site_info"}, {"$set": {"name": request.form.get('site_name'), "title": request.form.get('site_title')}}, upsert=True)
            flash("Site Branding Assets Synchronized!")
        else:
            settings_col.update_one({"type": "shortener"}, {"$set": {"url": request.form.get('url'), "api": request.form.get('api')}}, upsert=True)
            flash("API Backend Configuration Activated!")
        return redirect('/admin/settings')
    
    cfg = settings_col.find_one({"type": "shortener"}) or {}
    content = """
    <h1 class="text-3xl font-black mb-10 text-slate-800 tracking-tighter uppercase italic">Platform Configuration</h1>
    <div class="grid md:grid-cols-2 gap-10">
        <div class="bg-slate-50 p-10 rounded-[3rem] border shadow-inner">
            <h2 class="text-xl font-bold mb-6 text-indigo-700 underline">Site Branding</h2>
            <form method="POST">
                <input type="hidden" name="form_type" value="site_info">
                <label class="text-[9px] font-black text-slate-400 uppercase tracking-widest ml-1">App Title Name</label>
                <input name="site_name" value="{{ site.name }}" class="w-full p-4 rounded-xl border mb-4 font-black uppercase text-xl" required>
                <label class="text-[9px] font-black text-slate-400 uppercase tracking-widest ml-1">Meta Browser Title</label>
                <input name="site_title" value="{{ site.title }}" class="w-full p-4 rounded-xl border mb-6" required>
                <button class="w-full bg-indigo-600 text-white py-4 rounded-2xl font-black shadow-lg">UPDATE BRANDING</button>
            </form>
        </div>
        <div class="bg-slate-900 p-10 rounded-[3rem] border shadow-2xl text-white">
            <h2 class="text-xl font-bold mb-6 text-emerald-400 underline">External API Gateway</h2>
            <form method="POST">
                <input type="hidden" name="form_type" value="shortener">
                <label class="text-[9px] font-black text-slate-500 uppercase tracking-widest ml-1">Shortener Domain</label>
                <input name="url" value="{{ cfg.url }}" placeholder="site.xyz" class="w-full p-4 rounded-xl border border-slate-800 bg-slate-800 mb-4 outline-none focus:ring-1 ring-emerald-400" required>
                <label class="text-[9px] font-black text-slate-500 uppercase tracking-widest ml-1">Personal API Token</label>
                <input type="password" name="api" value="{{ cfg.api }}" placeholder="Secret Key" class="w-full p-4 rounded-xl border border-slate-800 bg-slate-800 mb-6 outline-none focus:ring-1 ring-emerald-400" required>
                <button class="w-full bg-emerald-600 text-slate-900 py-4 rounded-2xl font-black">SAVE BACKEND API</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_TEMPLATE.replace('{% block admin_content %}{% endblock %}', content), site=site, cfg=cfg, is_admin_route=True, active_page='settings')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        if request.form.get('key') == RECOVERY_KEY:
            users_col.update_one({"username": "admin"}, {"$set": {"password": generate_password_hash(request.form.get('pw'))}}, upsert=True)
            flash("System Credentials Override Successful!")
            return redirect('/admin-gate')
    content = """<div class="max-w-sm mx-auto mt-32 bg-white p-16 rounded-[4rem] shadow-2xl border text-center">
    <h2 class="text-2xl font-bold text-red-600 mb-8 uppercase tracking-tighter italic">Critical Override</h2>
    <form method="POST" class="space-y-4">
        <input name="key" placeholder="System Security Token" class="w-full p-4 border rounded-2xl outline-none" required>
        <input type="password" name="pw" placeholder="New Master Access PW" class="w-full p-4 border rounded-2xl outline-none" required>
        <button class="bg-red-600 text-white py-4 w-full rounded-2xl font-black shadow-xl tracking-widest">OVERRIDE NOW</button>
    </form></div>"""
    return render_template_string(LAYOUT_TEMPLATE.replace('{% block content %}{% endblock %}', content), site=get_site_info(), is_admin_route=False)

@app.route('/del/<type>/<id>')
def delete_process(type, id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    if type == 'app': apps_col.delete_one({"_id": ObjectId(id)})
    if type == 'ad': ads_col.delete_one({"_id": ObjectId(id)})
    flash("Permanent Removal Successful.")
    return redirect(request.referrer)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- Vercel Deployment Handler ---
handler = app
