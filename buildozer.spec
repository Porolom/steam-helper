[app]
title = Steam Helper
package.name = steamhelper
package.domain = com.lacos
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
version = 1.0
# Жестко фиксируем версии, чтобы p4a не скачал несовместимый Python/OpenSSL
requirements = python3==3.10.12,hostpython3==3.10.12,openssl,kivy==2.3.0,kivymd==1.2.0,requests,urllib3,chardet,idna,certifi,Cython==0.29.33
orientation = portrait
fullscreen = 1
android.permissions = INTERNET
android.accept_sdk_license = True
android.skip_update = False

# Пробуем ветку master (develop иногда нестабилен)
android.ndk = 25b
android.api = 31
android.minapi = 21
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
