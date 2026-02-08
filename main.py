from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests

app = Flask(__name__)
app.secret_key = "movie_pro_ultra_v3"

# --- MongoDB কানেকশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_database
movies_col = db.movies
settings_col = db.settings

# --- Helper: URL Shortener ---
def shorten_link(url):
    config = settings_col.find_one({"type": "config"})
    if config and config.get('api') and url and url.strip():
        # এপিআই লিঙ্কে অবশ্যই {url} থাকতে হবে। উদাহরণ: https://api.com/st?api=KEY&url={url}
        api_url = config.get('api').replace("{url}", url)
        try:
            r = requests.get(api_url, timeout=5)
            return r.text.strip() if r.status_code == 200 else url
        except:
            return url
    return url

# --- UI Styles & Scripts ---
HEAD_CSS = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css" />
<script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
<style>
    body { background-color: #0b0f19; color: white; font-family: 'Inter', sans-serif; overflow-x: hidden; }
    .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.05); }
    .corner-tag { position: absolute; padding: 2px 8px; font-size: 10px; font-weight: bold; border-radius: 4px; z-index: 10; }
    .swiper { width: 100%; height: 400px; border-radius: 20px; }
    .swiper-slide img { width: 100%; height: 100%; object-cover: cover; }
</style>
"""

def get_site_data():
    ads = settings_col.find_one({"type": "ads"}) or {"top": "", "bottom": "", "popup": ""}
    cfg = settings_col.find_one({"type": "config"}) or {"limit": 15, "api": ""}
    return ads, cfg

# --- USER ROUTES ---

@app.route('/')
def index():
    ads, cfg = get_site_data()
    q = request.args.get('q')
    cat = request.args.get('cat')
    
    # স্লাইডারের জন্য মুভি (যেগুলো 'slider' চেক করা আছে)
    slider_movies = list(movies_col.find({"in_slider": "on"}).limit(5))
    
    # হোমপেজ মুভি ফিল্টার ও লিমিট
    filter_query = {}
    if q: filter_query["name"] = {"$regex": q, "$options": "i"}
    if cat: filter_query["category"] = cat
    
    limit = int(cfg.get('limit', 15))
    movies = list(movies_col.find(filter_query).sort("_id", -1).limit(limit))
    
    # ইউনিক ক্যাটাগরি লিস্ট
    categories = movies_col.distinct("category")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD_CSS}<title>MoviePro - Premium</title></head>
    <body>
        <nav class="p-4 glass sticky top-0 z-50 flex justify-between items-center px-6">
            <a href="/" class="text-2xl font-black text-blue-500">MOVIE<span class="text-white">PRO</span></a>
            <form action="/" class="hidden md:flex bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
                <input name="q" placeholder="Search..." class="bg-transparent p-2 px-4 outline-none w-64 text-sm text-white">
                <button class="px-4 text-blue-500"><i class="fa fa-search"></i></button>
            </form>
            <a href="/admin" class="bg-blue-600 px-5 py-2 rounded-full text-xs font-bold uppercase">Admin</a>
        </nav>

        <div class="max-w-7xl mx-auto p-4 md:p-6">
            <div class="mb-6 text-center text-white">{ads['top'] | safe}</div>

            <!-- স্লাইডার -->
            {{% if slider_movies %}}
            <div class="swiper mySwiper mb-10 shadow-2xl">
                <div class="swiper-wrapper">
                    {{% for sm in slider_movies %}}
                    <div class="swiper-slide relative">
                        <img src="{{{{ sm.poster }}}}" class="object-cover">
                        <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent flex flex-col justify-end p-8">
                            <h2 class="text-3xl font-black italic">{{{{ sm.name }}}}</h2>
                            <a href="/movie/{{{{ sm._id }}}}" class="mt-4 bg-blue-600 w-max px-6 py-2 rounded-full font-bold text-sm">WATCH NOW</a>
                        </div>
                    </div>
                    {{% endfor %}}
                </div>
                <div class="swiper-pagination"></div>
            </div>
            {{% endif %}}

            <!-- ক্যাটাগরি ফিল্টার -->
            <div class="flex gap-3 overflow-x-auto pb-6 scrollbar-hide">
                <a href="/" class="bg-gray-800 px-6 py-2 rounded-full text-xs font-bold shrink-0">ALL</a>
                {{% for c in categories %}}
                <a href="/?cat={{{{ c }}}}" class="bg-blue-900/40 border border-blue-500/20 px-6 py-2 rounded-full text-xs font-bold shrink-0 uppercase tracking-widest">{{{{ c }}}}</a>
                {{% endfor %}}
            </div>

            <h2 class="text-xl font-bold mb-6 italic text-blue-500">Latest Uploads</h2>
            <div class="grid grid-cols-2 md:grid-cols-5 gap-6">
                {{% for movie in movies %}}
                <a href="/movie/{{{{ movie._id }}}}" class="group block relative rounded-2xl overflow-hidden shadow-2xl aspect-[2/3] border border-white/5 bg-gray-900">
                    <span class="corner-tag top-2 left-2 bg-blue-600">{{{{ movie.tag1 }}}}</span>
                    <span class="corner-tag top-2 right-2 bg-red-600">{{{{ movie.tag2 }}}}</span>
                    <span class="corner-tag bottom-2 left-2 bg-yellow-500 text-black">{{{{ movie.tag3 }}}}</span>
                    <span class="corner-tag bottom-2 right-2 bg-green-600">{{{{ movie.tag4 }}}}</span>
                    <img src="{{{{ movie.poster }}}}" class="w-full h-full object-cover group-hover:scale-110 transition duration-500">
                    <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent p-3 flex flex-col justify-end">
                        <div class="font-bold text-xs truncate">{{{{ movie.name }}}}</div>
                        <div class="text-[9px] text-gray-400 mt-1 uppercase">{{{{ movie.year }}}} | {{{{ movie.category }}}}</div>
                    </div>
                </a>
                {{% endfor %}}
            </div>
            
            <div class="mt-12 text-center">{ads['bottom'] | safe}</div>
        </div>
        {ads['popup'] | safe}

        <script>
            var swiper = new Swiper(".mySwiper", {{
                pagination: {{ el: ".swiper-pagination", clickable: true }},
                autoplay: {{ delay: 3000 }},
                loop: true
            }});
        </script>
    </body>
    </html>
    """
    return render_template_string(html, movies=movies, slider_movies=slider_movies, categories=categories)

@app.route('/movie/<id>')
def movie_details(id):
    movie = movies_col.find_one({"_id": ObjectId(id)})
    ads, _ = get_site_data()
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD_CSS}<title>{{{{ movie.name }}}}</title></head>
    <body class="p-4 md:p-10">
        <div class="max-w-5xl mx-auto">
            <div class="md:flex gap-10 glass p-8 rounded-3xl border border-white/10">
                <img src="{{{{ movie.poster }}}}" class="w-full md:w-72 rounded-2xl shadow-2xl mb-6">
                <div>
                    <h1 class="text-4xl font-black mb-4">{{{{ movie.name }}}}</h1>
                    <div class="flex gap-4 mb-6">
                        <span class="text-blue-400 font-bold uppercase text-xs italic tracking-widest">{{{{ movie.category }}}}</span>
                        <span class="text-gray-500 font-bold text-xs">{{{{ movie.year }}}}</span>
                    </div>
                    <p class="text-gray-400 leading-relaxed text-sm">{{{{ movie.story }}}}</p>
                </div>
            </div>

            <div class="mt-10 text-center">{ads['top'] | safe}</div>

            <h2 class="text-2xl font-bold mt-16 mb-8 italic">Download Episodes:</h2>
            <div class="space-y-6">
                {{% for ep in movie.episodes %}}
                <div class="glass p-6 rounded-3xl border-l-4 border-blue-600">
                    <h3 class="font-bold text-lg mb-4 text-blue-300 italic">Episode: {{{{ ep.ep_no }}}}</h3>
                    <div class="grid md:grid-cols-2 gap-4">
                        {{% for link in ep.links %}}
                        <div class="bg-black/30 p-4 rounded-xl border border-gray-800">
                            <span class="text-[10px] uppercase text-gray-500 block mb-3 font-bold italic">Quality: {{{{ link.quality }}}}</span>
                            <div class="flex gap-2">
                                <a href="{{{{ link.stream }}}}" target="_blank" class="bg-blue-600 p-2 px-4 rounded-lg text-xs font-bold grow text-center">STREAM</a>
                                <a href="{{{{ link.download }}}}" target="_blank" class="bg-green-600 p-2 px-4 rounded-lg text-xs font-bold grow text-center text-white">DOWNLOAD</a>
                                <a href="{{{{ link.telegram }}}}" target="_blank" class="bg-sky-500 p-2 px-4 rounded-lg text-xs font-bold grow text-center text-white"><i class="fab fa-telegram"></i></a>
                            </div>
                        </div>
                        {{% endfor %}}
                    </div>
                </div>
                {{% endfor %}}
            </div>
            <div class="mt-12 text-center">{ads['bottom'] | safe}</div>
        </div>
        {ads['popup'] | safe}
    </body>
    </html>
    """
    return render_template_string(html, movie=movie)

# --- ADMIN ROUTES ---

@app.route('/admin')
def admin():
    q = request.args.get('q')
    movies = list(movies_col.find({"name": {"$regex": q, "$options": "i"}})) if q else list(movies_col.find())
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD_CSS}<title>Admin Dashboard</title></head>
    <body class="p-6">
        <div class="max-w-6xl mx-auto">
            <div class="flex justify-between items-center mb-10">
                <h1 class="text-2xl font-black italic text-blue-500 uppercase tracking-tighter">Admin Panel</h1>
                <div class="flex gap-4">
                    <a href="/admin/add" class="bg-green-600 p-3 px-6 rounded-xl font-bold text-xs uppercase tracking-widest">+ Add Movie</a>
                    <a href="/admin/settings" class="bg-gray-800 p-3 px-6 rounded-xl font-bold text-xs uppercase tracking-widest"><i class="fa fa-cog"></i> Settings</a>
                </div>
            </div>
            <div class="grid gap-4">
                {{% for m in movies %}}
                <div class="glass p-4 rounded-2xl flex justify-between items-center">
                    <div class="flex items-center gap-4">
                        <img src="{{{{ m.poster }}}}" class="w-12 h-16 object-cover rounded">
                        <div>
                            <h3 class="font-bold">{{{{ m.name }}}}</h3>
                            <span class="text-[9px] font-bold text-gray-500 uppercase tracking-widest">{{{{ m.category }}}}</span>
                        </div>
                    </div>
                    <div class="flex gap-3">
                        <a href="/admin/edit/{{{{ m._id }}}}" class="text-yellow-500 p-2 hover:bg-white/5 rounded-xl transition"><i class="fa fa-edit"></i></a>
                        <a href="/admin/delete/{{{{ m._id }}}}" class="text-red-500 p-2 hover:bg-white/5 rounded-xl transition" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                    </div>
                </div>
                {{% endfor %}}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, movies=movies)

@app.route('/admin/save_movie', methods=['POST'])
def save_movie_data():
    mid = request.form.get('id')
    data = {
        "name": request.form['name'], "poster": request.form['poster'],
        "year": request.form['year'], "lang": request.form['lang'],
        "category": request.form['category'].upper(),
        "tag1": request.form['tag1'], "tag2": request.form['tag2'],
        "tag3": request.form['tag3'], "tag4": request.form['tag4'],
        "story": request.form['story'],
        "in_slider": request.form.get('in_slider', 'off')
    }
    if mid:
        movies_col.update_one({"_id": ObjectId(mid)}, {"$set": data})
    else:
        data['episodes'] = []
        movies_col.insert_one(data)
    return redirect('/admin')

@app.route('/admin/add')
@app.route('/admin/edit/<id>')
def movie_form(id=None):
    movie = movies_col.find_one({"_id": ObjectId(id)}) if id else None
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD_CSS}</head>
    <body class="p-6">
        <form method="POST" action="/admin/save_movie" class="max-w-4xl mx-auto glass p-10 rounded-[2.5rem] border border-white/10">
            <input type="hidden" name="id" value="{{{{ movie._id if movie else '' }}}}">
            <h2 class="text-2xl font-black mb-8 italic uppercase text-blue-500">Movie Settings</h2>
            
            <div class="grid md:grid-cols-2 gap-6 mb-6">
                <input name="name" value="{{{{ movie.name if movie else '' }}}}" placeholder="Movie Name" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none" required>
                <input name="poster" value="{{{{ movie.poster if movie else '' }}}}" placeholder="Poster URL" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                <input name="category" value="{{{{ movie.category if movie else '' }}}}" placeholder="Category (Action, Horror, etc.)" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                <div class="flex gap-4">
                    <input name="year" value="{{{{ movie.year if movie else '' }}}}" placeholder="Year" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                    <input name="lang" value="{{{{ movie.lang if movie else '' }}}}" placeholder="Lang" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 outline-none">
                </div>
            </div>

            <div class="flex items-center gap-2 mb-6 bg-blue-600/10 p-4 rounded-2xl border border-blue-500/20">
                <input type="checkbox" name="in_slider" {{{{ 'checked' if movie and movie.in_slider == 'on' else '' }}}} class="w-5 h-5">
                <label class="text-sm font-bold text-blue-400">Show this movie in Home Slider</label>
            </div>

            <div class="grid grid-cols-4 gap-2 mb-6">
                <input name="tag1" value="{{{{ movie.tag1 if movie else '' }}}}" placeholder="Top Left" class="bg-black/40 p-3 rounded-xl border border-gray-800 text-xs">
                <input name="tag2" value="{{{{ movie.tag2 if movie else '' }}}}" placeholder="Top Right" class="bg-black/40 p-3 rounded-xl border border-gray-800 text-xs">
                <input name="tag3" value="{{{{ movie.tag3 if movie else '' }}}}" placeholder="Bottom Left" class="bg-black/40 p-3 rounded-xl border border-gray-800 text-xs">
                <input name="tag4" value="{{{{ movie.tag4 if movie else '' }}}}" placeholder="Bottom Right" class="bg-black/40 p-3 rounded-xl border border-gray-800 text-xs">
            </div>

            <textarea name="story" placeholder="Story..." class="w-full bg-black/40 p-4 rounded-2xl h-32 border border-gray-800 outline-none mb-6 text-sm leading-relaxed">{{{{ movie.story if movie else '' }}}}</textarea>
            
            <div class="flex gap-4">
                <button class="bg-blue-600 py-4 px-10 rounded-2xl font-black grow shadow-2xl shadow-blue-600/20 uppercase tracking-widest">SAVE MOVIE</button>
                {{% if id %}}
                <a href="/admin/episodes/{{{{ id }}}}" class="bg-gray-800 px-10 py-4 rounded-2xl font-black text-blue-400 text-center uppercase tracking-widest">Episodes</a>
                {{% endif %}}
            </div>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, movie=movie, id=id)

# --- ইপিসোড সিস্টেম (FIXED) ---

@app.route('/admin/episodes/<mid>')
def manage_episodes_list(mid):
    movie = movies_col.find_one({"_id": ObjectId(mid)})
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD_CSS}</head>
    <body class="p-6">
        <div class="max-w-4xl mx-auto">
            <div class="flex justify-between items-center mb-10">
                <h2 class="text-2xl font-black italic text-blue-500 uppercase tracking-tighter">Episodes: {{{{ movie.name }}}}</h2>
                <a href="/admin/episode/add/{{{{ mid }}}}" class="bg-green-600 p-3 px-8 rounded-xl font-bold text-xs uppercase tracking-widest shadow-xl">+ New Episode</a>
            </div>
            <div class="grid gap-4">
                {{% for ep in movie.episodes %}}
                <div class="glass p-6 rounded-3xl flex justify-between items-center border border-white/5">
                    <span class="font-bold italic uppercase tracking-widest text-sm">Episode {{{{ ep.ep_no }}}}</span>
                    <div class="flex gap-4">
                        <a href="/admin/episode/edit/{{{{ mid }}}}/{{{{ loop.index0 }}}}" class="text-yellow-500 hover:scale-110 transition"><i class="fa fa-edit"></i></a>
                        <a href="/admin/episode/delete/{{{{ mid }}}}/{{{{ loop.index0 }}}}" class="text-red-500 hover:scale-110 transition" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                    </div>
                </div>
                {{% endfor %}}
            </div>
            <div class="mt-12"><a href="/admin" class="text-gray-500 font-bold underline hover:text-white transition">← Back Dashboard</a></div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, movie=movie, mid=mid)

@app.route('/admin/episode/save', methods=['POST'])
def save_episode_data():
    mid = request.form['mid']
    idx = request.form.get('idx')
    links = []
    for i in [1, 2]:
        links.append({
            "quality": request.form.get(f'q{i}_n'),
            "stream": shorten_link(request.form.get(f'q{i}_s')),
            "download": shorten_link(request.form.get(f'q{i}_d')),
            "telegram": shorten_link(request.form.get(f'q{i}_t'))
        })
    new_ep = {"ep_no": request.form['ep_no'], "links": links}
    movie = movies_col.find_one({"_id": ObjectId(mid)})
    if idx:
        movie['episodes'][int(idx)] = new_ep
        movies_col.update_one({"_id": ObjectId(mid)}, {"$set": {"episodes": movie['episodes']}})
    else:
        movies_col.update_one({"_id": ObjectId(mid)}, {"$push": {"episodes": new_ep}})
    return redirect(f'/admin/episodes/{mid}')

@app.route('/admin/episode/add/<mid>')
@app.route('/admin/episode/edit/<mid>/<int:idx>')
def episode_form(mid, idx=None):
    movie = movies_col.find_one({"_id": ObjectId(mid)})
    ep = movie['episodes'][idx] if idx is not None else None
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD_CSS}</head>
    <body class="p-6">
        <form method="POST" action="/admin/episode/save" class="max-w-2xl mx-auto glass p-10 rounded-[2.5rem] border border-white/10">
            <input type="hidden" name="mid" value="{{{{ mid }}}}">
            <input type="hidden" name="idx" value="{{{{ idx if idx is not None else '' }}}}">
            <h2 class="text-2xl font-black italic mb-10 uppercase text-blue-500 tracking-tighter">Episode Settings</h2>
            <input name="ep_no" value="{{{{ ep.ep_no if ep else '' }}}}" placeholder="Episode Number (e.g. 01)" class="w-full bg-black/40 p-5 rounded-2xl mb-8 border border-blue-600/30 outline-none font-bold" required>
            {{% for i in [1, 2] %}}
            <div class="bg-black/30 p-6 rounded-2xl border border-gray-800 space-y-4 mb-6 shadow-inner">
                <h3 class="text-blue-500 font-bold text-[10px] uppercase italic tracking-[0.2em] mb-4 opacity-50">Quality {{{{ i }}}} Links</h3>
                <input name="q{{{{i}}}}_n" value="{{{{ ep.links[i-1].quality if ep else '' }}}}" placeholder="Quality Name (e.g. 1080p)" class="w-full bg-black/40 p-3 rounded-xl border border-gray-800 outline-none text-sm">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input name="q{{{{i}}}}_s" value="{{{{ ep.links[i-1].stream if ep else '' }}}}" placeholder="Stream URL" class="bg-black/40 p-3 rounded-xl text-[10px] border border-gray-800 outline-none">
                    <input name="q{{{{i}}}}_d" value="{{{{ ep.links[i-1].download if ep else '' }}}}" placeholder="Download URL" class="bg-black/40 p-3 rounded-xl text-[10px] border border-gray-800 outline-none">
                    <input name="q{{{{i}}}}_t" value="{{{{ ep.links[i-1].telegram if ep else '' }}}}" placeholder="Telegram URL" class="bg-black/40 p-3 rounded-xl text-[10px] border border-gray-800 outline-none">
                </div>
            </div>
            {{% endfor %}}
            <button class="w-full bg-blue-600 p-5 rounded-2xl font-black shadow-2xl shadow-blue-600/30 uppercase tracking-[0.1em]">SAVE EPISODE</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, mid=mid, ep=ep, idx=idx)

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        settings_col.update_one({"type": "config"}, {"$set": {"api": request.form['api'], "limit": request.form['limit']}}, upsert=True)
        settings_col.update_one({"type": "ads"}, {"$set": {"top": request.form['top'], "bottom": request.form['bottom'], "popup": request.form['popup']}}, upsert=True)
        return redirect('/admin')
    cfg = settings_col.find_one({"type": "config"}) or {}
    ads = settings_col.find_one({"type": "ads"}) or {}
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD_CSS}</head>
    <body class="p-6">
        <form method="POST" class="max-w-4xl mx-auto glass p-10 rounded-[3rem] space-y-8 border border-white/5">
            <h2 class="text-3xl font-black italic text-blue-500 uppercase tracking-tighter">Site Management</h2>
            <div class="grid md:grid-cols-2 gap-6">
                <div>
                    <label class="text-[10px] font-black text-gray-500 uppercase ml-2 tracking-widest">Shortener API (use {{url}})</label>
                    <input name="api" value="{{{{ cfg.api if cfg else '' }}}}" placeholder="https://api.com/st?api=KEY&url={{url}}" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 mt-2 outline-none">
                </div>
                <div>
                    <label class="text-[10px] font-black text-gray-500 uppercase ml-2 tracking-widest">Home Page Movie Limit</label>
                    <input name="limit" type="number" value="{{{{ cfg.limit if cfg else 15 }}}}" class="w-full bg-black/40 p-4 rounded-2xl border border-gray-800 mt-2 outline-none">
                </div>
            </div>
            <div class="grid md:grid-cols-2 gap-8">
                <div class="col-span-2 md:col-span-1">
                    <label class="text-[10px] font-black text-yellow-500 uppercase ml-2 tracking-widest italic">Header Ad Code (HTML/JS)</label>
                    <textarea name="top" class="w-full bg-black/40 p-4 rounded-2xl h-40 border border-gray-800 mt-2 text-[10px] font-mono leading-relaxed">{{{{ ads.top if ads else '' }}}}</textarea>
                </div>
                <div class="col-span-2 md:col-span-1">
                    <label class="text-[10px] font-black text-yellow-500 uppercase ml-2 tracking-widest italic">Footer Ad Code (HTML/JS)</label>
                    <textarea name="bottom" class="w-full bg-black/40 p-4 rounded-2xl h-40 border border-gray-800 mt-2 text-[10px] font-mono leading-relaxed">{{{{ ads.bottom if ads else '' }}}}</textarea>
                </div>
                <div class="col-span-2">
                    <label class="text-[10px] font-black text-red-500 uppercase ml-2 tracking-widest italic">Popup / Overlay / Tracking Code</label>
                    <textarea name="popup" class="w-full bg-black/40 p-4 rounded-2xl h-32 border border-gray-800 mt-2 text-[10px] font-mono leading-relaxed">{{{{ ads.popup if ads else '' }}}}</textarea>
                </div>
            </div>
            <button class="w-full bg-blue-600 p-5 rounded-2xl font-black shadow-2xl shadow-blue-600/20 uppercase tracking-widest">UPDATE SETTINGS</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, cfg=cfg, ads=ads)

@app.route('/admin/delete/<id>')
def delete_movie(id):
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/admin/episode/delete/<mid>/<int:idx>')
def delete_episode(mid, idx):
    movie = movies_col.find_one({"_id": ObjectId(mid)})
    movie['episodes'].pop(idx)
    movies_col.update_one({"_id": ObjectId(mid)}, {"$set": {"episodes": movie['episodes']}})
    return redirect(f'/admin/episodes/{mid}')

if __name__ == '__main__':
    app.run(debug=True)
