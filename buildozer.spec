[app]
title = Steam Helper
package.name = steamhelper
package.domain = com.lacos
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
version = 1.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,urllib3,chardet,idna,certifi
orientation = portrait
fullscreen = 1
android.permissions = INTERNET
android.accept_sdk_license = True
android.skip_update = False

# Фиксы
android.ndk = 25b
android.api = 34
android.minapi = 21
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
