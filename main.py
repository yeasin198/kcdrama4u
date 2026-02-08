import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "movie_pro_ultra_unlimited_v10_fixed"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_database
import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

app = Flask(__name__)
app.secret_key = "movie_pro_ultra_unlimited_v10_fixed"

# --- MongoDB Connection ---
# আপনার কানেকশন স্ট্রিংটি এখানে থাকল
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_database
movies_col = db.movies
settings_col = db.settings

# --- Helper Functions ---

def shorten_link(url):
    """লিঙ্ক শর্টনার সাপোর্ট"""
    if not url or not url.strip(): return ""
    try:
        cfg = settings_col.find_one({"type": "config"})
        if cfg and cfg.get('api'):
            api_url = cfg.get('api').replace("{url}", url)
            r = requests.get(api_url, timeout=5)
            if r.status_code == 200:
                return r.text.strip()
    except Exception as e:
        print(f"Shortener Error: {e}")
    return url

def get_site_settings():
    """কনফিগারেশন এবং অ্যাড লোড করা"""
    cfg = settings_col.find_one({"type": "config"}) or {
        "limit": 15, 
        "slider_limit": 5, 
        "api": "",
        "site_name": "MoviePro"
    }
    ads = list(settings_col.find({"type": "ad_unit"}))
    return cfg, ads

# --- HTML TEMPLATES ---

COMMON_HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css" />
<script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap" rel="stylesheet">
<style>
    body { background-color: #0b0f19; color: white; font-family: 'Inter', sans-serif; overflow-x: hidden; }
    .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.05); }
    .corner-tag { position: absolute; padding: 2px 8px; font-size: 10px; font-weight: bold; border-radius: 4px; z-index: 10; }
    .swiper { width: 100%; height: 400px; border-radius: 24px; margin-bottom: 30px; }
    .swiper-slide img { width: 100%; height: 100%; object-fit: cover; }
    .movie-card:hover img { transform: scale(1.1); transition: 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
    ::-webkit-scrollbar { display: none; }
</style>
"""

NAVBAR_HTML = """
<nav class="p-4 glass sticky top-0 z-50 border-b border-white/5">
    <div class="max-w-7xl mx-auto flex justify-between items-center px-4">
        <a href="/" class="text-3xl font-black text-blue-500 uppercase italic tracking-tighter">
            {{ cfg.site_name }}<span class="text-white">PRO</span>
        </a>
        <div class="flex items-center gap-6">
            <form action="/" class="hidden md:flex bg-gray-950/50 border border-gray-800 rounded-full px-4 py-1">
                <input name="q" placeholder="Search movies..." class="bg-transparent outline-none text-sm p-1 w-48">
                <button class="text-blue-500"><i class="fa fa-search"></i></button>
            </form>
            <a href="/admin" class="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-full text-xs font-black uppercase tracking-widest transition shadow-lg shadow-blue-600/20">Admin</a>
        </div>
    </div>
</nav>
"""

# --- USER ROUTES ---

@app.route('/')
def index():
    cfg, ads = get_site_settings()
    q = request.args.get('q')
    cat = request.args.get('cat')
    
    slider_movies = list(movies_col.find({"in_slider": "on"}).sort("_id", -1).limit(int(cfg.get('slider_limit', 5))))
    
    filter_q = {}
    if q: filter_q["name"] = {"$regex": q, "$options": "i"}
    if cat: filter_q["category"] = cat
    
    movies = list(movies_col.find(filter_q).sort("_id", -1).limit(int(cfg.get('limit', 15))))
    categories = movies_col.distinct("category")
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>""" + COMMON_HEAD + """<title>{{ cfg.site_name }} - Home</title></head>
    <body>
        """ + NAVBAR_HTML + """
        <div class="max-w-7xl mx-auto p-4 md:p-6">
            <div class="mb-8 space-y-4 text-center">
                {% for ad in ads %}{% if ad.position == 'top' %}{{ ad.code | safe }}{% endif %}{% endfor %}
            </div>

            {% if slider_movies %}
            <div class="swiper mySwiper shadow-2xl border border-white/5">
                <div class="swiper-wrapper">
                    {% for sm in slider_movies %}
                    <div class="swiper-slide relative">
                        <img src="{{ sm.poster }}" alt="{{ sm.name }}">
                        <div class="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent flex flex-col justify-end p-8 md:p-16">
                            <span class="bg-blue-600 w-max px-3 py-1 rounded text-[10px] font-bold uppercase mb-3 tracking-widest">Featured</span>
                            <h2 class="text-4xl md:text-6xl font-black italic uppercase tracking-tighter leading-tight">{{ sm.name }}</h2>
                            <div class="flex gap-4 mt-6">
                                <a href="/movie/{{ sm._id }}" class="bg-white text-black px-10 py-3 rounded-full font-black text-sm hover:bg-blue-500 hover:text-white transition uppercase">Watch Now</a>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                <div class="swiper-pagination"></div>
            </div>
            {% endif %}

            <div class="flex gap-3 overflow-x-auto pb-8 no-scrollbar">
                <a href="/" class="bg-blue-600 px-8 py-2.5 rounded-full text-xs font-black uppercase tracking-widest">All</a>
                {% for c in categories %}
                <a href="/?cat={{ c }}" class="glass border border-white/10 hover:border-blue-500/50 px-8 py-2.5 rounded-full text-xs font-black uppercase tracking-widest transition shrink-0 italic">{{ c }}</a>
                {% endfor %}
            </div>

            <h2 class="text-2xl font-black mb-8 italic text-blue-500 border-l-8 border-blue-600 pl-4 uppercase tracking-tighter">Latest Releases</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6 md:gap-10">
                {% for m in movies %}
                <a href="/movie/{{ m._id }}" class="group relative rounded-3xl overflow-hidden aspect-[2/3] border border-white/5 bg-gray-900 block movie-card shadow-xl">
                    <span class="corner-tag top-3 left-3 bg-blue-600 shadow-lg">{{ m.tag1 }}</span>
                    <span class="corner-tag top-3 right-3 bg-red-600 shadow-lg">{{ m.tag2 }}</span>
                    <span class="corner-tag bottom-3 left-3 bg-yellow-500 text-black shadow-lg">{{ m.tag3 }}</span>
                    <span class="corner-tag bottom-3 right-3 bg-green-600 shadow-lg">{{ m.tag4 }}</span>
                    
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    
                    <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent p-5 flex flex-col justify-end">
                        <div class="font-black text-sm md:text-base leading-tight">{{ m.name }}</div>
                        <div class="text-[10px] text-gray-400 mt-2 font-bold uppercase tracking-widest">{{ m.year }} | {{ m.lang }}</div>
                    </div>
                </a>
                {% endfor %}
            </div>

            <div class="mt-20 space-y-6 text-center">
                {% for ad in ads %}{% if ad.position == 'bottom' %}{{ ad.code | safe }}{% endif %}{% endfor %}
            </div>
        </div>

        {% for ad in ads %}{% if ad.position == 'popup' %}{{ ad.code | safe }}{% endif %}{% endfor %}

        <script>
            new Swiper(".mySwiper", { 
                pagination: { el: ".swiper-pagination", clickable: true }, 
                autoplay: { delay: 5000 }, 
                loop: true,
                effect: 'fade'
            });
        </script>
    </body>
    </html>
    """, cfg=cfg, ads=ads, movies=movies, slider_movies=slider_movies, categories=categories)

@app.route('/movie/<id>')
def movie_details(id):
    try:
        movie = movies_col.find_one({"_id": ObjectId(id)})
        if not movie: return redirect('/')
        cfg, ads = get_site_settings()
    except: return redirect('/')
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>""" + COMMON_HEAD + """<title>{{ movie.name }} - Watch</title></head>
    <body class="p-4 md:p-10">
        <div class="max-w-6xl mx-auto">
            <a href="/" class="inline-flex items-center gap-2 text-gray-500 hover:text-white mb-10 font-bold transition">
                <i class="fa fa-arrow-left"></i> Back to Home
            </a>
            
            <div class="md:flex gap-12 glass p-8 md:p-12 rounded-[3rem] border border-white/10 shadow-2xl">
                <img src="{{ movie.poster }}" class="w-full md:w-80 rounded-[2rem] shadow-2xl mb-8 md:mb-0">
                <div class="flex-grow">
                    <h1 class="text-4xl md:text-6xl font-black mb-6 uppercase italic">{{ movie.name }}</h1>
                    <div class="flex flex-wrap gap-4 mb-8">
                        <span class="bg-blue-600 px-5 py-1.5 rounded-full text-xs font-black uppercase">{{ movie.category }}</span>
                        <span class="bg-gray-800 px-5 py-1.5 rounded-full text-xs font-black">{{ movie.year }}</span>
                        <span class="bg-gray-800 px-5 py-1.5 rounded-full text-xs font-black">{{ movie.lang }}</span>
                    </div>
                    <div class="bg-black/40 p-8 rounded-3xl border border-white/5">
                        <p class="text-gray-400 italic">"{{ movie.story }}"</p>
                    </div>
                </div>
            </div>

            <div class="my-16 text-center">
                {% for ad in ads %}{% if ad.position == 'top' %}{{ ad.code | safe }}{% endif %}{% endfor %}
            </div>

            <div class="grid gap-10">
                {% for ep in movie.episodes %}
                <div class="glass p-8 md:p-12 rounded-[3.5rem] border-l-[12px] border-blue-600">
                    <h3 class="font-black text-2xl mb-8 uppercase italic">Episode: {{ ep.ep_no }}</h3>
                    <div class="grid md:grid-cols-2 gap-8">
                        {% for link in ep.links %}
                        <div class="bg-black/60 p-6 rounded-3xl border border-white/5">
                            <span class="text-[11px] uppercase text-gray-500 block mb-5 font-black">{{ link.quality }}</span>
                            <div class="flex flex-wrap gap-4">
                                <a href="{{ link.stream }}" target="_blank" class="flex-grow bg-blue-600 py-4 rounded-2xl text-xs font-black text-center">Stream</a>
                                <a href="{{ link.download }}" target="_blank" class="flex-grow bg-green-600 py-4 rounded-2xl text-xs font-black text-center">Download</a>
                                <a href="{{ link.telegram }}" target="_blank" class="bg-sky-500 px-8 py-4 rounded-2xl text-xs text-center"><i class="fab fa-telegram"></i></a>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """, movie=movie, cfg=cfg, ads=ads)

# --- ADMIN ROUTES ---

@app.route('/admin')
def admin_dash():
    q = request.args.get('q')
    filter_q = {"name": {"$regex": q, "$options": "i"}} if q else {}
    movies = list(movies_col.find(filter_q).sort("_id", -1))
    cfg, _ = get_site_settings()
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>""" + COMMON_HEAD + """<title>Admin</title></head>
    <body class="p-6">
        <div class="max-w-6xl mx-auto">
            <div class="flex justify-between items-center mb-10">
                <h1 class="text-3xl font-black uppercase italic">Admin Panel</h1>
                <div class="flex gap-4">
                    <a href="/admin/add" class="bg-green-600 p-4 px-8 rounded-2xl font-black text-xs uppercase">+ Add Movie</a>
                    <a href="/admin/settings" class="bg-gray-800 p-4 px-6 rounded-2xl font-black text-xs uppercase"><i class="fa fa-cog"></i></a>
                </div>
            </div>
            <div class="grid gap-4">
                {% for m in movies %}
                <div class="glass p-4 rounded-3xl flex justify-between items-center border border-white/5">
                    <div class="flex items-center gap-6">
                        <img src="{{ m.poster }}" class="w-12 h-16 object-cover rounded-xl">
                        <h3 class="font-black text-lg">{{ m.name }}</h3>
                    </div>
                    <div class="flex gap-3">
                        <a href="/admin/edit/{{ m._id }}" class="p-3 bg-yellow-500 text-black rounded-xl font-black text-xs uppercase">Edit</a>
                        <a href="/admin/delete/{{ m._id }}" class="p-3 bg-red-500 text-white rounded-xl" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """, movies=movies, cfg=cfg)

@app.route('/admin/add', methods=['GET', 'POST'])
@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def manage_movie(id=None):
    movie = None
    if id:
        try: movie = movies_col.find_one({"_id": ObjectId(id)})
        except: return redirect('/admin')

    if request.method == 'POST' and 'save_movie' in request.form:
        data = {
            "name": request.form['name'], "poster": request.form['poster'],
            "year": request.form['year'], "lang": request.form['lang'],
            "category": request.form['category'].strip().upper(),
            "tag1": request.form['tag1'], "tag2": request.form['tag2'],
            "tag3": request.form['tag3'], "tag4": request.form['tag4'],
            "story": request.form['story'], "in_slider": request.form.get('in_slider', 'off')
        }
        if id:
            movies_col.update_one({"_id": ObjectId(id)}, {"$set": data})
            return redirect(url_for('manage_movie', id=id))
        else:
            data['episodes'] = []
            new_id = movies_col.insert_one(data).inserted_id
            return redirect(url_for('manage_movie', id=new_id))

    ep_idx = request.args.get('ep_idx')
    ep_to_edit = None
    if ep_idx is not None and movie and 'episodes' in movie:
        try: ep_to_edit = movie['episodes'][int(ep_idx)]
        except: pass

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>""" + COMMON_HEAD + """<title>Manage Movie</title></head>
    <body class="p-6">
        <div class="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12">
            <form method="POST" class="glass p-10 rounded-[3rem] border border-white/10">
                <h2 class="text-3xl font-black mb-10 italic text-blue-500 uppercase">Movie Info</h2>
                <div class="space-y-4">
                    <input name="name" value="{{ movie.name if movie else '' }}" placeholder="Movie Name" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none" required>
                    <input name="poster" value="{{ movie.poster if movie else '' }}" placeholder="Poster URL" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                    <div class="grid grid-cols-2 gap-4">
                        <input name="category" value="{{ movie.category if movie else '' }}" placeholder="Category" class="bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                        <input name="year" value="{{ movie.year if movie else '' }}" placeholder="Year" class="bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                    </div>
                    <input name="lang" value="{{ movie.lang if movie else '' }}" placeholder="Language" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                    <div class="grid grid-cols-2 gap-4">
                        <input name="tag1" value="{{ movie.tag1 if movie else '' }}" placeholder="Tag 1" class="bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                        <input name="tag2" value="{{ movie.tag2 if movie else '' }}" placeholder="Tag 2" class="bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                        <input name="tag3" value="{{ movie.tag3 if movie else '' }}" placeholder="Tag 3" class="bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                        <input name="tag4" value="{{ movie.tag4 if movie else '' }}" placeholder="Tag 4" class="bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                    </div>
                    <textarea name="story" placeholder="Storyline" class="w-full bg-black/40 p-4 rounded-2xl h-32 border border-gray-800 outline-none">{{ movie.story if movie else '' }}</textarea>
                    <label class="flex items-center gap-2"><input type="checkbox" name="in_slider" {{ 'checked' if movie and movie.in_slider == 'on' else '' }}> Slider Show</label>
                </div>
                <button name="save_movie" class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase mt-6">Save Movie</button>
                <a href="/admin" class="block text-center mt-4 text-gray-500 uppercase text-xs">Back to Dashboard</a>
            </form>

            {% if movie %}
            <div class="space-y-6">
                <form action="/admin/episode/save" method="POST" class="glass p-10 rounded-[3rem] border border-green-500/20">
                    <h2 class="text-2xl font-black mb-6 uppercase text-green-500">{{ 'Edit' if ep_to_edit else 'Add' }} Episode</h2>
                    <input type="hidden" name="mid" value="{{ movie._id }}">
                    <input type="hidden" name="idx" value="{{ ep_idx if ep_idx is not None else '' }}">
                    <input name="ep_no" value="{{ ep_to_edit.ep_no if ep_to_edit else '' }}" placeholder="Episode Number" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 mb-4" required>
                    
                    {% for i in range(1, 3) %}
                    {% set link_data = ep_to_edit.links[i-1] if ep_to_edit and ep_to_edit.links|length >= i else None %}
                    <div class="bg-black/20 p-4 rounded-2xl mb-4 border border-white/5">
                        <p class="text-[10px] uppercase font-black text-gray-500 mb-2">Slot {{i}}</p>
                        <input name="q{{i}}_n" value="{{ link_data.quality if link_data else '' }}" placeholder="Quality (e.g. 720p)" class="w-full bg-black/40 p-2 rounded-lg border border-gray-800 mb-2 text-sm">
                        <input name="q{{i}}_s" value="{{ link_data.stream if link_data else '' }}" placeholder="Stream Link" class="w-full bg-black/40 p-2 rounded-lg border border-gray-800 mb-2 text-xs">
                        <input name="q{{i}}_d" value="{{ link_data.download if link_data else '' }}" placeholder="Download Link" class="w-full bg-black/40 p-2 rounded-lg border border-gray-800 mb-2 text-xs">
                        <input name="q{{i}}_t" value="{{ link_data.telegram if link_data else '' }}" placeholder="Telegram Link" class="w-full bg-black/40 p-2 rounded-lg border border-gray-800 text-xs">
                    </div>
                    {% endfor %}
                    <button class="w-full bg-green-600 py-4 rounded-2xl font-black uppercase">Save Episode</button>
                </form>

                <div class="glass p-6 rounded-[2rem]">
                    <h3 class="font-black uppercase text-sm text-gray-500 mb-4">Episodes List</h3>
                    {% for ep in movie.episodes %}
                    <div class="flex justify-between items-center bg-black/40 p-4 rounded-xl mb-2">
                        <span class="font-black italic">EP {{ ep.ep_no }}</span>
                        <div class="flex gap-4 text-xs font-black uppercase">
                            <a href="/admin/edit/{{ movie._id }}?ep_idx={{ loop.index0 }}" class="text-yellow-500">Edit</a>
                            <a href="/admin/episode/delete/{{ movie._id }}/{{ loop.index0 }}" class="text-red-500" onclick="return confirm('Delete?')">Delete</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    """, movie=movie, ep_to_edit=ep_to_edit, ep_idx=ep_idx)

@app.route('/admin/episode/save', methods=['POST'])
def save_episode():
    mid = request.form['mid']
    idx = request.form.get('idx')
    
    links = []
    for i in range(1, 3):
        links.append({
            "quality": request.form.get(f'q{i}_n', 'HD'),
            "stream": shorten_link(request.form.get(f'q{i}_s', '')),
            "download": shorten_link(request.form.get(f'q{i}_d', '')),
            "telegram": shorten_link(request.form.get(f'q{i}_t', ''))
        })
    
    new_ep = {"ep_no": request.form['ep_no'], "links": links}
    
    try:
        movie = movies_col.find_one({"_id": ObjectId(mid)})
        if not movie: return redirect('/admin')
        
        episodes = movie.get('episodes', [])
        if idx and idx.strip() != "":
            episodes[int(idx)] = new_ep
        else:
            episodes.append(new_ep)
        
        movies_col.update_one({"_id": ObjectId(mid)}, {"$set": {"episodes": episodes}})
    except Exception as e:
        print(f"Error saving episode: {e}")
        
    return redirect(url_for('manage_movie', id=mid))

@app.route('/admin/episode/delete/<mid>/<int:idx>')
def delete_episode(mid, idx):
    try:
        movie = movies_col.find_one({"_id": ObjectId(mid)})
        if movie and 'episodes' in movie:
            eps = movie['episodes']
            if 0 <= idx < len(eps):
                eps.pop(idx)
                movies_col.update_one({"_id": ObjectId(mid)}, {"$set": {"episodes": eps}})
    except: pass
    return redirect(url_for('manage_movie', id=mid))

@app.route('/admin/delete/<id>')
def delete_movie(id):
    try: movies_col.delete_one({"_id": ObjectId(id)})
    except: pass
    return redirect('/admin')

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        if 'save_config' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {
                "api": request.form['api'], "limit": request.form['limit'], 
                "slider_limit": request.form['slider_limit'], "site_name": request.form.get('site_name', 'MoviePro')
            }}, upsert=True)
        elif 'add_ad' in request.form:
            settings_col.insert_one({"type": "ad_unit", "position": request.form['pos'], "code": request.form['code']})
        elif 'del_ad' in request.form:
            settings_col.delete_one({"_id": ObjectId(request.form['ad_id'])})
        return redirect('/admin/settings')
    
    cfg, ads = get_site_settings()
    return render_template_string("""
    <!DOCTYPE html>
    <html><head>""" + COMMON_HEAD + """</head><body class="p-6">
        <div class="max-w-4xl mx-auto space-y-10">
            <form method="POST" class="glass p-8 rounded-3xl">
                <h2 class="text-2xl font-black mb-6 uppercase italic">General Settings</h2>
                <div class="space-y-4">
                    <input name="site_name" value="{{ cfg.site_name }}" placeholder="Site Name" class="w-full bg-black/40 p-4 rounded-xl border border-gray-800">
                    <input name="api" value="{{ cfg.api }}" placeholder="Shortener API" class="w-full bg-black/40 p-4 rounded-xl border border-gray-800">
                    <div class="grid grid-cols-2 gap-4">
                        <input name="limit" type="number" value="{{ cfg.limit }}" class="bg-black/40 p-4 rounded-xl border border-gray-800">
                        <input name="slider_limit" type="number" value="{{ cfg.slider_limit }}" class="bg-black/40 p-4 rounded-xl border border-gray-800">
                    </div>
                    <button name="save_config" class="w-full bg-blue-600 py-4 rounded-xl font-black">Save Settings</button>
                </div>
            </form>
            <div class="glass p-8 rounded-3xl">
                <h2 class="text-2xl font-black mb-6 uppercase italic">Ads Management</h2>
                <form method="POST" class="space-y-4 mb-8">
                    <select name="pos" class="w-full bg-black/60 p-4 rounded-xl border border-gray-800">
                        <option value="top">Header</option>
                        <option value="bottom">Footer</option>
                        <option value="popup">Popup/Direct</option>
                    </select>
                    <textarea name="code" placeholder="Ad Code" class="w-full bg-black/40 p-4 rounded-xl border border-gray-800 h-32"></textarea>
                    <button name="add_ad" class="w-full bg-yellow-600 py-4 rounded-xl font-black">Add Ad</button>
                </form>
                {% for ad in ads %}
                <div class="flex justify-between items-center bg-black/40 p-4 rounded-xl mb-2">
                    <span class="text-xs font-black uppercase">{{ ad.position }}</span>
                    <form method="POST"><input type="hidden" name="ad_id" value="{{ ad._id }}"><button name="del_ad" class="text-red-500 text-xs font-black">Remove</button></form>
                </div>
                {% endfor %}
            </div>
            <a href="/admin" class="block text-center text-gray-500 uppercase font-black text-xs">Back</a>
        </div>
    </body></html>
    """, cfg=cfg, ads=ads)

if __name__ == '__main__':
    app.run(debug=True)
