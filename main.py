from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.appbar import MDTopAppBar, MDTopAppBarTitle
from kivymd.uix.navigationbar import (
    MDNavigationBar,
    MDNavigationItem,
    MDNavigationItemIcon,
    MDNavigationItemLabel
)
from kivymd.uix.list import MDList, MDListItem, MDListItemHeadlineText
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogButtonContainer
from kivymd.uix.screenmanager import MDScreenManager
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

        root_layout = MDBoxLayout(orientation='vertical')

        self.toolbar = MDTopAppBar(MDTopAppBarTitle(text="Steam Game Helper"))
        root_layout.add_widget(self.toolbar)

        self.screen_manager = MDScreenManager()

        self.screen_search = MDScreen(name="search")
        self.screen_taste = MDScreen(name="taste")
        self.screen_rec = MDScreen(name="rec")

        self.build_search_content(self.screen_search)
        self.build_taste_content(self.screen_taste)
        self.build_rec_content(self.screen_rec)

        self.screen_manager.add_widget(self.screen_search)
        self.screen_manager.add_widget(self.screen_taste)
        self.screen_manager.add_widget(self.screen_rec)

        root_layout.add_widget(self.screen_manager)

        self.bottom_nav = MDNavigationBar()

        self.tab_search = MDNavigationItem()
        self.tab_search.add_widget(MDNavigationItemIcon(icon="magnify"))
        self.tab_search.add_widget(MDNavigationItemLabel(text="Поиск"))
        self.tab_search.bind(on_release=lambda x: self.switch_tab("search"))

        self.tab_taste = MDNavigationItem()
        self.tab_taste.add_widget(MDNavigationItemIcon(icon="heart"))
        self.tab_taste.add_widget(MDNavigationItemLabel(text="Мои вкусы"))
        self.tab_taste.bind(on_release=lambda x: self.switch_tab("taste"))

        self.tab_rec = MDNavigationItem()
        self.tab_rec.add_widget(MDNavigationItemIcon(icon="star"))
        self.tab_rec.add_widget(MDNavigationItemLabel(text="Рекомендации"))
        self.tab_rec.bind(on_release=lambda x: self.switch_tab("rec"))

        self.bottom_nav.add_widget(self.tab_search)
        self.bottom_nav.add_widget(self.tab_taste)
        self.bottom_nav.add_widget(self.tab_rec)

        root_layout.add_widget(self.bottom_nav)

        self.tab_search.active = True
        self.screen_manager.current = "search"

        return root_layout

    def switch_tab(self, screen_name):
        self.screen_manager.current = screen_name
        self.tab_search.active = False
        self.tab_taste.active = False
        self.tab_rec.active = False
        if screen_name == "search":
            self.tab_search.active = True
        elif screen_name == "taste":
            self.tab_taste.active = True
        elif screen_name == "rec":
            self.tab_rec.active = True

    # ==========================================
    # ВКЛАДКА 1: ПОИСК
    # ==========================================
    def build_search_content(self, screen):
        layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        input_layout = MDBoxLayout(size_hint_y=None, height=dp(70), spacing=dp(10))
        self.search_input = MDTextField(hint_text="Название игры...", mode="filled", size_hint_x=0.7)
        btn = MDButton(MDButtonText(text="Найти"), style="filled", size_hint_x=0.3, on_release=self.do_search)

        input_layout.add_widget(self.search_input)
        input_layout.add_widget(btn)
        layout.add_widget(input_layout)

        scroll = MDScrollView()
        self.search_results_list = MDList()
        scroll.add_widget(self.search_results_list)
        layout.add_widget(scroll)

        screen.add_widget(layout)

    def do_search(self, instance):
        query = self.search_input.text.strip()
        if not query:
            self.show_message("Введи название игры!")
            return
        self.search_results_list.clear_widgets()
        self.search_results_list.add_widget(self.create_list_item("Ищем в Steam..."))
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
            self.search_results_list.add_widget(self.create_list_item("Ничего не найдено."))
            return
        for item in items[:10]:
            self.search_results_list.add_widget(self.create_game_card(item))

    # ==========================================
    # ВКЛАДКА 2: МОИ ВКУСЫ (через SteamSpy)
    # ==========================================
    def build_taste_content(self, screen):
        layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        btn = MDButton(MDButtonText(text="Проанализировать библиотеку"), style="filled", size_hint_y=None,
                       height=dp(50), on_release=self.do_analyze)
        layout.add_widget(btn)

        scroll = MDScrollView()
        self.taste_results_list = MDList()
        scroll.add_widget(self.taste_results_list)
        layout.add_widget(scroll)

        screen.add_widget(layout)

    def do_analyze(self, instance):
        self.taste_results_list.clear_widgets()
        self.taste_results_list.add_widget(self.create_list_item("Загружаем игры..."))
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

            blacklist = ["DSX", "Wallpaper Engine", "3DMark", "VRChat", "OBS Studio", "Blender", "Unity",
                         "Unreal Engine"]

            analyzed_games = 0

            for g in top_games:
                if analyzed_games >= 3:
                    break

                if any(word.lower() in g['name'].lower() for word in blacklist):
                    continue

                try:
                    spy_url = f"https://steamspy.com/api.php?request=appdetails&appid={g['appid']}"
                    spy_res = requests.get(spy_url, timeout=5).json()

                    tags = spy_res.get("tags", {})
                    if tags:
                        sorted_tags = sorted(tags, key=tags.get, reverse=True)
                        for tag in sorted_tags[:5]:
                            self.user_genres.add(tag)
                        analyzed_games += 1

                    time.sleep(1)  # Пауза для SteamSpy
                except:
                    pass

            Clock.schedule_once(lambda dt: self.update_taste_ui(games), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_message(f"Ошибка: {e}"), 0)

    def update_taste_ui(self, games):
        self.taste_results_list.clear_widgets()
        if not games:
            self.taste_results_list.add_widget(self.create_list_item("Не удалось получить игры."))
            return
        games.sort(key=lambda x: x.get("playtime_forever", 0), reverse=True)
        self.taste_results_list.add_widget(self.create_list_item(f"Найдено {len(games)} игр. Топ по времени:"))
        for g in games[:20]:
            hours = g.get("playtime_forever", 0) // 60
            if hours == 0: continue
            self.taste_results_list.add_widget(self.create_list_item(f"{g['name']} — {hours} ч."))

    # ==========================================
    # ВКЛАДКА 3: РЕКОМЕНДАЦИИ (по тегам SteamSpy)
    # ==========================================
    def build_rec_content(self, screen):
        layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        btn = MDButton(MDButtonText(text="Найти рекомендации"), style="filled", size_hint_y=None, height=dp(50),
                       on_release=self.do_recommend)
        layout.add_widget(btn)

        scroll = MDScrollView()
        self.rec_results_list = MDList()
        scroll.add_widget(self.rec_results_list)
        layout.add_widget(scroll)

        screen.add_widget(layout)

    def do_recommend(self, instance):
        self.rec_results_list.clear_widgets()
        self.rec_results_list.add_widget(self.create_list_item("Ищем игры по твоим тегам..."))
        threading.Thread(target=self.fetch_recommend, daemon=True).start()

    def fetch_recommend(self):
        if not self.user_genres:
            Clock.schedule_once(lambda dt: self.show_message("Сначала нажми 'Проанализировать библиотеку'!"), 0)
            return

        search_tags = list(self.user_genres)[:5]

        Clock.schedule_once(lambda dt: self.rec_results_list.clear_widgets(), 0)
        Clock.schedule_once(lambda dt: self.rec_results_list.add_widget(
            self.create_list_item(f"Ищем по тегам: {', '.join(search_tags[:3])}...")), 0)

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
            self.rec_results_list.add_widget(self.create_list_item("Ничего не найдено."))
            return
        for item in items:
            self.rec_results_list.add_widget(self.create_game_card(item))

    # ==========================================
    # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    # ==========================================
    def create_list_item(self, text):
        return MDListItem(MDListItemHeadlineText(text=text))

    def convert_to_rub(self, tenge_price):
        rate = 5.5
        return tenge_price / rate

    def create_game_card(self, item):
        card = MDCard(orientation='vertical', size_hint_y=None, height=dp(150), padding=dp(10), spacing=dp(5),
                      ripple_behavior=True)

        name = item.get("name", "Unknown")
        app_id = item.get("id")
        price_info = item.get("price", {})

        if item.get("is_free"):
            price_text = "Бесплатно"
            color = (0, 1, 0, 1)
        elif price_info:
            final_tenge = price_info.get("final", 0) / 100
            final_rub = self.convert_to_rub(final_tenge)
            price_text = f"{final_rub:,.0f} руб. / {final_tenge:,.0f} тенге"
            color = (1, 0.8, 0, 1)
        else:
            price_text = "Цена не указана"
            color = (0.5, 0.5, 0.5, 1)

        card.add_widget(MDLabel(text=f"Игра: {name}", bold=True, theme_text_color="Custom", text_color=(0, 1, 1, 1)))
        card.add_widget(
            MDLabel(text=price_text, theme_text_color="Custom", text_color=color, size_hint_y=None, height=dp(20)))

        btn = MDButton(MDButtonText(text="Открыть в Steam"), style="text",
                       on_release=lambda x: webbrowser.open(f"https://store.steampowered.com/app/{app_id}"))
        card.add_widget(btn)

        return card

    def show_message(self, text):
        dialog = MDDialog(
            MDDialogHeadlineText(text="Уведомление"),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=lambda x: dialog.dismiss()
                )
            )
        )
        dialog.open()


if __name__ == '__main__':
    SteamHelperApp().run()