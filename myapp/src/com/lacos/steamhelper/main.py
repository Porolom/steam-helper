from flask import Flask, render_template_string, request
import requests
import urllib.parse
import os

# =====================================================================
# ВСТАВЬ СВОИ ДАННЫЕ СЮДА
# =====================================================================
STEAM_API_KEY = "2667FD64FA34D5286F5A0F9EFE4D035E"
STEAM_ID = "76561199204302070"
# =====================================================================

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steam Game Helper</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #58a6ff; text-align: center; }
        .container { max-width: 800px; margin: 0 auto; }
        .tabs { display: flex; justify-content: center; margin-bottom: 20px; }
        .tab-btn { background-color: #21262d; color: white; border: 1px solid #30363d; padding: 10px 20px; cursor: pointer; border-radius: 5px; margin: 0 5px; font-size: 16px; }
        .tab-btn.active { background-color: #58a6ff; color: black; font-weight: bold; }
        .card { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; margin-bottom: 10px; }
        .card h3 { margin: 0 0 10px 0; color: #00FFFF; }
        .price { font-weight: bold; color: #FFD700; }
        .free { color: #00FF00; }
        input[type="text"] { width: 70%; padding: 10px; border-radius: 5px; border: 1px solid #30363d; background-color: #0d1117; color: white; }
        button { padding: 10px 20px; background-color: #238636; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #2ea043; }
        .hidden { display: none; }
        a { color: #58a6ff; text-decoration: none; }
        .error { color: #f85149; }
        .success { color: #3fb950; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 Steam Game Helper</h1>

        <div class="tabs">
            <button class="tab-btn active" onclick="showTab('search')">🔍 Поиск</button>
            <button class="tab-btn" onclick="showTab('taste')">❤️ Мои вкусы</button>
            <button class="tab-btn" onclick="showTab('rec')">✨ Рекомендации</button>
        </div>

        <div id="tab-search">
            <form method="POST" action="/search" style="text-align:center; margin-bottom: 20px;">
                <input type="text" name="query" placeholder="Название игры (например, Stardew)..." required>
                <button type="submit">Найти</button>
            </form>
            {% if search_results %}
                {% for item in search_results %}
                    <div class="card">
                        <h3>🎮 {{ item.name }}</h3>
                        <p class="price">{{ item.price_text }}</p>
                        <a href="https://store.steampowered.com/app/{{ item.app_id }}" target="_blank">Открыть в Steam →</a>
                    </div>
                {% endfor %}
            {% elif search_error %}
                <p class="error">{{ search_error }}</p>
            {% endif %}
        </div>

        <div id="tab-taste" class="hidden">
            <form method="POST" action="/analyze" style="text-align:center; margin-bottom: 20px;">
                <button type="submit">📊 Проанализировать библиотеку</button>
            </form>
            {% if taste_results %}
                <p class="success">✅ Найдено {{ taste_results.total }} игр. Топ по времени:</p>
                {% for game in taste_results.games %}
                    <div class="card">
                        <h3>🎮 {{ game.name }}</h3>
                        <p>⏳ {{ game.hours }} часов</p>
                    </div>
                {% endfor %}
            {% elif taste_error %}
                <p class="error">{{ taste_error }}</p>
            {% endif %}
        </div>

        <div id="tab-rec" class="hidden">
            <form method="POST" action="/recommend" style="text-align:center; margin-bottom: 20px;">
                <button type="submit">✨ Найти рекомендации</button>
            </form>
            {% if rec_results %}
                <p class="success">✨ Найдено {{ rec_results|length }} игр:</p>
                {% for item in rec_results %}
                    <div class="card">
                        <h3>🎮 {{ item.name }}</h3>
                        <p class="price">{{ item.price_text }}</p>
                        <a href="https://store.steampowered.com/app/{{ item.app_id }}" target="_blank">Открыть в Steam →</a>
                    </div>
                {% endfor %}
            {% elif rec_error %}
                <p class="error">{{ rec_error }}</p>
            {% endif %}
        </div>
    </div>

    <script>
        function showTab(tabName) {
            document.getElementById('tab-search').classList.add('hidden');
            document.getElementById('tab-taste').classList.add('hidden');
            document.getElementById('tab-rec').classList.add('hidden');

            document.getElementById('tab-' + tabName).classList.remove('hidden');

            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""


def get_price_text(item):
    if item.get("is_free"): return "Бесплатно"
    price_info = item.get("price", {})
    if price_info:
        final_price = price_info.get("final", 0) / 100
        return f"{final_price:,.2f} ₸"
    return "Цена не указана"


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if not query: return render_template_string(HTML_TEMPLATE, search_error="Введи запрос!")

    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(query)}&l=russian&cc=KZ"
        res = requests.get(url, timeout=10).json()
        items = res.get("items", [])

        results = []
        for item in items[:10]:
            results.append({
                "name": item.get("name", "Unknown"),
                "app_id": item.get("id"),
                "price_text": get_price_text(item)
            })
        return render_template_string(HTML_TEMPLATE, search_results=results)
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, search_error=f"Ошибка: {e}")


@app.route('/analyze', methods=['POST'])
def analyze():
    if not STEAM_API_KEY or not STEAM_ID:
        return render_template_string(HTML_TEMPLATE, taste_error="Впиши ключи в код!")

    try:
        url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={STEAM_ID}&include_appinfo=true&include_played_free_games=true"
        res = requests.get(url, timeout=15).json()
        games = res.get("response", {}).get("games", [])

        if not games:
            return render_template_string(HTML_TEMPLATE, taste_error="Не удалось получить игры. Проверь профиль.")

        games.sort(key=lambda x: x.get("playtime_forever", 0), reverse=True)
        top_games = []
        for g in games[:20]:
            hours = g.get("playtime_forever", 0) // 60
            if hours > 0:
                top_games.append({"name": g['name'], "hours": hours})

        return render_template_string(HTML_TEMPLATE, taste_results={"total": len(games), "games": top_games})
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, taste_error=f"Ошибка: {e}")


@app.route('/recommend', methods=['POST'])
def recommend():
    queries = ["RPG", "Action", "Strategy"]

    try:
        all_recs = []
        for q in queries:
            url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(q)}&l=russian&cc=KZ"
            res = requests.get(url, timeout=10).json()
            items = res.get("items", [])
            for item in items:
                all_recs.append({
                    "name": item.get("name", "Unknown"),
                    "app_id": item.get("id"),
                    "price_text": get_price_text(item)
                })

        seen = set()
        unique = []
        for r in all_recs:
            if r['app_id'] not in seen:
                seen.add(r['app_id'])
                unique.append(r)

        return render_template_string(HTML_TEMPLATE, rec_results=unique[:10])
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, rec_error=f"Ошибка: {e}")


if __name__ == '__main__':
    # Блок для запуска через py2apk (Android)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=False)