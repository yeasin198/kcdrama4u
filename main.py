import os
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- কনফিগারেশন ---
# ভেরিয়েবলগুলো না পেলে ডিফল্ট মান ব্যবহার হবে
app.secret_key = os.environ.get("SESSION_SECRET", "any_random_secret_string_123")
RECOVERY_KEY = os.environ.get("RECOVERY_KEY", "admin@reset")

# MongoDB কানেকশন
try:
    MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster"
    client = MongoClient(MONGO_URI)
    db = client['app_store_database']
    apps_col = db['apps']
    users_col = db['users']
    ads_col = db['ads']
    settings_col = db['settings']
except Exception as e:
    print(f"Database Connection Error: {e}")

# --- ডিজাইন (HTML) ---
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>App Hub Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-50 text-gray-900">
    <nav class="bg-indigo-700 p-4 text-white shadow-lg">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-2xl font-black">APP<span class="text-indigo-300">HUB</span></a>
            <div class="space-x-4 flex items-center text-xs font-bold uppercase">
                <a href="/">Home</a>
                {% if session.get('logged_in') %}
                    <a href="/admin">Apps</a>
                    <a href="/admin/ads">Ads</a>
                    <a href="/admin/settings">API</a>
                    <a href="/logout" class="text-red-300">Logout</a>
                {% else %}
                    <a href="/login" class="bg-white text-indigo-700 px-3 py-1 rounded">Login</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <div class="container mx-auto p-4 md:p-8">
        {% with msgs = get_flashed_messages() %}{% for m in msgs %}
            <div class="bg-indigo-100 border-l-4 border-indigo-500 p-3 mb-5 text-indigo-700 text-sm shadow-sm">{{ m }}</div>
        {% endfor %}{% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    apps = list(apps_col.find().sort('_id', -1))
    ads = list(ads_col.find())
    content = """
    <div class="max-w-4xl mx-auto mb-8 space-y-4">
        {% for ad in ads %}<div class="bg-white p-2 rounded shadow-sm flex justify-center">{{ ad.code | safe }}</div>{% endfor %}
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {% for app in apps %}
        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 flex flex-col items-center">
            <img src="{{app.logo}}" class="w-16 h-16 rounded-xl mb-3 shadow">
            <h3 class="font-bold text-center text-gray-800">{{app.name}}</h3>
            <span class="text-[10px] bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full font-bold my-2">{{app.category}}</span>
            <p class="text-xs text-gray-400 text-center mb-4 h-8 overflow-hidden">{{app.info}}</p>
            <a href="/download/{{app._id}}" class="w-full bg-indigo-600 text-white text-center py-2 rounded-xl font-bold hover:bg-indigo-700">Download</a>
        </div>
        {% endfor %}
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), apps=apps, ads=ads)

@app.route('/download/<id>')
def download_logic(id):
    app_data = apps_col.find_one({"_id": ObjectId(id)})
    short_cfg = settings_col.find_one({"type": "shortener"})
    original_url = app_data['download_link']
    if short_cfg and short_cfg.get('url') and short_cfg.get('api'):
        try:
            res = requests.get(f"https://{short_cfg['url']}/api?api={short_cfg['api']}&url={original_url}", timeout=10).json()
            short_url = res.get('shortenedUrl') or res.get('shortedUrl')
            if short_url: return redirect(short_url)
        except: pass
    return redirect(original_url)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        apps_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo'), "category": request.form.get('category'), "release_date": request.form.get('release_date'), "version": request.form.get('version'), "info": request.form.get('info'), "download_link": request.form.get('download_link')})
        flash("App Added Successfully")
    apps = list(apps_col.find().sort('_id', -1))
    content = """
    <div class="grid lg:grid-cols-3 gap-6">
        <form method="POST" class="bg-white p-6 rounded-xl shadow-sm border space-y-3">
            <h2 class="font-bold mb-2">Upload New App</h2>
            <input type="text" name="name" placeholder="Name" class="w-full border p-2 rounded" required>
            <input type="text" name="logo" placeholder="Logo URL" class="w-full border p-2 rounded" required>
            <select name="category" class="w-full border p-2 rounded"><option>Mobile</option><option>Desktop</option><option>iOS</option></select>
            <input type="date" name="release_date" class="w-full border p-2 rounded" required>
            <input type="text" name="version" placeholder="Version" class="w-full border p-2 rounded" required>
            <textarea name="info" placeholder="Info" class="w-full border p-2 rounded h-20" required></textarea>
            <input type="text" name="download_link" placeholder="Direct Link" class="w-full border p-2 rounded" required>
            <button class="w-full bg-indigo-600 text-white py-2 rounded font-bold">Publish</button>
        </form>
        <div class="lg:col-span-2 bg-white rounded-xl shadow-sm overflow-hidden">
            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 border-b"><tr><th class="p-3">Name</th><th class="p-3">Action</th></tr></thead>
                <tbody>{% for a in apps %}<tr class="border-b">
                    <td class="p-3 flex items-center gap-2"><img src="{{a.logo}}" class="w-6 h-6 rounded">{{a.name}}</td>
                    <td class="p-3"><a href="/del/app/{{a._id}}" class="text-red-500 font-bold">Delete</a></td>
                </tr>{% endfor %}</tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), apps=apps)

@app.route('/admin/ads', methods=['GET', 'POST'])
def ads():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        ads_col.insert_one({"name": request.form.get('name'), "code": request.form.get('code')})
        flash("Ad Added")
    ads_list = list(ads_col.find())
    content = """
    <div class="max-w-2xl mx-auto bg-white p-6 rounded-xl shadow border">
        <h2 class="font-bold mb-4">Ad Manager</h2>
        <form method="POST" class="space-y-4 mb-6">
            <input type="text" name="name" placeholder="Ad Label" class="w-full border p-2 rounded" required>
            <textarea name="code" placeholder="Ad Script" class="w-full border p-2 rounded h-32" required></textarea>
            <button class="bg-indigo-600 text-white px-4 py-2 rounded">Save Ad</button>
        </form>
        {% for d in ads_list %}<div class="flex justify-between border-t p-2"><span>{{d.name}}</span><a href="/del/ad/{{d._id}}" class="text-red-500">Delete</a></div>{% endfor %}
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), ads_list=ads_list)

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings_page():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        settings_col.update_one({"type": "shortener"}, {"$set": {"url": request.form.get('url'), "api": request.form.get('api')}}, upsert=True)
        flash("Settings Updated")
    cfg = settings_col.find_one({"type": "shortener"}) or {}
    content = """
    <div class="max-w-md mx-auto bg-white p-6 rounded shadow">
        <h2 class="font-bold mb-4">API Settings</h2>
        <form method="POST" class="space-y-4">
            <input type="text" name="url" value="{{cfg.url}}" placeholder="Shortener Domain" class="w-full border p-2 rounded" required>
            <input type="text" name="api" value="{{cfg.api}}" placeholder="API Key" class="w-full border p-2 rounded" required>
            <button class="w-full bg-indigo-600 text-white py-2 rounded">Update</button>
        </form>
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), cfg=cfg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    u = users_col.find_one({"username": "admin"})
    if request.method == 'POST':
        p = request.form.get('password')
        if not u:
            users_col.insert_one({"username": "admin", "password": generate_password_hash(p)})
            session['logged_in'] = True
            return redirect(url_for('admin'))
        if check_password_hash(u['password'], p):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        flash("Wrong Password")
    content = """
    <div class="max-w-xs mx-auto mt-20 bg-white p-6 rounded shadow border text-center">
        <h2 class="font-bold mb-4 uppercase">Admin Login</h2>
        <form method="POST"><input type="password" name="password" class="w-full border p-2 mb-4 text-center rounded" required>
        <button class="w-full bg-indigo-600 text-white py-2 rounded">Login</button></form>
        <a href="/forgot" class="text-xs text-gray-400 mt-4 block">Reset?</a>
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content))

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        if request.form.get('key') == RECOVERY_KEY:
            users_col.update_one({"username": "admin"}, {"$set": {"password": generate_password_hash(request.form.get('pw'))}}, upsert=True)
            flash("Reset Success")
            return redirect(url_for('login'))
        flash("Incorrect Key")
    content = """<form method="POST" class="max-w-xs mx-auto mt-20 bg-white p-6 rounded border space-y-3">
        <input name="key" placeholder="Recovery Key" class="w-full border p-2"><input name="pw" placeholder="New PW" class="w-full border p-2"><button class="w-full bg-red-600 text-white py-2">Reset</button>
    </form>"""
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content))

@app.route('/del/<type>/<id>')
def delete(type, id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    if type == 'app': apps_col.delete_one({"_id": ObjectId(id)})
    elif type == 'ad': ads_col.delete_one({"_id": ObjectId(id)})
    return redirect(request.referrer)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Vercel-এর জন্য এক্সপোজ করা হলো
handler = app
