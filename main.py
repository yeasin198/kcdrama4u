from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import requests

app = Flask(__name__)

# --- সিকিউরিটি কনফিগারেশন ---
# Vercel Environment Variables থেকে আসবে, না থাকলে ডিফল্ট কাজ করবে
app.secret_key = os.environ.get("SESSION_SECRET", "my_super_secret_112233")
RECOVERY_KEY = os.environ.get("RECOVERY_KEY", "admin@123")

# --- MongoDB কানেকশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster"
client = MongoClient(MONGO_URI)
db = client['app_directory_v2']
apps_collection = db['apps']
users_collection = db['users']
ads_collection = db['ads']
settings_collection = db['settings']

# --- HTML লেআউট (Tailwind CSS) ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>App Hub - Premium Downloads</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-slate-50 text-slate-800">
    <nav class="bg-indigo-700 text-white shadow-xl sticky top-0 z-50">
        <div class="container mx-auto px-4 py-3 flex justify-between items-center">
            <a href="/" class="text-2xl font-black tracking-tighter">APP<span class="text-indigo-300">HUB</span></a>
            <div class="flex items-center space-x-4">
                <a href="/" class="font-medium hover:text-indigo-200 transition">Home</a>
                {% if session.get('logged_in') %}
                    <a href="/admin" class="text-sm bg-indigo-800 px-3 py-1.5 rounded-lg hover:bg-indigo-900">Apps</a>
                    <a href="/admin/ads" class="text-sm bg-indigo-800 px-3 py-1.5 rounded-lg hover:bg-indigo-900">Ads</a>
                    <a href="/admin/settings" class="text-sm bg-indigo-800 px-3 py-1.5 rounded-lg hover:bg-indigo-900">API</a>
                    <a href="/logout" class="text-sm bg-red-500 px-3 py-1.5 rounded-lg hover:bg-red-600">Logout</a>
                {% else %}
                    <a href="/login" class="bg-white text-indigo-700 px-4 py-1.5 rounded-lg font-bold shadow-sm">Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mx-auto px-4 py-8">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for msg in messages %}
                <div class="mb-6 p-4 rounded-xl bg-indigo-100 border-l-4 border-indigo-500 text-indigo-800 shadow-sm animate-pulse">
                    {{ msg }}
                </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <footer class="text-center py-10 text-slate-400 text-sm">
        &copy; 2024 App Hub Directory. All Rights Reserved.
    </div>
</body>
</html>
"""

# --- রুটস (Routes) ---

@app.route('/')
def index():
    apps = list(apps_collection.find().sort('_id', -1))
    all_ads = list(ads_collection.find())
    
    home_content = """
    <!-- Ads Section Top -->
    <div class="max-w-4xl mx-auto mb-8 space-y-4">
        {% for ad in ads %}
            <div class="bg-white p-2 rounded shadow-sm flex justify-center overflow-hidden">
                {{ ad.code | safe }}
            </div>
        {% endfor %}
    </div>

    <h1 class="text-2xl font-bold mb-6 flex items-center gap-2">
        <i class="fas fa-fire text-orange-500"></i> Featured Applications
    </h1>
    
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {% for app in apps %}
        <div class="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 hover:shadow-xl transition-all duration-300 group">
            <div class="flex flex-col items-center">
                <img src="{{app.logo}}" class="w-20 h-20 rounded-2xl shadow-md mb-4 group-hover:scale-110 transition-transform">
                <h3 class="font-bold text-lg text-center line-clamp-1">{{app.name}}</h3>
                <div class="flex gap-2 my-2">
                    <span class="text-[10px] font-bold bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full uppercase">{{app.category}}</span>
                    <span class="text-[10px] font-bold bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full uppercase">v{{app.version}}</span>
                </div>
                <p class="text-xs text-slate-400 text-center mb-4 line-clamp-2 h-8">{{app.info}}</p>
                <a href="/download/{{app._id}}" class="w-full bg-slate-900 text-white text-center py-3 rounded-2xl font-bold hover:bg-indigo-700 shadow-lg shadow-indigo-100 transition">
                    <i class="fas fa-download mr-1 text-sm"></i> Download
                </a>
            </div>
        </div>
        {% endfor %}
    </div>
    """
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', home_content), apps=apps, ads=all_ads)

@app.route('/download/<id>')
def download_handler(id):
    app_data = apps_collection.find_one({"_id": ObjectId(id)})
    if not app_data: return "App Not Found", 404
    
    target_url = app_data['download_link']
    short_set = settings_collection.find_one({"type": "shortener"})
    
    if short_set and short_set.get('url') and short_set.get('api'):
        try:
            # Shortener API Call
            api_req = f"https://{short_set['url']}/api?api={short_set['api']}&url={target_url}"
            res = requests.get(api_req, timeout=5).json()
            if res.get('shortenedUrl'): return redirect(res['shortenedUrl'])
            if res.get('shortedUrl'): return redirect(res['shortedUrl'])
        except:
            pass
            
    return redirect(target_url)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    if request.method == 'POST':
        apps_collection.insert_one({
            "name": request.form.get('name'), "logo": request.form.get('logo'),
            "category": request.form.get('category'), "release_date": request.form.get('release_date'),
            "version": request.form.get('version'), "info": request.form.get('info'),
            "download_link": request.form.get('download_link'), "created_at": datetime.now()
        })
        flash("App Published Successfully!")
        return redirect(url_for('admin'))
    
    apps = list(apps_collection.find().sort('_id', -1))
    admin_content = """
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="bg-white p-6 rounded-3xl shadow-sm border">
            <h2 class="text-xl font-bold mb-6 text-indigo-700">Add New App</h2>
            <form method="POST" class="space-y-4">
                <input type="text" name="name" placeholder="Application Name" class="w-full border-slate-200 border p-3 rounded-xl outline-none focus:border-indigo-500" required>
                <input type="text" name="logo" placeholder="Logo Image URL" class="w-full border-slate-200 border p-3 rounded-xl outline-none focus:border-indigo-500" required>
                <select name="category" class="w-full border-slate-200 border p-3 rounded-xl outline-none">
                    <option>Mobile</option><option>Desktop</option><option>iOS</option>
                </select>
                <div class="flex gap-2">
                    <input type="date" name="release_date" class="w-1/2 border-slate-200 border p-3 rounded-xl text-sm" required>
                    <input type="text" name="version" placeholder="Version" class="w-1/2 border-slate-200 border p-3 rounded-xl" required>
                </div>
                <textarea name="info" placeholder="Short Description..." class="w-full border-slate-200 border p-3 rounded-xl h-24 outline-none focus:border-indigo-500" required></textarea>
                <input type="text" name="download_link" placeholder="Direct Download Link" class="w-full border-slate-200 border p-3 rounded-xl outline-none focus:border-indigo-500" required>
                <button class="w-full bg-indigo-600 text-white py-4 rounded-2xl font-bold hover:bg-indigo-700 transition shadow-lg shadow-indigo-100">Publish App</button>
            </form>
        </div>
        <div class="lg:col-span-2">
            <div class="bg-white rounded-3xl shadow-sm border overflow-hidden">
                <table class="w-full text-left">
                    <thead class="bg-slate-50">
                        <tr><th class="p-4 font-bold text-slate-500">App Details</th><th class="p-4 font-bold text-slate-500">Platform</th><th class="p-4 text-right">Action</th></tr>
                    </thead>
                    <tbody>
                        {% for app in apps %}
                        <tr class="border-t border-slate-50">
                            <td class="p-4 flex items-center gap-3">
                                <img src="{{app.logo}}" class="w-10 h-10 rounded-lg">
                                <div><p class="font-bold text-slate-700 leading-none">{{app.name}}</p><small class="text-slate-400">v{{app.version}}</small></div>
                            </td>
                            <td class="p-4"><span class="bg-slate-100 text-slate-600 px-2 py-1 rounded text-[10px] font-bold">{{app.category}}</span></td>
                            <td class="p-4 text-right"><a href="/delete/app/{{app._id}}" class="text-red-500 hover:bg-red-50 px-3 py-2 rounded-lg transition" onclick="return confirm('Delete App?')"><i class="fas fa-trash"></i></a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', admin_content), apps=apps)

@app.route('/admin/ads', methods=['GET', 'POST'])
def ads_manager():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        ads_collection.insert_one({"name": request.form.get('name'), "code": request.form.get('code'), "created_at": datetime.now()})
        flash("Ad Code Integrated!")
    all_ads = list(ads_collection.find().sort('_id', -1))
    ads_content = """
    <div class="max-w-3xl mx-auto">
        <div class="bg-white p-8 rounded-3xl shadow-sm border mb-8">
            <h2 class="text-xl font-bold mb-6">Unlimited Ads Manager</h2>
            <form method="POST" class="space-y-4">
                <input type="text" name="name" placeholder="Ad Name (e.g. Adsterra 728x90)" class="w-full border-slate-200 border p-3 rounded-xl outline-none" required>
                <textarea name="code" placeholder="Paste Script Code / HTML / JS here..." class="w-full border-slate-200 border p-3 rounded-xl h-40 font-mono text-sm" required></textarea>
                <button class="bg-indigo-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-indigo-700 transition">Save Ad Code</button>
            </form>
        </div>
        <div class="bg-white rounded-3xl shadow-sm border overflow-hidden">
            {% for ad in ads %}
            <div class="flex justify-between items-center p-5 border-b last:border-0">
                <div><p class="font-bold text-slate-700">{{ad.name}}</p><small class="text-slate-400">Status: Active</small></div>
                <a href="/delete/ad/{{ad._id}}" class="bg-red-50 text-red-500 px-4 py-2 rounded-xl text-xs font-bold hover:bg-red-100">Remove</a>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', ads_content), ads=all_ads)

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings_manager():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        settings_collection.update_one({"type": "shortener"}, {"$set": {"url": request.form.get('url'), "api": request.form.get('api')}}, upsert=True)
        flash("API Settings Updated!")
    curr = settings_collection.find_one({"type": "shortener"}) or {}
    set_content = """
    <div class="max-w-md mx-auto bg-white p-8 rounded-3xl shadow-sm border">
        <h2 class="text-xl font-bold mb-6"><i class="fas fa-link mr-2"></i>Link Shortener API</h2>
        <form method="POST" class="space-y-4">
            <div><label class="text-xs font-bold text-slate-400 uppercase ml-1">Shortener Domain</label>
            <input type="text" name="url" value="{{curr.url}}" placeholder="e.g. shrinkme.io" class="w-full border-slate-200 border p-3 rounded-xl outline-none focus:border-indigo-500" required></div>
            <div><label class="text-xs font-bold text-slate-400 uppercase ml-1">Personal API Key</label>
            <input type="password" name="api" value="{{curr.api}}" placeholder="your_api_token" class="w-full border-slate-200 border p-3 rounded-xl outline-none focus:border-indigo-500" required></div>
            <button class="w-full bg-slate-900 text-white py-4 rounded-2xl font-bold shadow-lg">Update API Settings</button>
        </form>
    </div>
    """
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', set_content), curr=curr)

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = users_collection.find_one({"username": "admin"})
    if request.method == 'POST':
        pw = request.form.get('password')
        if not user:
            users_collection.insert_one({"username": "admin", "password": generate_password_hash(pw)})
            flash("Admin Created! Logging you in...")
            session['logged_in'] = True
            return redirect(url_for('admin'))
        if check_password_hash(user['password'], pw):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        flash("Wrong Admin Password!")
    login_html = """
    <div class="max-w-sm mx-auto mt-16 bg-white p-8 rounded-3xl shadow-2xl border border-indigo-50">
        <h2 class="text-2xl font-black text-center mb-8 text-indigo-700 underline decoration-indigo-200">ADMIN ACCESS</h2>
        <form method="POST" class="space-y-5">
            <input type="password" name="password" placeholder="Enter Access Code" class="w-full border-slate-200 border p-4 rounded-2xl outline-none focus:ring-2 ring-indigo-500 text-center" required>
            <button class="w-full bg-indigo-600 text-white py-4 rounded-2xl font-bold shadow-indigo-200 shadow-xl">LOG IN</button>
        </form>
        <div class="mt-8 text-center"><a href="/forgot" class="text-xs text-slate-400 hover:text-indigo-600 transition">Trouble Logging In?</a></div>
    </div>
    """
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', login_html))

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        if request.form.get('key') == RECOVERY_KEY:
            users_collection.update_one({"username": "admin"}, {"$set": {"password": generate_password_hash(request.form.get('pw'))}}, upsert=True)
            flash("Password Reset Successful!")
            return redirect(url_for('login'))
        flash("Invalid Recovery Key!")
    forgot_html = """
    <div class="max-w-sm mx-auto mt-16 bg-white p-8 rounded-3xl shadow-2xl border border-red-50">
        <h2 class="text-2xl font-black text-center mb-8 text-red-600">RESET SYSTEM</h2>
        <form method="POST" class="space-y-5">
            <input type="text" name="key" placeholder="System Recovery Key" class="w-full border-slate-200 border p-4 rounded-2xl outline-none focus:ring-2 ring-red-500" required>
            <input type="password" name="pw" placeholder="New Admin Password" class="w-full border-slate-200 border p-4 rounded-2xl outline-none focus:ring-2 ring-red-500" required>
            <button class="w-full bg-red-600 text-white py-4 rounded-2xl font-bold shadow-red-200 shadow-xl">OVERRIDE PASSWORD</button>
        </form>
    </div>
    """
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', forgot_html))

@app.route('/delete/<type>/<id>')
def delete_logic(type, id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    if type == 'app': apps_collection.delete_one({"_id": ObjectId(id)})
    if type == 'ad': ads_collection.delete_one({"_id": ObjectId(id)})
    flash("Entry Deleted!")
    return redirect(request.referrer)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('index'))

# --- Vercel Export ---
def handler(request):
    return app(request)

if __name__ == '__main__':
    app.run(debug=True)
