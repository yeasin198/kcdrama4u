from flask import Flask, render_template_string, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests

app = Flask(__name__)
app.secret_key = "advance_movie_key_99"

# --- MongoDB কানেকশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.pro_movie_db
movies_col = db.movies
settings_col = db.settings  # অ্যাড এবং API সেটিংসের জন্য

# --- Helper Function: URL Shortener ---
def shorten_link(url):
    settings = settings_col.find_one({"type": "config"})
    if settings and settings.get('shortener_api') and url:
        api_url = settings.get('shortener_api').replace("{url}", url)
        try:
            r = requests.get(api_url, timeout=5)
            # অনেক API সরাসরি টেক্সট দেয়, কেউ JSON দেয়। এখানে জেনেরিক রাখা হলো।
            return r.text if r.status_code == 200 else url
        except:
            return url
    return url

# --- UI Components ---
HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    body { background-color: #0f172a; color: white; font-family: 'Segoe UI', sans-serif; }
    .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
    .corner-tag { position: absolute; padding: 2px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; z-index: 10; }
</style>
"""

def get_ads():
    ad_data = settings_col.find_one({"type": "ads"})
    return ad_data if ad_data else {"top": "", "bottom": "", "popup": ""}

# --- Routes ---

# ১. ইউজার হোম (সার্চসহ)
@app.route('/')
def index():
    query = request.args.get('q')
    ads = get_ads()
    if query:
        movies = list(movies_col.find({"name": {"$regex": query, "$options": "i"}}))
    else:
        movies = list(movies_col.find())
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}<title>Movie Home</title></head>
    <body>
        <nav class="p-4 glass sticky top-0 z-50 flex justify-between items-center px-6">
            <a href="/" class="text-2xl font-black text-blue-500">MOVIE<span class="text-white">NET</span></a>
            <form action="/" method="GET" class="hidden md:flex bg-gray-800 rounded-lg">
                <input name="q" placeholder="Search movies..." class="bg-transparent p-2 px-4 outline-none w-64">
                <button class="px-4 text-blue-500"><i class="fa fa-search"></i></button>
            </form>
            <a href="/admin" class="bg-blue-600 px-4 py-2 rounded-lg text-sm font-bold">Admin</a>
        </nav>
        
        <div class="max-w-7xl mx-auto p-4">
            <div class="my-4 text-center">{ads['top']}</div> <!-- Top Ad -->
            
            <form action="/" method="GET" class="md:hidden flex mb-6 bg-gray-800 rounded-lg">
                <input name="q" placeholder="Search..." class="bg-transparent p-3 flex-grow outline-none">
                <button class="px-6 bg-blue-600 rounded-r-lg"><i class="fa fa-search"></i></button>
            </form>

            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
                {{% for movie in movies %}}
                <a href="/movie/{{{{ movie._id }}}}" class="relative group block bg-gray-800 rounded-xl overflow-hidden shadow-lg border border-gray-700">
                    <span class="corner-tag top-2 left-2 bg-blue-600">{{{{ movie.tag1 }}}}</span>
                    <span class="corner-tag top-2 right-2 bg-red-600">{{{{ movie.tag2 }}}}</span>
                    <span class="corner-tag bottom-2 left-2 bg-yellow-500 text-black">{{{{ movie.tag3 }}}}</span>
                    <span class="corner-tag bottom-2 right-2 bg-green-600">{{{{ movie.tag4 }}}}</span>
                    <img src="{{{{ movie.poster }}}}" class="w-full h-64 md:h-80 object-cover group-hover:scale-105 transition duration-500">
                    <div class="p-3">
                        <h3 class="font-bold truncate text-sm">{{{{ movie.name }}}}</h3>
                        <p class="text-xs text-gray-400 mt-1">{{{{ movie.year }}}} | {{{{ movie.lang }}}}</p>
                    </div>
                </a>
                {{% endfor %}}
            </div>
            
            <div class="my-8 text-center">{ads['bottom']}</div> <!-- Bottom Ad -->
        </div>
        {ads['popup']} <!-- Popup Ad Code -->
    </body>
    </html>
    """
    return render_template_string(html, movies=movies)

# ২. মুভি ডিটেইলস ও ইপিসোড লিস্ট
@app.route('/movie/<id>')
def movie_details(id):
    movie = movies_col.find_one({"_id": ObjectId(id)})
    ads = get_ads()
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}<title>{{{{ movie.name }}}}</title></head>
    <body>
        <div class="max-w-5xl mx-auto p-4 py-8">
            <a href="/" class="inline-block mb-6 text-blue-500"><i class="fa fa-arrow-left"></i> Back to Home</a>
            <div class="md:flex gap-8 glass p-6 rounded-3xl">
                <img src="{{{{ movie.poster }}}}" class="w-full md:w-72 rounded-2xl shadow-2xl mb-6 md:mb-0 border border-gray-700">
                <div class="flex-grow">
                    <h1 class="text-3xl md:text-5xl font-black">{{{{ movie.name }}}}</h1>
                    <div class="flex gap-4 my-4">
                        <span class="bg-gray-700 px-3 py-1 rounded text-sm">{{{{ movie.year }}}}</span>
                        <span class="bg-blue-900/50 text-blue-400 px-3 py-1 rounded text-sm font-bold">{{{{ movie.lang }}}}</span>
                    </div>
                    <p class="text-gray-400 leading-relaxed text-sm md:text-base">{{{{ movie.story }}}}</p>
                </div>
            </div>

            <div class="mt-10">{ads['top']}</div>

            <div class="mt-12">
                <h2 class="text-2xl font-bold mb-6 flex items-center gap-3">
                    <div class="w-2 h-8 bg-blue-600 rounded"></div> Watch Episodes
                </h2>
                <div class="space-y-6">
                    {{% for ep in movie.episodes %}}
                    <div class="glass p-5 rounded-2xl border-l-4 border-blue-500">
                        <h3 class="font-bold text-lg mb-4 text-blue-300">Episode: {{{{ ep.ep_no }}}}</h3>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {{% for link in ep.links %}}
                            <div class="bg-gray-900/50 p-4 rounded-xl border border-gray-700">
                                <span class="text-[10px] font-black uppercase text-gray-500 tracking-widest">{{{{ link.quality }}}} Quality</span>
                                <div class="flex flex-wrap gap-2 mt-3">
                                    <a href="{{{{ link.stream }}}}" target="_blank" class="bg-blue-600 hover:bg-blue-700 p-2 px-4 rounded-lg text-xs font-bold"><i class="fa fa-play mr-1"></i> Stream</a>
                                    <a href="{{{{ link.download }}}}" target="_blank" class="bg-green-600 hover:bg-green-700 p-2 px-4 rounded-lg text-xs font-bold"><i class="fa fa-download mr-1"></i> Download</a>
                                    <a href="{{{{ link.telegram }}}}" target="_blank" class="bg-sky-500 hover:bg-sky-600 p-2 px-4 rounded-lg text-xs font-bold"><i class="fab fa-telegram mr-1"></i> Telegram</a>
                                </div>
                            </div>
                            {{% endfor %}}
                        </div>
                    </div>
                    {{% endfor %}}
                </div>
            </div>
            <div class="mt-10">{ads['bottom']}</div>
        </div>
        {ads['popup']}
    </body>
    </html>
    """
    return render_template_string(html, movie=movie)

# --- এডমিন প্যানেল ---

# এডমিন হোম ও সার্চ
@app.route('/admin')
def admin_home():
    q = request.args.get('q')
    if q:
        movies = list(movies_col.find({"name": {"$regex": q, "$options": "i"}}))
    else:
        movies = list(movies_col.find())
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}<title>Admin</title></head>
    <body class="bg-gray-950">
        <div class="flex min-h-screen">
            <!-- Sidebar -->
            <div class="w-64 glass p-6 hidden md:block border-r border-gray-800">
                <h2 class="text-xl font-bold text-blue-500 mb-10">ADMIN PANEL</h2>
                <nav class="space-y-4">
                    <a href="/admin" class="block p-3 bg-blue-600 rounded-lg font-bold">Movies List</a>
                    <a href="/admin/add" class="block p-3 hover:bg-gray-800 rounded-lg transition">Add New Movie</a>
                    <a href="/admin/settings" class="block p-3 hover:bg-gray-800 rounded-lg transition">Settings & Ads</a>
                </nav>
            </div>
            <!-- Main Content -->
            <div class="flex-grow p-4 md:p-8">
                <div class="flex flex-col md:flex-row justify-between mb-8 gap-4">
                    <form action="/admin" class="flex bg-gray-800 rounded-lg w-full md:w-96 border border-gray-700">
                        <input name="q" placeholder="Search movies..." class="bg-transparent p-2 px-4 flex-grow outline-none">
                        <button class="px-4 text-blue-500"><i class="fa fa-search"></i></button>
                    </form>
                    <a href="/admin/add" class="bg-green-600 px-6 py-2 rounded-lg font-bold text-center">+ Add Movie</a>
                </div>

                <div class="grid gap-4">
                    {{% for movie in movies %}}
                    <div class="glass p-4 rounded-xl flex items-center justify-between border border-gray-800">
                        <div class="flex items-center gap-4">
                            <img src="{{{{ movie.poster }}}}" class="w-12 h-16 rounded object-cover">
                            <div>
                                <h3 class="font-bold text-sm md:text-base">{{{{ movie.name }}}}</h3>
                                <p class="text-xs text-gray-500">{{{{ movie.year }}}}</p>
                            </div>
                        </div>
                        <div class="flex gap-2">
                            <a href="/admin/edit/{{{{ movie._id }}}}" class="p-2 text-yellow-500 hover:bg-yellow-500/10 rounded"><i class="fa fa-edit"></i></a>
                            <a href="/admin/delete/{{{{ movie._id }}}}" class="p-2 text-red-500 hover:bg-red-500/10 rounded" onclick="return confirm('Delete this movie?')"><i class="fa fa-trash"></i></a>
                        </div>
                    </div>
                    {{% endfor %}}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, movies=movies)

# মুভি অ্যাড ও এডিট (একই ফর্ম)
@app.route('/admin/save_movie', methods=['POST'])
@app.route('/admin/add')
@app.route('/admin/edit/<id>')
def manage_movie(id=None):
    movie = None
    if id:
        movie = movies_col.find_one({"_id": ObjectId(id)})
    
    if request.method == 'POST':
        movie_id = request.form.get('id')
        data = {
            "name": request.form['name'],
            "poster": request.form['poster'],
            "year": request.form['year'],
            "lang": request.form['lang'],
            "tag1": request.form['tag1'], "tag2": request.form['tag2'],
            "tag3": request.form['tag3'], "tag4": request.form['tag4'],
            "story": request.form['story']
        }
        if movie_id:
            movies_col.update_one({"_id": ObjectId(movie_id)}, {"$set": data})
        else:
            data['episodes'] = []
            movies_col.insert_one(data)
        return redirect('/admin')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}</head>
    <body class="p-4 md:p-10">
        <div class="max-w-3xl mx-auto glass p-8 rounded-3xl border border-gray-700">
            <h2 class="text-2xl font-black mb-8">{'Edit Movie' if id else 'Add New Movie'}</h2>
            <form action="/admin/save_movie" method="POST" class="grid grid-cols-2 gap-6">
                <input type="hidden" name="id" value="{{{{ movie._id if movie else '' }}}}">
                <div class="col-span-2">
                    <label class="text-xs text-gray-500 font-bold ml-1">MOVIE NAME</label>
                    <input name="name" value="{{{{ movie.name if movie else '' }}}}" class="w-full bg-gray-950 p-3 rounded-xl mt-1 border border-gray-800 focus:border-blue-500 outline-none" required>
                </div>
                <div class="col-span-2">
                    <label class="text-xs text-gray-500 font-bold ml-1">POSTER URL</label>
                    <input name="poster" value="{{{{ movie.poster if movie else '' }}}}" class="w-full bg-gray-950 p-3 rounded-xl mt-1 border border-gray-800 focus:border-blue-500 outline-none">
                </div>
                <div>
                    <label class="text-xs text-gray-500 font-bold ml-1">YEAR</label>
                    <input name="year" value="{{{{ movie.year if movie else '' }}}}" class="w-full bg-gray-950 p-3 rounded-xl mt-1 border border-gray-800 outline-none">
                </div>
                <div>
                    <label class="text-xs text-gray-500 font-bold ml-1">LANGUAGE</label>
                    <input name="lang" value="{{{{ movie.lang if movie else '' }}}}" class="w-full bg-gray-950 p-3 rounded-xl mt-1 border border-gray-800 outline-none">
                </div>
                <div class="col-span-2 grid grid-cols-4 gap-2">
                    <input name="tag1" value="{{{{ movie.tag1 if movie else '' }}}}" placeholder="Tag 1" class="bg-gray-950 p-2 rounded-lg text-xs border border-gray-800">
                    <input name="tag2" value="{{{{ movie.tag2 if movie else '' }}}}" placeholder="Tag 2" class="bg-gray-950 p-2 rounded-lg text-xs border border-gray-800">
                    <input name="tag3" value="{{{{ movie.tag3 if movie else '' }}}}" placeholder="Tag 3" class="bg-gray-950 p-2 rounded-lg text-xs border border-gray-800">
                    <input name="tag4" value="{{{{ movie.tag4 if movie else '' }}}}" placeholder="Tag 4" class="bg-gray-950 p-2 rounded-lg text-xs border border-gray-800">
                </div>
                <div class="col-span-2">
                    <label class="text-xs text-gray-500 font-bold ml-1">STORYLINE</label>
                    <textarea name="story" class="w-full bg-gray-950 p-3 rounded-xl mt-1 h-32 border border-gray-800 outline-none">{{{{ movie.story if movie else '' }}}}</textarea>
                </div>
                <div class="col-span-2 flex gap-4">
                    <button class="flex-grow bg-blue-600 py-4 rounded-2xl font-bold hover:bg-blue-700 transition">Save Movie</button>
                    {{% if id %}}
                    <a href="/admin/episodes/{{{{ movie._id }}}}" class="bg-gray-800 px-6 py-4 rounded-2xl font-bold text-blue-400">Manage Episodes</a>
                    {{% endif %}}
                </div>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, movie=movie, id=id)

# ইপিসোড ম্যানেজমেন্ট (লিঙ্ক শর্ট সহ)
@app.route('/admin/episodes/<id>')
def episode_list(id):
    movie = movies_col.find_one({"_id": ObjectId(id)})
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}</head>
    <body class="p-6">
        <div class="max-w-4xl mx-auto">
            <div class="flex justify-between items-center mb-10">
                <h2 class="text-2xl font-bold">Episodes of {{{{ movie.name }}}}</h2>
                <a href="/admin/episode/add/{{{{ movie._id }}}}" class="bg-blue-600 px-6 py-2 rounded-lg font-bold">+ New Episode</a>
            </div>
            <div class="space-y-4">
                {{% for ep in movie.episodes %}}
                <div class="glass p-5 rounded-2xl flex justify-between items-center border border-gray-800">
                    <span class="font-bold text-lg">Episode {{{{ ep.ep_no }}}}</span>
                    <div class="flex gap-4">
                        <a href="/admin/episode/edit/{{{{ movie._id }}}}/{{{{ loop.index0 }}}}" class="text-yellow-500">Edit</a>
                        <a href="/admin/episode/delete/{{{{ movie._id }}}}/{{{{ loop.index0 }}}}" class="text-red-500" onclick="return confirm('Delete episode?')">Delete</a>
                    </div>
                </div>
                {{% endfor %}}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, movie=movie)

@app.route('/admin/episode/save', methods=['POST'])
@app.route('/admin/episode/add/<mid>')
@app.route('/admin/episode/edit/<mid>/<int:index>')
def manage_episode(mid, index=None):
    movie = movies_col.find_one({"_id": ObjectId(mid)})
    episode = movie['episodes'][index] if index is not None else None
    
    if request.method == 'POST':
        mid = request.form['mid']
        idx = request.form.get('index')
        
        # লিঙ্ক শর্ট করা হচ্ছে যদি API থাকে
        links = []
        for i in range(1, 3): # কোয়ালিটি ১ ও ২
            links.append({
                "quality": request.form.get(f'q{i}_name'),
                "stream": shorten_link(request.form.get(f'q{i}_stream')),
                "download": shorten_link(request.form.get(f'q{i}_down')),
                "telegram": shorten_link(request.form.get(f'q{i}_tele'))
            })
        
        new_ep = {"ep_no": request.form['ep_no'], "links": links}
        
        if idx:
            movie['episodes'][int(idx)] = new_ep
            movies_col.update_one({"_id": ObjectId(mid)}, {"$set": {"episodes": movie['episodes']}})
        else:
            movies_col.update_one({"_id": ObjectId(mid)}, {"$push": {"episodes": new_ep}})
        return redirect(f'/admin/episodes/{mid}')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}</head>
    <body class="p-6">
        <form method="POST" action="/admin/episode/save" class="max-w-2xl mx-auto glass p-8 rounded-3xl">
            <input type="hidden" name="mid" value="{{{{ mid }}}}">
            <input type="hidden" name="index" value="{{{{ index if index is not None else '' }}}}">
            <h2 class="text-2xl font-bold mb-8 italic">Episode Settings</h2>
            <input name="ep_no" value="{{{{ episode.ep_no if episode else '' }}}}" placeholder="Episode No (e.g. 01)" class="w-full bg-gray-950 p-4 rounded-xl mb-8 border border-blue-500/30 outline-none shadow-inner" required>
            
            {{% for i in [0, 1] %}}
            <div class="bg-gray-900/50 p-6 rounded-2xl mb-6 border border-gray-800">
                <h3 class="text-blue-500 font-bold mb-4 uppercase text-sm">Quality {{{{ i+1 }}}} Links</h3>
                <input name="q{{{{ i+1 }}}}_name" value="{{{{ episode.links[i].quality if episode else '' }}}}" placeholder="Quality (720p/1080p)" class="w-full bg-gray-950 p-3 rounded-lg mb-4 border border-gray-800 outline-none">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input name="q{{{{ i+1 }}}}_stream" value="{{{{ episode.links[i].stream if episode else '' }}}}" placeholder="Stream URL" class="bg-gray-950 p-3 rounded-lg text-xs border border-gray-800">
                    <input name="q{{{{ i+1 }}}}_down" value="{{{{ episode.links[i].download if episode else '' }}}}" placeholder="Download URL" class="bg-gray-950 p-3 rounded-lg text-xs border border-gray-800">
                    <input name="q{{{{ i+1 }}}}_tele" value="{{{{ episode.links[i].telegram if episode else '' }}}}" placeholder="Telegram URL" class="bg-gray-950 p-3 rounded-lg text-xs border border-gray-800">
                </div>
            </div>
            {{% endfor %}}
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-bold">Save Episode Links</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, mid=mid, episode=episode, index=index)

# ৩. সেটিংস ও অ্যাড ম্যানেজমেন্ট
@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        settings_col.update_one({"type": "config"}, {"$set": {"shortener_api": request.form['api']}}, upsert=True)
        settings_col.update_one({"type": "ads"}, {"$set": {
            "top": request.form['ad_top'],
            "bottom": request.form['ad_bottom'],
            "popup": request.form['ad_popup']
        }}, upsert=True)
        return redirect('/admin')
    
    cfg = settings_col.find_one({"type": "config"}) or {}
    ads = settings_col.find_one({"type": "ads"}) or {}
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}</head>
    <body class="p-6">
        <form method="POST" class="max-w-4xl mx-auto glass p-8 rounded-3xl space-y-8">
            <h2 class="text-2xl font-bold border-b border-gray-800 pb-4">Site Settings</h2>
            
            <div>
                <label class="block text-sm font-bold text-blue-500 mb-2">URL Shortener API URL (Use {{url}} as placeholder)</label>
                <input name="api" value="{{{{ cfg.shortener_api if cfg else '' }}}}" placeholder="https://api.shorter.com/st?api=KEY&url={{url}}" class="w-full bg-gray-950 p-4 rounded-xl border border-gray-800 outline-none">
            </div>

            <div class="grid md:grid-cols-2 gap-8">
                <div class="col-span-2 md:col-span-1">
                    <label class="block text-sm font-bold text-yellow-500 mb-2">Header / Top Ad Code</label>
                    <textarea name="ad_top" class="w-full bg-gray-950 p-4 rounded-xl h-32 border border-gray-800 text-xs">{{{{ ads.top if ads else '' }}}}</textarea>
                </div>
                <div class="col-span-2 md:col-span-1">
                    <label class="block text-sm font-bold text-yellow-500 mb-2">Footer / Bottom Ad Code</label>
                    <textarea name="ad_bottom" class="w-full bg-gray-950 p-4 rounded-xl h-32 border border-gray-800 text-xs">{{{{ ads.bottom if ads else '' }}}}</textarea>
                </div>
                <div class="col-span-2">
                    <label class="block text-sm font-bold text-red-500 mb-2">Popup / Direct Link / JS Code</label>
                    <textarea name="ad_popup" class="w-full bg-gray-950 p-4 rounded-xl h-32 border border-gray-800 text-xs">{{{{ ads.popup if ads else '' }}}}</textarea>
                </div>
            </div>
            <button class="w-full bg-green-600 py-4 rounded-2xl font-bold">Save All Settings</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, cfg=cfg, ads=ads)

@app.route('/admin/delete/<id>')
def delete_movie(id):
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/admin/episode/delete/<mid>/<int:index>')
def delete_episode(mid, index):
    movie = movies_col.find_one({"_id": ObjectId(mid)})
    movie['episodes'].pop(index)
    movies_col.update_one({"_id": ObjectId(mid)}, {"$set": {"episodes": movie['episodes']}})
    return redirect(f'/admin/episodes/{mid}')

if __name__ == '__main__':
    app.run(debug=True)
