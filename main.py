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
app.secret_key = os.environ.get("SESSION_SECRET", "super_high_secure_long_secret_key_v100_final_2024")
RECOVERY_KEY = os.environ.get("RECOVERY_KEY", "admin@2024")

# --- MONGODB CONNECTION ---
try:
    ca = certifi.where()
    MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(MONGO_URI, tlsCAFile=ca, serverSelectionTimeoutMS=5000)
    db = client['app_hub_production_ultimate_system']
    apps_col = db['apps']
    users_col = db['users']
    ads_col = db['ads']
    settings_col = db['settings']
except Exception as e:
    print(f"DATABASE CONNECTION ERROR: {e}")

# --- DYNAMIC SITE HELPERS ---
def get_site_info():
    info = settings_col.find_one({"type": "site_info"})
    if not info:
        return {
            "name": "APPHUB PRO", 
            "title": "Ultimate Premium App Store", 
            "logo": "https://cdn-icons-png.flaticon.com/512/2589/2589127.png",
            "desc": "Ultimate platform for high-performance applications. Discover, search and download your favorite tools with maximum speed and security.",
            "copyright": "2024 APPHUB PRO Ultimate PRO v10.0",
            "fb": "#", "tw": "#", "ig": "#"
        }
    return info

def get_footer_links():
    links = settings_col.find_one({"type": "footer_links"})
    if not links:
        return {
            "cat1_n": "Android Applications", "cat1_u": "/?cat=Android Applications",
            "cat2_n": "iOS Applications", "cat2_u": "/?cat=iOS Applications",
            "cat3_n": "Desktop Software", "cat3_u": "/?cat=Desktop Software",
            "cat4_n": "Latest Games", "cat4_u": "/?cat=Latest Games"
        }
    return links

def get_legal_content(page_type):
    site = get_site_info()
    content = settings_col.find_one({"type": "legal_page", "page": page_type})
    if not content:
        # অটোমেটিক টেক্সট জেনারেশন
        if page_type == "privacy":
            return f"Privacy Policy for {site['name']}: Your privacy is important to us. We do not collect personal data without your consent. All downloads on {site['name']} are verified and secure."
        elif page_type == "terms":
            return f"Terms of Service for {site['name']}: By using this website, you agree to comply with our terms. Content provided here is for personal use only. {site['name']} is not responsible for third-party content."
        elif page_type == "dmca":
            return f"DMCA Notice for {site['name']}: We respect intellectual property rights. If any content on {site['name']} violates your copyright, please contact us with proof for immediate removal."
    return content['text']

def get_shortener():
    return settings_col.find_one({"type": "shortener"}) or {"url": "", "api": ""}

# --- HTML TEMPLATES ---

BASE_CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css" />
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');
    body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; color: #0f172a; scroll-behavior: smooth; }
    .glass-nav { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(226, 232, 240, 0.8); }
    .hero-gradient { background: linear-gradient(135deg, #4f46e5 0%, #1e1b4b 100%); }
    .pro-card { background: white; border: 1px solid #f1f5f9; border-radius: 2.5rem; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
    .pro-card:hover { transform: translateY(-10px); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1); border-color: #6366f1; }
    .sidebar-link { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-radius: 18px; font-weight: 600; color: #94a3b8; transition: 0.3s; }
    .sidebar-link:hover { background: rgba(99, 102, 241, 0.1); color: #6366f1; }
    .sidebar-active { background: #6366f1 !important; color: white !important; box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4); }
    .swiper { width: 100%; height: 320px; border-radius: 2rem; overflow: hidden; margin-bottom: 3rem; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.3); }
    @media (max-width: 768px) { .swiper { height: 260px; border-radius: 1.5rem; } }
    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .btn-main { background: #6366f1; color: white; padding: 12px 28px; border-radius: 18px; font-weight: 700; transition: 0.3s; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.4); }
    input, textarea, select { border: 2px solid #f1f5f9; border-radius: 18px; padding: 14px 18px; outline: none; transition: 0.3s; background: #fff; }
    input:focus { border-color: #6366f1; }
    .footer-bg { background: #0f172a; color: #94a3b8; }
    @media (max-width: 1024px) {
        .admin-sidebar { height: auto !important; position: relative !important; width: 100% !important; }
        .sidebar-links-container { display: flex; overflow-x: auto; padding-bottom: 10px; gap: 10px; }
        .sidebar-link { white-space: nowrap; padding: 10px 15px; }
    }
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
    <nav class="glass-nav h-auto min-h-20 sticky top-0 z-50 py-3">
        <div class="container mx-auto px-6 flex flex-col lg:flex-row items-center justify-between gap-4">
            <div class="flex items-center justify-between w-full lg:w-auto">
                <a href="/" class="flex items-center gap-3">
                    <img src="{{ site.logo }}" class="w-8 h-8 md:w-10 md:h-10 rounded-xl">
                    <span class="text-xl md:text-2xl font-black text-slate-900 tracking-tighter uppercase">{{ site.name }}</span>
                </a>
            </div>
            <div class="flex-1 w-full max-w-xl">
                <form action="/" method="GET" class="w-full flex bg-slate-100 rounded-2xl px-5 py-2.5 items-center border border-slate-200">
                    <input type="text" name="q" placeholder="Search apps, games, tools..." class="bg-transparent outline-none text-sm w-full font-medium" value="{{ q }}">
                    <button type="submit"><i class="fas fa-search text-indigo-600"></i></button>
                </form>
            </div>
        </div>
    </nav>
    {% endif %}

    <div class="{% if is_admin_route %}flex flex-col lg:flex-row min-h-screen{% else %}container mx-auto px-6 py-6 md:py-12{% endif %}">
        {% if is_admin_route %}
        <div class="admin-sidebar w-80 bg-slate-950 text-slate-400 p-8 flex flex-col lg:sticky lg:top-0 lg:h-screen shadow-2xl overflow-y-auto">
            <div class="flex items-center gap-3 mb-8 lg:mb-12 border-b border-slate-900 pb-6">
                <img src="{{ site.logo }}" class="w-10 h-10 rounded-xl shadow-lg">
                <span class="text-xl font-black text-white uppercase tracking-tighter italic italic">{{ site.name }}</span>
            </div>
            <div class="sidebar-links-container flex-1 space-y-0 lg:space-y-3">
                <a href="/admin/dashboard" class="sidebar-link {% if active == 'dashboard' %}sidebar-active{% endif %}"><i class="fas fa-chart-line"></i> Dashboard</a>
                <a href="/admin/apps" class="sidebar-link {% if active == 'apps' %}sidebar-active{% endif %}"><i class="fas fa-cube"></i> Apps Manager</a>
                <a href="/admin/ads" class="sidebar-link {% if active == 'ads' %}sidebar-active{% endif %}"><i class="fas fa-ad"></i> Ads Manager</a>
                <a href="/admin/layout" class="sidebar-link {% if active == 'layout' %}sidebar-active{% endif %}"><i class="fas fa-paint-roller"></i> Layout Manager</a>
                <a href="/admin/settings" class="sidebar-link {% if active == 'settings' %}sidebar-active{% endif %}"><i class="fas fa-sliders-h"></i> System Settings</a>
            </div>
            <div class="pt-8 border-t border-slate-900 flex flex-col gap-4 mt-6">
                <a href="/" class="text-emerald-400 font-black flex items-center gap-3 text-sm"><i class="fas fa-external-link-alt"></i> OPEN SITE</a>
                <a href="/logout" class="text-red-500 font-black flex items-center gap-3 text-sm"><i class="fas fa-power-off"></i> LOGOUT</a>
            </div>
        </div>
        <div class="flex-1 bg-white p-6 md:p-12 overflow-y-auto">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for msg in messages %}
                        <div class="bg-indigo-600 text-white p-5 rounded-3xl mb-10 shadow-2xl flex justify-between">
                            <span><i class="fas fa-check-circle mr-2"></i> {{ msg }}</span>
                            <button onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            {% block admin_content %}{% endblock %}
        </div>
        {% else %}
        <div class="w-full min-h-[70vh]">
            {% block content %}{% endblock %}
        </div>
        {% endif %}
    </div>

    {% if not is_admin_route %}
    <footer class="footer-bg py-16 md:py-20 mt-10 md:mt-20">
        <div class="container mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-16">
            <div>
                <h3 class="text-white text-2xl font-black mb-6 uppercase">{{ site.name }}</h3>
                <p class="text-sm leading-relaxed mb-8">{{ site.desc }}</p>
                <div class="flex gap-4">
                    <a href="{{ site.fb }}" target="_blank" class="w-10 h-10 bg-slate-900 rounded-full flex items-center justify-center hover:bg-indigo-600 transition"><i class="fab fa-facebook-f text-white"></i></a>
                    <a href="{{ site.tw }}" target="_blank" class="w-10 h-10 bg-slate-900 rounded-full flex items-center justify-center hover:bg-indigo-600 transition"><i class="fab fa-twitter text-white"></i></a>
                </div>
            </div>
            <div>
                <h4 class="text-white font-bold mb-6 uppercase tracking-widest">Explore Categories</h4>
                <ul class="space-y-3 text-sm">
                    <li><a href="{{ footer.cat1_u }}" class="hover:text-indigo-400 transition">{{ footer.cat1_n }}</a></li>
                    <li><a href="{{ footer.cat2_u }}" class="hover:text-indigo-400 transition">{{ footer.cat2_n }}</a></li>
                    <li><a href="{{ footer.cat3_u }}" class="hover:text-indigo-400 transition">{{ footer.cat3_n }}</a></li>
                    <li><a href="{{ footer.cat4_u }}" class="hover:text-indigo-400 transition">{{ footer.cat4_n }}</a></li>
                </ul>
            </div>
            <div>
                <h4 class="text-white font-bold mb-6 uppercase tracking-widest">Support & Legal</h4>
                <ul class="space-y-3 text-sm">
                    <li><a href="/p/privacy" class="hover:text-indigo-400 transition">Privacy Policy</a></li>
                    <li><a href="/p/terms" class="hover:text-indigo-400 transition">Terms of Service</a></li>
                    <li><a href="/p/dmca" class="hover:text-indigo-400 transition">DMCA Takedown</a></li>
                </ul>
            </div>
        </div>
        <div class="border-t border-slate-900 mt-16 pt-8 text-center text-[10px] font-bold uppercase tracking-[0.3em]">
            &copy; {{ site.copyright }}. All Rights Reserved.
        </div>
    </footer>
    {% endif %}

    <script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
    <script>
        const swiper = new Swiper('.swiper', {
            loop: true, autoplay: { delay: 4000, disableOnInteraction: false },
            pagination: { el: '.swiper-pagination', clickable: true },
            effect: 'fade', fadeEffect: { crossFade: true }
        });
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def home():
    site = get_site_info()
    footer = get_footer_links()
    q = request.args.get('q', '')
    cat = request.args.get('cat', '')
    
    query = {}
    if q: query["name"] = {"$regex": q, "$options": "i"}
    elif cat: query["category"] = cat
        
    apps = list(apps_col.find(query).sort('_id', -1))
    featured = list(apps_col.find({"featured": "on"}).limit(5)) if not (q or cat) else []
    ads = list(ads_col.find())
    
    content = """
    {% if featured %}
    <div class="swiper mb-10 shadow-2xl rounded-[2.5rem] overflow-hidden">
        <div class="swiper-wrapper bg-indigo-900">
            {% for f in featured %}
            <div class="swiper-slide p-10 md:p-20 text-white hero-gradient relative">
                <h2 class="text-4xl md:text-6xl font-black mb-4 uppercase italic tracking-tighter">{{ f.name }}</h2>
                <p class="mb-8 opacity-80 max-w-2xl line-clamp-2">{{ f.info }}</p>
                <a href="/app/{{f._id}}" class="bg-white text-indigo-900 px-8 py-3 rounded-full font-black inline-block shadow-lg">EXPLORE NOW</a>
            </div>
            {% endfor %}
        </div>
        <div class="swiper-pagination"></div>
    </div>
    {% endif %}

    <h2 class="text-3xl font-black mb-8 uppercase italic tracking-tighter">
        {% if q %}Search Result for "{{q}}"{% elif cat %}{{cat}} Apps{% else %}Latest Releases{% endif %}
    </h2>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        {% for app in apps %}
        <a href="/app/{{app._id}}" class="pro-card p-8 flex flex-col items-center text-center group">
            <img src="{{app.logo}}" class="w-24 h-24 rounded-[2rem] shadow-xl border-4 border-white mb-6 group-hover:scale-110 transition duration-300">
            <h3 class="font-black text-xl mb-4 uppercase tracking-tighter line-clamp-1">{{app.name}}</h3>
            <div class="btn-main w-full justify-center py-4 bg-slate-900 group-hover:bg-indigo-600 shadow-xl">DOWNLOAD</div>
        </a>
        {% endfor %}
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', content), site=site, footer=footer, apps=apps, featured=featured, ads=ads, q=q, cat=cat, is_admin_route=False)

@app.route('/app/<id>')
def details(id):
    site = get_site_info()
    footer = get_footer_links()
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    if not app_data: return redirect('/')
    content = """
    <div class="bg-white rounded-[3rem] p-10 md:p-20 shadow-2xl flex flex-col md:flex-row gap-10 items-center border border-slate-100">
        <img src="{{app.logo}}" class="w-64 h-64 rounded-[4rem] border-[12px] border-slate-50 shadow-2xl">
        <div class="flex-1 text-center md:text-left">
            <h1 class="text-5xl md:text-7xl font-black mb-6 uppercase tracking-tighter italic">{{app.name}}</h1>
            <p class="text-xl mb-10 opacity-70 italic leading-relaxed">"{{app.info}}"</p>
            <div class="flex flex-wrap gap-4 mb-12 justify-center md:justify-start">
                <span class="bg-indigo-600 text-white px-8 py-3 rounded-full font-black text-xs uppercase shadow-lg">{{app.category}}</span>
                <span class="bg-emerald-50 text-emerald-600 px-8 py-3 rounded-full font-black text-xs uppercase border border-emerald-100">Version {{app.version}}</span>
            </div>
            <a href="/get/{{app._id}}" class="bg-slate-900 text-white px-16 py-6 rounded-full font-black text-2xl inline-block shadow-2xl hover:bg-indigo-700 transition">SECURE DOWNLOAD</a>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', content), site=site, footer=footer, app=app_data, is_admin_route=False)

@app.route('/p/<slug>')
def legal_pages(slug):
    site = get_site_info()
    footer = get_footer_links()
    if slug not in ["privacy", "terms", "dmca"]: return redirect('/')
    
    title = slug.replace("privacy", "Privacy Policy").replace("terms", "Terms of Service").replace("dmca", "DMCA Takedown")
    content = get_legal_content(slug)
    
    page_html = f"""
    <div class="bg-white rounded-[3rem] p-10 md:p-20 shadow-2xl border border-slate-100 max-w-4xl mx-auto">
        <h1 class="text-5xl font-black mb-10 uppercase italic tracking-tighter text-indigo-600">{title}</h1>
        <div class="prose prose-lg text-slate-600 leading-loose whitespace-pre-line font-medium">
            {content}
        </div>
        <div class="mt-16 pt-8 border-t border-slate-100">
            <a href="/" class="text-indigo-600 font-black flex items-center gap-2"><i class="fas fa-arrow-left"></i> BACK TO HOME</a>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', page_html), site=site, footer=footer, is_admin_route=False)

@app.route('/admin/apps', methods=['GET', 'POST'])
def admin_apps():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    footer = get_footer_links()
    
    if request.method == 'POST':
        apps_col.insert_one({
            "name": request.form.get('name'), "logo": request.form.get('logo'),
            "category": request.form.get('category'), "release_date": request.form.get('release_date'),
            "version": request.form.get('version'), "info": request.form.get('info'),
            "download_link": request.form.get('download_link'), "featured": request.form.get('featured'),
            "created_at": datetime.now()
        })
        flash("Application saved successfully.")
        return redirect('/admin/apps')
    
    admin_q = request.args.get('admin_q', '')
    query = {"name": {"$regex": admin_q, "$options": "i"}} if admin_q else {}
    apps = list(apps_col.find(query).sort('_id', -1))
    
    content = """
    <h1 class="text-5xl font-black mb-12 uppercase italic tracking-tighter">Apps Manager</h1>
    <div class="grid lg:grid-cols-12 gap-10">
        <div class="lg:col-span-4 bg-white p-8 rounded-[3rem] border-2 shadow-2xl h-fit sticky lg:top-10">
            <h2 class="font-black mb-6 border-b pb-4 uppercase text-indigo-600">Add New App</h2>
            <form method="POST" class="space-y-4">
                <input name="name" placeholder="App Title" class="w-full" required>
                <input name="logo" placeholder="Logo Link" class="w-full" required>
                <div class="grid grid-cols-2 gap-2"><input type="date" name="release_date"><input name="version" placeholder="v1.0"></div>
                <select name="category" class="w-full font-bold" required>
                    <option value="" disabled selected>Select Category</option>
                    <option>Android Applications</option>
                    <option>iOS Applications</option>
                    <option>Desktop Software</option>
                    <option>Latest Games</option>
                </select>
                <textarea name="info" placeholder="Short Description" class="w-full h-24" required></textarea>
                <input name="download_link" placeholder="Final Download Link" class="w-full" required>
                <label class="flex items-center gap-2 font-black text-indigo-600"><input type="checkbox" name="featured"> Show in Slider</label>
                <button class="bg-indigo-600 text-white w-full py-4 rounded-2xl font-black shadow-lg">PUBLISH NOW</button>
            </form>
        </div>
        <div class="lg:col-span-8">
            <form class="flex bg-slate-100 p-2 rounded-2xl border mb-6 shadow-inner">
                <input name="admin_q" placeholder="Search apps to manage..." class="bg-transparent w-full p-2 font-bold outline-none" value="{{admin_q}}">
                <button class="bg-indigo-600 text-white px-8 py-2 rounded-xl font-black">SEARCH</button>
            </form>
            <div class="bg-white rounded-[2.5rem] border shadow-2xl overflow-hidden overflow-x-auto">
                <table class="w-full text-left">
                    <thead class="bg-slate-900 text-white uppercase text-xs"><tr><th class="p-6">Asset Details</th><th class="p-6 text-right">Actions</th></tr></thead>
                    <tbody>
                        {% for a in apps %}
                        <tr class="border-b hover:bg-slate-50 transition">
                            <td class="p-6 flex items-center gap-4">
                                <img src="{{a.logo}}" class="w-12 h-12 rounded-xl border"> <div><b class="text-slate-800">{{a.name}}</b><p class="text-[10px] uppercase font-black text-slate-400">{{a.category}}</p></div>
                            </td>
                            <td class="p-6 text-right whitespace-nowrap">
                                <a href="/admin/edit/app/{{a._id}}" class="text-indigo-600 font-bold bg-indigo-50 px-5 py-2 rounded-xl mr-2">EDIT</a>
                                <a href="/del/app/{{a._id}}" class="text-red-500 font-bold bg-red-50 px-5 py-2 rounded-xl" onclick="return confirm('Delete permanently?')">DEL</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, footer=footer, apps=apps, admin_q=admin_q, is_admin_route=True, active="apps")

@app.route('/admin/edit/app/<id>', methods=['GET', 'POST'])
def edit_app(id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    footer = get_footer_links()
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        apps_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'), "logo": request.form.get('logo'),
            "category": request.form.get('category'), "version": request.form.get('version'),
            "info": request.form.get('info'), "download_link": request.form.get('download_link'),
            "featured": request.form.get('featured')
        }})
        flash("Application updated successfully.")
        return redirect('/admin/apps')
    content = """
    <h1 class="text-4xl font-black mb-10 uppercase italic tracking-tighter">Edit {{app_data.name}}</h1>
    <div class="bg-white p-10 rounded-[3rem] border-2 shadow-2xl max-w-3xl">
        <form method="POST" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div><label class="text-xs font-black uppercase text-slate-400 ml-2">Name</label><input name="name" value="{{app_data.name}}" class="w-full"></div>
                <div><label class="text-xs font-black uppercase text-slate-400 ml-2">Logo URL</label><input name="logo" value="{{app_data.logo}}" class="w-full"></div>
                <div><label class="text-xs font-black uppercase text-slate-400 ml-2">Category</label>
                    <select name="category" class="w-full font-bold">
                        <option {% if app_data.category == 'Android Applications' %}selected{% endif %}>Android Applications</option>
                        <option {% if app_data.category == 'iOS Applications' %}selected{% endif %}>iOS Applications</option>
                        <option {% if app_data.category == 'Desktop Software' %}selected{% endif %}>Desktop Software</option>
                        <option {% if app_data.category == 'Latest Games' %}selected{% endif %}>Latest Games</option>
                    </select>
                </div>
                <div><label class="text-xs font-black uppercase text-slate-400 ml-2">Version</label><input name="version" value="{{app_data.version}}" class="w-full"></div>
            </div>
            <div><label class="text-xs font-black uppercase text-slate-400 ml-2">Description</label><textarea name="info" class="w-full h-40">{{app_data.info}}</textarea></div>
            <div><label class="text-xs font-black uppercase text-slate-400 ml-2">Download URL</label><input name="download_link" value="{{app_data.download_link}}" class="w-full"></div>
            <div class="flex items-center gap-6">
                <button class="bg-indigo-600 text-white px-12 py-4 rounded-2xl font-black shadow-xl">UPDATE ASSET</button>
                <a href="/admin/apps" class="text-slate-400 font-bold">Cancel</a>
            </div>
        </form>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, footer=footer, app_data=app_data, is_admin_route=True, active="apps")

@app.route('/admin/layout', methods=['GET', 'POST'])
def admin_layout():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    footer = get_footer_links()
    if request.method == 'POST':
        l_type = request.form.get('l_type')
        if l_type == 'branding':
            settings_col.update_one({"type": "site_info"}, {"$set": {"name": request.form.get('name'), "logo": request.form.get('logo'), "title": request.form.get('title'), "desc": request.form.get('desc'), "copyright": request.form.get('copyright')}}, upsert=True)
        elif l_type == 'legal':
            page = request.form.get('page')
            settings_col.update_one({"type": "legal_page", "page": page}, {"$set": {"text": request.form.get('text')}}, upsert=True)
        flash("Layout updated.")
        return redirect('/admin/layout')
    
    content = """
    <h1 class="text-5xl font-black mb-12 uppercase italic tracking-tighter">Layout Manager</h1>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
        <div class="bg-white p-10 rounded-[3rem] border-2 shadow-2xl h-fit">
            <h2 class="text-xl font-black mb-8 border-b pb-4 uppercase text-indigo-600">Branding Settings</h2>
            <form method="POST" class="space-y-4">
                <input type="hidden" name="l_type" value="branding">
                <textarea name="desc" class="w-full h-24" placeholder="Footer About Text">{{site.desc}}</textarea>
                <input name="name" value="{{site.name}}" placeholder="Site Name">
                <input name="logo" value="{{site.logo}}" placeholder="Logo Link">
                <input name="copyright" value="{{site.copyright}}" placeholder="Copyright Text">
                <button class="bg-indigo-600 text-white w-full py-4 rounded-2xl font-black">SAVE BRANDING</button>
            </form>
        </div>
        
        <div class="bg-slate-50 p-10 rounded-[3rem] border-2 shadow-2xl h-fit">
            <h2 class="text-xl font-black mb-8 border-b pb-4 uppercase text-emerald-600">Legal Pages Editor</h2>
            <form method="POST" class="space-y-4">
                <input type="hidden" name="l_type" value="legal">
                <select name="page" class="w-full font-bold">
                    <option value="privacy">Privacy Policy</option>
                    <option value="terms">Terms of Service</option>
                    <option value="dmca">DMCA Takedown</option>
                </select>
                <textarea name="text" class="w-full h-64" placeholder="Paste or Type legal text here..."></textarea>
                <button class="bg-emerald-600 text-white w-full py-4 rounded-2xl font-black">SAVE PAGE TEXT</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, footer=footer, active="layout", is_admin_route=True)

# --- মূল কোডের বাকি রাউটসমূহ ---

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    footer = get_footer_links()
    stats = {"apps": apps_col.count_documents({}), "ads": ads_col.count_documents({}), "featured": apps_col.count_documents({"featured": "on"})}
    content = """
    <h1 class="text-6xl font-black mb-12 uppercase italic tracking-tighter">Dashboard</h1>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-10 mb-10">
        <div class="bg-indigo-600 p-12 rounded-[3.5rem] text-white shadow-2xl relative overflow-hidden">
            <i class="fas fa-cube absolute -right-10 -bottom-10 text-[200px] opacity-10"></i>
            <div class="text-8xl font-black tracking-tighter">{{ stats.apps }}</div><p class="font-black uppercase opacity-70">Total Apps</p>
        </div>
        <div class="bg-slate-900 p-12 rounded-[3.5rem] text-white shadow-2xl relative overflow-hidden border-4 border-slate-800">
            <i class="fas fa-ad absolute -right-10 -bottom-10 text-[200px] opacity-10"></i>
            <div class="text-8xl font-black tracking-tighter">{{ stats.ads }}</div><p class="font-black uppercase opacity-70">Ads Active</p>
        </div>
        <div class="bg-orange-500 p-12 rounded-[3.5rem] text-white shadow-2xl relative overflow-hidden">
            <i class="fas fa-star absolute -right-10 -bottom-10 text-[200px] opacity-10"></i>
            <div class="text-8xl font-black tracking-tighter">{{ stats.featured }}</div><p class="font-black uppercase opacity-70">Featured Slider</p>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, footer=footer, stats=stats, is_admin_route=True, active="dashboard")

@app.route('/admin/ads', methods=['GET', 'POST'])
def admin_ads():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    footer = get_footer_links()
    if request.method == 'POST':
        ads_col.insert_one({"name": request.form.get('name'), "code": request.form.get('code'), "created_at": datetime.now()})
        flash("Ad integrated.")
        return redirect('/admin/ads')
    ads_list = list(ads_col.find())
    content = """
    <h1 class="text-4xl font-black mb-10 uppercase italic tracking-tighter">Ads Placement</h1>
    <div class="grid lg:grid-cols-2 gap-10">
        <div class="bg-white p-10 rounded-[3rem] border shadow-2xl h-fit">
            <form method="POST" class="space-y-6"><input name="name" placeholder="Ad Unit Name" class="w-full" required><textarea name="code" placeholder="Paste script code here" class="w-full h-80" required></textarea><button class="bg-indigo-600 text-white w-full py-4 rounded-2xl font-black">DEPLOY AD</button></form>
        </div>
        <div class="space-y-6">{% for ad in ads %}<div class="p-8 bg-white border rounded-[2.5rem] flex justify-between shadow-sm items-center"><div><b class="text-2xl">{{ ad.name }}</b></div> <a href="/del/ad/{{ad._id}}" class="text-red-500 font-bold">REMOVE</a></div>{% endfor %}</div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, footer=footer, ads=ads_list, is_admin_route=True, active="ads")

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    footer = get_footer_links()
    if request.method == 'POST':
        settings_col.update_one({"type": "shortener"}, {"$set": {"url": request.form.get('url'), "api": request.form.get('api')}}, upsert=True)
        flash("Settings Saved.")
        return redirect('/admin/settings')
    cfg = get_shortener()
    content = """
    <h1 class="text-4xl font-black mb-10 uppercase italic tracking-tighter">API Settings</h1>
    <div class="bg-slate-950 p-12 rounded-[4rem] text-white border-4 border-slate-900 shadow-2xl">
        <form method="POST" class="space-y-8">
            <input name="url" value="{{cfg.url}}" placeholder="domain.com" class="w-full bg-slate-900 border-slate-800 text-white font-bold p-6">
            <input name="api" value="{{cfg.api}}" placeholder="API Secret Key" class="w-full bg-slate-900 border-slate-800 text-white font-bold p-6">
            <button class="bg-emerald-500 text-black w-full py-6 rounded-[2rem] font-black text-xl">UPDATE SYSTEM API</button>
        </form>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, footer=footer, cfg=cfg, is_admin_route=True, active="settings")

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

@app.route('/admin-gate', methods=['GET', 'POST'])
def login():
    site = get_site_info()
    admin_user = users_col.find_one({"username": "admin"})
    if request.method == 'POST':
        pw = request.form.get('password')
        if not admin_user:
            users_col.insert_one({"username": "admin", "password": generate_password_hash(pw)})
            session['logged_in'] = True
            return redirect('/admin/dashboard')
        if check_password_hash(admin_user['password'], pw):
            session['logged_in'] = True
            return redirect('/admin/dashboard')
        flash("Authentication Failed!")
    content = f"""
    <div class="max-w-lg mx-auto mt-32 bg-white p-20 rounded-[5rem] shadow-2xl text-center border-4">
        <h2 class="text-4xl font-black mb-10 text-slate-900 uppercase italic italic">Admin Auth</h2>
        <form method="POST" class="space-y-8"><input type="password" name="password" class="w-full bg-slate-50 p-6 rounded-[2rem] text-center font-black text-2xl" required><button class="bg-indigo-600 text-white w-full py-6 rounded-[2rem] font-black text-xl shadow-xl">LOG IN</button></form>
    </div>
    """
    return render_template_string(f"<!DOCTYPE html><html><head>{BASE_CSS}</head><body>{content}</body></html>")

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        if request.form.get('key') == RECOVERY_KEY:
            users_col.update_one({"username": "admin"}, {"$set": {"password": generate_password_hash(request.form.get('pw'))}}, upsert=True)
            flash("Success.")
            return redirect('/admin-gate')
    content = """
    <div class="max-w-xl mx-auto mt-32 bg-white p-20 rounded-[5rem] shadow-2xl text-center"><form method="POST" class="space-y-8"><input name="key" placeholder="Key" class="w-full border-2"><input type="password" name="pw" placeholder="New" class="w-full border-2"><button class="bg-red-600 text-white w-full py-5 rounded-[2rem] font-black uppercase">RESET</button></form></div>
    """
    return render_template_string(f"<!DOCTYPE html><html><head>{BASE_CSS}</head><body>{content}</body></html>")

@app.route('/del/<type>/<id>')
def delete_entry(type, id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    if type == 'app': apps_col.delete_one({"_id": ObjectId(id)})
    if type == 'ad': ads_col.delete_one({"_id": ObjectId(id)})
    flash("Deleted.")
    return redirect(request.referrer)

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
