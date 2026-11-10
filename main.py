from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock
from kivy.metrics import dp
import requests
import urllib.parse
import threading
import webbrowser
import time

# =====================================================================
# ВСТАВЬ СВОИ ДАННЫЕ СЮДА
# =====================================================================
STEAM_API_KEY = "2667FD64FA34D5286F5A0F9EFE4D035E"
STEAM_ID = "76561199204302070"
# =====================================================================

class SteamHelperApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.title = "Steam Game Helper"
        
        self.user_genres = set()
        self.user_owned_ids = set()
        
        # Главный экран
        screen = MDScreen()
        
        # Верхняя панель
        self.toolbar = MDTopAppBar(title="Steam Game Helper")
        screen.add_widget(self.toolbar)
        
        # Нижняя навигация
        self.bottom_nav = MDBottomNavigation()
        
        # Вкладка 1: Поиск
        self.tab_search = MDBottomNavigationItem(name="search", text="Поиск", icon="magnify")
        self.build_search_content()
        self.bottom_nav.add_widget(self.tab_search)
        
        # Вкладка 2: Мои вкусы
        self.tab_taste = MDBottomNavigationItem(name="taste", text="Мои вкусы", icon="heart")
        self.build_taste_content()
        self.bottom_nav.add_widget(self.tab_taste)
        
        # Вкладка 3: Рекомендации
        self.tab_rec = MDBottomNavigationItem(name="rec", text="Рекомендации", icon="star")
        self.build_rec_content()
        self.bottom_nav.add_widget(self.tab_rec)
        
        screen.add_widget(self.bottom_nav)
        return screen

    # ==========================================
    # ВКЛАДКА 1: ПОИСК
    # ==========================================
    def build_search_content(self):
        layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        input_layout = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        self.search_input = MDTextField(hint_text="Название игры...", mode="rectangle", size_hint_x=0.7)
        btn = MDRaisedButton(text="Найти", size_hint_x=0.3, on_release=self.do_search)
        
        input_layout.add_widget(self.search_input)
        input_layout.add_widget(btn)
        layout.add_widget(input_layout)
        
        scroll = MDScrollView()
        self.search_results_list = MDList()
        scroll.add_widget(self.search_results_list)
        layout.add_widget(scroll)
        
        self.tab_search.add_widget(layout)

    def do_search(self, instance):
        query = self.search_input.text.strip()
        if not query:
            self.show_message("Введи название игры!")
            return
        self.search_results_list.clear_widgets()
        self.search_results_list.add_widget(OneLineListItem(text="Ищем в Steam..."))
        threading.Thread(target=self.fetch_games, args=(query,), daemon=True).start()

    def fetch_games(self, query):
        try:
            url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(query)}&l=russian&cc=KZ"
            res = requests.get(url, timeout=10).json()
            items = res.get("items", [])
            Clock.schedule_once(lambda dt: self.update_search_ui(items), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_message(f"Ошибка: {e}"), 0)

    def update_search_ui(self, items):
        self.search_results_list.clear_widgets()
        if not items:
            self.search_results_list.add_widget(OneLineListItem(text="Ничего не найдено."))
            return
        for item in items[:10]:
            self.search_results_list.add_widget(self.create_game_card(item))

    # ==========================================
    # ВКЛАДКА 2: МОИ ВКУСЫ (через SteamSpy)
    # ==========================================
    def build_taste_content(self):
        layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        btn = MDRaisedButton(text="Проанализировать библиотеку", size_hint_y=None, height=dp(50), on_release=self.do_analyze)
        layout.add_widget(btn)
        
        scroll = MDScrollView()
        self.taste_results_list = MDList()
        scroll.add_widget(self.taste_results_list)
        layout.add_widget(scroll)
        
        self.tab_taste.add_widget(layout)

    def do_analyze(self, instance):
        self.taste_results_list.clear_widgets()
        self.taste_results_list.add_widget(OneLineListItem(text="Загружаем игры..."))
        threading.Thread(target=self.fetch_taste, daemon=True).start()

    def fetch_taste(self):
        if not STEAM_API_KEY or not STEAM_ID:
            Clock.schedule_once(lambda dt: self.show_message("Впиши ключи в код!"), 0)
            return
        try:
            url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={STEAM_ID}&include_appinfo=true&include_played_free_games=true"
            res = requests.get(url, timeout=15).json()
            games = res.get("response", {}).get("games", [])
            
            self.user_owned_ids = set(str(g['appid']) for g in games)
            self.user_genres = set()
            
            games.sort(key=lambda x: x.get("playtime_forever", 0), reverse=True)
            top_games = games[:8]
            
            blacklist = ["DSX", "Wallpaper Engine", "3DMark", "VRChat", "OBS Studio", "Blender", "Unity", "Unreal Engine"]
            analyzed_games = 0
            
            for g in top_games:
                if analyzed_games >= 3: break
                if any(word.lower() in g['name'].lower() for word in blacklist): continue
                    
                try:
                    spy_url = f"https://steamspy.com/api.php?request=appdetails&appid={g['appid']}"
                    spy_res = requests.get(spy_url, timeout=5).json()
                    tags = spy_res.get("tags", {})
                    if tags:
                        sorted_tags = sorted(tags, key=tags.get, reverse=True)
                        for tag in sorted_tags[:5]:
                            self.user_genres.add(tag)
                        analyzed_games += 1
                    time.sleep(1)
                except:
                    pass
            
            Clock.schedule_once(lambda dt: self.update_taste_ui(games), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_message(f"Ошибка: {e}"), 0)

    def update_taste_ui(self, games):
        self.taste_results_list.clear_widgets()
        if not games:
            self.taste_results_list.add_widget(OneLineListItem(text="Не удалось получить игры."))
            return
        games.sort(key=lambda x: x.get("playtime_forever", 0), reverse=True)
        self.taste_results_list.add_widget(OneLineListItem(text=f"Найдено {len(games)} игр. Топ по времени:"))
        for g in games[:20]:
            hours = g.get("playtime_forever", 0) // 60
            if hours == 0: continue
            self.taste_results_list.add_widget(OneLineListItem(text=f"{g['name']} — {hours} ч."))

    # ==========================================
    # ВКЛАДКА 3: РЕКОМЕНДАЦИИ
    # ==========================================
    def build_rec_content(self):
        layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        btn = MDRaisedButton(text="Найти рекомендации", size_hint_y=None, height=dp(50), on_release=self.do_recommend)
        layout.add_widget(btn)
        
        scroll = MDScrollView()
        self.rec_results_list = MDList()
        scroll.add_widget(self.rec_results_list)
        layout.add_widget(scroll)
        
        self.tab_rec.add_widget(layout)

    def do_recommend(self, instance):
        self.rec_results_list.clear_widgets()
        self.rec_results_list.add_widget(OneLineListItem(text="Ищем игры..."))
        threading.Thread(target=self.fetch_recommend, daemon=True).start()

    def fetch_recommend(self):
        if not self.user_genres:
            Clock.schedule_once(lambda dt: self.show_message("Сначала нажми 'Проанализировать библиотеку'!"), 0)
            return

        search_tags = list(self.user_genres)[:5]
        Clock.schedule_once(lambda dt: self.rec_results_list.clear_widgets(), 0)
        Clock.schedule_once(lambda dt: self.rec_results_list.add_widget(OneLineListItem(text=f"Ищем по тегам: {', '.join(search_tags[:3])}...")), 0)

        all_recs = []
        try:
            for tag in search_tags:
                search_url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(tag)}&l=russian&cc=KZ"
                res = requests.get(search_url, timeout=10).json()
                items = res.get("items", [])
                for item in items:
                    if str(item.get("id")) not in self.user_owned_ids:
                        all_recs.append(item)
            
            seen = set()
            unique = []
            for r in all_recs:
                if r['id'] not in seen:
                    seen.add(r['id'])
                    unique.append(r)
                    
            Clock.schedule_once(lambda dt: self.update_rec_ui(unique[:10]), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_message(f"Ошибка: {e}"), 0)

    def update_rec_ui(self, items):
        self.rec_results_list.clear_widgets()
        if not items:
            self.rec_results_list.add_widget(OneLineListItem(text="Ничего не найдено."))
            return
        for item in items:
            self.rec_results_list.add_widget(self.create_game_card(item))

    # ==========================================
    # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    # ==========================================
    def create_game_card(self, item):
        card = MDCard(orientation='vertical', size_hint_y=None, height=dp(150), padding=dp(10), spacing=dp(5), ripple_behavior=True)
        
        name = item.get("name", "Unknown")
        app_id = item.get("id")
        price_info = item.get("price", {})
        
        if item.get("is_free"):
            price_text = "Бесплатно"
            color = (0, 1, 0, 1)
        elif price_info:
            final_tenge = price_info.get("final", 0) / 100
            final_rub = final_tenge / 5.5
            price_text = f"{final_rub:,.0f} руб. / {final_tenge:,.0f} тенге"
            color = (1, 0.8, 0, 1)
        else:
            price_text = "Цена не указана"
            color = (0.5, 0.5, 0.5, 1)
        
        card.add_widget(MDLabel(text=f"Игра: {name}", bold=True, theme_text_color="Custom", text_color=(0,1,1,1)))
        card.add_widget(MDLabel(text=price_text, theme_text_color="Custom", text_color=color, size_hint_y=None, height=dp(20)))
        
        btn = MDFlatButton(text="Открыть в Steam", on_release=lambda x: webbrowser.open(f"https://store.steampowered.com/app/{app_id}"))
        card.add_widget(btn)
        
        return card

    def show_message(self, text):
        dialog = MDDialog(title="Уведомление", text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())])
        dialog.open()

if __name__ == '__main__':
    SteamHelperApp().run()
