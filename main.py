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
    # আপনার দেওয়া MongoDB কানেকশন লিঙ্ক
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
            "cat1_n": "Android Applications", "cat1_u": "#",
            "cat2_n": "iOS Premium Tools", "cat2_u": "#",
            "cat3_n": "Desktop Software", "cat3_u": "#",
            "cat4_n": "Latest Games", "cat4_u": "#",
            "leg1_n": "Privacy Policy", "leg1_u": "#",
            "leg2_n": "Terms of Service", "leg2_u": "#",
            "leg3_n": "DMCA Takedown", "leg3_u": "#"
        }
    return links

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
    
    /* স্লাইডার হাইট ছোট করা হয়েছে */
    .swiper { width: 100%; height: 320px; border-radius: 2rem; overflow: hidden; margin-bottom: 3rem; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.3); }
    @media (max-width: 768px) { .swiper { height: 260px; border-radius: 1.5rem; } }

    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .btn-main { background: #6366f1; color: white; padding: 12px 28px; border-radius: 18px; font-weight: 700; transition: 0.3s; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.4); }
    .btn-main:hover { background: #4f46e5; transform: scale(1.05); }
    input, textarea, select { border: 2px solid #f1f5f9; border-radius: 18px; padding: 14px 18px; outline: none; transition: 0.3s; background: #fff; }
    input:focus { border-color: #6366f1; box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1); }
    .footer-bg { background: #0f172a; color: #94a3b8; }
    
    /* Admin Mobile Sidebar Auto Mode */
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
                <div class="lg:hidden text-[10px] font-black bg-indigo-600 text-white px-3 py-1.5 rounded-full uppercase tracking-widest">v10.0 PRO</div>
            </div>
            
            <!-- ইউজার প্যানেল সার্চ বার (মোবাইল ও ডেক্সটপ অটো মোড) -->
            <div class="flex flex-1 w-full max-w-xl mx-0 lg:mx-12">
                <form action="/" method="GET" class="w-full flex bg-slate-100 rounded-2xl px-5 py-2.5 items-center border border-slate-200">
                    <input type="text" name="q" placeholder="Search apps, games, tools..." class="bg-transparent outline-none text-sm w-full font-medium" value="{{ q }}">
                    <button type="submit"><i class="fas fa-search text-indigo-600"></i></button>
                </form>
            </div>

            <div class="hidden lg:flex items-center gap-4">
                <div class="text-[10px] font-black bg-indigo-600 text-white px-3 py-1.5 rounded-full uppercase tracking-widest">v10.0 Pro</div>
            </div>
        </div>
    </nav>
    {% endif %}

    <div class="{% if is_admin_route %}flex flex-col lg:flex-row min-h-screen{% else %}container mx-auto px-6 py-6 md:py-12{% endif %}">
        {% if is_admin_route %}
        <div class="admin-sidebar w-80 bg-slate-950 text-slate-400 p-8 flex flex-col lg:sticky lg:top-0 lg:h-screen shadow-2xl overflow-y-auto">
            <div class="flex items-center gap-3 mb-8 lg:mb-12 border-b border-slate-900 pb-6">
                <img src="{{ site.logo }}" class="w-10 h-10 rounded-xl shadow-lg">
                <span class="text-xl font-black text-white uppercase tracking-tighter italic">{{ site.name }}</span>
            </div>
            <div class="sidebar-links-container flex-1 space-y-0 lg:space-y-3">
                <a href="/admin/dashboard" class="sidebar-link {% if active == 'dashboard' %}sidebar-active{% endif %}"><i class="fas fa-chart-line"></i> Dashboard</a>
                <a href="/admin/apps" class="sidebar-link {% if active == 'apps' %}sidebar-active{% endif %}"><i class="fas fa-cube"></i> Apps Manager</a>
                <a href="/admin/ads" class="sidebar-link {% if active == 'ads' %}sidebar-active{% endif %}"><i class="fas fa-ad"></i> Ad Manager</a>
                <a href="/admin/layout" class="sidebar-link {% if active == 'layout' %}sidebar-active{% endif %}"><i class="fas fa-paint-roller"></i> Layout Manager</a>
                <a href="/admin/settings" class="sidebar-link {% if active == 'settings' %}sidebar-active{% endif %}"><i class="fas fa-sliders-h"></i> System Settings</a>
            </div>
            <div class="pt-8 border-t border-slate-900 flex flex-row lg:flex-col gap-4 mt-6">
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
                    <a href="{{ site.fb }}" class="w-10 h-10 bg-slate-900 rounded-full flex items-center justify-center hover:bg-indigo-600 transition"><i class="fab fa-facebook-f text-white"></i></a>
                    <a href="{{ site.tw }}" class="w-10 h-10 bg-slate-900 rounded-full flex items-center justify-center hover:bg-indigo-600 transition"><i class="fab fa-twitter text-white"></i></a>
                    <a href="{{ site.ig }}" class="w-10 h-10 bg-slate-900 rounded-full flex items-center justify-center hover:bg-indigo-600 transition"><i class="fab fa-instagram text-white"></i></a>
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
                    <li><a href="{{ footer.leg1_u }}" class="hover:text-indigo-400 transition">{{ footer.leg1_n }}</a></li>
                    <li><a href="{{ footer.leg2_u }}" class="hover:text-indigo-400 transition">{{ footer.leg2_n }}</a></li>
                    <li><a href="{{ footer.leg3_u }}" class="hover:text-indigo-400 transition">{{ footer.leg3_n }}</a></li>
                    <li><a href="/admin-gate" class="hover:text-indigo-400 transition">Administrator Access</a></li>
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
    if q:
        apps = list(apps_col.find({"name": {"$regex": q, "$options": "i"}}).sort('_id', -1))
        featured = []
    else:
        apps = list(apps_col.find().sort('_id', -1))
        featured = list(apps_col.find({"featured": "on"}).limit(5))
    
    ads = list(ads_col.find())
    
    content = """
    {% if featured %}
    <div class="swiper mb-10 shadow-2xl">
        <div class="swiper-wrapper">
            {% for f in featured %}
            <div class="swiper-slide hero-gradient relative flex items-center p-8 md:p-16 lg:p-20 text-white overflow-hidden">
                <div class="absolute inset-0 bg-indigo-950 opacity-20 z-0"></div>
                <div class="relative z-10 max-w-2xl">
                    <span class="bg-indigo-500 text-[10px] font-black px-4 py-1.5 rounded-full uppercase mb-4 inline-block tracking-widest shadow-xl">Featured Choice</span>
                    <h2 class="text-3xl md:text-5xl lg:text-6xl font-black mb-4 leading-tight tracking-tighter uppercase italic">{{ f.name }}</h2>
                    <p class="text-indigo-100 text-xs md:text-lg mb-8 line-clamp-2">{{ f.info }}</p>
                    <a href="/app/{{f._id}}" class="bg-white text-indigo-900 px-8 py-3 rounded-2xl font-black text-xs md:text-base flex items-center gap-2 w-fit">EXPLORE DETAILS</a>
                </div>
                <div class="absolute right-[-30px] top-1/2 -translate-y-1/2 hidden lg:block rotate-12 transition duration-1000">
                    <img src="{{f.logo}}" class="w-[300px] h-[300px] rounded-[4rem] shadow-2xl border-[15px] border-white/10 opacity-60">
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="swiper-pagination"></div>
    </div>
    {% endif %}

    <div class="flex flex-col md:flex-row items-center justify-between mb-8 gap-6">
        <h2 class="text-2xl md:text-4xl font-black text-slate-900 tracking-tighter uppercase italic">{% if q %}SEARCH: "{{q}}"{% else %}LATEST DISCOVERIES{% endif %}</h2>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 md:gap-12">
        {% for app in apps %}
        <a href="/app/{{app._id}}" class="pro-card p-6 md:p-10 group text-center flex flex-col items-center">
            <div class="relative mb-6">
                <img src="{{app.logo}}" class="w-24 h-24 md:w-32 md:h-32 rounded-[2.5rem] shadow-2xl relative z-10 border-4 border-white group-hover:scale-110 transition">
                {% if app.featured == 'on' %}<div class="absolute -top-2 -right-2 bg-orange-500 text-white text-[8px] font-black px-2 py-0.5 rounded-full z-20">PRO</div>{% endif %}
            </div>
            <h3 class="font-black text-xl md:text-2xl text-slate-800 mb-3 tracking-tighter uppercase line-clamp-1">{{app.name}}</h3>
            <p class="text-xs text-slate-400 line-clamp-2 h-10 mb-8 italic">{{app.info}}</p>
            <div class="btn-main w-full justify-center py-4 bg-slate-900 group-hover:bg-indigo-600 shadow-xl text-sm">DOWNLOAD NOW</div>
        </a>
        {% endfor %}
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', content), site=site, footer=footer, apps=apps, featured=featured, ads=ads, q=q, is_admin_route=False)

@app.route('/app/<id>')
def details(id):
    site = get_site_info()
    footer = get_footer_links()
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    if not app_data: return redirect('/')
    
    content = """
    <div class="max-w-6xl mx-auto">
        <div class="bg-white rounded-[2.5rem] md:rounded-[4rem] shadow-2xl p-6 md:p-20 flex flex-col md:flex-row gap-10 lg:gap-20 items-center border border-slate-100 relative">
            <img src="{{app.logo}}" class="w-48 h-48 md:w-80 rounded-[4rem] md:rounded-[5rem] shadow-2xl border-[15px] border-slate-50">
            <div class="flex-1 text-center md:text-left">
                <h1 class="text-4xl md:text-7xl font-black text-slate-950 mb-6 tracking-tighter italic uppercase">{{app.name}}</h1>
                <p class="text-slate-500 text-lg md:text-2xl mb-8 italic">"{{app.info}}"</p>
                <div class="flex gap-4 mb-10 justify-center md:justify-start">
                    <span class="bg-indigo-600 text-white px-6 py-2 rounded-full font-black text-xs uppercase">{{app.category}}</span>
                    <span class="bg-emerald-50 text-emerald-600 px-6 py-2 rounded-full font-black text-xs uppercase border border-emerald-100">V {{app.version}}</span>
                </div>
                <a href="/get/{{app._id}}" class="inline-flex items-center gap-4 bg-slate-900 text-white px-10 py-5 md:px-20 md:py-8 rounded-full font-black text-xl md:text-3xl shadow-2xl">SECURE DOWNLOAD</a>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block content %}{% endblock %}', content), site=site, footer=footer, app=app_data, is_admin_route=False)

@app.route('/admin/layout', methods=['GET', 'POST'])
def admin_layout():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    footer = get_footer_links()
    
    if request.method == 'POST':
        l_type = request.form.get('l_type')
        if l_type == 'branding':
            settings_col.update_one({"type": "site_info"}, {"$set": {
                "name": request.form.get('name'), "logo": request.form.get('logo'),
                "title": request.form.get('title'), "desc": request.form.get('desc'),
                "copyright": request.form.get('copyright'), "fb": request.form.get('fb'),
                "tw": request.form.get('tw'), "ig": request.form.get('ig')
            }}, upsert=True)
        elif l_type == 'links':
            settings_col.update_one({"type": "footer_links"}, {"$set": {
                "cat1_n": request.form.get('cat1_n'), "cat1_u": request.form.get('cat1_u'),
                "cat2_n": request.form.get('cat2_n'), "cat2_u": request.form.get('cat2_u'),
                "cat3_n": request.form.get('cat3_n'), "cat3_u": request.form.get('cat3_u'),
                "cat4_n": request.form.get('cat4_n'), "cat4_u": request.form.get('cat4_u'),
                "leg1_n": request.form.get('leg1_n'), "leg1_u": request.form.get('leg1_u'),
                "leg2_n": request.form.get('leg2_n'), "leg2_u": request.form.get('leg2_u'),
                "leg3_n": request.form.get('leg3_n'), "leg3_u": request.form.get('leg3_u')
            }}, upsert=True)
        flash("Layout settings updated successfully.")
        return redirect('/admin/layout')

    content = """
    <h1 class="text-4xl md:text-5xl font-black mb-12 italic uppercase">Layout Manager</h1>
    
    <div class="space-y-12">
        <!-- Box 1: Branding -->
        <div class="bg-white p-8 md:p-12 rounded-[3rem] border-2 border-slate-100 shadow-xl">
            <h2 class="text-2xl font-black text-indigo-600 mb-8 uppercase border-b pb-4">Box 1: Branding & Description</h2>
            <form method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <input type="hidden" name="l_type" value="branding">
                <div class="col-span-full">
                    <label class="text-xs font-bold uppercase ml-2 text-slate-400">Footer About Text</label>
                    <textarea name="desc" class="w-full h-24">{{ site.desc }}</textarea>
                </div>
                <div><label class="text-xs font-bold uppercase ml-2 text-slate-400">Site Name</label><input name="name" value="{{site.name}}" class="w-full"></div>
                <div><label class="text-xs font-bold uppercase ml-2 text-slate-400">Site Title</label><input name="title" value="{{site.title}}" class="w-full"></div>
                <div><label class="text-xs font-bold uppercase ml-2 text-slate-400">Logo URL</label><input name="logo" value="{{site.logo}}" class="w-full"></div>
                <div><label class="text-xs font-bold uppercase ml-2 text-slate-400">Copyright Text</label><input name="copyright" value="{{site.copyright}}" class="w-full"></div>
                <div><label class="text-xs font-bold uppercase ml-2 text-slate-400">Facebook URL</label><input name="fb" value="{{site.fb}}" class="w-full"></div>
                <div><label class="text-xs font-bold uppercase ml-2 text-slate-400">Twitter URL</label><input name="tw" value="{{site.tw}}" class="w-full"></div>
                <div><label class="text-xs font-bold uppercase ml-2 text-slate-400">Instagram URL</label><input name="ig" value="{{site.ig}}" class="w-full"></div>
                <div class="col-span-full"><button class="btn-main w-full justify-center py-5">SAVE BRANDING</button></div>
            </form>
        </div>

        <!-- Box 2: Links -->
        <div class="bg-slate-50 p-8 md:p-12 rounded-[3rem] border-2 border-slate-100 shadow-xl">
            <h2 class="text-2xl font-black text-emerald-600 mb-8 uppercase border-b pb-4">Box 2: Footer Categories & Support Links</h2>
            <form method="POST" class="space-y-10">
                <input type="hidden" name="l_type" value="links">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
                    <div class="space-y-4">
                        <h3 class="font-black text-slate-700">Explore Categories</h3>
                        <div class="grid grid-cols-2 gap-2"><input name="cat1_n" value="{{footer.cat1_n}}" placeholder="Name"><input name="cat1_u" value="{{footer.cat1_u}}" placeholder="URL"></div>
                        <div class="grid grid-cols-2 gap-2"><input name="cat2_n" value="{{footer.cat2_n}}" placeholder="Name"><input name="cat2_u" value="{{footer.cat2_u}}" placeholder="URL"></div>
                        <div class="grid grid-cols-2 gap-2"><input name="cat3_n" value="{{footer.cat3_n}}" placeholder="Name"><input name="cat3_u" value="{{footer.cat3_u}}" placeholder="URL"></div>
                        <div class="grid grid-cols-2 gap-2"><input name="cat4_n" value="{{footer.cat4_n}}" placeholder="Name"><input name="cat4_u" value="{{footer.cat4_u}}" placeholder="URL"></div>
                    </div>
                    <div class="space-y-4">
                        <h3 class="font-black text-slate-700">Support & Legal Links</h3>
                        <div class="grid grid-cols-2 gap-2"><input name="leg1_n" value="{{footer.leg1_n}}" placeholder="Name"><input name="leg1_u" value="{{footer.leg1_u}}" placeholder="URL"></div>
                        <div class="grid grid-cols-2 gap-2"><input name="leg2_n" value="{{footer.leg2_n}}" placeholder="Name"><input name="leg2_u" value="{{footer.leg2_u}}" placeholder="URL"></div>
                        <div class="grid grid-cols-2 gap-2"><input name="leg3_n" value="{{footer.leg3_n}}" placeholder="Name"><input name="leg3_u" value="{{footer.leg3_u}}" placeholder="URL"></div>
                    </div>
                </div>
                <button class="btn-main w-full justify-center py-5 bg-slate-900">SAVE ALL LINKS</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, footer=footer, active="layout", is_admin_route=True)

# --- মূল কোডের বাকি রাউটসমূহ (অপরিবর্তিত) ---

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
        except Exception as e:
            print(f"SHORTENER ERROR: {e}")
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
        flash("Invalid Administrative Credentials!")
    content = f"""
    <div class="max-w-lg mx-auto mt-32 bg-white p-20 rounded-[5rem] shadow-2xl text-center">
        <h2 class="text-4xl font-black mb-10 text-slate-900 uppercase italic">Admin Auth</h2>
        <form method="POST" class="space-y-8">
            <input type="password" name="password" placeholder="ENTER ACCESS CODE" class="w-full bg-slate-50 p-6 rounded-[2rem] text-center font-black text-2xl" required>
            <button class="bg-indigo-600 text-white w-full py-6 rounded-[2rem] font-black text-xl shadow-xl">Authenticate</button>
        </form>
    </div>
    """
    return render_template_string(f"<!DOCTYPE html><html><head>{BASE_CSS}</head><body class='bg-slate-100'>{content}</body></html>")

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    stats = {"apps": apps_col.count_documents({}), "ads": ads_col.count_documents({}), "featured": apps_col.count_documents({"featured": "on"})}
    content = """
    <h1 class="text-5xl md:text-6xl font-black text-slate-950 mb-12 uppercase italic">Dashboard Overview</h1>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-12 mb-20">
        <div class="bg-indigo-600 p-12 rounded-[4rem] text-white shadow-2xl">
            <div class="text-8xl font-black">{{ stats.apps }}</div>
            <p class="font-black uppercase opacity-70">Total Apps</p>
        </div>
        <div class="bg-slate-950 p-12 rounded-[4rem] text-white shadow-2xl">
            <div class="text-8xl font-black">{{ stats.ads }}</div>
            <p class="font-black uppercase opacity-70">Ad Units</p>
        </div>
        <div class="bg-orange-500 p-12 rounded-[4rem] text-white shadow-2xl">
            <div class="text-8xl font-black">{{ stats.featured }}</div>
            <p class="font-black uppercase opacity-70">Featured</p>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, stats=stats, is_admin_route=True, active="dashboard")

@app.route('/admin/apps', methods=['GET', 'POST'])
def admin_apps():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        apps_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo'), "category": request.form.get('category'), "release_date": request.form.get('release_date'), "version": request.form.get('version'), "info": request.form.get('info'), "download_link": request.form.get('download_link'), "featured": request.form.get('featured'), "created_at": datetime.now()})
        flash("App published successfully.")
        return redirect('/admin/apps')
    apps = list(apps_col.find().sort('_id', -1))
    content = """
    <h1 class="text-5xl md:text-6xl font-black mb-16 uppercase italic">Apps Manager</h1>
    <div class="grid xl:grid-cols-12 gap-16">
        <div class="xl:col-span-4 bg-white p-12 rounded-[4rem] border shadow-2xl h-fit">
            <form method="POST" class="space-y-6">
                <input name="name" placeholder="Name" class="w-full" required>
                <input name="logo" placeholder="Logo Link" class="w-full" required>
                <input type="date" name="release_date" class="w-full" required>
                <input name="version" placeholder="v1.0" class="w-full" required>
                <select name="category" class="w-full"><option>Mobile (Android)</option><option>iOS (Apple)</option><option>Desktop (PC)</option></select>
                <textarea name="info" placeholder="Info" class="w-full h-32" required></textarea>
                <input name="download_link" placeholder="Download Link" class="w-full" required>
                <label class="flex items-center gap-4"><input type="checkbox" name="featured"> Slider Highlight</label>
                <button class="btn-main w-full justify-center">SAVE APP</button>
            </form>
        </div>
        <div class="xl:col-span-8 bg-white rounded-[4rem] border shadow-2xl overflow-hidden overflow-x-auto">
            <table class="w-full text-left min-w-[500px]">
                <thead class="bg-slate-900 text-white"><tr><th class="p-8">App Info</th><th class="p-8 text-right">Action</th></tr></thead>
                <tbody>
                    {% for a in apps %}
                    <tr class="border-b"><td class="p-8 flex items-center gap-4"><img src="{{a.logo}}" class="w-16 h-16 rounded-2xl"> <b>{{a.name}}</b></td><td class="p-8 text-right"><a href="/del/app/{{a._id}}" class="text-red-500 font-bold">REMOVE</a></td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, apps=apps, is_admin_route=True, active="apps")

@app.route('/admin/ads', methods=['GET', 'POST'])
def admin_ads():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        ads_col.insert_one({"name": request.form.get('name'), "code": request.form.get('code'), "created_at": datetime.now()})
        flash("Ad deployed.")
        return redirect('/admin/ads')
    ads_list = list(ads_col.find())
    content = """
    <h1 class="text-5xl md:text-6xl font-black mb-16 uppercase italic">Ads Manager</h1>
    <div class="grid lg:grid-cols-2 gap-16">
        <div class="bg-white p-12 rounded-[4rem] border shadow-2xl h-fit">
            <form method="POST" class="space-y-6"><input name="name" placeholder="Ad Name" class="w-full" required><textarea name="code" placeholder="Script Code" class="w-full h-80" required></textarea><button class="btn-main w-full justify-center">DEPLOY</button></form>
        </div>
        <div class="space-y-8">{% for ad in ads %}<div class="p-8 bg-white border rounded-[3rem] flex justify-between shadow-sm"><b>{{ ad.name }}</b> <a href="/del/ad/{{ad._id}}" class="text-red-500 font-bold">DEL</a></div>{% endfor %}</div>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, ads=ads_list, is_admin_route=True, active="ads")

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_info()
    if request.method == 'POST':
        settings_col.update_one({"type": "shortener"}, {"$set": {"url": request.form.get('url'), "api": request.form.get('api')}}, upsert=True)
        flash("API Settings Updated.")
        return redirect('/admin/settings')
    cfg = get_shortener()
    content = """
    <h1 class="text-5xl md:text-6xl font-black mb-16 uppercase italic">Shortener API</h1>
    <div class="bg-slate-950 p-12 md:p-20 rounded-[4rem] text-white">
        <form method="POST" class="space-y-8">
            <input name="url" value="{{cfg.url}}" placeholder="domain.xyz" class="w-full bg-slate-900 border-slate-800 text-white font-bold">
            <input name="api" value="{{cfg.api}}" placeholder="API Key" class="w-full bg-slate-900 border-slate-800 text-white font-bold">
            <button class="w-full bg-emerald-500 py-6 rounded-[2rem] text-black font-black text-xl">UPDATE API</button>
        </form>
    </div>
    """
    return render_template_string(BASE_LAYOUT.replace('{% block admin_content %}{% endblock %}', content), site=site, cfg=cfg, is_admin_route=True, active="settings")

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        if request.form.get('key') == RECOVERY_KEY:
            users_col.update_one({"username": "admin"}, {"$set": {"password": generate_password_hash(request.form.get('pw'))}}, upsert=True)
            flash("System Password Recovered!")
            return redirect('/admin-gate')
    content = """
    <div class="max-w-xl mx-auto mt-32 bg-white p-20 rounded-[5rem] shadow-2xl text-center">
        <form method="POST" class="space-y-8">
            <input name="key" placeholder="RECOVERY KEY" class="w-full" required>
            <input type="password" name="pw" placeholder="NEW PASSWORD" class="w-full" required>
            <button class="bg-red-600 text-white w-full py-6 rounded-[2rem] font-black uppercase">RECOVER ACCESS</button>
        </form>
    </div>
    """
    return render_template_string(f"<!DOCTYPE html><html><head>{BASE_CSS}</head><body>{content}</body></html>")

@app.route('/del/<type>/<id>')
def delete_entry(type, id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    if type == 'app': apps_col.delete_one({"_id": ObjectId(id)})
    if type == 'ad': ads_col.delete_one({"_id": ObjectId(id)})
    flash("Deleted successfully.")
    return redirect(request.referrer)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- DEPLOYMENT HANDLER ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
