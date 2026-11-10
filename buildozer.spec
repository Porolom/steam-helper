[app]
title = Steam Helper
package.name = steamhelper
package.domain = com.lacos
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
version = 1.0
requirements = openssl,python3,kivy,kivymd,materialyoucolor,exceptiongroup,asyncgui,asynckivy,requests,urllib3,chardet,idna,certifi
orientation = portrait
fullscreen = 1
android.permissions = INTERNET
android.accept_sdk_license = True
android.skip_update = False

# Фиксы для стабильной сборки
android.ndk = 25b
p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
