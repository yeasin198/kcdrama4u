import os
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# --- ডাটাবেস কানেকশন ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['webseries_db']
series_collection = db['series']

# --- ডিজাইন এবং স্টাইল (CSS) ---
COMMON_STYLE = """
<style>
    :root { --primary: #E50914; --bg: #0b0b0b; --card-bg: #1f1f1f; --text: #ffffff; }
    body { background-color: var(--bg); color: var(--text); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; }
    header { background: #000; padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--primary); box-shadow: 0 2px 10px rgba(0,0,0,0.5); }
    .logo { color: var(--primary); font-size: 24px; font-weight: bold; text-decoration: none; text-transform: uppercase; letter-spacing: 1px; }
    .container { padding: 20px 5%; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; }
    .card { background: var(--card-bg); border-radius: 8px; overflow: hidden; position: relative; text-decoration: none; color: white; transition: 0.3s; border: 1px solid #333; }
    .card:hover { transform: translateY(-5px); border-color: var(--primary); }
    .card img { width: 100%; height: 240px; object-fit: cover; }
    .poster-badge { position: absolute; top: 8px; left: 8px; background: var(--primary); color: white; padding: 3px 10px; font-size: 10px; border-radius: 3px; font-weight: bold; text-transform: uppercase; }
    .card-info { padding: 10px; font-size: 13px; text-align: center; font-weight: 500; }
    .detail-container { max-width: 850px; margin: auto; }
    .meta-info { margin: 15px 0; color: #bbb; font-size: 14px; background: #222; padding: 10px; border-radius: 5px; }
    .ep-box { background: #1a1a1a; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid var(--primary); }
    .ep-btns { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
    .btn { padding: 10px 18px; border-radius: 4px; text-decoration: none; font-size: 12px; font-weight: bold; color: white; text-align: center; transition: 0.2s; }
    .btn:hover { opacity: 0.8; }
    .btn-dl { background: #27ae60; }
    .btn-st { background: #2980b9; }
    .btn-tg { background: #0088cc; }
    .admin-form { max-width: 750px; margin: auto; background: #1a1a1a; padding: 25px; border-radius: 12px; border: 1px solid #333; }
    label { display: block; margin-top: 10px; font-size: 14px; color: #aaa; }
    input, textarea { width: 100%; padding: 12px; margin: 8px 0; background: #262626; color: white; border: 1px solid #333; border-radius: 5px; box-sizing: border-box; font-size: 14px; }
    input:focus { border-color: var(--primary); outline: none; }
    .ep-input-group { background: #222; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px dashed #444; position: relative; }
    .add-ep-btn { background: #333; color: white; padding: 12px; border: 1px solid #444; cursor: pointer; margin-top: 10px; width: 100%; border-radius: 5px; font-weight: bold; transition: 0.3s; }
    .add-ep-btn:hover { background: #444; border-color: var(--primary); }
    .submit-btn { background: var(--primary); color: white; border: none; padding: 18px; width: 100%; cursor: pointer; font-weight: bold; font-size: 18px; margin-top: 30px; border-radius: 5px; box-shadow: 0 4px 15px rgba(229, 9, 20, 0.3); }
    .story-text { line-height: 1.6; color: #ccc; font-size: 15px; }
</style>
"""

# --- HTML টেমপ্লেট সমূহ ---

# ১. হোম পেজ (Home)
HOME_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSeries BD - Home</title>""" + COMMON_STYLE + """
</head>
<body>
    <header><a href="/" class="logo">WebSeries BD</a><a href="/admin" style="color:#aaa; text-decoration:none; font-size:14px;">Admin Panel</a></header>
    <div class="container">
        <h3 style="margin-bottom:20px; border-left:4px solid var(--primary); padding-left:10px;">সাম্প্রতিক আপলোড</h3>
        <div class="grid">
            {% for s in series %}
            <a href="/series/{{ s._id }}" class="card">
                {% if s.poster_text %}<div class="poster-badge">{{ s.poster_text }}</div>{% endif %}
                <img src="{{ s.poster }}" alt="Poster">
                <div class="card-info">{{ s.title }} ({{ s.year }})</div>
            </a>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

# ২. বিস্তারিত পেজ (Detail)
DETAIL_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ series.title }} - WebSeries BD</title>""" + COMMON_STYLE + """
</head>
<body>
    <header><a href="/" class="logo">WebSeries BD</a></header>
    <div class="container detail-container">
        <center><img src="{{ series.poster }}" style="width:220px; border-radius:10px; border: 2px solid #333;"></center>
        <h1 style="text-align:center; margin-top:20px;">{{ series.title }}</h1>
        <div class="meta-info">
            <b>সাল:</b> {{ series.year }} | <b>ভাষা:</b> {{ series.language }}
        </div>
        <div class="story-text">
            <h3 style="color:var(--primary); margin-bottom:5px;">গল্প:</h3>
            {{ series.description }}
        </div>
        <hr style="margin:30px 0; border:0; border-top:1px solid #333;">
        <h3 style="margin-bottom:20px;">ডাউনলোড এবং অনলাইন স্ট্রিম লিঙ্ক:</h3>
        {% for ep in series.episodes %}
        <div class="ep-box">
            <strong style="font-size:16px;">এপিসোড নাম্বার: {{ ep.ep_no }}</strong>
            <div class="ep-btns">
                {% if ep.dl_link %}<a href="{{ ep.dl_link }}" class="btn btn-dl" target="_blank">Download Link</a>{% endif %}
                {% if ep.st_link %}<a href="{{ ep.st_link }}" class="btn btn-st" target="_blank">Stream Online</a>{% endif %}
                {% if ep.tg_link %}<a href="{{ ep.tg_link }}" class="btn btn-tg" target="_blank">Telegram File</a>{% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

# ৩. অ্যাডমিন প্যানেল (Admin)
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - Add Movie</title>""" + COMMON_STYLE + """
</head>
<body>
    <header><a href="/" class="logo">WebSeries BD</a></header>
    <div class="container">
        <div class="admin-form">
            <h2 style="color:var(--primary); margin-top:0;">নতুন মুভি/সিরিজ যুক্ত করুন</h2>
            <form method="POST">
                <label>মুভির নাম</label>
                <input name="title" placeholder="যেমন: Money Heist" required>
                
                <div style="display:flex; gap:10px;">
                    <div style="flex:1;"><label>সাল</label><input name="year" placeholder="2024" required></div>
                    <div style="flex:1;"><label>ভাষা</label><input name="lang" placeholder="Hindi" required></div>
                </div>

                <label>পোস্টার ইউআরএল (Link)</label>
                <input name="poster" placeholder="https://image-link.com/photo.jpg" required>
                
                <label>পোস্টার টেক্স (Badge)</label>
                <input name="poster_text" placeholder="যেমন: 4K, Dual Audio, Full Series">
                
                <label>মুভির গল্প/ডেসক্রিপশন</label>
                <textarea name="desc" placeholder="মুভির বিস্তারিত গল্প এখানে লিখুন..." rows="4"></textarea>
                
                <label>লিঙ্ক শর্টনার বেস ইউআরএল (ঐচ্ছিক)</label>
                <input name="shortener" placeholder="যেমন: https://stfly.me/api?api=YOUR_KEY&url=">

                <h3 style="margin-top:30px; padding-bottom:10px; border-bottom:1px solid #333;">এপিসোড এবং লিঙ্ক সমূহ:</h3>
                <div id="ep-container">
                    <div class="ep-input-group">
                        <input name="ep_no[]" placeholder="এপিসোড নাম্বার (যেমন: 01)" required>
                        <input name="dl_link[]" placeholder="ডাউনলোড লিঙ্ক (Download Link)">
                        <input name="st_link[]" placeholder="স্ট্রিম লিঙ্ক (Stream Online)">
                        <input name="tg_link[]" placeholder="টেলিগ্রাম লিঙ্ক (Telegram Link)">
                    </div>
                </div>
                
                <button type="button" class="add-ep-btn" onclick="addEpisode()">+ নতুন এপিসোড বক্স যোগ করুন</button>
                
                <button type="submit" class="submit-btn">পাবলিশ করুন (Publish)</button>
            </form>
        </div>
    </div>

    <script>
        function addEpisode() {
            const container = document.getElementById('ep-container');
            const newEp = document.createElement('div');
            newEp.className = 'ep-input-group';
            newEp.innerHTML = `
                <input name="ep_no[]" placeholder="এপিসোড নাম্বার" required>
                <input name="dl_link[]" placeholder="ডাউনলোড লিঙ্ক">
                <input name="st_link[]" placeholder="স্ট্রিম লিঙ্ক">
                <input name="tg_link[]" placeholder="টেলিগ্রাম লিঙ্ক">
            `;
            container.appendChild(newEp);
        }
    </script>
</body>
</html>
"""

# --- ব্যাকএন্ড লজিক এবং রাউটিং ---

@app.route('/')
def home():
    all_data = list(series_collection.find().sort("_id", -1))
    return render_template_string(HOME_HTML, series=all_data)

@app.route('/series/<id>')
def detail(id):
    series_data = series_collection.find_one({"_id": ObjectId(id)})
    if not series_data: return "সিরিজ খুঁজে পাওয়া যায়নি!", 404
    return render_template_string(DETAIL_HTML, series=series_data)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        shortener = request.form.get('shortener', "").strip()
        
        # ডাটা রিসিভ করা (লিস্ট হিসেবে)
        ep_nos = request.form.getlist('ep_no[]')
        dl_links = request.form.getlist('dl_link[]')
        st_links = request.form.getlist('st_link[]')
        tg_links = request.form.getlist('tg_link[]')
        
        ep_list = []
        for i in range(len(ep_nos)):
            # যদি শর্টনার থাকে তবে লিঙ্কের সাথে যোগ হবে
            def process_link(l):
                l = l.strip()
                if not l or l == "#": return ""
                return shortener + l if shortener else l
            
            ep_list.append({
                "ep_no": ep_nos[i].strip(),
                "dl_link": process_link(dl_links[i]),
                "st_link": process_link(st_links[i]),
                "tg_link": process_link(tg_links[i])
            })

        series_collection.insert_one({
            "title": request.form.get('title'),
            "year": request.form.get('year'),
            "language": request.form.get('lang'),
            "poster": request.form.get('poster'),
            "poster_text": request.form.get('poster_text'),
            "description": request.form.get('desc'),
            "episodes": ep_list
        })
        return redirect(url_for('home'))
    
    return render_template_string(ADMIN_HTML)

if __name__ == '__main__':
    # Render, Koyeb বা লোকাল হোস্টে চালানোর জন্য পোর্ট কনফিগারেশন
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
