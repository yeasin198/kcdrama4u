import os
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "movies_secret_key"

# --- MongoDB Connection ---
# আপনি চাইলে এই URI টি আপনার MongoDB Atlas থেকে পরিবর্তন করে নিতে পারেন
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['webseries_db']
series_collection = db['series']

# --- CSS Design (Responsive for Mobile & Desktop) ---
COMMON_STYLE = """
<style>
    :root { --primary: #E50914; --bg: #0b0b0b; --card-bg: #1a1a1a; --text: #ffffff; --border: #333; }
    body { background-color: var(--bg); color: var(--text); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
    
    /* Header & Navigation */
    header { background: #000; padding: 15px 5%; display: flex; flex-direction: column; align-items: center; border-bottom: 2px solid var(--primary); sticky: top; position: sticky; top: 0; z-index: 1000; }
    @media (min-width: 768px) { header { flex-direction: row; justify-content: space-between; } }
    .logo { color: var(--primary); font-size: 26px; font-weight: bold; text-decoration: none; text-transform: uppercase; margin-bottom: 10px; }
    @media (min-width: 768px) { .logo { margin-bottom: 0; } }

    /* Search Box */
    .search-container { width: 100%; max-width: 500px; display: flex; background: #222; border-radius: 5px; overflow: hidden; border: 1px solid var(--border); }
    .search-container input { border: none; background: transparent; color: white; padding: 10px; width: 100%; outline: none; }
    .search-container button { background: var(--primary); border: none; color: white; padding: 0 20px; cursor: pointer; font-weight: bold; }

    /* Admin Nav Links */
    .nav-links { margin-top: 10px; font-size: 14px; }
    @media (min-width: 768px) { .nav-links { margin-top: 0; } }
    .nav-links a { color: #aaa; text-decoration: none; margin-left: 15px; transition: 0.3s; }
    .nav-links a:hover { color: var(--primary); }

    /* Main Container */
    .container { padding: 20px 5%; }
    
    /* Movie Grid */
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; }
    @media (min-width: 768px) { .grid { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; } }

    /* Movie Card */
    .card { background: var(--card-bg); border-radius: 10px; overflow: hidden; position: relative; text-decoration: none; color: white; transition: 0.4s; border: 1px solid var(--border); display: block; }
    .card:hover { transform: translateY(-8px); border-color: var(--primary); box-shadow: 0 5px 15px rgba(229, 9, 20, 0.3); }
    .card img { width: 100%; aspect-ratio: 2/3; object-fit: cover; }
    .badge { position: absolute; top: 8px; left: 8px; background: var(--primary); color: white; padding: 3px 10px; font-size: 11px; border-radius: 4px; font-weight: bold; }
    .card-info { padding: 12px; text-align: center; font-weight: 500; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    /* Detail View */
    .detail-flex { display: flex; flex-direction: column; gap: 30px; }
    @media (min-width: 768px) { .detail-flex { flex-direction: row; } }
    .poster-img { width: 100%; max-width: 300px; border-radius: 15px; border: 3px solid var(--border); align-self: center; }
    .info-content { flex: 1; }
    .info-content h1 { margin-top: 0; font-size: 32px; color: var(--primary); }
    .story { color: #ccc; line-height: 1.6; background: #1a1a1a; padding: 15px; border-radius: 8px; border-left: 4px solid var(--primary); }

    /* Episode List */
    .ep-box { background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid var(--border); }
    .ep-btns { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
    .btn { padding: 10px 20px; border-radius: 5px; text-decoration: none; color: white; font-size: 13px; font-weight: bold; transition: 0.3s; text-align: center; flex: 1; min-width: 100px; }
    .btn-dl { background: #27ae60; } .btn-dl:hover { background: #219150; }
    .btn-st { background: #2980b9; } .btn-st:hover { background: #216999; }
    .btn-tg { background: #0088cc; } .btn-tg:hover { background: #0077b3; }

    /* Admin Panel Styling */
    .admin-table-container { overflow-x: auto; margin-top: 20px; }
    .admin-table { width: 100%; border-collapse: collapse; min-width: 600px; }
    .admin-table th, .admin-table td { padding: 12px; border: 1px solid var(--border); text-align: left; }
    .admin-table th { background: #222; }
    .action-btns a { text-decoration: none; padding: 5px 12px; border-radius: 4px; font-size: 12px; margin-right: 5px; color: white; }
    .edit-btn { background: #f39c12; }
    .del-btn { background: #e74c3c; border: none; cursor: pointer; color: white; padding: 5px 12px; border-radius: 4px; font-size: 12px; }

    /* Form Styling */
    .form-card { max-width: 800px; margin: auto; background: #1a1a1a; padding: 30px; border-radius: 15px; border: 1px solid var(--border); }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; color: #aaa; }
    input, textarea, select { width: 100%; padding: 12px; background: #222; color: white; border: 1px solid var(--border); border-radius: 6px; box-sizing: border-box; }
    .submit-btn { width: 100%; padding: 15px; background: var(--primary); border: none; color: white; font-weight: bold; font-size: 18px; border-radius: 8px; cursor: pointer; margin-top: 20px; box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4); }
    .ep-input-group { background: #262626; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px dashed #555; position: relative; }
    .add-ep-btn { background: #444; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 10px; }
</style>
"""

# --- Header Helper ---
def get_header(admin_view=False):
    action_url = "/admin" if admin_view else "/"
    return f"""
    <header>
        <a href="/" class="logo">WebSeries BD</a>
        <form action="{action_url}" method="GET" class="search-container">
            <input type="text" name="q" placeholder="মুভি বা সিরিজ খুঁজুন..." value="{request.args.get('q', '')}">
            <button type="submit">Search</button>
        </form>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="/admin">Admin View</a>
            { '<a href="/admin/add" style="background:var(--primary); color:white; padding:5px 10px; border-radius:5px; margin-left:10px;">+ New Post</a>' if admin_view else '' }
        </div>
    </header>
    """

# --- Routes ---

@app.route('/')
def home():
    query = request.args.get('q', '')
    filt = {"title": {"$regex": query, "$options": "i"}} if query else {}
    movies = list(series_collection.find(filt).sort("_id", -1))
    
    html = f"""<!DOCTYPE html><html lang="bn"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>WebSeries BD - Home</title>{COMMON_STYLE}</head><body>"""
    html += get_header()
    html += '<div class="container">'
    html += f'<h3>{"সার্চ রেজাল্ট: " + query if query else "সব মুভি এবং সিরিজ"}</h3>'
    html += '<div class="grid">'
    for s in movies:
        html += f"""
        <a href="/series/{s['_id']}" class="card">
            {f'<div class="badge">{s.get("poster_text")}</div>' if s.get("poster_text") else ''}
            <img src="{s.get('poster')}" alt="Poster">
            <div class="card-info">{s.get('title')} ({s.get('year')})</div>
        </a>
        """
    if not movies:
        html += '<p style="text-align:center; grid-column: 1/-1;">কোনো মুভি পাওয়া যায়নি!</p>'
    html += '</div></div></body></html>'
    return render_template_string(html)

@app.route('/series/<id>')
def detail(id):
    s = series_collection.find_one({"_id": ObjectId(id)})
    if not s: return "Not Found", 404
    
    html = f"""<!DOCTYPE html><html lang="bn"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{s.get('title')}</title>{COMMON_STYLE}</head><body>"""
    html += get_header()
    html += f"""
    <div class="container">
        <div class="detail-flex">
            <img src="{s.get('poster')}" class="poster-img">
            <div class="info-content">
                <h1>{s.get('title')} ({s.get('year')})</h1>
                <p><b>ভাষা:</b> {s.get('language')} | <b>সাল:</b> {s.get('year')}</p>
                <div class="story"><b>গল্প:</b><br>{s.get('description')}</div>
            </div>
        </div>
        <hr style="border:0; border-top:1px solid var(--border); margin:40px 0;">
        <h3>এপিসোড এবং ডাউনলোড লিঙ্ক সমূহ:</h3>
        {''.join([f'''
        <div class="ep-box">
            <strong>Episode No: {ep['ep_no']}</strong>
            <div class="ep-btns">
                {f'<a href="{ep["dl_link"]}" class="btn btn-dl" target="_blank">Download</a>' if ep.get("dl_link") else ''}
                {f'<a href="{ep["st_link"]}" class="btn btn-st" target="_blank">Stream Online</a>' if ep.get("st_link") else ''}
                {f'<a href="{ep["tg_link"]}" class="btn btn-tg" target="_blank">Telegram File</a>' if ep.get("tg_link") else ''}
            </div>
        </div>
        ''' for ep in s.get('episodes', [])])}
    </div></body></html>
    """
    return render_template_string(html)

# --- Admin Routes (Search, Add, Edit, Delete) ---

@app.route('/admin')
def admin_panel():
    query = request.args.get('q', '')
    filt = {"title": {"$regex": query, "$options": "i"}} if query else {}
    movies = list(series_collection.find(filt).sort("_id", -1))
    
    html = f"""<!DOCTYPE html><html lang="bn"><head><title>Admin Panel</title>{COMMON_STYLE}</head><body>"""
    html += get_header(admin_view=True)
    html += '<div class="container"><h2>মুভি ম্যানেজমেন্ট</h2><div class="admin-table-container">'
    html += '<table class="admin-table"><thead><tr><th>পোস্টার</th><th>মুভির নাম</th><th>সাল</th><th>অ্যাকশন</th></tr></thead><tbody>'
    for s in movies:
        html += f"""
        <tr>
            <td><img src="{s.get('poster')}" style="width:50px; border-radius:5px;"></td>
            <td>{s.get('title')}</td>
            <td>{s.get('year')}</td>
            <td class="action-btns">
                <a href="/admin/edit/{s['_id']}" class="edit-btn">Edit</a>
                <form action="/admin/delete/{s['_id']}" method="POST" style="display:inline;" onsubmit="return confirm('ডিলেট করতে চান?')">
                    <button type="submit" class="del-btn">Delete</button>
                </form>
            </td>
        </tr>
        """
    html += '</tbody></table></div></div></body></html>'
    return render_template_string(html)

@app.route('/admin/add', methods=['GET', 'POST'])
@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def manage_movie(id=None):
    movie = series_collection.find_one({"_id": ObjectId(id)}) if id else None
    
    if request.method == 'POST':
        shortener = request.form.get('shortener', "").strip()
        ep_nos = request.form.getlist('ep_no[]')
        dl_links = request.form.getlist('dl_link[]')
        st_links = request.form.getlist('st_link[]')
        tg_links = request.form.getlist('tg_link[]')
        
        episodes = []
        for i in range(len(ep_nos)):
            def proc_link(l): return shortener + l.strip() if shortener and l.strip() else l.strip()
            episodes.append({
                "ep_no": ep_nos[i],
                "dl_link": proc_link(dl_links[i]),
                "st_link": proc_link(st_links[i]),
                "tg_link": proc_link(tg_links[i])
            })
            
        data = {
            "title": request.form.get('title'),
            "year": request.form.get('year'),
            "language": request.form.get('lang'),
            "poster": request.form.get('poster'),
            "poster_text": request.form.get('poster_text'),
            "description": request.form.get('desc'),
            "episodes": episodes
        }
        
        if id: series_collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        else: series_collection.insert_one(data)
        return redirect(url_for('admin_panel'))

    # Form HTML
    html = f"""<!DOCTYPE html><html lang="bn"><head><title>Add/Edit Movie</title>{COMMON_STYLE}</head><body>"""
    html += get_header(admin_view=True)
    html += f"""<div class="container"><div class="form-card">
        <h2>{'এডিট করুন: ' + movie['title'] if movie else 'নতুন মুভি যোগ করুন'}</h2>
        <form method="POST">
            <div class="form-group"><label>মুভির নাম</label><input name="title" value="{movie['title'] if movie else ''}" required></div>
            <div style="display:flex; gap:10px;">
                <div class="form-group" style="flex:1;"><label>সাল</label><input name="year" value="{movie['year'] if movie else ''}" required></div>
                <div class="form-group" style="flex:1;"><label>ভাষা</label><input name="lang" value="{movie['language'] if movie else ''}" required></div>
            </div>
            <div class="form-group"><label>পোস্টার লিঙ্ক (URL)</label><input name="poster" value="{movie['poster'] if movie else ''}" required></div>
            <div class="form-group"><label>পোস্টার টেক্স (যেমন: HD, 4K)</label><input name="poster_text" value="{movie['poster_text'] if movie else ''}"></div>
            <div class="form-group"><label>মুভির গল্প</label><textarea name="desc" rows="5">{movie['description'] if movie else ''}</textarea></div>
            <div class="form-group"><label>লিঙ্ক শর্টনার বেস লিঙ্ক (ঐচ্ছিক)</label><input name="shortener" placeholder="https://stfly.me/api?api=key&url="></div>
            
            <h3 style="margin-top:30px; border-bottom:1px solid #444; padding-bottom:5px;">এপিসোড সমূহ:</h3>
            <div id="ep-container">
                { "".join([f'''
                <div class="ep-input-group">
                    <input name="ep_no[]" placeholder="এপিসোড নাম্বার" value="{e['ep_no']}" required>
                    <input name="dl_link[]" placeholder="Download Link" value="{e['dl_link']}">
                    <input name="st_link[]" placeholder="Stream Link" value="{e['st_link']}">
                    <input name="tg_link[]" placeholder="Telegram Link" value="{e['tg_link']}">
                </div>
                ''' for e in movie['episodes']]) if movie else '<div class="ep-input-group"><input name="ep_no[]" placeholder="এপিসোড নং" required><input name="dl_link[]" placeholder="Download Link"><input name="st_link[]" placeholder="Stream Link"><input name="tg_link[]" placeholder="Telegram Link"></div>' }
            </div>
            <button type="button" class="add-ep-btn" onclick="addEpisode()">+ নতুন এপিসোড যোগ করুন</button>
            <button type="submit" class="submit-btn">{'আপডেট করুন' if id else 'পাবলিশ করুন'}</button>
        </form>
    </div></div>
    <script>
        function addEpisode() {{
            const div = document.createElement('div');
            div.className = 'ep-input-group';
            div.innerHTML = '<input name="ep_no[]" placeholder="এপিসোড নং" required><input name="dl_link[]" placeholder="Download Link"><input name="st_link[]" placeholder="Stream Link"><input name="tg_link[]" placeholder="Telegram Link">';
            document.getElementById('ep-container').appendChild(div);
        }}
    </script></body></html>"""
    return render_template_string(html)

@app.route('/admin/delete/<id>', methods=['POST'])
def delete_movie(id):
    series_collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
