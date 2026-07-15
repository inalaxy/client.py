[app]
title = P2P Messenger
package.name = p2pmessenger
package.domain = org.yourname
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3,kivy

# (CRITICAL) Network permissions for P2P network broadcasts
android.permissions = INTERNET, ACCESS_WIFI_STATE, CHANGE_WIFI_MULTICAST_STATE, ACCESS_NETWORK_STATE

orientation = portrait
osx.kivy_version = 2.3.0
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
