import socket
import threading
import time
import sys
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line

PORT = 50002
BROADCAST_IP = "255.255.255.255"

# --- SYSTEM PALETTE ---
COLOR_BG = (0.07, 0.08, 0.10, 1)          # #121318 True dark background
COLOR_SURFACE = (0.12, 0.13, 0.17, 1)     # #1f212b Soft dark card surface
COLOR_SURFACE_LIGHT = (0.18, 0.20, 0.26, 1) # #2e3342 Hover & Input background
COLOR_PRIMARY = (0.39, 0.45, 0.96, 1)     # #6373f5 Vibrant Royal Blue (Primary Accent)
COLOR_TEXT_PRIMARY = (0.95, 0.96, 0.98, 1) # #f2f5fa Bright text
COLOR_TEXT_MUTED = (0.55, 0.58, 0.65, 1)   # #8c94a6 Secondary muted details
COLOR_BORDER = (0.16, 0.18, 0.22, 1)      # Subtle border separation
COLOR_ONLINE = (0.15, 0.68, 0.38, 1)      # Smooth emerald green
COLOR_OFFLINE = (0.75, 0.22, 0.17, 1)     # Crimson red


# --- Modern Rounded Canvas Containers ---

class BackgroundBoxLayout(BoxLayout):
    def __init__(self, bg_color, radius=[0, 0, 0, 0], has_border=False, border_color=COLOR_BORDER, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        self.has_border = has_border
        self.border_color = border_color
        
        with self.canvas.before:
            self.color_instruction = Color(*self.bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=self.radius)
            if self.has_border:
                self.border_color_instruction = Color(*self.border_color)
                self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, *self.radius), width=1.1)
                
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        if self.has_border:
            self.border.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, *self.radius)


class InteractiveButton(Button):
    def __init__(self, bg_color=COLOR_PRIMARY, radius=[10], **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.bg_color = bg_color
        self.radius = radius
        self.font_name = "Roboto" if sys.platform != "win32" else "Arial"
        
        with self.canvas.before:
            self.color_instruction = Color(*self.bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=self.radius)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class PremiumTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = COLOR_SURFACE_LIGHT
        self.foreground_color = COLOR_TEXT_PRIMARY
        self.cursor_color = COLOR_PRIMARY
        self.padding = [16, 14, 16, 14]
        self.font_size = '14sp'
        self.hint_text_color = COLOR_TEXT_MUTED


# ==========================================
# 1. PROFILE / ONBOARDING SCREEN
# ==========================================
class ProfileScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance

        main_layout = BackgroundBoxLayout(bg_color=COLOR_BG, orientation='vertical', padding=[30, 50, 30, 40], spacing=25)

        # App Identity Section
        header_box = BoxLayout(orientation='vertical', size_hint_y=None, height=120, spacing=8)
        title = Label(
            text="Decentralized Chat",
            font_size='28sp',
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="center"
        )
        subtitle = Label(
            text="Zero servers. Fully local. Instant connection.",
            font_size='13sp',
            color=COLOR_TEXT_MUTED,
            halign="center"
        )
        header_box.add_widget(title)
        header_box.add_widget(subtitle)
        main_layout.add_widget(header_box)

        # Profile Creation Card
        form_card = BackgroundBoxLayout(
            bg_color=COLOR_SURFACE, 
            radius=[16], 
            orientation='vertical', 
            padding=[24, 24, 24, 24], 
            spacing=16,
            size_hint_y=None,
            height=300,
            has_border=True
        )

        # Elegant Text Input
        self.username_input = PremiumTextInput(
            hint_text="Enter custom username...",
            multiline=False,
            size_hint_y=None,
            height=50
        )
        form_card.add_widget(self.username_input)

        # Dropdowns
        self.avatar_spinner = Spinner(
            text="🦊 Fox",
            values=("🦊 Fox", "🐱 Cat", "🐼 Panda", "🐯 Tiger", "👽 Alien", "🤖 Robot"),
            size_hint_y=None,
            height=48,
            background_normal="",
            background_color=COLOR_SURFACE_LIGHT,
            color=COLOR_TEXT_PRIMARY,
            option_cls='SpinnerOption'
        )
        form_card.add_widget(self.avatar_spinner)

        self.status_spinner = Spinner(
            text="🟢 Active & Ready",
            values=("🟢 Active & Ready", "🎮 In-game", "🚀 Hacking...", "☕ Away from keyboard"),
            size_hint_y=None,
            height=48,
            background_normal="",
            background_color=COLOR_SURFACE_LIGHT,
            color=COLOR_TEXT_PRIMARY
        )
        form_card.add_widget(self.status_spinner)

        # Error label
        self.error_label = Label(text="", color=(0.9, 0.3, 0.3, 1), size_hint_y=None, height=24, font_size='12sp', bold=True)
        form_card.add_widget(self.error_label)

        main_layout.add_widget(form_card)

        # Primary Join Button
        join_btn = InteractiveButton(
            text="Create Identity",
            bg_color=COLOR_PRIMARY,
            size_hint_y=None,
            height=54,
            bold=True
        )
        join_btn.bind(on_release=self.register_user)
        main_layout.add_widget(join_btn)

        main_layout.add_widget(Label())  # Layout Spacer
        self.add_widget(main_layout)

    def register_user(self, instance):
        username = self.username_input.text.strip()
        if not username:
            self.error_label.text = "Username cannot be empty!"
            return

        self.app.my_profile = {
            "username": username,
            "avatar": self.avatar_spinner.text,
            "status": self.status_spinner.text
        }
        
        self.app.store.put('user_profile', **self.app.my_profile)
        self.app.setup_network_and_ui()


# ==========================================
# 2. MAIN CHAT INTERFACE SCREEN
# ==========================================
class ChatScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance

        self.main_split = BoxLayout(orientation='horizontal')

        # --- Sidebar Left ---
        self.sidebar = BackgroundBoxLayout(bg_color=COLOR_BG, orientation='vertical', size_hint_x=0.32, padding=[12, 16, 12, 16], spacing=12)
        
        lbl_online = Label(
            text="PEERS RECORDED",
            font_size='10sp',
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=24,
            halign="left"
        )
        lbl_online.bind(size=lbl_online.setter('text_size'))
        self.sidebar.add_widget(lbl_online)

        self.peers_scroll = ScrollView(size_hint_y=0.84)
        self.peers_list = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.peers_list.bind(minimum_height=self.peers_list.setter('height'))
        self.peers_scroll.add_widget(self.peers_list)
        self.sidebar.add_widget(self.peers_scroll)

        # Sidebar Footer
        self.my_profile_box = BackgroundBoxLayout(
            bg_color=COLOR_SURFACE, 
            radius=[12], 
            orientation='horizontal', 
            size_hint_y=0.10, 
            padding=[12, 8, 12, 8], 
            spacing=10,
            has_border=True
        )
        self.my_profile_lbl = Label(text="", halign="left", valign="middle", markup=True, font_size='13sp')
        self.my_profile_lbl.bind(size=self.my_profile_lbl.setter('text_size'))
        self.my_profile_box.add_widget(self.my_profile_lbl)
        self.sidebar.add_widget(self.my_profile_box)

        self.main_split.add_widget(self.sidebar)

        # --- Chat Window Right ---
        self.chat_pane = BackgroundBoxLayout(bg_color=COLOR_SURFACE, orientation='vertical', size_hint_x=0.68)

        # Chat Window Top Header
        self.chat_header = BackgroundBoxLayout(
            bg_color=COLOR_BG, 
            orientation='horizontal', 
            size_hint_y=0.09, 
            padding=[20, 10, 20, 10],
            has_border=True,
            border_color=COLOR_BORDER
        )
        self.chat_title = Label(
            text="Choose an identity on the left to start direct messaging",
            bold=True,
            font_size='14sp',
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle"
        )
        self.chat_title.bind(size=self.chat_title.setter('text_size'))
        self.chat_header.add_widget(self.chat_title)
        self.chat_pane.add_widget(self.chat_header)

        # Scrollable Active Feed
        self.feed_scroll = ScrollView(size_hint_y=0.81, do_scroll_x=False)
        self.feed_layout = GridLayout(cols=1, spacing=14, size_hint_y=None, padding=[16, 16, 16, 16])
        self.feed_layout.bind(minimum_height=self.feed_layout.setter('height'))
        self.feed_scroll.add_widget(self.feed_layout)
        self.chat_pane.add_widget(self.feed_scroll)

        # Bottom Input / Delivery Bar
        self.bottom_bar = BoxLayout(orientation='horizontal', size_hint_y=0.10, padding=[16, 10, 16, 14], spacing=10)
        self.entry_field = PremiumTextInput(
            hint_text="No peer selected...",
            multiline=False,
            disabled=True
        )
        self.entry_field.bind(on_text_validate=self.send_click)
        self.bottom_bar.add_widget(self.entry_field)

        self.send_btn = InteractiveButton(
            text="Send",
            disabled=True,
            size_hint_x=0.18,
            bg_color=COLOR_PRIMARY
        )
        self.send_btn.bind(on_release=self.send_click)
        self.bottom_bar.add_widget(self.send_btn)

        self.chat_pane.add_widget(self.bottom_bar)
        self.main_split.add_widget(self.chat_pane)

        self.add_widget(self.main_split)

    def populate_my_profile(self):
        profile = self.app.my_profile
        self.my_profile_lbl.text = f"[b]{profile['avatar'].split()[-1]} {profile['username']}[/b]\n[size=11sp][color=8c94a6]{profile['status']}[/color][/size]"

    def update_friends_list(self):
        self.peers_list.clear_widgets()
        sorted_peers = sorted(self.app.active_peers.items(), key=lambda item: item[1].get('online', False), reverse=True)

        for ip, info in sorted_peers:
            is_selected = (ip == self.app.selected_ip)
            is_online = info.get('online', False)
            
            status_dot = "🟢" if is_online else "🔴"
            status_text = f"{status_dot} {info['status'] if is_online else 'Offline'}"
            
            btn_text = f"  {info['avatar'].split()[-1]}  [b]{info['username']}[/b]\n  [size=10sp][color=8c94a6]{status_text}[/color][/size]"
            
            if is_selected:
                bg_color = COLOR_PRIMARY
            elif is_online:
                bg_color = COLOR_SURFACE_LIGHT
            else:
                bg_color = COLOR_BG
                
            btn = InteractiveButton(
                text=btn_text,
                size_hint_y=None,
                height=64,
                bg_color=bg_color,
                halign="left",
                valign="middle",
                markup=True,
                radius=[12]
            )
            if not is_online:
                btn.opacity = 0.55
                
            btn.bind(size=lambda s, w: setattr(s, 'text_size', (s.width - 24, None)))
            btn.bind(on_release=lambda instance, ip_ref=ip: self.select_friend(ip_ref))
            self.peers_list.add_widget(btn)

    def select_friend(self, ip):
        self.app.selected_ip = ip
        info = self.app.active_peers[ip]
        is_online = info.get('online', False)
        
        self.chat_title.text = f"💬  {info['avatar']}  {info['username']} ({'Online' if is_online else 'Offline'})"
        
        if is_online:
            self.entry_field.disabled = False
            self.send_btn.disabled = False
            self.entry_field.hint_text = "Type local peer message..."
        else:
            self.entry_field.disabled = True
            self.send_btn.disabled = True
            self.entry_field.hint_text = "Peer is currently offline. Viewing history only."

        self.refresh_chat_display()
        self.update_friends_list()
        
        if is_online:
            self.entry_field.focus = True

    def send_click(self, instance):
        msg_text = self.entry_field.text.strip()
        if msg_text and self.app.selected_ip:
            payload = f"MSG:{msg_text}"
            try:
                self.app.sock.sendto(payload.encode('utf-8'), (self.app.selected_ip, PORT))
                self.app.chat_history[self.app.selected_ip].append({
                    "sender": "You",
                    "text": msg_text,
                    "is_me": True
                })
                
                self.app.chats_store.put(self.app.selected_ip, history=self.app.chat_history[self.app.selected_ip])
                
                self.entry_field.text = ""
                self.refresh_chat_display()
                self.entry_field.focus = True
            except Exception:
                pass

    def refresh_chat_display(self):
        self.feed_layout.clear_widgets()
        ip = self.app.selected_ip
        if ip in self.app.chat_history:
            for item in self.app.chat_history[ip]:
                is_me = item["is_me"]
                
                bubble_layout = BoxLayout(orientation='horizontal', size_hint_y=None)
                spacer = Label(size_hint_x=0.20)
                
                bubble_text = f"{item['text']}" if is_me else f"[b][size=10sp][color=8c94a6]{item['sender']}[/color][/size][/b]\n{item['text']}"
                bubble_color = COLOR_PRIMARY if is_me else COLOR_SURFACE_LIGHT
                bubble_radius = [14, 14, 3, 14] if is_me else [14, 14, 14, 3]
                
                bubble = BackgroundBoxLayout(
                    bg_color=bubble_color,
                    radius=bubble_radius,
                    orientation='vertical',
                    size_hint_x=0.80,
                    size_hint_y=None,
                    padding=[14, 10, 14, 10]
                )
                
                lbl = Label(
                    text=bubble_text,
                    markup=True,
                    size_hint_y=None,
                    halign="left",
                    valign="top",
                    text_size=(None, None),
                    color=COLOR_TEXT_PRIMARY,
                    font_size='13sp'
                )
                lbl.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
                lbl.bind(texture_size=lambda s, t_sz: setattr(s, 'height', t_sz[1]))
                lbl.bind(height=lambda s, h: setattr(s.parent, 'height', h + 20))
                lbl.bind(height=lambda s, h: setattr(s.parent.parent, 'height', h + 20))
                
                bubble.add_widget(lbl)
                
                if is_me:
                    bubble_layout.add_widget(spacer)
                    bubble_layout.add_widget(bubble)
                else:
                    bubble_layout.add_widget(bubble)
                    bubble_layout.add_widget(spacer)
                    
                self.feed_layout.add_widget(bubble_layout)
                
            self.feed_scroll.scroll_y = 0


# ==========================================
# 3. KIVY APPLICATION CONTROLLER
# ==========================================
class P2PChatKivyApp(App):
    def build(self):
        self.title = "Offline P2P Messenger"
        
        self.sock = None
        self.my_profile = {}
        self.active_peers = {}     
        self.chat_history = {}     
        self.selected_ip = None
        self.my_ip = "127.0.0.1"

        self.store = JsonStore('user_profile.json')
        self.peers_store = JsonStore('peers_store.json')
        self.chats_store = JsonStore('chats_store.json')

        self.load_persisted_data()

        self.sm = ScreenManager()
        self.profile_screen = ProfileScreen(self, name="profile")
        self.chat_screen = ChatScreen(self, name="chat")
        
        self.sm.add_widget(self.profile_screen)
        self.sm.add_widget(self.chat_screen)

        if self.store.exists('user_profile'):
            saved_profile = self.store.get('user_profile')
            self.my_profile = {
                "username": saved_profile['username'],
                "avatar": saved_profile['avatar'],
                "status": saved_profile['status']
            }
            Clock.schedule_once(lambda dt: self.setup_network_and_ui())
        else:
            self.sm.current = "profile"

        return self.sm

    def load_persisted_data(self):
        for ip in self.peers_store.keys():
            peer_data = self.peers_store.get(ip)
            self.active_peers[ip] = {
                "username": peer_data.get("username", "Unknown"),
                "avatar": peer_data.get("avatar", "👤"),
                "status": peer_data.get("status", ""),
                "online": False
            }
            
        for ip in self.chats_store.keys():
            chat_data = self.chats_store.get(ip)
            self.chat_history[ip] = chat_data.get("history", [])

    def setup_network_and_ui(self):
        self.chat_screen.populate_my_profile()
        self.chat_screen.update_friends_list()
        self.sm.current = "chat"
        self.init_socket()
        
        threading.Thread(target=self.receive_loop, daemon=True).start()
        threading.Thread(target=self.broadcast_presence, daemon=True).start()

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            self.my_ip = s.getsockname()[0]
        except Exception:
            self.my_ip = '127.0.0.1'
        finally:
            s.close()
        return self.my_ip

    def init_socket(self):
        self.get_local_ip()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            self.sock.bind(("", PORT))
        except Exception as e:
            print(f"Could not bind port {PORT}: {e}")
            sys.exit(1)

    def broadcast_presence(self):
        while True:
            try:
                if self.my_profile:
                    payload = {
                        "type": "DISCOVER",
                        "username": self.my_profile["username"],
                        "avatar": self.my_profile["avatar"],
                        "status": self.my_profile["status"]
                    }
                    msg = json.dumps(payload)
                    self.sock.sendto(msg.encode('utf-8'), (BROADCAST_IP, PORT))
            except Exception:
                pass
            time.sleep(5)

    def receive_loop(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                ip = addr[0]
                
                if ip == self.my_ip or ip == "127.0.0.1":
                    continue
                    
                message = data.decode('utf-8')
                
                if message.startswith("{"):
                    try:
                        payload = json.loads(message)
                        msg_type = payload.get("type")
                        
                        if msg_type in ["DISCOVER", "DISCOVER_ACK"]:
                            username = payload.get("username", "Unknown")
                            avatar = payload.get("avatar", "👤")
                            status = payload.get("status", "")
                            
                            self.active_peers[ip] = {
                                "username": username,
                                "avatar": avatar,
                                "status": status,
                                "online": True
                            }
                            
                            self.peers_store.put(ip, username=username, avatar=avatar, status=status)
                            
                            if ip not in self.chat_history:
                                self.chat_history[ip] = []
                                self.chats_store.put(ip, history=[])
                                
                            if msg_type == "DISCOVER":
                                reply = {
                                    "type": "DISCOVER_ACK",
                                    "username": self.my_profile["username"],
                                    "avatar": self.my_profile["avatar"],
                                    "status": self.my_profile["status"]
                                }
                                self.sock.sendto(json.dumps(reply).encode('utf-8'), (ip, PORT))
                            
                            Clock.schedule_once(lambda dt: self.chat_screen.update_friends_list())
                                
                    except json.JSONDecodeError:
                        pass
                        
                elif message.startswith("MSG:"):
                    actual_msg = message.split(":", 1)[1]
                    peer_data = self.active_peers.get(ip, {"username": "Unknown", "avatar": "👤"})
                    sender_display = f"{peer_data['avatar']} {peer_data['username']}"
                    
                    self.chat_history.setdefault(ip, []).append({
                        "sender": sender_display,
                        "text": actual_msg,
                        "is_me": False
                    })
                    
                    self.chats_store.put(ip, history=self.chat_history[ip])
                    
                    if self.selected_ip == ip:
                        Clock.schedule_once(lambda dt: self.chat_screen.refresh_chat_display())
                        
            except Exception:
                break


if __name__ == "__main__":
    P2PChatKivyApp().run()
