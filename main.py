import os
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- সিকিউরিটি কনফিগারেশন ---
app.secret_key = os.environ.get("SESSION_SECRET", "final_secret_pro_1122")
RECOVERY_KEY = os.environ.get("RECOVERY_KEY", "admin@secret")

# --- MongoDB কানেকশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster"
client = MongoClient(MONGO_URI)
db = client['app_hub_pro_v4']
apps_col = db['apps']
users_col = db['users']
ads_col = db['ads']
settings_col = db['settings']

# --- সাইটের নাম ও তথ্য ডাটাবেজ থেকে নিয়ে আসার ফাংশন ---
def get_site_info():
    info = settings_col.find_one({"type": "site_info"})
    if not info:
        return {"name": "APPHUB", "title": "Ultimate App Store"}
    return info

# --- এইচটিএমএল ডিজাইন (Tailwind + Swiper.js) ---
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site.name }} - {{ site.title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.css" />
    <style>
        .sidebar-active { background: #4f46e5; color: white; border-radius: 1rem; }
        .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .swiper { width: 100%; height: 350px; border-radius: 2rem; }
    </style>
</head>
<body class="bg-slate-50 font-sans antialiased text-slate-900">
    {% if not is_admin_route %}
    <nav class="bg-white border-b sticky top-0 z-50">
        <div class="container mx-auto px-4 h-16 flex items-center justify-between">
            <a href="/" class="text-2xl font-black text-indigo-600 uppercase">{{ site.name }}</a>
            <form action="/" method="GET" class="hidden md:flex bg-slate-100 rounded-full px-4 py-1.5 items-center">
                <input type="text" name="q" placeholder="Search apps..." class="bg-transparent outline-none text-sm w-64">
                <button type="submit"><i class="fas fa-search text-slate-400"></i></button>
            </form>
            <div class="text-xs font-bold text-slate-400">PRO VERSION</div>
        </div>
    </nav>
    {% endif %}

    <div class="{% if is_admin_route %}flex min-h-screen{% else %}container mx-auto px-4 py-8{% endif %}">
        {% if is_admin_route %}
        <div class="w-72 bg-slate-900 text-slate-300 flex flex-col p-6 sticky top-0 h-screen">
            <div class="text-xl font-black text-white mb-10 italic uppercase">{{ site.name }} ADMIN</div>
            <div class="flex-1 space-y-2">
                <a href="/admin/dashboard" class="flex items-center gap-3 p-4 transition {{ 'sidebar-active' if active_page == 'dashboard' }}"><i class="fas fa-home"></i> Dashboard</a>
                <a href="/admin/apps" class="flex items-center gap-3 p-4 transition {{ 'sidebar-active' if active_page == 'apps' }}"><i class="fas fa-box"></i> Manage Apps</a>
                <a href="/admin/ads" class="flex items-center gap-3 p-4 transition {{ 'sidebar-active' if active_page == 'ads' }}"><i class="fas fa-ad"></i> Advertisements</a>
                <a href="/admin/settings" class="flex items-center gap-3 p-4 transition {{ 'sidebar-active' if active_page == 'settings' }}"><i class="fas fa-cog"></i> Site Settings</a>
            </div>
            <div class="border-t border-slate-800 pt-6 space-y-4">
                <a href="/" class="block text-emerald-400 font-bold"><i class="fas fa-globe mr-2"></i>Live Site</a>
                <a href="/logout" class="block text-red-400 font-bold"><i class="fas fa-sign-out-alt mr-2"></i>Logout</a>
            </div>
        </div>
        <div class="flex-1 p-10 bg-white">
            {% with messages = get_flashed_messages() %}{% for msg in messages %}
                <div class="bg-indigo-600 text-white p-4 rounded-2xl mb-6 shadow-lg">{{ msg }}</div>
            {% endfor %}{% endwith %}
            {% block admin_content %}{% endblock %}
        </div>
        {% else %}
            {% with messages = get_flashed_messages() %}{% for msg in messages %}
                <div class="bg-indigo-100 text-indigo-700 p-4 rounded-xl mb-6 border-l-4 border-indigo-600">{{ msg }}</div>
            {% endfor %}{% endwith %}
            {% block content %}{% endblock %}
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
    <script>const swiper = new Swiper('.swiper', { loop: true, autoplay: { delay: 3000 }, pagination: { el: '.swiper-pagination', clickable: true } });</script>
</body>
</html>
"""

# --- USER ROUTES ---

@app.route('/')
def home():
    site = get_site_info()
    q = request.args.get('q', '')
    if q:
        apps = list(apps_col.find({"name": {"$regex": q, "$options": "i"}}).sort('_id', -1))
        featured = []
    else:
        apps = list(apps_col.find().sort('_id', -1))
        featured = list(apps_col.find({"featured": "on"}).limit(5))
    
    ads = list(ads_col.find())
    
    content = """
    {% if featured %}
    <div class="swiper mb-12 shadow-2xl">
        <div class="swiper-wrapper">
            {% for f in featured %}
            <div class="swiper-slide bg-indigo-900 flex items-center p-10 text-white relative overflow-hidden">
                <div class="z-10 max-w-lg">
                    <span class="bg-indigo-500 text-[10px] font-bold px-3 py-1 rounded-full uppercase mb-4 inline-block">Featured</span>
                    <h2 class="text-4xl font-black mb-4">{{ f.name }}</h2>
                    <p class="text-indigo-200 mb-6 line-clamp-2">{{ f.info }}</p>
                    <a href="/app/{{f._id}}" class="bg-white text-indigo-900 px-8 py-3 rounded-full font-black">Details</a>
                </div>
                <img src="{{f.logo}}" class="absolute right-10 w-48 h-48 rounded-[3rem] rotate-12 opacity-80 hidden md:block">
            </div>
            {% endfor %}
        </div>
        <div class="swiper-pagination"></div>
    </div>
    {% endif %}

    <div class="mb-10 space-y-4">
        {% for ad in ads %}<div class="bg-white p-2 rounded-xl shadow-sm border flex justify-center overflow-hidden">{{ ad.code | safe }}</div>{% endfor %}
    </div>

    <h2 class="text-2xl font-black mb-8">{% if q %}Results for "{{q}}"{% else %}All Apps{% endif %}</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        {% for app in apps %}
        <a href="/app/{{app._id}}" class="bg-white p-6 rounded-[2.5rem] border shadow-sm hover:shadow-2xl transition group text-center">
            <img src="{{app.logo}}" class="w-24 h-24 rounded-3xl mx-auto mb-4 group-hover:scale-110 transition">
            <h3 class="font-bold text-lg">{{app.name}}</h3>
            <div class="text-[10px] font-bold text-indigo-600 mt-2 mb-4 uppercase">{{app.category}} • v{{app.version}}</div>
            <div class="mt-4 bg-indigo-600 text-white py-3 rounded-2xl font-black">Download</div>
        </a>
        {% endfor %}
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', content), site=site, apps=apps, featured=featured, ads=ads, q=q, is_admin_route=False)

@app.route('/app/<id>')
def details(id):
    site = get_site_info()
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    if not app_data: return redirect('/')
    content = """
    <div class="max-w-4xl mx-auto bg-white rounded-[3rem] shadow-2xl border p-10 flex flex-col md:flex-row gap-10 items-center">
        <img src="{{app.logo}}" class="w-56 h-56 rounded-[3.5rem] shadow-2xl">
        <div class="flex-1 text-center md:text-left">
            <h1 class="text-4xl font-black mb-4">{{app.name}}</h1>
            <p class="text-slate-500 mb-8">{{app.info}}</p>
            <a href="/get/{{app._id}}" class="bg-indigo-600 text-white px-12 py-4 rounded-full font-black text-xl shadow-xl">DOWNLOAD APK</a>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', content), site=site, app=app_data, is_admin_route=False)

@app.route('/get/<id>')
def download_logic(id):
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    short_cfg = settings_col.find_one({"type": "shortener"})
    target = app_data['download_link']
    if short_cfg and short_cfg.get('url') and short_cfg.get('api'):
        try:
            res = requests.get(f"https://{short_cfg['url']}/api?api={short_cfg['api']}&url={target}", timeout=10).json()
            short_url = res.get('shortenedUrl') or res.get('shortedUrl')
            if short_url: return redirect(short_url)
        except: pass
    return redirect(target)

# --- ADMIN PANEL ---

@app.route('/admin-gate', methods=['GET', 'POST'])
def login():
    site = get_site_info()
    admin = users_col.find_one({"username": "admin"})
    if request.method == 'POST':
        pw = request.form.get('password')
        if not admin:
            users_col.insert_one({"username": "admin", "password": generate_password_hash(pw)})
            session['logged_in'] = True
            return redirect('/admin/dashboard')
        if check_password_hash(admin['password'], pw):
            session['logged_in'] = True
            return redirect('/admin/dashboard')
        flash("Incorrect Password!")
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', 
        """<div class="max-w-sm mx-auto mt-24 bg-white p-12 rounded-[3rem] shadow-2xl border text-center">
        <h2 class="text-3xl font-black mb-8 text-indigo-700">LOGIN</h2>
        <form method="POST"><input type="password" name="password" class="w-full bg-slate-50 p-4 rounded-2xl text-center mb-6 outline-none border" required>
        <button class="w-full bg-indigo-600 text-white py-4 rounded-2xl font-black">LOG IN</button></form></div>"""), site=site, is_admin_route=False)

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    stats = {"apps": apps_col.count_documents({}), "ads": ads_col.count_documents({})}
    content = """
    <h1 class="text-4xl font-black mb-10">Dashboard</h1>
    <div class="grid grid-cols-2 gap-8">
        <div class="bg-indigo-600 p-10 rounded-[2rem] text-white">
            <div class="text-5xl font-black">{{stats.apps}}</div><div class="font-bold uppercase">Total Apps</div>
        </div>
        <div class="bg-slate-900 p-10 rounded-[2rem] text-white">
            <div class="text-5xl font-black">{{stats.ads}}</div><div class="font-bold uppercase">Ad Units</div>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, stats=stats, is_admin_route=True, active_page='dashboard')

@app.route('/admin/apps', methods=['GET', 'POST'])
def admin_apps():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        apps_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo'), "category": request.form.get('category'), "release_date": request.form.get('release_date'), "version": request.form.get('version'), "info": request.form.get('info'), "download_link": request.form.get('download_link'), "featured": request.form.get('featured')})
        flash("App Saved!")
    apps = list(apps_col.find().sort('_id', -1))
    content = """
    <div class="grid lg:grid-cols-3 gap-10">
        <form method="POST" class="bg-slate-50 p-8 rounded-[2rem] space-y-4">
            <input name="name" placeholder="App Name" class="w-full p-4 rounded-xl border" required>
            <input name="logo" placeholder="Logo URL" class="w-full p-4 rounded-xl border" required>
            <select name="category" class="w-full p-4 rounded-xl border"><option>Mobile</option><option>PC</option></select>
            <div class="flex gap-2"><input type="date" name="release_date" class="w-1/2 p-4 rounded-xl border"><input name="version" placeholder="v1.0" class="w-1/2 p-4 rounded-xl border"></div>
            <textarea name="info" placeholder="Description" class="w-full p-4 rounded-xl border h-24"></textarea>
            <input name="download_link" placeholder="Main URL" class="w-full p-4 rounded-xl border" required>
            <label class="flex items-center gap-2"><input type="checkbox" name="featured"> Slider App</label>
            <button class="w-full bg-indigo-600 text-white py-4 rounded-2xl font-black">PUBLISH</button>
        </form>
        <div class="lg:col-span-2 bg-white rounded-2xl border overflow-hidden">
            <table class="w-full text-left">
                {% for a in apps %}<tr class="border-b"><td class="p-4">{{a.name}}</td><td class="p-4 text-right"><a href="/del/app/{{a._id}}" class="text-red-500">Delete</a></td></tr>{% endfor %}
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, apps=apps, is_admin_route=True, active_page='apps')

@app.route('/admin/ads', methods=['GET', 'POST'])
def admin_ads():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        ads_col.insert_one({"name": request.form.get('name'), "code": request.form.get('code')})
        flash("Ad Saved!")
    ads = list(ads_col.find())
    content = """
    <form method="POST" class="bg-slate-50 p-10 rounded-[2rem] space-y-4 mb-10">
        <input name="name" placeholder="Ad Spot" class="w-full p-4 rounded-xl border">
        <textarea name="code" placeholder="Ad Code" class="w-full p-4 rounded-xl border h-40 font-mono text-xs"></textarea>
        <button class="bg-indigo-600 text-white px-10 py-4 rounded-2xl font-black">SAVE AD</button>
    </form>
    {% for ad in ads %}<div class="flex justify-between p-4 border-b"><span>{{ad.name}}</span><a href="/del/ad/{{ad._id}}" class="text-red-500">Remove</a></div>{% endfor %}
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, ads=ads, is_admin_route=True, active_page='ads')

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == "site_info":
            settings_col.update_one({"type": "site_info"}, {"$set": {"name": request.form.get('site_name'), "title": request.form.get('site_title')}}, upsert=True)
            flash("Site Info Updated!")
        else:
            settings_col.update_one({"type": "shortener"}, {"$set": {"url": request.form.get('url'), "api": request.form.get('api')}}, upsert=True)
            flash("API Updated!")
        return redirect('/admin/settings')
    
    cfg = settings_col.find_one({"type": "shortener"}) or {}
    content = """
    <div class="grid md:grid-cols-2 gap-10">
        <div class="bg-slate-50 p-10 rounded-[2rem] space-y-4">
            <h2 class="text-xl font-bold">Site Branding</h2>
            <form method="POST">
                <input type="hidden" name="form_type" value="site_info">
                <input name="site_name" value="{{site.name}}" placeholder="Site Name" class="w-full p-4 rounded-xl border mb-4">
                <input name="site_title" value="{{site.title}}" placeholder="Site Meta Title" class="w-full p-4 rounded-xl border mb-4">
                <button class="w-full bg-indigo-600 text-white py-4 rounded-2xl font-black">UPDATE NAME</button>
            </form>
        </div>
        <div class="bg-slate-50 p-10 rounded-[2rem] space-y-4">
            <h2 class="text-xl font-bold">Shortener API</h2>
            <form method="POST">
                <input type="hidden" name="form_type" value="shortener">
                <input name="url" value="{{cfg.url}}" placeholder="Domain" class="w-full p-4 rounded-xl border mb-4">
                <input name="api" value="{{cfg.api}}" placeholder="API Key" class="w-full p-4 rounded-xl border mb-4">
                <button class="w-full bg-slate-900 text-white py-4 rounded-2xl font-black">UPDATE API</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, cfg=cfg, is_admin_route=True, active_page='settings')

@app.route('/del/<type>/<id>')
def delete(type, id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    if type == 'app': apps_col.delete_one({"_id": ObjectId(id)})
    if type == 'ad': ads_col.delete_one({"_id": ObjectId(id)})
    return redirect(request.referrer)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

handler = app
if __name__ == '__main__':
    app.run(debug=True)
