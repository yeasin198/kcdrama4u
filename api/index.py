import os
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "super-secret-key-pro-max-2024-v5")
RECOVERY_KEY = os.environ.get("RECOVERY_KEY", "admin@2024")

# --- MongoDB কানেকশন ও কালেকশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster"
client = MongoClient(MONGO_URI)
db = client['app_hub_production_final']
apps_col = db['apps']
users_col = db['users']
ads_col = db['ads']
settings_col = db['settings']

# --- গ্লোবাল ফাংশন: সাইটের তথ্য ও বিজ্ঞাপন ---
def get_site_data():
    info = settings_col.find_one({"type": "site_info"})
    if not info:
        return {"name": "APPHUB", "title": "Ultimate Pro App Store", "logo": "https://cdn-icons-png.flaticon.com/512/2589/2589127.png"}
    return info

def get_ads():
    return list(ads_col.find())

# --- প্রোফেশনাল ডিজাইন (CSS & UI লজিক) ---
UI_STYLE = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.css" />
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');
    body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }
    .glass-nav { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(226, 232, 240, 0.8); }
    .card-gradient { background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%); border: 1px solid #e2e8f0; transition: all 0.4s ease; }
    .card-gradient:hover { transform: translateY(-10px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); border-color: #6366f1; }
    .sidebar-item { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-radius: 16px; transition: 0.3s; color: #94a3b8; font-weight: 600; }
    .sidebar-item:hover { background: rgba(99, 102, 241, 0.1); color: #6366f1; }
    .sidebar-active { background: #6366f1 !important; color: white !important; box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4); }
    .swiper-slide { border-radius: 30px; overflow: hidden; display: flex; align-items: center; justify-content: center; }
    .btn-pro { background: #6366f1; color: white; padding: 12px 24px; border-radius: 14px; font-weight: 700; transition: 0.3s; display: inline-flex; align-items: center; gap: 8px; }
    .btn-pro:hover { background: #4f46e5; transform: scale(1.05); box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3); }
    .info-badge { background: rgba(99, 102, 241, 0.1); color: #6366f1; padding: 4px 12px; border-radius: 100px; font-size: 11px; font-weight: 800; text-transform: uppercase; }
    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
"""

# --- মেইন লেআউট ---
def get_layout(content, is_admin=False, active_page=""):
    site = get_site_data()
    if is_admin:
        return render_template_string(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Dashboard | {site['name']}</title>
            {UI_STYLE}
        </head>
        <body class="bg-slate-50 flex min-h-screen">
            <!-- Sidebar -->
            <div class="w-80 bg-white border-r p-6 flex flex-col h-screen sticky top-0">
                <div class="flex items-center gap-3 mb-10 px-2">
                    <img src="{site['logo']}" class="w-10 h-10 rounded-xl">
                    <span class="text-2xl font-extrabold tracking-tighter text-slate-900 uppercase">{site['name']}</span>
                </div>
                <div class="flex-1 space-y-2">
                    <a href="/admin/dashboard" class="sidebar-item {'sidebar-active' if active_page == 'dashboard' else ''}"><i class="fas fa-home"></i> Dashboard</a>
                    <a href="/admin/apps" class="sidebar-item {'sidebar-active' if active_page == 'apps' else ''}"><i class="fas fa-box"></i> Manage Apps</a>
                    <a href="/admin/ads" class="sidebar-item {'sidebar-active' if active_page == 'ads' else ''}"><i class="fas fa-ad"></i> Ad Manager</a>
                    <a href="/admin/settings" class="sidebar-item {'sidebar-active' if active_page == 'settings' else ''}"><i class="fas fa-cog"></i> Site Settings</a>
                </div>
                <div class="pt-6 border-t space-y-3">
                    <a href="/" class="sidebar-item text-emerald-500"><i class="fas fa-external-link-alt"></i> View Site</a>
                    <a href="/logout" class="sidebar-item text-red-500"><i class="fas fa-sign-out-alt"></i> Logout</a>
                </div>
            </div>
            <!-- Main Content -->
            <div class="flex-1 p-10 overflow-y-auto">
                <div class="max-w-6xl mx-auto">
                    {% with messages = get_flashed_messages() %}{% for msg in messages %}
                        <div class="bg-indigo-600 text-white p-5 rounded-2xl mb-8 shadow-xl animate-bounce flex justify-between">
                            <span><b>Success:</b> {msg}</span>
                            <button onclick="this.parentElement.remove()">×</button>
                        </div>
                    {% endfor %}{% endwith %}
                    {content}
                </div>
            </div>
        </body>
        </html>
        """)
    else:
        return render_template_string(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{site['name']} - {site['title']}</title>
            {UI_STYLE}
        </head>
        <body class="bg-slate-50">
            <nav class="glass-nav h-20 sticky top-0 z-50">
                <div class="container mx-auto px-6 h-full flex items-center justify-between">
                    <a href="/" class="flex items-center gap-3">
                        <img src="{site['logo']}" class="w-10 h-10 rounded-xl">
                        <span class="text-2xl font-black text-slate-900 uppercase tracking-tighter">{site['name']}</span>
                    </a>
                    <div class="hidden md:flex items-center gap-8">
                        <form action="/" method="GET" class="bg-slate-100 rounded-2xl px-5 py-2.5 flex items-center border border-slate-200 focus-within:border-indigo-500 transition">
                            <input type="text" name="q" placeholder="Search for apps..." class="bg-transparent outline-none text-sm w-72 text-slate-600">
                            <button type="submit"><i class="fas fa-search text-slate-400"></i></button>
                        </form>
                    </div>
                    <div class="text-xs font-bold text-slate-400">PRO STORE V5</div>
                </div>
            </nav>
            <div class="container mx-auto px-6 py-10">
                {% with messages = get_flashed_messages() %}{% for msg in messages %}
                    <div class="bg-indigo-100 text-indigo-700 p-5 rounded-3xl mb-8 border-l-8 border-indigo-600 shadow-sm">{msg}</div>
                {% endfor %}{% endwith %}
                {content}
            </div>
            <footer class="py-16 text-center text-slate-400 border-t mt-20">
                <p class="font-bold">&copy; {datetime.now().year} {site['name']} - Ultimate Pro Store</p>
                <p class="text-xs mt-2 uppercase tracking-widest">Designed for High Performance</p>
            </footer>
            <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
            <script>const swiper = new Swiper('.swiper', {{ loop: true, autoplay: {{ delay: 4000 }}, pagination: {{ el: '.swiper-pagination', clickable: true }} }});</script>
        </body>
        </html>
        """)

# --- ইউজার রাউটস ---

@app.route('/')
def home():
    q = request.args.get('q', '')
    site = get_site_data()
    ads = get_ads()
    
    if q:
        apps = list(apps_col.find({"name": {"$regex": q, "$options": "i"}}).sort('_id', -1))
        featured = []
    else:
        apps = list(apps_col.find().sort('_id', -1))
        featured = list(apps_col.find({"featured": "on"}).limit(5))
    
    content = """
    <!-- Pro Slider -->
    {% if featured %}
    <div class="swiper mb-16 shadow-2xl">
        <div class="swiper-wrapper">
            {% for f in featured %}
            <div class="swiper-slide bg-slate-900 h-[450px] relative">
                <div class="absolute inset-0 bg-gradient-to-r from-indigo-900 to-transparent opacity-90 z-10"></div>
                <div class="relative z-20 px-16 flex items-center h-full w-full">
                    <div class="max-w-2xl">
                        <span class="info-badge mb-6 inline-block bg-indigo-500 text-white">Featured Editor's Choice</span>
                        <h2 class="text-6xl font-black text-white mb-6 leading-tight">{{ f.name }}</h2>
                        <p class="text-indigo-100 text-lg mb-10 line-clamp-2 opacity-80">{{ f.info }}</p>
                        <a href="/app/{{f._id}}" class="btn-pro px-10 py-5 text-xl">View Details & Download <i class="fas fa-arrow-right"></i></a>
                    </div>
                </div>
                <img src="{{f.logo}}" class="absolute right-20 top-1/2 -translate-y-1/2 w-64 h-64 rounded-[4rem] shadow-2xl rotate-6 group-hover:rotate-0 transition duration-1000 hidden lg:block">
            </div>
            {% endfor %}
        </div>
        <div class="swiper-pagination"></div>
    </div>
    {% endif %}

    <!-- Top Ads -->
    <div class="mb-12 space-y-6">
        {% for ad in ads %}<div class="bg-white p-4 rounded-3xl border border-slate-200 flex justify-center overflow-hidden shadow-sm">{{ ad.code | safe }}</div>{% endfor %}
    </div>

    <!-- Apps Grid -->
    <div class="flex items-center justify-between mb-10 border-b pb-6">
        <h2 class="text-3xl font-extrabold text-slate-800">{% if q %}Search: "{{q}}"{% else %}Popular Applications{% endif %}</h2>
        <span class="bg-slate-200 px-4 py-1.5 rounded-full text-xs font-bold text-slate-600 uppercase">{{ apps|length }} Apps Available</span>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
        {% for app in apps %}
        <a href="/app/{{app._id}}" class="card-gradient p-8 rounded-[3rem] text-center relative group">
            <div class="relative mb-6">
                <img src="{{app.logo}}" class="w-28 h-28 rounded-[2.5rem] mx-auto shadow-2xl group-hover:scale-110 transition duration-500">
                {% if app.featured %}
                <div class="absolute -top-2 -right-2 bg-orange-500 text-white text-[10px] font-black px-3 py-1 rounded-full shadow-lg">PRO</div>
                {% endif %}
            </div>
            <h3 class="font-extrabold text-xl text-slate-800 mb-2 truncate px-2">{{app.name}}</h3>
            <div class="flex justify-center gap-2 mb-4">
                <span class="info-badge">{{app.category}}</span>
                <span class="bg-emerald-100 text-emerald-600 px-3 py-1 rounded-full text-[10px] font-bold">V {{app.version}}</span>
            </div>
            <p class="text-xs text-slate-400 line-clamp-2 h-8 mb-6">{{app.info}}</p>
            <div class="btn-pro w-full justify-center">Download Now <i class="fas fa-cloud-download-alt"></i></div>
        </a>
        {% endfor %}
    </div>
    """
    return get_layout(render_template_string(content, featured=featured, apps=apps, ads=ads, q=q))

@app.route('/app/<id>')
def details(id):
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    if not app_data: return redirect('/')
    content = f"""
    <div class="max-w-5xl mx-auto bg-white rounded-[4rem] shadow-2xl border border-slate-100 overflow-hidden">
        <div class="p-16 flex flex-col md:flex-row items-center gap-16">
            <div class="relative">
                <img src="{app_data['logo']}" class="w-72 h-72 rounded-[4.5rem] shadow-2xl">
                <div class="absolute -bottom-6 -right-6 bg-indigo-600 text-white p-6 rounded-full shadow-2xl">
                    <i class="fas fa-certificate text-3xl"></i>
                </div>
            </div>
            <div class="flex-1 text-center md:text-left">
                <div class="flex flex-wrap gap-3 mb-6 justify-center md:justify-start">
                    <span class="btn-pro bg-slate-100 text-indigo-600 border-none px-6 py-2 text-sm">{app_data['category']}</span>
                    <span class="btn-pro bg-emerald-50 text-emerald-600 border-none px-6 py-2 text-sm">Official Version {app_data['version']}</span>
                </div>
                <h1 class="text-6xl font-black text-slate-900 mb-6 leading-tight tracking-tighter">{app_data['name']}</h1>
                <p class="text-slate-500 text-xl leading-relaxed mb-10 opacity-80">{app_data['info']}</p>
                <div class="grid grid-cols-2 gap-6 mb-12">
                    <div class="bg-slate-50 p-6 rounded-3xl border">
                        <p class="text-xs font-bold text-slate-400 uppercase mb-1">Release Date</p>
                        <p class="font-bold text-slate-700">{app_data['release_date']}</p>
                    </div>
                    <div class="bg-slate-50 p-6 rounded-3xl border">
                        <p class="text-xs font-bold text-slate-400 uppercase mb-1">Platform</p>
                        <p class="font-bold text-slate-700">{app_data['category']} Device</p>
                    </div>
                </div>
                <a href="/get/{id}" class="btn-pro px-16 py-6 text-2xl w-full md:w-auto justify-center italic shadow-2xl shadow-indigo-200">
                    <i class="fas fa-download"></i> SECURE DOWNLOAD NOW
                </a>
            </div>
        </div>
    </div>
    """
    return get_layout(content)

@app.route('/get/<id>')
def download_logic(id):
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    if not app_data: return redirect('/')
    short_cfg = settings_col.find_one({"type": "shortener"})
    target = app_data['download_link']
    if short_cfg and short_cfg.get('url') and short_cfg.get('api'):
        try:
            res = requests.get(f"https://{short_cfg['url']}/api?api={short_cfg['api']}&url={target}", timeout=10).json()
            short_url = res.get('shortenedUrl') or res.get('shortedUrl')
            if short_url: return redirect(short_url)
        except: pass
    return redirect(target)

# --- এডমিন অথেন্টিকেশন ---

@app.route('/admin-gate', methods=['GET', 'POST'])
def login():
    site = get_site_data()
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
        flash("Incorrect Private Key!")
    
    content = f"""
    <div class="max-w-md mx-auto mt-32 bg-white p-16 rounded-[4rem] shadow-2xl border text-center">
        <img src="{site['logo']}" class="w-20 h-20 mx-auto mb-8 rounded-2xl shadow-lg">
        <h2 class="text-3xl font-black mb-10 text-slate-900 tracking-tighter">SECURE LOGIN</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Admin Passcode" class="w-full bg-slate-50 p-5 rounded-2xl text-center mb-8 outline-none border focus:border-indigo-500 transition-all font-bold" required>
            <button class="btn-pro w-full justify-center py-5 uppercase tracking-widest">Authenticate Access</button>
        </form>
        <div class="mt-8"><a href="/forgot" class="text-xs font-bold text-slate-400 hover:text-indigo-600 transition underline">Reset Password Key</a></div>
    </div>
    """
    return render_template_string(f"<!DOCTYPE html><html><head>{UI_STYLE}</head><body class='bg-slate-50'>{content}</body></html>")

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'): return redirect('/admin-gate')
    stats = {
        "apps": apps_col.count_documents({}),
        "ads": ads_col.count_documents({}),
        "featured": apps_col.count_documents({"featured": "on"})
    }
    content = f"""
    <div class="mb-12">
        <h1 class="text-5xl font-black text-slate-900 tracking-tighter mb-4">Dashboard Overview</h1>
        <p class="text-slate-400 font-semibold uppercase tracking-widest text-sm">Management Console</p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-10 mb-16">
        <div class="bg-indigo-600 p-10 rounded-[3rem] text-white shadow-2xl shadow-indigo-200">
            <div class="text-6xl font-black mb-4">{stats['apps']}</div>
            <div class="font-extrabold uppercase text-xs tracking-widest opacity-80">Applications Live</div>
        </div>
        <div class="bg-slate-900 p-10 rounded-[3rem] text-white shadow-2xl shadow-slate-300">
            <div class="text-6xl font-black mb-4">{stats['ads']}</div>
            <div class="font-extrabold uppercase text-xs tracking-widest opacity-80">Ad Units Integrated</div>
        </div>
        <div class="bg-orange-500 p-10 rounded-[3rem] text-white shadow-2xl shadow-orange-200">
            <div class="text-6xl font-black mb-4">{stats['featured']}</div>
            <div class="font-extrabold uppercase text-xs tracking-widest opacity-80">Home Slider Active</div>
        </div>
    </div>
    <div class="bg-white p-12 rounded-[4rem] border border-slate-100 flex items-center justify-between">
        <div class="max-w-xl">
            <h2 class="text-3xl font-black text-slate-900 mb-4">Welcome Back, Admin!</h2>
            <p class="text-slate-500 text-lg">Your server is running optimally. You can manage your apps, ads, and site branding using the sidebar on the left.</p>
        </div>
        <img src="https://cdn-icons-png.flaticon.com/512/3649/3649460.png" class="w-48 hidden lg:block opacity-20">
    </div>
    """
    return get_layout(content, is_admin=True, active_page="dashboard")

@app.route('/admin/apps', methods=['GET', 'POST'])
def admin_apps():
    if not session.get('logged_in'): return redirect('/admin-gate')
    if request.method == 'POST':
        apps_col.insert_one({
            "name": request.form.get('name'), "logo": request.form.get('logo'),
            "category": request.form.get('category'), "release_date": request.form.get('release_date'),
            "version": request.form.get('version'), "info": request.form.get('info'),
            "download_link": request.form.get('download_link'), "featured": request.form.get('featured')
        })
        flash("App Uploaded to Live Server!")
        return redirect('/admin/apps')
    
    q = request.args.get('q', '')
    apps = list(apps_col.find({"name": {"$regex": q, "$options": "i"}}).sort('_id', -1)) if q else list(apps_col.find().sort('_id', -1))
    
    content = f"""
    <div class="flex flex-col md:flex-row justify-between items-center mb-12 gap-6">
        <h1 class="text-5xl font-black text-slate-900 tracking-tighter">Application Hub</h1>
        <form class="bg-white px-8 py-3 rounded-full border-2 border-slate-100 flex items-center w-full md:w-96 focus-within:border-indigo-500 transition">
            <input type="text" name="q" placeholder="Search and manage apps..." class="bg-transparent outline-none text-sm w-full font-bold text-slate-600" value="{q}">
            <button type="submit"><i class="fas fa-search text-indigo-600"></i></button>
        </form>
    </div>
    <div class="grid lg:grid-cols-3 gap-12">
        <!-- Add Form -->
        <form method="POST" class="bg-slate-50 p-10 rounded-[3.5rem] space-y-5 border border-slate-200">
            <h2 class="text-2xl font-black mb-8 text-indigo-600 underline decoration-indigo-200 italic">Publish New App</h2>
            <input name="name" placeholder="Full Application Name" class="w-full p-5 rounded-2xl border-none outline-none focus:ring-4 ring-indigo-500/20 font-bold" required>
            <input name="logo" placeholder="Direct Logo Link (PNG/JPG URL)" class="w-full p-5 rounded-2xl border-none outline-none focus:ring-4 ring-indigo-500/20" required>
            <select name="category" class="w-full p-5 rounded-2xl border-none outline-none font-bold">
                <option>Mobile (Android)</option><option>PC / Desktop</option><option>iOS (Apple)</option>
            </select>
            <div class="flex gap-4">
                <input type="date" name="release_date" class="w-1/2 p-5 rounded-2xl border-none outline-none" required>
                <input name="version" placeholder="Version (e.g. 1.5.0)" class="w-1/2 p-5 rounded-2xl border-none outline-none font-bold" required>
            </div>
            <textarea name="info" placeholder="Write a short description about this app..." class="w-full p-5 rounded-2xl border-none outline-none h-32 focus:ring-4 ring-indigo-500/20" required></textarea>
            <input name="download_link" placeholder="Final Download Redirect Link" class="w-full p-5 rounded-2xl border-none outline-none focus:ring-4 ring-indigo-500/20" required>
            <label class="flex items-center gap-3 font-bold text-indigo-600 p-2 cursor-pointer">
                <input type="checkbox" name="featured" class="w-6 h-6 rounded-lg accent-indigo-600"> Highlight in Slider
            </label>
            <button class="btn-pro w-full justify-center py-5 uppercase text-lg tracking-widest">Publish Live App</button>
        </form>
        <!-- Table -->
        <div class="lg:col-span-2 bg-white rounded-[3.5rem] border border-slate-100 overflow-hidden shadow-sm">
            <table class="w-full text-left">
                <thead class="bg-slate-50 border-b">
                    <tr><th class="p-6 font-bold text-slate-400 uppercase text-xs tracking-widest">Live Apps</th><th class="p-6 text-right font-bold text-slate-400 uppercase text-xs tracking-widest">Operations</th></tr>
                </thead>
                <tbody>
                    {{% for a in apps %}}
                    <tr class="border-b last:border-0 hover:bg-slate-50 transition duration-300">
                        <td class="p-6 flex items-center gap-6">
                            <img src="{{{{a.logo}}}}" class="w-14 h-14 rounded-2xl shadow-xl">
                            <div>
                                <p class="font-extrabold text-slate-800 text-lg mb-1 leading-none">{{{{a.name}}}}</p>
                                <div class="flex items-center gap-2">
                                    <span class="text-[9px] font-black bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded uppercase">{{{{a.category}}}}</span>
                                    {{% if a.featured %}}<span class="text-[9px] font-black bg-orange-500 text-white px-2 py-0.5 rounded uppercase">Slider Active</span>{{% endif %}}
                                </div>
                            </div>
                        </td>
                        <td class="p-6 text-right">
                            <a href="/del/app/{{{{a._id}}}}" class="text-red-500 font-black text-sm bg-red-50 px-6 py-3 rounded-2xl hover:bg-red-500 hover:text-white transition duration-300" onclick="return confirm('WARNING: Are you sure you want to delete this app permanently?')">REMOVE APP</a>
                        </td>
                    </tr>
                    {{% endfor %}}
                </tbody>
            </table>
        </div>
    </div>
    """
    return get_layout(render_template_string(content, apps=apps, q=q), is_admin=True, active_page="apps")

@app.route('/admin/ads', methods=['GET', 'POST'])
def admin_ads():
    if not session.get('logged_in'): return redirect('/admin-gate')
    if request.method == 'POST':
        ads_col.insert_one({"name": request.form.get('name'), "code": request.form.get('code')})
        flash("Ad Script Successfully Deployed!")
        return redirect('/admin/ads')
    ads = list(ads_col.find())
    content = f"""
    <div class="mb-12">
        <h1 class="text-5xl font-black text-slate-900 tracking-tighter mb-4">Advertisement Manager</h1>
        <p class="text-slate-400 font-semibold uppercase tracking-widest text-sm">Monetization Control</p>
    </div>
    <div class="grid lg:grid-cols-3 gap-12">
        <form method="POST" class="bg-slate-50 p-10 rounded-[3.5rem] space-y-5 border border-slate-200">
            <h2 class="text-2xl font-black mb-8 text-emerald-600 underline decoration-emerald-200 italic">Inject New Ad</h2>
            <input name="name" placeholder="Ad Spot Identity (e.g. Header)" class="w-full p-5 rounded-2xl border-none outline-none font-bold" required>
            <textarea name="code" placeholder="Paste full Ad Script (HTML/JS) here..." class="w-full p-5 rounded-2xl border-none outline-none h-64 font-mono text-xs focus:ring-4 ring-emerald-500/20" required></textarea>
            <button class="btn-pro w-full justify-center py-5 bg-emerald-600 hover:bg-emerald-700 uppercase tracking-widest">Deploy Ad Script</button>
        </form>
        <div class="lg:col-span-2 space-y-6">
            <h2 class="text-2xl font-black text-slate-800 mb-6">Active Ad Units ({{ ads|length }})</h2>
            {{% for ad in ads %}}
            <div class="flex justify-between items-center p-8 bg-white border border-slate-100 rounded-[2.5rem] shadow-sm hover:shadow-xl transition">
                <div class="flex items-center gap-6">
                    <div class="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center text-xl"><i class="fas fa-ad"></i></div>
                    <div>
                        <p class="font-black text-slate-800 text-xl mb-1 leading-none">{{{{ad.name}}}}</p>
                        <p class="text-xs font-bold text-emerald-500 uppercase">Script Active & Live</p>
                    </div>
                </div>
                <a href="/del/ad/{{{{ad._id}}}}" class="text-red-500 font-black text-sm bg-red-50 px-8 py-3 rounded-2xl hover:bg-red-500 hover:text-white transition">DISABLE UNIT</a>
            </div>
            {{% endfor %}}
        </div>
    </div>
    """
    return get_layout(render_template_string(content, ads=ads), is_admin=True, active_page="ads")

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('logged_in'): return redirect('/admin-gate')
    site = get_site_data()
    if request.method == 'POST':
        f_type = request.form.get('form_type')
        if f_type == "site_info":
            settings_col.update_one({"type": "site_info"}, {"$set": {"name": request.form.get('site_name'), "title": request.form.get('site_title'), "logo": request.form.get('site_logo')}}, upsert=True)
            flash("Site Branding Updated & Deployed!")
        elif f_type == "shortener":
            settings_col.update_one({"type": "shortener"}, {"$set": {"url": request.form.get('url'), "api": request.form.get('api')}}, upsert=True)
            flash("Link Shortener API Configured!")
        return redirect('/admin/settings')
    
    cfg = settings_col.find_one({"type": "shortener"}) or {}
    content = f"""
    <div class="mb-12">
        <h1 class="text-5xl font-black text-slate-900 tracking-tighter mb-4">System Settings</h1>
        <p class="text-slate-400 font-semibold uppercase tracking-widest text-sm">Site Branding & Backend APIs</p>
    </div>
    <div class="grid md:grid-cols-2 gap-12">
        <!-- Site Branding -->
        <div class="bg-slate-50 p-12 rounded-[4rem] border border-slate-200">
            <h2 class="text-3xl font-black mb-10 text-indigo-700 underline decoration-indigo-200">Site Branding</h2>
            <form method="POST" class="space-y-6">
                <input type="hidden" name="form_type" value="site_info">
                <div>
                    <label class="text-[10px] font-black text-slate-400 uppercase ml-2 tracking-widest">Brand Name</label>
                    <input name="site_name" value="{site['name']}" placeholder="Site Identity" class="w-full p-5 rounded-2xl border-none font-black text-xl uppercase tracking-tighter" required>
                </div>
                <div>
                    <label class="text-[10px] font-black text-slate-400 uppercase ml-2 tracking-widest">Meta Title Tag</label>
                    <input name="site_title" value="{site['title']}" placeholder="Ultimate Store SEO Title" class="w-full p-5 rounded-2xl border-none" required>
                </div>
                <div>
                    <label class="text-[10px] font-black text-slate-400 uppercase ml-2 tracking-widest">Brand Icon URL (PNG)</label>
                    <input name="site_logo" value="{site['logo']}" placeholder="Link to Logo" class="w-full p-5 rounded-2xl border-none" required>
                </div>
                <button class="btn-pro w-full justify-center py-5 shadow-2xl shadow-indigo-200">Update Branding & Assets</button>
            </form>
        </div>
        <!-- Link Shortener -->
        <div class="bg-slate-50 p-12 rounded-[4rem] border border-slate-200">
            <h2 class="text-3xl font-black mb-10 text-orange-600 underline decoration-orange-200">Link Shortener</h2>
            <form method="POST" class="space-y-6">
                <input type="hidden" name="form_type" value="shortener">
                <div>
                    <label class="text-[10px] font-black text-slate-400 uppercase ml-2 tracking-widest">API Domain</label>
                    <input name="url" value="{cfg.get('url','')}" placeholder="e.g. sjjdjdjdjdj.xyz" class="w-full p-5 rounded-2xl border-none font-bold" required>
                </div>
                <div>
                    <label class="text-[10px] font-black text-slate-400 uppercase ml-2 tracking-widest">Personal API Token</label>
                    <input type="password" name="api" value="{cfg.get('api','')}" placeholder="Secret API Access Key" class="w-full p-5 rounded-2xl border-none" required>
                </div>
                <button class="btn-pro w-full justify-center py-5 bg-orange-600 hover:bg-orange-700 shadow-2xl shadow-orange-200">Apply API Integration</button>
            </form>
            <p class="mt-8 text-center text-xs text-slate-400 font-bold uppercase tracking-widest">Redirect System Powered by Admin API</p>
        </div>
    </div>
    """
    return get_layout(content, is_admin=True, active_page="settings")

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        if request.form.get('key') == RECOVERY_KEY:
            users_col.update_one({"username": "admin"}, {"$set": {"password": generate_password_hash(request.form.get('pw'))}}, upsert=True)
            flash("System Override Successful! Secure the new password.")
            return redirect('/admin-gate')
        flash("Unauthorized Access: Recovery Key Failed!")
    content = f"""
    <div class="max-w-md mx-auto mt-32 bg-white p-16 rounded-[4rem] shadow-2xl border border-red-100 text-center">
        <h2 class="text-3xl font-black mb-10 text-red-600 tracking-tighter italic uppercase underline">Critical Override</h2>
        <form method="POST" class="space-y-5">
            <input name="key" placeholder="System Recovery Key" class="w-full p-5 border-none bg-slate-50 rounded-2xl outline-none focus:ring-4 ring-red-500/20 text-center" required>
            <input type="password" name="pw" placeholder="New Master Password" class="w-full p-5 border-none bg-slate-50 rounded-2xl outline-none focus:ring-4 ring-red-500/20 text-center" required>
            <button class="btn-pro w-full justify-center py-5 bg-red-600 hover:bg-red-700 shadow-2xl shadow-red-200 uppercase tracking-widest">Update Master System</button>
        </form>
    </div>
    """
    return render_template_string(f"<!DOCTYPE html><html><head>{UI_STYLE}</head><body class='bg-slate-50'>{content}</body></html>")

@app.route('/del/<type>/<id>')
def delete(type, id):
    if not session.get('logged_in'): return redirect('/admin-gate')
    if type == 'app': apps_col.delete_one({"_id": ObjectId(id)})
    if type == 'ad': ads_col.delete_one({"_id": ObjectId(id)})
    flash("Permanent Removal Complete.")
    return redirect(request.referrer)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Vercel Handler
handler = app
if __name__ == '__main__':
    app.run(debug=True)
