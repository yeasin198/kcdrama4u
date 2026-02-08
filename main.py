from flask import Flask, render_template_string, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "super_secret_movie_key"

# --- MongoDB কানেকশন (এখানে আপনার URI দিন) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.movie_site_db
movies_col = db.movies

# --- CSS & Layout ---
HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    body { background-color: #0b0f19; color: white; font-family: 'Inter', sans-serif; }
    .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
    .corner-tag { position: absolute; padding: 2px 6px; font-size: 10px; font-weight: bold; border-radius: 4px; z-index: 10; }
</style>
"""

NAV = """
<nav class="p-4 glass sticky top-0 z-50 flex justify-between items-center px-6">
    <a href="/" class="text-2xl font-black text-blue-500 tracking-tighter">MOVIE<span class="text-white">PRO</span></a>
    <div class="space-x-4">
        <a href="/" class="hover:text-blue-400">Home</a>
        <a href="/admin" class="bg-blue-600 px-4 py-2 rounded-lg text-sm font-bold">Admin</a>
    </div>
</nav>
"""

# --- ROUTES ---

# ১. হোমপেজ (ইউজার প্যানেল)
@app.route('/')
def index():
    movies = list(movies_col.find())
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}<title>MoviePro - Home</title></head>
    <body>
        {NAV}
        <div class="max-w-7xl mx-auto p-6">
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
                {{% for movie in movies %}}
                <a href="/movie/{{{{ movie._id }}}}" class="relative group block">
                    <div class="relative overflow-hidden rounded-xl shadow-2xl">
                        <!-- ৪ কোণায় ৪টি ট্যাগ -->
                        <span class="corner-tag top-2 left-2 bg-blue-600">{{{{ movie.tag1 }}}}</span>
                        <span class="corner-tag top-2 right-2 bg-yellow-500 text-black">{{{{ movie.tag2 }}}}</span>
                        <span class="corner-tag bottom-2 left-2 bg-red-600">{{{{ movie.tag3 }}}}</span>
                        <span class="corner-tag bottom-2 right-2 bg-green-600">{{{{ movie.tag4 }}}}</span>
                        
                        <img src="{{{{ movie.poster }}}}" class="w-full h-72 object-cover group-hover:scale-110 transition duration-500">
                        <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-80"></div>
                    </div>
                    <div class="mt-3">
                        <h3 class="font-bold truncate text-sm">{{{{ movie.name }}}}</h3>
                        <p class="text-xs text-gray-400">{{{{ movie.year }}}} • {{{{ movie.lang }}}}</p>
                    </div>
                </a>
                {{% endfor %}}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, movies=movies)

# ২. মুভি ডিটেইলস পেজ (ইপিসোড এবং ডাউনলোড লিঙ্ক)
@app.route('/movie/<id>')
def movie_details(id):
    movie = movies_col.find_one({"_id": ObjectId(id)})
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}<title>{{{{ movie.name }}}}</title></head>
    <body>
        {NAV}
        <div class="max-w-5xl mx-auto p-6">
            <div class="md:flex gap-8">
                <img src="{{{{ movie.poster }}}}" class="w-full md:w-64 rounded-2xl shadow-2xl mb-6 md:mb-0">
                <div>
                    <h1 class="text-4xl font-bold">{{{{ movie.name }}}} ({{{{ movie.year }}}})</h1>
                    <p class="text-blue-400 mt-2 font-semibold">Language: {{{{ movie.lang }}}}</p>
                    <div class="mt-6">
                        <h2 class="text-xl font-bold border-l-4 border-blue-500 pl-3 mb-3">Storyline</h2>
                        <p class="text-gray-400 leading-relaxed">{{{{ movie.story }}}}</p>
                    </div>
                </div>
            </div>

            <!-- ইপিসোড সেকশন -->
            <div class="mt-12">
                <h2 class="text-2xl font-bold mb-6">Episodes</h2>
                <div class="space-y-4">
                    {{% for ep in movie.episodes %}}
                    <div class="glass p-5 rounded-xl">
                        <h3 class="font-bold text-lg text-blue-400 mb-4 italic text-sm">Episode {{{{ ep.ep_no }}}}</h3>
                        <div class="flex flex-wrap gap-3">
                            {{% for link in ep.links %}}
                            <div class="bg-gray-800 p-3 rounded-lg border border-gray-700 w-full sm:w-auto">
                                <span class="text-xs font-bold block mb-2 text-gray-400 uppercase tracking-widest">{{{{ link.quality }}}} Quality</span>
                                <div class="flex gap-2">
                                    <a href="{{{{ link.stream }}}}" class="bg-blue-600 p-2 rounded text-xs px-4"><i class="fa fa-play mr-1"></i> Stream</a>
                                    <a href="{{{{ link.download }}}}" class="bg-green-600 p-2 rounded text-xs px-4"><i class="fa fa-download mr-1"></i> Download</a>
                                    <a href="{{{{ link.telegram }}}}" class="bg-sky-500 p-2 rounded text-xs px-4"><i class="fab fa-telegram mr-1"></i> Telegram</a>
                                </div>
                            </div>
                            {{% endfor %}}
                        </div>
                    </div>
                    {{% endfor %}}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, movie=movie)

# ৩. এডমিন প্যানেল - মুভি লিস্ট
@app.route('/admin')
def admin():
    movies = list(movies_col.find())
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}<title>Admin Panel</title></head>
    <body>
        {NAV}
        <div class="max-w-5xl mx-auto p-6">
            <div class="flex justify-between mb-8">
                <h1 class="text-2xl font-bold">Manage Movies</h1>
                <a href="/admin/add" class="bg-green-600 px-6 py-2 rounded-lg font-bold">Add New Movie</a>
            </div>
            <div class="grid gap-4">
                {{% for movie in movies %}}
                <div class="glass p-4 rounded-xl flex justify-between items-center">
                    <div>
                        <h3 class="font-bold">{{{{ movie.name }}}}</h3>
                        <p class="text-xs text-gray-400">Episodes: {{{{ movie.episodes|length }}}}</p>
                    </div>
                    <div class="space-x-3">
                        <a href="/admin/add_episode/{{{{ movie._id }}}}" class="text-blue-500 font-bold text-sm">+ Add Episode</a>
                        <a href="/admin/delete/{{{{ movie._id }}}}" class="text-red-500 text-sm">Delete</a>
                    </div>
                </div>
                {{% endfor %}}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, movies=movies)

# ৪. নতুন মুভি অ্যাড
@app.route('/admin/add', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        data = {
            "name": request.form['name'],
            "poster": request.form['poster'],
            "year": request.form['year'],
            "lang": request.form['lang'],
            "tag1": request.form['tag1'], "tag2": request.form['tag2'],
            "tag3": request.form['tag3'], "tag4": request.form['tag4'],
            "story": request.form['story'],
            "episodes": []
        }
        movies_col.insert_one(data)
        return redirect('/admin')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}</head>
    <body>
        {NAV}
        <div class="max-w-2xl mx-auto p-6 glass m-10 rounded-2xl">
            <h2 class="text-2xl font-bold mb-6">Upload Movie</h2>
            <form method="POST" class="grid grid-cols-2 gap-4">
                <input name="name" placeholder="Movie Name" class="bg-gray-800 p-3 rounded col-span-2 outline-none border border-gray-700 focus:border-blue-500" required>
                <input name="poster" placeholder="Poster Image URL" class="bg-gray-800 p-3 rounded col-span-2 outline-none border border-gray-700">
                <input name="year" placeholder="Year (2024)" class="bg-gray-800 p-3 rounded outline-none border border-gray-700">
                <input name="lang" placeholder="Language (Bangla/Hindi)" class="bg-gray-800 p-3 rounded outline-none border border-gray-700">
                <input name="tag1" placeholder="Top Left Tag" class="bg-gray-800 p-2 rounded text-sm outline-none border border-gray-700">
                <input name="tag2" placeholder="Top Right Tag" class="bg-gray-800 p-2 rounded text-sm outline-none border border-gray-700">
                <input name="tag3" placeholder="Bottom Left Tag" class="bg-gray-800 p-2 rounded text-sm outline-none border border-gray-700">
                <input name="tag4" placeholder="Bottom Right Tag" class="bg-gray-800 p-2 rounded text-sm outline-none border border-gray-700">
                <textarea name="story" placeholder="Storyline..." class="bg-gray-800 p-3 rounded col-span-2 h-32 outline-none border border-gray-700"></textarea>
                <button class="bg-blue-600 py-3 rounded-xl font-bold col-span-2 mt-4 hover:bg-blue-700 transition">Save Movie</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

# ৫. ইপিসোড অ্যাড করার সিস্টেম (মাল্টিপল কোয়ালিটি লিঙ্কের সাথে)
@app.route('/admin/add_episode/<id>', methods=['GET', 'POST'])
def add_episode(id):
    if request.method == 'POST':
        # এক ইপিসোডে ৩টি কোয়ালিটি অ্যাড করা হচ্ছে
        new_episode = {
            "ep_no": request.form['ep_no'],
            "links": [
                {
                    "quality": request.form['q1_name'],
                    "stream": request.form['q1_stream'],
                    "download": request.form['q1_down'],
                    "telegram": request.form['q1_tele']
                },
                {
                    "quality": request.form['q2_name'],
                    "stream": request.form['q2_stream'],
                    "download": request.form['q2_down'],
                    "telegram": request.form['q2_tele']
                }
            ]
        }
        movies_col.update_one({"_id": ObjectId(id)}, {"$push": {"episodes": new_episode}})
        return redirect('/admin')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{HEAD}</head>
    <body>
        {NAV}
        <div class="max-w-2xl mx-auto p-6 glass m-10 rounded-2xl">
            <h2 class="text-xl font-bold mb-4">Add Episode & Links</h2>
            <form method="POST">
                <input name="ep_no" placeholder="Episode Number (e.g. 01)" class="w-full bg-gray-800 p-3 rounded mb-6 border border-blue-500">
                
                <div class="grid grid-cols-2 gap-4 bg-gray-900 p-4 rounded-xl mb-6">
                    <h3 class="col-span-2 text-blue-400 font-bold underline">Quality 01 (e.g. 720p)</h3>
                    <input name="q1_name" placeholder="Quality Name" class="bg-gray-800 p-2 rounded outline-none border border-gray-700">
                    <input name="q1_stream" placeholder="Stream Link" class="bg-gray-800 p-2 rounded outline-none border border-gray-700">
                    <input name="q1_down" placeholder="Download Link" class="bg-gray-800 p-2 rounded outline-none border border-gray-700">
                    <input name="q1_tele" placeholder="Telegram Link" class="bg-gray-800 p-2 rounded outline-none border border-gray-700">
                </div>

                <div class="grid grid-cols-2 gap-4 bg-gray-900 p-4 rounded-xl">
                    <h3 class="col-span-2 text-green-400 font-bold underline">Quality 02 (e.g. 1080p)</h3>
                    <input name="q2_name" placeholder="Quality Name" class="bg-gray-800 p-2 rounded outline-none border border-gray-700">
                    <input name="q2_stream" placeholder="Stream Link" class="bg-gray-800 p-2 rounded outline-none border border-gray-700">
                    <input name="q2_down" placeholder="Download Link" class="bg-gray-800 p-2 rounded outline-none border border-gray-700">
                    <input name="q2_tele" placeholder="Telegram Link" class="bg-gray-800 p-2 rounded outline-none border border-gray-700">
                </div>

                <button class="w-full bg-blue-600 py-3 rounded-xl font-bold mt-6">Upload Episode</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/admin/delete/<id>')
def delete_movie(id):
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
