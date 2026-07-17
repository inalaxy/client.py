[app]

# (str) Title of your application (This will show on the launcher)
title = Messengo

# (str) Package name (strictly lowercase, no spaces, letters/digits only)
package.name = messengo

# (str) Package domain (needed to build unique app id)
package.domain = org.messengo

# (str) Source code directory
source.dir = .

# (list) Source files to include (keep extensions clean)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application version
version = 0.1

# (list) Application requirements
# Added hostpython3 which is necessary for the build process.
requirements = hostpython3,python3,kivy,openssl,sqlite3

# (list) Network permissions for P2P local discovery broadcasts
# Added CHANGE_WIFI_STATE to support local peer socket bindings and UDP broadcasts on Android
android.permissions = INTERNET, ACCESS_WIFI_STATE, CHANGE_WIFI_STATE, CHANGE_WIFI_MULTICAST_STATE, ACCESS_NETWORK_STATE

# (str) Supported orientation (set to landscape, portrait or all)
orientation = portrait

# (int) Target Android API (Modern target matching Android requirements)
android.api = 34

# (int) Minimum API supported (Android 5.0+)
android.minapi = 21

# (str) Softinput mode - This automatically forces the layout to shrink dynamically when the phone keyboard slides up
android.softinput_mode = resize

# (list) Supported architectures
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enable Android cloud backup
android.allow_backup = True

# (int) Fullscreen mode (0 = Status bar visible, 1 = Status bar hidden)
fullscreen = 0
