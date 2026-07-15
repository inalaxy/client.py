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
from kivy.graphics import Color, RoundedRectangle, Rectangle

PORT = 50002
BROADCAST_IP = "255.255.255.255"

# --- PALETTE DEFINITIONS ---
COLOR_BG = (0.11, 0.11, 0.14, 1)          # #1c1c24 Deep dark background
COLOR_SURFACE = (0.16, 0.17, 0.21, 1)     # #2a2b36 Card background
COLOR_PRIMARY = (0.34, 0.39, 0.94, 1)     # #5865f2 Discord-ish Accent Blue
COLOR_PRIMARY_HOVER = (0.27, 0.32, 0.8, 1)
COLOR_TEXT_MUTED = (0.6, 0.62, 0.68, 1)


# --- Custom Styled Canvas Widgets ---

class BackgroundBoxLayout(BoxLayout):
    def __init__(self, bg_color, radius=[0, 0, 0, 0], **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            self.color_instruction = Color(*self.bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=self.radius)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class SmoothButton(Button):
    def __init__(self, bg_color=COLOR_PRIMARY, radius=[8], **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0) # Clear default texture tint
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            self.color_instruction = Color(*self.bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=self.radius)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class SmoothTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0.2, 0.21, 0.26, 1) # Sleek inner dark inputs
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = COLOR_PRIMARY
        self.padding = [12, 12, 12, 12]


# ==========================================
# 1. PROFILE / ONBOARDING SCREEN
# ==========================================
class ProfileScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance

        main_layout = BackgroundBoxLayout(bg_color=COLOR_BG, orientation='vertical', padding=[40, 60, 40, 40], spacing=25)

        # Title / Welcome Header
        header_box = BoxLayout(orientation='vertical', size_hint_y=None, height=100, spacing=8)
        title = Label(
            text="Offline P2P Messenger",
            font_size='26sp',
            bold=True,
            color=(1, 1, 1, 1)
        )
        subtitle = Label(
            text="Let's build your profile to start chatting",
            font_size='14sp',
            color=COLOR_TEXT_MUTED
        )
        header_box.add_widget(title)
        header_box.add_widget(subtitle)
        main_layout.add_widget(header_box)

        # Form fields container (Mimicking a floating card)
        form_card = BackgroundBoxLayout(
            bg_color=COLOR_SURFACE, 
            radius=[12], 
            orientation='vertical', 
            padding=20, 
            spacing=15,
            size_hint_y=None,
            height=280
        )

        self.username_input = SmoothTextInput(
            hint_text="Choose Username (e.g. NeonCoder)",
            multiline=False,
            size_hint_y=None,
            height=46
        )
        form_card.add_widget(self.username_input)

        # Avatar Spinner
        self.avatar_spinner = Spinner(
            text="🦊 Fox",
            values=("🦊 Fox", "🐱 Cat", "🐼 Panda", "🐯 Tiger", "👽 Alien", "🤖 Robot"),
            size_hint_y=None,
            height=46,
            background_normal="",
            background_color=(0.2, 0.21, 0.26, 1),
            color=(1, 1, 1, 1)
        )
        form_card.add_widget(self.avatar_spinner)

        # Status Spinner
        self.status_spinner = Spinner(
            text="🟢 Active & Ready",
            values=("🟢 Active & Ready", "🎮 Gaming", "🚀 Coding...", "☕ Coffee break"),
            size_hint_y=None,
            height=46,
            background_normal="",
            background_color=(0.2, 0.21, 0.26, 1),
            color=(1, 1, 1, 1)
        )
        form_card.add_widget(self.status_spinner)

        # Error label
        self.error_label = Label(text="", color=(1, 0.3, 0.3, 1), size_hint_y=None, height=30, font_size='13sp')
        form_card.add_widget(self.error_label)

        main_layout.add_widget(form_card)

        # Submit Button
        join_btn = SmoothButton(
            text="Create Account & Join",
            bg_color=COLOR_PRIMARY,
            size_hint_y=None,
            height=50,
            bold=True
        )
        join_btn.bind(on_release=self.register_user)
        main_layout.add_widget(join_btn)

        # Fill bottom spacing
        main_layout.add_widget(Label())
        self.add_widget(main_layout)

    def register_user(self, instance):
        username = self.username_input.text.strip()
        if not username:
            self.error_label.text = "Please pick a cool username to continue!"
            return

        # Save profile inside App
        self.app.my_profile = {
            "username": username,
            "avatar": self.avatar_spinner.text,
            "status": self.status_spinner.text
        }
        
        # Save persistence storage (JSON File Store)
        self.app.store.put('user_profile', **self.app.my_profile)
        
        # Initialize networking and transition
        self.app.setup_network_and_ui()


# ==========================================
# 2. MAIN CHAT INTERFACE SCREEN
# ==========================================
class ChatScreen(Screen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance

        # Main Split Panel (Sidebar Left, Chat Window Right)
        self.main_split = BoxLayout(orientation='horizontal')

        # --- Sidebar Left ---
        self.sidebar = BackgroundBoxLayout(bg_color=COLOR_BG, orientation='vertical', size_hint_x=0.35, padding=12, spacing=10)
        
        lbl_online = Label(
            text="ONLINE PEERS",
            font_size='11sp',
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=20,
            halign="left"
        )
        lbl_online.bind(size=lbl_online.setter('text_size'))
        self.sidebar.add_widget(lbl_online)

        # Scroll container for peers
        self.peers_scroll = ScrollView(size_hint_y=0.85)
        self.peers_list = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.peers_list.bind(minimum_height=self.peers_list.setter('height'))
        self.peers_scroll.add_widget(self.peers_list)
        self.sidebar.add_widget(self.peers_scroll)

        # Footer profile area (Inside sidebar)
        self.my_profile_box = BackgroundBoxLayout(
            bg_color=COLOR_SURFACE, 
            radius=[8], 
            orientation='horizontal', 
            size_hint_y=0.12, 
            padding=10, 
            spacing=10
        )
        self.my_profile_lbl = Label(text="", halign="left", valign="middle", markup=True)
        self.my_profile_lbl.bind(size=self.my_profile_lbl.setter('text_size'))
        self.my_profile_box.add_widget(self.my_profile_lbl)
        self.sidebar.add_widget(self.my_profile_box)

        self.main_split.add_widget(self.sidebar)

        # --- Chat Window Right ---
        self.chat_pane = BackgroundBoxLayout(bg_color=COLOR_SURFACE, orientation='vertical', size_hint_x=0.65)

        # Chat Header
        self.chat_header = BackgroundBoxLayout(
            bg_color=(0.14, 0.15, 0.18, 1), 
            orientation='horizontal', 
            size_hint_y=0.1, 
            padding=15
        )
        self.chat_title = Label(
            text="Select a peer to start chatting",
            bold=True,
            font_size='15sp',
            halign="left",
            valign="middle"
        )
        self.chat_title.bind(size=self.chat_title.setter('text_size'))
        self.chat_header.add_widget(self.chat_title)
        self.chat_pane.add_widget(self.chat_header)

        # Chat Message Feed (Scrollable)
        self.feed_scroll = ScrollView(size_hint_y=0.8, do_scroll_x=False)
        self.feed_layout = GridLayout(cols=1, spacing=12, size_hint_y=None, padding=15)
        self.feed_layout.bind(minimum_height=self.feed_layout.setter('height'))
        self.feed_scroll.add_widget(self.feed_layout)
        self.chat_pane.add_widget(self.feed_scroll)

        # Bottom Entry Row
        self.bottom_bar = BoxLayout(orientation='horizontal', size_hint_y=0.1, padding=12, spacing=10)
        self.entry_field = SmoothTextInput(
            hint_text="Type a message...",
            multiline=False,
            disabled=True
        )
        self.entry_field.bind(on_text_validate=self.send_click)
        self.bottom_bar.add_widget(self.entry_field)

        self.send_btn = SmoothButton(
            text="Send",
            disabled=True,
            size_hint_x=0.2,
            bg_color=COLOR_PRIMARY
        )
        self.send_btn.bind(on_release=self.send_click)
        self.bottom_bar.add_widget(self.send_btn)

        self.chat_pane.add_widget(self.bottom_bar)
        self.main_split.add_widget(self.chat_pane)

        self.add_widget(self.main_split)

    def populate_my_profile(self):
        profile = self.app.my_profile
        self.my_profile_lbl.text = f"[b]{profile['avatar'].split()[-1]} {profile['username']}[/b]\n[size=11sp][color=949ba4]{profile['status']}[/color][/size]"

    def update_friends_list(self):
        self.peers_list.clear_widgets()
        for ip, info in self.app.active_peers.items():
            is_selected = (ip == self.app.selected_ip)
            
            btn_text = f"  {info['avatar'].split()[-1]}  [b]{info['username']}[/b]\n  [size=11sp]{info['status']}[/size]"
            
            # Interactive visual highlighting for selected peers
            bg_color = COLOR_PRIMARY if is_selected else (0.2, 0.21, 0.26, 1)
            btn = SmoothButton(
                text=btn_text,
                size_hint_y=None,
                height=65,
                bg_color=bg_color,
                halign="left",
                valign="middle",
                markup=True
            )
            btn.bind(size=lambda s, w: setattr(s, 'text_size', (s.width - 20, None)))
            btn.bind(on_release=lambda instance, ip_ref=ip: self.select_friend(ip_ref))
            self.peers_list.add_widget(btn)

    def select_friend(self, ip):
        self.app.selected_ip = ip
        info = self.app.active_peers[ip]
        self.chat_title.text = f"💬  {info['avatar']}  {info['username']}"
        self.entry_field.disabled = False
        self.send_btn.disabled = False
        self.refresh_chat_display()
        self.update_friends_list()
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
                spacer = Label(size_hint_x=0.25)
                
                # Dynamic rich text in bubbles
                bubble_text = f"{item['text']}" if is_me else f"[b][size=11sp]{item['sender']}[/size][/b]\n{item['text']}"
                
                # Beautiful modern bubble colors and shapes
                bubble_color = COLOR_PRIMARY if is_me else (0.24, 0.25, 0.31, 1)
                bubble_radius = [14, 14, 2, 14] if is_me else [14, 14, 14, 2] # Custom curved corners
                
                bubble = BackgroundBoxLayout(
                    bg_color=bubble_color,
                    radius=bubble_radius,
                    orientation='vertical',
                    size_hint_x=0.75,
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
                    color=(1, 1, 1, 1)
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
        self.active_peers = {}     # { IP: { "username": ..., "avatar": ..., "status": ... } }
        self.chat_history = {}     # { IP: [ {"sender": ..., "text": ..., "is_me": ...} ] }
        self.selected_ip = None
        self.my_ip = "127.0.0.1"

        # Safe local storage
        self.store = JsonStore('user_profile.json')

        self.sm = ScreenManager()
        self.profile_screen = ProfileScreen(self, name="profile")
        self.chat_screen = ChatScreen(self, name="chat")
        
        self.sm.add_widget(self.profile_screen)
        self.sm.add_widget(self.chat_screen)

        # Profile retrieval
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

    def setup_network_and_ui(self):
        self.chat_screen.populate_my_profile()
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

    # --- Background Network Tasks ---

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
                            
                            if ip not in self.active_peers:
                                self.active_peers[ip] = {
                                    "username": username,
                                    "avatar": avatar,
                                    "status": status
                                }
                                self.chat_history[ip] = []
                                
                                if msg_type == "DISCOVER":
                                    reply = {
                                        "type": "DISCOVER_ACK",
                                        "username": self.my_profile["username"],
                                        "avatar": self.my_profile["avatar"],
                                        "status": self.my_profile["status"]
                                    }
                                    self.sock.sendto(json.dumps(reply).encode('utf-8'), (ip, PORT))
                            else:
                                self.active_peers[ip].update({
                                    "username": username,
                                    "avatar": avatar,
                                    "status": status
                                })
                            
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
                    
                    if self.selected_ip == ip:
                        Clock.schedule_once(lambda dt: self.chat_screen.refresh_chat_display())
                        
            except Exception:
                break


if __name__ == "__main__":
    P2PChatKivyApp().run()
