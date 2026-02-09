import os
import requests
import certifi
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- CONFIGURATION & SECURITY ---
app.secret_key = os.environ.get("SESSION_SECRET", "super_high_secure_long_secret_key_ultimate_v2024")
RECOVERY_KEY = os.environ.get("RECOVERY_KEY", "admin@2024")

# --- MONGODB CONNECTION ---
try:
    ca = certifi.where()
    MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(MONGO_URI, tlsCAFile=ca, serverSelectionTimeoutMS=5000)
    db = client['app_hub_production_ultimate_system']
    
    # Collections
    apps_col = db['apps']
    users_col = db['users']
    ads_col = db['ads']
    settings_col = db['settings']
    categories_col = db['categories']
    media_col = db['media']
    
except Exception as e:
    print(f"DATABASE CONNECTION ERROR: {e}")

# --- HELPERS: DYNAMIC DATA ---
def get_site_info():
    info = settings_col.find_one({"type": "site_info"})
    if not info:
        return {
            "name": "APPHUB PRO", 
            "title": "Ultimate Premium App Store", 
            "logo": "https://cdn-icons-png.flaticon.com/512/2589/2589127.png",
            "desc": "The ultimate platform for high-performance applications and games. Discover and download with maximum speed.",
            "copyright": "2024 APPHUB PRO Ultimate Edition v10.0",
            "fb": "#", "ig": "#", "tw": "#"
        }
    return info

def get_shortener():
    return settings_col.find_one({"type": "shortener"}) or {"url": "", "api": ""}

def get_legal_content(page_type):
    content = settings_col.find_one({"type": "legal_page", "page": page_type})
    if not content: return f"The {page_type} content is not set yet. Please update from admin panel."
    return content['text']

# --- UI ASSETS (CSS & SCRIPTS) ---
BASE_CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css" />
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; color: #0f172a; overflow-x: hidden; }
    .glass-nav { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(12px); border-bottom: 1px solid #e2e8f0; }
    .pro-card { background: white; border: 1px solid #f1f5f9; border-radius: 2rem; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
    .pro-card:hover { transform: translateY(-8px); box-shadow: 0 25px 50px -12px rgba(99, 102, 241, 0.15); border-color: #6366f1; }
    .sidebar-link { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-radius: 18px; font-weight: 600; color: #94a3b8; transition: 0.3s; }
    .sidebar-active { background: #6366f1 !important; color: white !important; box-shadow: 0 10px 20px -5px rgba(99, 102, 241, 0.4); }
    .btn-main { background: #6366f1; color: white; padding: 12px 28px; border-radius: 18px; font-weight: 800; display: inline-flex; align-items: center; gap: 8px; transition: 0.3s; }
    .btn-main:hover { background: #4f46e5; transform: scale(1.05); }
    input, textarea, select { border: 2px solid #f1f5f9; border-radius: 18px; padding: 14px 18px; outline: none; background: #fff; width: 100%; transition: 0.3s; }
    input:focus { border-color: #6366f1; box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1); }
    .swiper { width: 100%; border-radius: 2.5rem; height: 400px; margin-bottom: 3rem; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.2); }
    .line-clamp-1 { display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
"""

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site.name }} - {{ site.title }}</title>
    """ + BASE_CSS + """
</head>
<body>
    {% if not is_admin_route %}
    <nav class="glass-nav sticky top-0 z-50 py-4">
        <div class="container mx-auto px-6 flex flex-col lg:flex-row items-center justify-between gap-4">
            <a href="/" class="flex items-center gap-3">
                <img src="{{ site.logo }}" class="w-10 h-10 rounded-xl shadow-lg">
                <span class="text-2xl font-black text-slate-900 tracking-tighter uppercase italic">{{ site.name }}</span>
            </a>
            <form action="/" method="GET" class="flex bg-slate-100 rounded-2xl px-5 py-2 w-full max-w-xl border border-slate-200">
                <input type="text" name="q" placeholder="Search premium apps, games, tools..." class="bg-transparent border-none p-0 w-full text-sm font-semibold outline-none">
                <button type="submit"><i class="fas fa-search text-indigo-600 text-lg"></i></button>
            </form>
        </div>
    </nav>
    {% endif %}

    <div class="{% if is_admin_route %}flex flex-col lg:flex-row min-h-screen{% else %}container mx-auto px-6 py-10{% endif %}">
        {% if is_admin_route %}
        <!-- ADMIN SIDEBAR -->
        <div class="w-full lg:w-80 bg-slate-950 text-slate-400 p-8 flex flex-col lg:h-screen lg:sticky lg:top-0">
            <div class="flex items-center gap-4 mb-10 border-b border-slate-900 pb-8">
                <img src="{{ site.logo }}" class="w-10 h-10 rounded-xl">
                <div>
                    <h2 class="text-white font-black uppercase text-xl italic leading-none">{{ site.name }}</h2>
                    <span class="text-[10px] font-bold text-indigo-400 tracking-[0.2em]">ADMIN PANEL</span>
                </div>
            </div>
            <div class="space-y-2 flex-1 overflow-y-auto pr-2">
                <a href="/admin/dashboard" class="sidebar-link {% if active == 'dashboard' %}sidebar-active{% endif %}"><i class="fas fa-chart-line"></i> Dashboard</a>
                <a href="/admin/categories" class="sidebar-link {% if active == 'categories' %}sidebar-active{% endif %}"><i class="fas fa-tags"></i> Categories</a>
                <a href="/admin/apps" class="sidebar-link {% if active == 'apps' %}sidebar-active{% endif %}"><i class="fas fa-rocket"></i> Apps Manager</a>
                <a href="/admin/media" class="sidebar-link {% if active == 'media' %}sidebar-active{% endif %}"><i class="fas fa-photo-video"></i> Media Center</a>
                <a href="/admin/ads" class="sidebar-link {% if active == 'ads' %}sidebar-active{% endif %}"><i class="fas fa-ad"></i> Ads Manager</a>
                <a href="/admin/layout" class="sidebar-link {% if active == 'layout' %}sidebar-active{% endif %}"><i class="fas fa-window-restore"></i> Site Layout</a>
                <a href="/admin/settings" class="sidebar-link {% if active == 'settings' %}sidebar-active{% endif %}"><i class="fas fa-user-shield"></i> Settings</a>
            </div>
            <div class="mt-8 pt-6 border-t border-slate-900">
                <a href="/" target="_blank" class="text-emerald-400 font-black block mb-5 flex items-center gap-3"><i class="fas fa-external-link-alt"></i> VIEW SITE</a>
                <a href="/logout" class="text-red-500 font-black flex items-center gap-3"><i class="fas fa-power-off"></i> LOGOUT SYSTEM</a>
            </div>
        </div>
        <!-- ADMIN CONTENT AREA -->
        <div class="flex-1 p-6 lg:p-12 bg-white">
            {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}
            <div class="bg-indigo-600 text-white p-5 rounded-3xl mb-10 shadow-xl flex justify-between items-center animate-bounce">
                <span class="font-bold"><i class="fas fa-check-circle mr-2"></i> {{ m }}</span>
                <button onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
            </div>
            {% endfor %}{% endif %}{% endwith %}
            {% block admin_content %}{% endblock %}
        </div>
        {% else %}
        <!-- USER CONTENT AREA -->
        <div class="min-h-[80vh]">
            {% block content %}{% endblock %}
        </div>
        {% endif %}
    </div>

    {% if not is_admin_route %}
    <footer class="bg-slate-950 text-slate-500 py-20 mt-20">
        <div class="container mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-16">
            <div>
                <h3 class="text-white text-3xl font-black mb-6 uppercase italic tracking-tighter">{{ site.name }}</h3>
                <p class="text-sm leading-relaxed mb-8">{{ site.desc }}</p>
                <div class="flex gap-4">
                    <a href="{{ site.fb }}" class="w-12 h-12 bg-slate-900 rounded-2xl flex items-center justify-center hover:bg-indigo-600 transition hover:-translate-y-2"><i class="fab fa-facebook-f text-white text-xl"></i></a>
                    <a href="{{ site.ig }}" class="w-12 h-12 bg-slate-900 rounded-2xl flex items-center justify-center hover:bg-indigo-600 transition hover:-translate-y-2"><i class="fab fa-instagram text-white text-xl"></i></a>
                </div>
            </div>
            <div>
                <h4 class="text-white font-bold mb-8 uppercase text-sm tracking-widest">Legal & Policy</h4>
                <div class="flex flex-col gap-4 font-bold text-sm">
                    <a href="/p/privacy" class="hover:text-indigo-400 transition">Privacy Policy</a>
                    <a href="/p/terms" class="hover:text-indigo-400 transition">Terms of Service</a>
                    <a href="/p/dmca" class="hover:text-indigo-400 transition">DMCA Notice</a>
                </div>
            </div>
            <div>
                <h4 class="text-white font-bold mb-8 uppercase text-sm tracking-widest">Support</h4>
                <p class="text-sm mb-6">Need help or have a DMCA request? Contact our team via social media or email.</p>
                <div class="bg-slate-900 p-6 rounded-3xl border border-slate-800">
                    <span class="text-[10px] block mb-1 uppercase font-black text-indigo-400">System Status</span>
                    <span class="text-white font-black">All Servers Operational</span>
                </div>
            </div>
        </div>
        <div class="container mx-auto px-6 border-t border-slate-900 mt-20 pt-10 text-center text-[11px] font-black uppercase tracking-[0.3em]">
            &copy; {{ site.copyright }}
        </div>
    </footer>
    {% endif %}

    <script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
    <script>
        const swiper = new Swiper('.swiper', {
            loop: true, autoplay: { delay: 4000 },
            pagination: { el: '.swiper-pagination', clickable: true },
            navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
        });
    </script>
</body>
</html>
"""

# --- USER ROUTES ---

@app.route('/')
def home():
    site = get_site_info()
    q = request.args.get('q', '')
    
    all_media = list(media_col.find().sort('_id', -1))
    all_categories = list(categories_col.find().sort('name', 1))
    
    if q:
        apps = list(apps_col.find({"name": {"$regex": q, "$options": "i"}}).sort('_id', -1))
        home_data = [{"cat_name": f"Search Results: {q}", "apps": apps}]
        all_media = []
    else:
        home_data = []
        for cat in all_categories:
            limit = int(cat.get('limit', 6))
            cat_apps = list(apps_col.find({"category": cat['name']}).sort('_id', -1).limit(limit))
            if cat_apps:
                home_data.append({"cat_name": cat['name'], "apps": cat_apps})

    content = """
    {% if all_media %}
    <div class="swiper">
        <div class="swiper-wrapper">
            {% for m in all_media %}
            <div class="swiper-slide relative group">
                <img src="{{ m.url }}" class="w-full h-full object-cover">
                <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent flex flex-col justify-end p-12">
                    <h2 class="text-white text-4xl md:text-6xl font-black uppercase italic tracking-tighter mb-4">{{ m.title }}</h2>
                    <a href="{{ m.link }}" target="_blank" class="bg-indigo-600 text-white px-10 py-4 rounded-2xl font-black inline-block w-fit shadow-2xl">EXPLORE NOW</a>
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="swiper-pagination"></div>
    </div>
    {% endif %}

    {% for section in home_data %}
    <div class="mb-20">
        <div class="flex justify-between items-end mb-10 border-b-4 border-slate-50 pb-5">
            <h2 class="text-3xl font-black uppercase italic tracking-tighter text-slate-900">{{ section.cat_name }}</h2>
            <a href="/category/{{ section.cat_name }}" class="text-indigo-600 font-black text-xs uppercase tracking-widest bg-indigo-50 px-6 py-2 rounded-full">View All</a>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-8">
            {% for app in section.apps %}
            <a href="/app/{{app._id}}" class="pro-card p-6 flex flex-col items-center text-center group">
                <div class="relative mb-6">
                    <img src="{{app.logo}}" class="w-24 h-24 rounded-[2rem] shadow-2xl group-hover:rotate-6 transition duration-500 border-4 border-white">
                    <span class="absolute -top-3 -right-3 bg-indigo-600 text-white text-[9px] font-black px-3 py-1.5 rounded-full shadow-lg">PREMIUM</span>
                </div>
                <h3 class="font-black text-slate-800 text-base mb-4 line-clamp-1 uppercase italic">{{app.name}}</h3>
                <div class="w-full bg-slate-950 text-white py-3.5 rounded-2xl text-[10px] font-black uppercase tracking-widest group-hover:bg-indigo-600 transition">DOWNLOAD</div>
            </a>
            {% endfor %}
        </div>
    </div>
    {% endfor %}
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', content), site=site, home_data=home_data, all_media=all_media, is_admin_route=False)

@app.route('/app/<id>')
def details(id):
    site = get_site_info()
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    if not app_data: return redirect('/')
    content = """
    <div class="bg-white rounded-[4rem] p-10 lg:p-20 shadow-2xl flex flex-col lg:flex-row gap-16 items-center lg:items-start border border-slate-100">
        <img src="{{app.logo}}" class="w-64 h-64 rounded-[4rem] shadow-2xl border-[12px] border-slate-50">
        <div class="flex-1 text-center lg:text-left">
            <h1 class="text-5xl lg:text-7xl font-black mb-8 uppercase italic tracking-tighter text-slate-900">{{app.name}}</h1>
            <p class="text-slate-500 text-2xl mb-12 font-medium leading-relaxed">"{{app.info}}"</p>
            <div class="flex flex-wrap justify-center lg:justify-start gap-5 mb-12">
                <div class="bg-indigo-600 text-white px-10 py-3 rounded-full font-black text-xs uppercase shadow-xl">{{app.category}}</div>
                <div class="bg-emerald-50 text-emerald-600 border border-emerald-100 px-10 py-3 rounded-full font-black text-xs uppercase italic">Ver: {{app.version}}</div>
            </div>
            <a href="/get/{{app._id}}" class="bg-slate-950 text-white px-16 py-7 rounded-[2.5rem] font-black text-2xl inline-block shadow-2xl hover:bg-indigo-600 transition transform hover:scale-105 uppercase tracking-tighter italic">Get Download Link</a>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', content), site=site, app=app_data, is_admin_route=False)

@app.route('/p/<slug>')
def legal_pages(slug):
    site = get_site_info()
    if slug not in ["privacy", "terms", "dmca"]: return redirect('/')
    content = get_legal_content(slug)
    page_html = f"""
    <div class="max-w-4xl mx-auto bg-white p-12 lg:p-24 rounded-[4rem] shadow-2xl border">
        <h1 class="text-5xl font-black mb-10 uppercase italic tracking-tighter text-indigo-600 border-b-4 border-slate-50 pb-6">{slug} Policy</h1>
        <div class="text-slate-600 text-xl leading-loose whitespace-pre-line font-medium">{content}</div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', page_html), site=site, is_admin_route=False)

# --- ADMIN: DASHBOARD ---

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    stats = {
        "apps": apps_col.count_documents({}),
        "cats": categories_col.count_documents({}),
        "media": media_col.count_documents({}),
        "ads": ads_col.count_documents({})
    }
    content = """
    <h1 class="text-5xl font-black mb-12 uppercase italic tracking-tighter">System Analytics</h1>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        <div class="bg-indigo-600 p-10 rounded-[3rem] text-white shadow-2xl">
            <div class="text-7xl font-black mb-2">{{ stats.apps }}</div>
            <p class="font-bold uppercase opacity-60 text-xs tracking-[0.2em]">Total Applications</p>
        </div>
        <div class="bg-slate-900 p-10 rounded-[3rem] text-white shadow-2xl border-4 border-slate-800">
            <div class="text-7xl font-black mb-2">{{ stats.cats }}</div>
            <p class="font-bold uppercase opacity-60 text-xs tracking-[0.2em]">Active Categories</p>
        </div>
        <div class="bg-emerald-500 p-10 rounded-[3rem] text-white shadow-2xl">
            <div class="text-7xl font-black mb-2">{{ stats.media }}</div>
            <p class="font-bold uppercase opacity-60 text-xs tracking-[0.2em]">Media Banners</p>
        </div>
        <div class="bg-orange-500 p-10 rounded-[3rem] text-white shadow-2xl">
            <div class="text-7xl font-black mb-2">{{ stats.ads }}</div>
            <p class="font-bold uppercase opacity-60 text-xs tracking-[0.2em]">Integrated Ads</p>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, stats=stats, is_admin_route=True, active="dashboard")

# --- ADMIN: CATEGORIES (UNLIMITED) ---

@app.route('/admin/categories', methods=['GET', 'POST'])
def admin_categories():
    if not session.get('logged_in'): return redirect('/admin-gate')
    if request.method == 'POST':
        name = request.form.get('name')
        limit = request.form.get('limit', 6)
        categories_col.update_one({"name": name}, {"$set": {"name": name, "limit": int(limit)}}, upsert=True)
        flash(f"Category '{name}' has been updated.")
        return redirect('/admin/categories')
    
    cats = list(categories_col.find().sort('name', 1))
    site = get_site_info()
    content = """
    <h1 class="text-5xl font-black mb-12 uppercase italic tracking-tighter">Category Manager</h1>
    <div class="grid lg:grid-cols-12 gap-12">
        <form method="POST" class="lg:col-span-4 bg-slate-50 p-10 rounded-[3rem] border-2 border-dashed border-slate-200 h-fit space-y-5">
            <h2 class="font-black text-indigo-600 uppercase italic">Add / Edit Category</h2>
            <input name="name" placeholder="Category Name (e.g. Games)" required>
            <input type="number" name="limit" placeholder="Home Post Limit (e.g. 12)" required>
            <button class="btn-main w-full py-5 text-lg">SAVE CATEGORY</button>
        </form>
        <div class="lg:col-span-8 bg-white border-2 rounded-[3rem] overflow-hidden shadow-xl">
            <table class="w-full text-left">
                <thead class="bg-slate-950 text-white text-[11px] uppercase font-bold tracking-widest">
                    <tr><th class="p-6">Category Name</th><th class="p-6 text-center">Post Limit</th><th class="p-6 text-right">Actions</th></tr>
                </thead>
                <tbody class="text-sm font-bold">
                    {% for c in cats %}
                    <tr class="border-t hover:bg-slate-50 transition">
                        <td class="p-6 text-slate-800">{{ c.name }}</td>
                        <td class="p-6 text-center font-black text-indigo-600">{{ c.limit }}</td>
                        <td class="p-6 text-right space-x-3">
                            <a href="/admin/del-cat/{{ c._id }}" class="text-red-500 hover:underline" onclick="return confirm('Confirm deletion?')">DELETE</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, cats=cats, is_admin_route=True, active="categories")

# --- ADMIN: APPS MANAGER ---

@app.route('/admin/apps', methods=['GET', 'POST'])
def admin_apps():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    cats = list(categories_col.find().sort('name', 1))
    
    if request.method == 'POST':
        apps_col.insert_one({
            "name": request.form.get('name'), "logo": request.form.get('logo'),
            "category": request.form.get('category'), "version": request.form.get('version'),
            "info": request.form.get('info'), "download_link": request.form.get('download_link'),
            "created_at": datetime.now()
        })
        flash("Application published successfully.")
        return redirect('/admin/apps')
    
    all_apps = list(apps_col.find().sort('_id', -1))
    content = """
    <h1 class="text-5xl font-black mb-12 uppercase italic tracking-tighter">Apps Manager</h1>
    <div class="grid lg:grid-cols-12 gap-12">
        <form method="POST" class="lg:col-span-4 bg-slate-50 p-10 rounded-[3rem] border-2 border-slate-200 h-fit space-y-4">
            <h2 class="font-black text-indigo-600 uppercase italic">Publish New App</h2>
            <input name="name" placeholder="Application Title" required>
            <input name="logo" placeholder="Logo Link (URL)" required>
            <select name="category" required>
                <option value="" disabled selected>Select Category</option>
                {% for c in cats %}<option value="{{c.name}}">{{c.name}}</option>{% endfor %}
            </select>
            <input name="version" placeholder="Version (e.g. 2.1.0)">
            <textarea name="info" placeholder="Short Meta Description" class="h-32" required></textarea>
            <input name="download_link" placeholder="Direct Download URL" required>
            <button class="btn-main w-full py-5 text-lg">PUBLISH APP</button>
        </form>
        <div class="lg:col-span-8 bg-white border-2 rounded-[3rem] overflow-hidden shadow-xl overflow-x-auto">
            <table class="w-full text-left">
                <thead class="bg-slate-950 text-white text-[11px] uppercase font-bold tracking-widest">
                    <tr><th class="p-6">Asset Details</th><th class="p-6">Category</th><th class="p-6 text-right">Actions</th></tr>
                </thead>
                <tbody class="text-sm">
                    {% for a in all_apps %}
                    <tr class="border-t hover:bg-slate-50">
                        <td class="p-6 flex items-center gap-4">
                            <img src="{{a.logo}}" class="w-12 h-12 rounded-xl border-2 border-white shadow-md">
                            <span class="font-bold text-slate-800">{{a.name}}</span>
                        </td>
                        <td class="p-6 uppercase font-black text-slate-400 text-[10px]">{{a.category}}</td>
                        <td class="p-6 text-right space-x-4">
                            <a href="/admin/edit-app/{{a._id}}" class="text-indigo-600 font-bold">EDIT</a>
                            <a href="/del/app/{{a._id}}" class="text-red-500 font-bold" onclick="return confirm('Delete this app?')">DEL</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, all_apps=all_apps, cats=cats, is_admin_route=True, active="apps")

@app.route('/admin/edit-app/<id>', methods=['GET', 'POST'])
def edit_app(id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    site = get_site_info()
    cats = list(categories_col.find().sort('name', 1))
    
    if request.method == 'POST':
        apps_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'), "logo": request.form.get('logo'),
            "category": request.form.get('category'), "version": request.form.get('version'),
            "info": request.form.get('info'), "download_link": request.form.get('download_link')
        }})
        flash("Application data updated.")
        return redirect('/admin/apps')
        
    content = """
    <h1 class="text-4xl font-black mb-10 uppercase italic">Edit: {{app_data.name}}</h1>
    <form method="POST" class="max-w-3xl bg-white p-10 rounded-[3rem] border-2 shadow-2xl space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <input name="name" value="{{app_data.name}}" required>
            <input name="logo" value="{{app_data.logo}}" required>
            <select name="category" required>
                {% for c in cats %}<option value="{{c.name}}" {% if c.name == app_data.category %}selected{% endif %}>{{c.name}}</option>{% endfor %}
            </select>
            <input name="version" value="{{app_data.version}}">
        </div>
        <textarea name="info" class="h-40" required>{{app_data.info}}</textarea>
        <input name="download_link" value="{{app_data.download_link}}" required>
        <div class="flex gap-4">
            <button class="btn-main flex-1 py-5">UPDATE DATA</button>
            <a href="/admin/apps" class="bg-slate-100 text-slate-500 px-10 py-5 rounded-[18px] font-bold">CANCEL</a>
        </div>
    </form>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, app_data=app_data, cats=cats, is_admin_route=True, active="apps")

# --- ADMIN: MEDIA CENTER (UNLIMITED) ---

@app.route('/admin/media', methods=['GET', 'POST'])
def admin_media():
    if not session.get('logged_in'): return redirect('/admin-gate')
    if request.method == 'POST':
        media_col.insert_one({
            "title": request.form.get('title'), "url": request.form.get('url'),
            "link": request.form.get('link'), "created_at": datetime.now()
        })
        flash("Media banner has been added.")
        return redirect('/admin/media')
    
    media_list = list(media_col.find().sort('_id', -1))
    site = get_site_info()
    content = """
    <h1 class="text-5xl font-black mb-12 uppercase italic tracking-tighter">Media Center</h1>
    <div class="grid lg:grid-cols-12 gap-12">
        <form method="POST" class="lg:col-span-4 bg-slate-50 p-10 rounded-[3rem] border-2 border-dashed border-slate-200 h-fit space-y-5">
            <h2 class="font-black text-emerald-600 uppercase italic">New Slider Banner</h2>
            <input name="title" placeholder="Banner Headline" required>
            <input name="url" placeholder="Banner Image URL" required>
            <input name="link" placeholder="Redirect Link (Button Link)" required>
            <button class="bg-emerald-600 text-white w-full py-5 rounded-2xl font-bold shadow-lg">PUBLISH BANNER</button>
        </form>
        <div class="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-8">
            {% for m in media_list %}
            <div class="bg-white border-2 rounded-[2.5rem] overflow-hidden shadow-xl flex flex-col group">
                <div class="relative overflow-hidden h-48">
                    <img src="{{ m.url }}" class="w-full h-full object-cover group-hover:scale-110 transition duration-700">
                </div>
                <div class="p-6">
                    <h3 class="font-black uppercase text-sm truncate mb-1 italic">{{ m.title }}</h3>
                    <p class="text-[10px] text-slate-400 truncate mb-5 font-bold uppercase tracking-widest">{{ m.link }}</p>
                    <a href="/admin/del-media/{{ m._id }}" class="text-red-500 font-black text-xs hover:underline" onclick="return confirm('Remove media?')">REMOVE FROM SLIDER</a>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, media_list=media_list, is_admin_route=True, active="media")

# --- ADMIN: ADS & LAYOUT ---

@app.route('/admin/ads', methods=['GET', 'POST'])
def admin_ads():
    if not session.get('logged_in'): return redirect('/admin-gate')
    if request.method == 'POST':
        ads_col.insert_one({"name": request.form.get('name'), "code": request.form.get('code'), "created_at": datetime.now()})
        flash("Advertisement integrated successfully.")
        return redirect('/admin/ads')
    ads_list = list(ads_col.find())
    site = get_site_info()
    content = """
    <h1 class="text-5xl font-black mb-12 uppercase italic tracking-tighter">Ads Placement</h1>
    <div class="grid lg:grid-cols-2 gap-12">
        <form method="POST" class="bg-slate-50 p-10 rounded-[3rem] border-2 border-slate-200 space-y-5">
            <input name="name" placeholder="Ad Spot Name (e.g. Header Banner)" required>
            <textarea name="code" placeholder="Paste Ad HTML/JS Code Here" class="h-64 font-mono text-sm" required></textarea>
            <button class="btn-main w-full py-5">DEPLOY AD CODE</button>
        </form>
        <div class="space-y-6">
            {% for ad in ads_list %}
            <div class="bg-white border-2 p-8 rounded-[2.5rem] flex justify-between items-center shadow-lg">
                <span class="font-black uppercase text-sm italic tracking-widest text-slate-700">{{ ad.name }}</span>
                <a href="/del/ad/{{ ad._id }}" class="text-red-500 font-black text-xs">REMOVE CODE</a>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, ads_list=ads_list, is_admin_route=True, active="ads")

@app.route('/admin/layout', methods=['GET', 'POST'])
def admin_layout():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        l_type = request.form.get('l_type')
        if l_type == 'branding':
            settings_col.update_one({"type": "site_info"}, {"$set": {
                "name": request.form.get('name'), "logo": request.form.get('logo'), 
                "title": request.form.get('title'), "desc": request.form.get('desc'), 
                "copyright": request.form.get('copyright'), "fb": request.form.get('fb'), "ig": request.form.get('ig')
            }}, upsert=True)
        elif l_type == 'legal':
            settings_col.update_one({"type": "legal_page", "page": request.form.get('page')}, {"$set": {"text": request.form.get('text')}}, upsert=True)
        flash("Layout and branding settings saved.")
        return redirect('/admin/layout')
    
    content = """
    <h1 class="text-5xl font-black mb-12 uppercase italic tracking-tighter">Site Customization</h1>
    <div class="grid lg:grid-cols-2 gap-12">
        <!-- BRANDING -->
        <form method="POST" class="bg-white p-10 rounded-[3rem] border-2 shadow-xl space-y-5 h-fit">
            <input type="hidden" name="l_type" value="branding">
            <h2 class="font-black uppercase italic text-indigo-600 border-b pb-4">Branding & Socials</h2>
            <div class="grid grid-cols-2 gap-4">
                <input name="name" value="{{site.name}}" placeholder="Site Name">
                <input name="logo" value="{{site.logo}}" placeholder="Logo URL">
            </div>
            <input name="title" value="{{site.title}}" placeholder="Browser Tab Title">
            <textarea name="desc" class="h-24">{{site.desc}}</textarea>
            <input name="copyright" value="{{site.copyright}}" placeholder="Copyright Text">
            <div class="grid grid-cols-2 gap-4">
                <input name="fb" value="{{site.fb}}" placeholder="Facebook Link">
                <input name="ig" value="{{site.ig}}" placeholder="Instagram Link">
            </div>
            <button class="btn-main w-full py-5">SAVE ALL BRANDING</button>
        </form>
        <!-- LEGAL PAGES -->
        <form method="POST" class="bg-slate-50 p-10 rounded-[3rem] border-2 border-dashed border-slate-200 space-y-5 h-fit">
            <input type="hidden" name="l_type" value="legal">
            <h2 class="font-black uppercase italic text-emerald-600 border-b pb-4">Legal Page Editor</h2>
            <select name="page" required>
                <option value="privacy">Privacy Policy</option>
                <option value="terms">Terms of Service</option>
                <option value="dmca">DMCA Takedown</option>
            </select>
            <textarea name="text" placeholder="Paste policy text here..." class="h-80 font-medium"></textarea>
            <button class="btn-main w-full py-5 bg-emerald-600">UPDATE LEGAL CONTENT</button>
        </form>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, is_admin_route=True, active="layout")

# --- ADMIN: SETTINGS (API & AUTH) ---

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('logged_in'): return redirect('/admin-gate')
    if request.method == 'POST':
        settings_col.update_one({"type": "shortener"}, {"$set": {"url": request.form.get('url'), "api": request.form.get('api')}}, upsert=True)
        flash("API Configuration Saved.")
        return redirect('/admin/settings')
    
    cfg = get_shortener()
    site = get_site_info()
    content = """
    <h1 class="text-5xl font-black mb-12 uppercase italic tracking-tighter">System API Settings</h1>
    <div class="bg-slate-950 p-16 rounded-[4rem] shadow-2xl border-4 border-slate-900">
        <h2 class="text-emerald-400 font-black uppercase mb-8 italic tracking-widest text-sm">Universal Link Shortener (API)</h2>
        <form method="POST" class="space-y-8">
            <div class="space-y-2">
                <label class="text-white text-[10px] uppercase font-black ml-4 tracking-widest opacity-50">Shortener Domain</label>
                <input name="url" value="{{cfg.url}}" placeholder="e.g. gplinks.in" class="bg-slate-900 border-none text-white font-bold py-6 text-xl">
            </div>
            <div class="space-y-2">
                <label class="text-white text-[10px] uppercase font-black ml-4 tracking-widest opacity-50">Secret API Token</label>
                <input name="api" value="{{cfg.api}}" placeholder="Paste API Key Here" class="bg-slate-900 border-none text-white font-bold py-6 text-xl">
            </div>
            <button class="bg-emerald-500 text-black w-full py-6 rounded-[2rem] font-black text-2xl hover:bg-white transition duration-500">UPDATE GLOBAL API</button>
        </form>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, cfg=cfg, is_admin_route=True, active="settings")

# --- AUTH SYSTEM (LOGIN/FORGOT) ---

@app.route('/admin-gate', methods=['GET', 'POST'])
def login():
    site = get_site_info()
    if request.method == 'POST':
        pw = request.form.get('password')
        admin = users_col.find_one({"username": "admin"})
        if not admin:
            users_col.insert_one({"username": "admin", "password": generate_password_hash(pw)})
            session['logged_in'] = True; return redirect('/admin/dashboard')
        if check_password_hash(admin['password'], pw):
            session['logged_in'] = True; return redirect('/admin/dashboard')
        flash("Invalid Credentials.")
    return render_template_string(f"""
    <!DOCTYPE html><html><head>{BASE_CSS}</head>
    <body class="bg-slate-100 flex items-center justify-center min-h-screen p-6">
        <form method="POST" class="bg-white p-12 rounded-[4rem] shadow-2xl w-full max-w-md text-center border-4 border-white">
            <img src="{site['logo']}" class="w-24 h-24 rounded-[2rem] mx-auto mb-10 shadow-xl border-4 border-slate-50">
            <h2 class="text-4xl font-black mb-10 uppercase italic tracking-tighter">System Access</h2>
            <input type="password" name="password" class="text-center font-black text-3xl mb-8 p-6" placeholder="••••••••" required>
            <button class="bg-slate-950 text-white w-full py-6 rounded-3xl font-black text-xl shadow-2xl hover:bg-indigo-600 transition duration-500">UNLOCK PANEL</button>
            <a href="/forgot" class="block mt-8 text-xs font-bold text-slate-400 uppercase tracking-widest">Forgot Password?</a>
        </form>
    </body></html>
    """)

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        if request.form.get('key') == RECOVERY_KEY:
            users_col.update_one({"username": "admin"}, {"$set": {"password": generate_password_hash(request.form.get('pw'))}}, upsert=True)
            flash("System password has been reset.")
            return redirect('/admin-gate')
    return render_template_string(f"<!DOCTYPE html><html><head>{BASE_CSS}</head><body class='bg-slate-100 flex items-center justify-center min-h-screen'><form method='POST' class='bg-white p-12 rounded-[3.5rem] shadow-xl w-full max-w-md space-y-6'><h2 class='font-black uppercase italic text-center'>Emergency Reset</h2><input name='key' placeholder='Recovery Key' required><input type='password' name='pw' placeholder='New Password' required><button class='btn-main w-full py-5 text-xl'>RESET NOW</button></form></body></html>")

# --- SYSTEM CORE (DOWNLOAD & DELETE) ---

@app.route('/get/<id>')
def download_process(id):
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    if not app_data: return redirect('/')
    cfg = get_shortener()
    target = app_data['download_link']
    if cfg.get('url') and cfg.get('api'):
        try:
            api_endpoint = f"https://{cfg['url']}/api?api={cfg['api']}&url={target}"
            res = requests.get(api_endpoint, timeout=12).json()
            short_url = res.get('shortenedUrl') or res.get('shortedUrl')
            if short_url: return redirect(short_url)
        except: pass
    return redirect(target)

@app.route('/admin/del-cat/<id>')
def delete_cat(id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    categories_col.delete_one({"_id": ObjectId(id)})
    flash("Category deleted.")
    return redirect('/admin/categories')

@app.route('/admin/del-media/<id>')
def delete_media(id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    media_col.delete_one({"_id": ObjectId(id)})
    flash("Media banner removed.")
    return redirect('/admin/media')

@app.route('/del/<type>/<id>')
def delete_entry(type, id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    if type == 'app': apps_col.delete_one({"_id": ObjectId(id)})
    if type == 'ad': ads_col.delete_one({"_id": ObjectId(id)})
    flash("Entry has been permanently removed.")
    return redirect(request.referrer)

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

# --- RUN APPLICATION ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
