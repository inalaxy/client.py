import socket
import threading
import time
import sys
import json
import hashlib
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
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse

PORT = 50002
BROADCAST_IP = "255.255.255.255"

# --- PREMIUM SAAS COLOR PALETTE ---
COLOR_BG = (0.05, 0.05, 0.07, 1)          # #0D0D11 Deep obsidian black
COLOR_SURFACE = (0.10, 0.11, 0.14, 1)     # #1A1B24 Premium dark surface
COLOR_SURFACE_LIGHT = (0.15, 0.16, 0.20, 1) # #262933 Active/Hover state
COLOR_PRIMARY = (0.31, 0.40, 0.93, 1)     # #4F66ED Electric Indigo
COLOR_BORDER = (0.18, 0.19, 0.24, 1)      # Subtle layout boundaries
COLOR_TEXT_PRIMARY = (0.96, 0.96, 0.98, 1) # Crisp off-white
COLOR_TEXT_MUTED = (0.50, 0.53, 0.60, 1)   # Cool grey details
COLOR_ONLINE = (0.06, 0.80, 0.48, 1)      # Emerald green status
COLOR_OFFLINE = (0.84, 0.25, 0.25, 1)     # Deep crimson

# Premium generated gradient pools for initials avatars
AVATAR_COLORS = [
    (0.31, 0.40, 0.93, 1), # Indigo
    (0.06, 0.80, 0.48, 1), # Emerald
    (0.85, 0.38, 0.18, 1), # Coral
    (0.62, 0.31, 0.93, 1), # Purple
    (0.18, 0.70, 0.85, 1), # Cyan
]

def get_initials(username: str) -> str:
    parts = username.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return username.strip()[:2].upper() if username else "??"

def get_avatar_color(username: str) -> tuple:
    if not username:
        return AVATAR_COLORS[0]
    hash_val = int(hashlib.md5(username.lower().encode('utf-8')).hexdigest(), 16)
    return AVATAR_COLORS[hash_val % len(AVATAR_COLORS)]


# --- HIGH-END CUSTOM UI COMPONENTS ---

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


class VisualAvatar(BoxLayout):
    """Dynamic procedural circle avatar rendering initials based on username hashing."""
    def __init__(self, username, size_hint=(None, None), size=(40, 40), **kwargs):
        super().__init__(size_hint=size_hint, size=size, orientation='vertical', **kwargs)
        self.username = username
        self.initials = get_initials(username)
        self.bg_color = get_avatar_color(username)
        
        with self.canvas.before:
            Color(*self.bg_color)
            self.circle = Ellipse(pos=self.pos, size=self.size)
            
        self.lbl = Label(
            text=self.initials,
            font_size=str(int(self.height * 0.38)) + 'sp',
            bold=True,
            color=(1, 1, 1, 1),
            halign="center",
            valign="middle"
        )
        self.lbl.bind(size=self.lbl.setter('text_size'))
        self.add_widget(self.lbl)
        
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, instance, value):
        self.circle.pos = instance.pos
        self.circle.size = instance.size


class InteractiveButton(Button):
    def __init__(self, bg_color=COLOR_PRIMARY, radius=[8], **kwargs):
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

        main_layout = BackgroundBoxLayout(bg_color=COLOR_BG, orientation='vertical', padding=[40, 60, 40, 50], spacing=30)

        # High-end branding header
        header_box = BoxLayout(orientation='vertical', size_hint_y=None, height=130, spacing=10)
        title = Label(
            text="DECENTRALIZED NODE",
            font_size='26sp',
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="center"
        )
        subtitle = Label(
            text="Secure. Zero Servers. Local LAN Mesh Routing.",
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
            padding=[28, 30, 28, 30], 
            spacing=20,
            size_hint_y=None,
            height=260,
            has_border=True
        )

        label_inst = Label(
            text="CREATE UNIQUE NODE PROFILE ID",
            font_size='11sp',
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=20,
            halign="left"
        )
        label_inst.bind(size=label_inst.setter('text_size'))
        form_card.add_widget(label_inst)

        # Dynamic profile naming input
        self.username_input = PremiumTextInput(
            hint_text="e.g., John Doe, Node-99",
            multiline=False,
            size_hint_y=None,
            height=54
        )
        form_card.add_widget(self.username_input)

        self.status_spinner = Spinner(
            text="🟢 Active Node",
            values=("🟢 Active Node", "📡 In-game", "💻 Developing...", "☕ Away from desk"),
            size_hint_y=None,
            height=50,
            background_normal="",
            background_color=COLOR_SURFACE_LIGHT,
            color=COLOR_TEXT_PRIMARY
        )
        form_card.add_widget(self.status_spinner)

        # Error handling labels
        self.error_label = Label(text="", color=COLOR_OFFLINE, size_hint_y=None, height=24, font_size='12sp', bold=True)
        form_card.add_widget(self.error_label)

        main_layout.add_widget(form_card)

        # Primary call-to-action button
        join_btn = InteractiveButton(
            text="INITIALIZE PROFILE",
            bg_color=COLOR_PRIMARY,
            size_hint_y=None,
            height=56,
            bold=True
        )
        join_btn.bind(on_release=self.register_user)
        main_layout.add_widget(join_btn)

        main_layout.add_widget(Label())  # Layout Spacer
        self.add_widget(main_layout)

    def register_user(self, instance):
        username = self.username_input.text.strip()
        if not username:
            self.error_label.text = "Error: Username parameter is empty."
            return

        self.app.my_profile = {
            "username": username,
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

        # --- Sidebar (Left Navigation) ---
        self.sidebar = BackgroundBoxLayout(bg_color=COLOR_BG, orientation='vertical', size_hint_x=0.30, padding=[12, 20, 12, 16], spacing=14)
        
        lbl_online = Label(
            text="ACTIVE MESH PEERS",
            font_size='10sp',
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=24,
            halign="left"
        )
        lbl_online.bind(size=lbl_online.setter('text_size'))
        self.sidebar.add_widget(lbl_online)

        self.peers_scroll = ScrollView(size_hint_y=0.82)
        self.peers_list = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.peers_list.bind(minimum_height=self.peers_list.setter('height'))
        self.peers_scroll.add_widget(self.peers_list)
        self.sidebar.add_widget(self.peers_scroll)

        # Dynamic Footer Displaying User profile details
        self.my_profile_box = BackgroundBoxLayout(
            bg_color=COLOR_SURFACE, 
            radius=[12], 
            orientation='horizontal', 
            size_hint_y=0.12, 
            padding=[10, 10, 10, 10], 
            spacing=10,
            has_border=True
        )
        self.sidebar.add_widget(self.my_profile_box)
        self.main_split.add_widget(self.sidebar)

        # --- Main Chat Window Area (Right Pane) ---
        self.chat_pane = BackgroundBoxLayout(bg_color=COLOR_SURFACE, orientation='vertical', size_hint_x=0.70)

        # Premium Chat Pane Header Context Bar
        self.chat_header = BackgroundBoxLayout(
            bg_color=COLOR_BG, 
            orientation='horizontal', 
            size_hint_y=0.10, 
            padding=[24, 12, 24, 12],
            has_border=True,
            border_color=COLOR_BORDER
        )
        self.chat_title = Label(
            text="Select an active mesh peer from the left sidebar to initialize encryption",
            bold=True,
            font_size='13sp',
            color=COLOR_TEXT_MUTED,
            halign="left",
            valign="middle"
        )
        self.chat_title.bind(size=self.chat_title.setter('text_size'))
        self.chat_header.add_widget(self.chat_title)
        self.chat_pane.add_widget(self.chat_header)

        # Chat Message Viewport Feed
        self.feed_scroll = ScrollView(size_hint_y=0.78, do_scroll_x=False)
        self.feed_layout = GridLayout(cols=1, spacing=16, size_hint_y=None, padding=[24, 24, 24, 24])
        self.feed_layout.bind(minimum_height=self.feed_layout.setter('height'))
        self.feed_scroll.add_widget(self.feed_layout)
        self.chat_pane.add_widget(self.feed_scroll)

        # Input & Actions Footer Toolbar
        self.bottom_bar = BoxLayout(orientation='horizontal', size_hint_y=0.12, padding=[24, 12, 24, 16], spacing=12)
        self.entry_field = PremiumTextInput(
            hint_text="Terminal offline. Select client identity...",
            multiline=False,
            disabled=True
        )
        self.entry_field.bind(on_text_validate=self.send_click)
        self.bottom_bar.add_widget(self.entry_field)

        self.send_btn = InteractiveButton(
            text="SEND",
            disabled=True,
            size_hint_x=0.15,
            bg_color=COLOR_PRIMARY
        )
        self.send_btn.bind(on_release=self.send_click)
        self.bottom_bar.add_widget(self.send_btn)

        self.chat_pane.add_widget(self.bottom_bar)
        self.main_split.add_widget(self.chat_pane)

        self.add_widget(self.main_split)

    def populate_my_profile(self):
        self.my_profile_box.clear_widgets()
        profile = self.app.my_profile
        
        avatar_widget = VisualAvatar(username=profile['username'], size=(36, 36))
        text_layout = BoxLayout(orientation='vertical', spacing=2)
        
        name_lbl = Label(text=f"[b]{profile['username']}[/b]", markup=True, halign="left", font_size='13sp', color=COLOR_TEXT_PRIMARY)
        status_lbl = Label(text=f"[size=10sp]{profile['status']}[/size]", markup=True, halign="left", color=COLOR_TEXT_MUTED)
        
        name_lbl.bind(size=name_lbl.setter('text_size'))
        status_lbl.bind(size=status_lbl.setter('text_size'))
        
        text_layout.add_widget(name_lbl)
        text_layout.add_widget(status_lbl)
        
        self.my_profile_box.add_widget(avatar_widget)
        self.my_profile_box.add_widget(text_layout)

    def update_friends_list(self):
        self.peers_list.clear_widgets()
        sorted_peers = sorted(self.app.active_peers.items(), key=lambda item: item[1].get('online', False), reverse=True)

        for ip, info in sorted_peers:
            is_selected = (ip == self.app.selected_ip)
            is_online = info.get('online', False)
            status_text = info['status'] if is_online else 'Offline Node'
            
            # Interactive container for sidebar items
            bg_color = COLOR_PRIMARY if is_selected else (COLOR_SURFACE_LIGHT if is_online else COLOR_BG)
            peer_container = BackgroundBoxLayout(
                bg_color=bg_color,
                radius=[8],
                orientation='horizontal',
                size_hint_y=None,
                height=60,
                padding=[8, 8, 8, 8],
                spacing=10
            )
            
            avatar = VisualAvatar(username=info['username'], size=(36, 36))
            text_container = BoxLayout(orientation='vertical', spacing=2)
            
            peer_name = Label(
                text=f"[b]{info['username']}[/b]", 
                markup=True, 
                halign="left", 
                valign="middle", 
                font_size='12sp',
                color=COLOR_TEXT_PRIMARY
            )
            peer_name.bind(size=peer_name.setter('text_size'))
            
            status_dot = "🟢" if is_online else "🔴"
            peer_status = Label(
                text=f"{status_dot} [size=10sp]{status_text}[/size]", 
                markup=True, 
                halign="left", 
                valign="middle", 
                color=COLOR_TEXT_MUTED if not is_selected else COLOR_TEXT_PRIMARY
            )
            peer_status.bind(size=peer_status.setter('text_size'))
            
            text_container.add_widget(peer_name)
            text_container.add_widget(peer_status)
            
            peer_container.add_widget(avatar)
            peer_container.add_widget(text_container)
            
            if not is_online:
                peer_container.opacity = 0.5
                
            # Bind physical clicks to component selection trigger
            btn = Button(background_color=(0, 0, 0, 0), size_hint=(1, 1))
            btn.bind(on_release=lambda instance, ip_ref=ip: self.select_friend(ip_ref))
            
            outer_overlay = BoxLayout(size_hint_y=None, height=60)
            peer_container.add_widget(btn) # Add invisible button into composition
            
            self.peers_list.add_widget(peer_container)

    def select_friend(self, ip):
        self.app.selected_ip = ip
        info = self.app.active_peers[ip]
        is_online = info.get('online', False)
        
        self.chat_title.text = f"💬  CONNECTING ENCRYPTED TUNNEL TO:  [b]{info['username'].upper()}[/b] ({'ONLINE' if is_online else 'OFFLINE'})"
        self.chat_title.markup = True
        
        if is_online:
            self.entry_field.disabled = False
            self.send_btn.disabled = False
            self.entry_field.hint_text = "Type message..."
        else:
            self.entry_field.disabled = True
            self.send_btn.disabled = True
            self.entry_field.hint_text = "Target offline. History visualization mode active."

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
                spacer = Label(size_hint_x=0.25)
                
                bubble_text = f"{item['text']}" if is_me else f"[b][size=11sp][color=4F66ED]{item['sender']}[/color][/size][/b]\n{item['text']}"
                bubble_color = COLOR_PRIMARY if is_me else COLOR_SURFACE_LIGHT
                # Sophisticated dynamic professional asymmetric rounding
                bubble_radius = [14, 14, 4, 14] if is_me else [14, 14, 14, 4]
                
                bubble = BackgroundBoxLayout(
                    bg_color=bubble_color,
                    radius=bubble_radius,
                    orientation='vertical',
                    size_hint_x=0.75,
                    size_hint_y=None,
                    padding=[16, 12, 16, 12]
                )
                
                lbl = Label(
                    text=bubble_text,
                    markup=True,
                    size_hint_y=None,
                    halign="left",
                    valign="top",
                    color=COLOR_TEXT_PRIMARY,
                    font_size='13sp',
                    line_height=1.2
                )
                lbl.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
                lbl.bind(texture_size=lambda s, t_sz: setattr(s, 'height', t_sz[1]))
                lbl.bind(height=lambda s, h: setattr(s.parent, 'height', h + 24))
                lbl.bind(height=lambda s, h: setattr(s.parent.parent, 'height', h + 24))
                
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
        self.title = "Decentralized Mesh Messenger"
        
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
                            status = payload.get("status", "")
                            
                            self.active_peers[ip] = {
                                "username": username,
                                "status": status,
                                "online": True
                            }
                            
                            self.peers_store.put(ip, username=username, status=status)
                            
                            if ip not in self.chat_history:
                                self.chat_history[ip] = []
                                self.chats_store.put(ip, history=[])
                                
                            if msg_type == "DISCOVER":
                                reply = {
                                    "type": "DISCOVER_ACK",
                                    "username": self.my_profile["username"],
                                    "status": self.my_profile["status"]
                                }
                                self.sock.sendto(json.dumps(reply).encode('utf-8'), (ip, PORT))
                            
                            Clock.schedule_once(lambda dt: self.chat_screen.update_friends_list())
                                
                    except json.JSONDecodeError:
                        pass
                        
                elif message.startswith("MSG:"):
                    actual_msg = message.split(":", 1)[1]
                    peer_data = self.active_peers.get(ip, {"username": "Unknown"})
                    sender_display = f"{peer_data['username']}"
                    
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
