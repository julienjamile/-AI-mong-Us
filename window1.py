import pygame
import math
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_IMAGES = ASSETS_DIR / "images"
ASSETS_SOUNDS = ASSETS_DIR / "sounds"
ASSETS_FONTS = ASSETS_DIR / "fonts"

def asset_image_path(name):
    return ASSETS_IMAGES / name

def asset_sound_path(name):
    return ASSETS_SOUNDS / name

# ── WINDOWS DPI FIX ────────────────────────────────────────────────────────
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# ── WINDOWS TITLE BAR MANAGEMENT ───────────────────────────────────────────
try:
    import ctypes.wintypes as wt
    from ctypes import windll, Structure, POINTER, c_int
    
    # Windows API constants
    GWL_STYLE = -16
    GWL_EXSTYLE = -20
    WS_CAPTION = 0x00C00000  # Title bar
    WS_MAXIMIZEBOX = 0x00010000  # Maximize button
    WS_MINIMIZEBOX = 0x00020000  # Minimize button
    WS_SYSMENU = 0x00080000  # System menu (also enables close button)
    
    def get_hwnd():
        """Get the pygame window handle on Windows"""
        try:
            return pygame.display.get_surface().get_flags()
        except:
            pass
        # Alternative method to get HWND
        try:
            return int(pygame.display.get_wm_info()['window'])
        except:
            return None
    
    def get_window_handle():
        """Get actual window handle via pygame"""
        try:
            info = pygame.display.get_wm_info()
            if 'window' in info:
                return info['window']
        except:
            pass
        return None
    
    def show_title_bar():
        """Show window title bar with minimize and close buttons (maximize disabled)"""
        try:
            hwnd = get_window_handle()
            if hwnd:
                style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
                # Add caption and system menu (close button), but NOT maximize button
                new_style = style | WS_CAPTION | WS_MINIMIZEBOX | WS_SYSMENU
                new_style = new_style & ~WS_MAXIMIZEBOX  # Remove maximize button
                windll.user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
                windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)  # SWP_FRAMECHANGED
        except:
            pass
    
    def hide_title_bar():
        """Hide window title bar"""
        try:
            hwnd = get_window_handle()
            if hwnd:
                style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
                new_style = style & ~(WS_CAPTION | WS_MAXIMIZEBOX | WS_MINIMIZEBOX | WS_SYSMENU)
                windll.user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
                windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)  # SWP_FRAMECHANGED
        except:
            pass
    
    TITLE_BAR_AVAILABLE = True
except:
    TITLE_BAR_AVAILABLE = False
    def show_title_bar(): pass
    def hide_title_bar(): pass

# ── FIXED DESIGN RESOLUTION (match Figma exactly) ─────────────────────────
DESIGN_W = 1366
DESIGN_H = 768

# ── CONFIGURATION ──────────────────────────────────────────────────────────
FONT_NAME    = "ArcadeGamer.ttf"
PINK         = (255, 149, 213)
PINK_DARK    = (120,  40,  80)
PINK_GLOW    = (255, 100, 200)
NEON_CYAN    = ( 80, 230, 220)
WHITE        = (255, 255, 255)
DARK_BG      = ( 30,  15,  35)
MODAL_BG     = ( 45,  25,  55)
GRADIENT_TOP = ( 85,  75,  90)
GRADIENT_BOT = (175, 140, 205)

# ── HELPERS ────────────────────────────────────────────────────────────────
def get_arcade_font(size):
    if Path(FONT_NAME).exists():
        try:
            return pygame.font.Font(FONT_NAME, size)
        except:
            pass
    return pygame.font.SysFont("consolas", size, bold=True)

def draw_retro_text(surface, text, size, cx, cy, color=WHITE):
    font = get_arcade_font(size)
    shadow = font.render(text, False, PINK_DARK)
    surface.blit(shadow, shadow.get_rect(center=(int(cx) + 3, int(cy) + 3)))
    main = font.render(text, False, color)
    surface.blit(main, main.get_rect(center=(int(cx), int(cy))))

def draw_text_pixel(surface, text, size, color, cx, cy):
    font = get_arcade_font(size)
    surf = font.render(text, False, color)
    surface.blit(surf, surf.get_rect(center=(int(cx), int(cy))))

def draw_text_wrapped(surface, text, size, color, cx, top_y, max_width, line_spacing=1.2):
    font = get_arcade_font(size)
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    for index, line in enumerate(lines):
        surf = font.render(line, False, color)
        surface.blit(surf, surf.get_rect(center=(int(cx), int(top_y + index * size * line_spacing))))

# ── SCALED MOUSE POSITION ──────────────────────────────────────────────────
# Converts real mouse pos → design-space pos when using SCALED flag
def design_mouse_pos():
    mx, my = pygame.mouse.get_pos()
    return mx, my  # pygame.SCALED handles this automatically

# ── BOUNCE SCENE (INTRO) ──────────────────────────────────────────────────
class BounceScene:
    W, H = DESIGN_W, DESIGN_H

    def __init__(self, surface):
        self.surface = surface
        # Ground at 45% of design height
        self.ground_y   = int(self.H * 0.45)
        self.char_y     = self.ground_y + 280
        self.vy         = -50.0
        self.gravity    = 0.6
        self.bounce_damp= 0.60
        self.bouncing   = False
        self.done       = False
        self.start_timer= 60
        self.end_timer  = 90

        self.bot_image = None
        if asset_image_path("bot.png").exists():
            self.bot_image = pygame.image.load(asset_image_path("bot.png")).convert_alpha()

        self.gradient_surface = self._make_gradient()

    def _make_gradient(self):
        g = pygame.Surface((1, self.H))
        top, bot = GRADIENT_TOP, GRADIENT_BOT
        for y in range(self.H):
            t = y / self.H
            r = int(top[0] + (bot[0] - top[0]) * t)
            gv = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            pygame.draw.line(g, (r, gv, b), (0, y), (1, y))
        return g

    def draw_scene(self, surface):
        cx = self.W // 2
        surface.blit(pygame.transform.scale(self.gradient_surface, (self.W, self.H)), (0, 0))

        # Shadow ellipse — large & dark when bot is near ground, tiny & faded when high up
        dist    = max(0, self.ground_y - self.char_y)   # 0 = on ground, 280 = peak height
        t       = 1.0 - min(dist / 280, 1.0)            # 1.0 on ground → 0.0 at peak
        sh_sc   = 0.20 + t * 0.80                       # size:  0.20 (tiny) → 1.0 (full)
        alpha   = int(40 + t * 160)                     # alpha: 40   (faint) → 200 (dark)
        sh_w    = int(190 * sh_sc)
        sh_h    = int(24  * sh_sc)
        sh_surf = pygame.Surface((sh_w + 2, sh_h + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(sh_surf, (20, 10, 25, alpha), (0, 0, sh_w, sh_h))
        surface.blit(sh_surf, (cx - sh_w // 2, self.ground_y + 95 - sh_h // 2))

        if self.bot_image:
            iw, ih = self.bot_image.get_width(), self.bot_image.get_height()
            surface.blit(self.bot_image,
                (cx - iw // 2, int(self.char_y) - ih // 2))

    def update(self):
        if self.start_timer > 0:
            self.start_timer -= 1
            if self.start_timer == 0:
                self.bouncing = True
            return

        if self.bouncing:
            self.vy      += self.gravity
            self.char_y  += self.vy
            if self.char_y >= self.ground_y:
                self.char_y = self.ground_y
                if abs(self.vy) > 2.0:
                    self.vy = -self.vy * self.bounce_damp
                else:
                    self.vy, self.bouncing = 0, False

        if not self.bouncing and self.start_timer == 0:
            if self.end_timer > 0:
                self.end_timer -= 1
            else:
                self.done = True

# ── SELECTION SCENE ───────────────────────────────────────────────────────
# Figma node 51-52 layout — buttons at ~27% and ~73% horizontal
class SelectionScene:
    W, H = DESIGN_W, DESIGN_H

    def __init__(self, button_sound=None):
        self.button_sound = button_sound
        self.ticks     = 0
        self.light_pos = 0.0

        self.bg = None
        if asset_image_path("selection_bg.png").exists():
            self.bg = pygame.image.load(asset_image_path("selection_bg.png")).convert()

        self.bot_img = None
        if asset_image_path("bot.png").exists():
            raw = pygame.image.load(asset_image_path("bot.png")).convert_alpha()
            self.bot_img = pygame.transform.smoothscale(
                raw, (int(raw.get_width() * 1.5), int(raw.get_height() * 1.5)))

        # Figma: Back button center ≈ (370, 407), Play button center ≈ (997, 407)
        self.back_hb = pygame.Rect(0, 0, 240, 110)
        self.back_hb.center = (int(self.W * 0.271), int(self.H * 0.530))

        self.play_hb = pygame.Rect(0, 0, 240, 110)
        self.play_hb.center = (int(self.W * 0.730), int(self.H * 0.530))

    def _draw_hover_light(self, surface, rect):
        rad   = rect.height // 2
        px, py, pw, ph = rect.x, rect.y, rect.width, rect.height
        sw, sh = pw - 2*rad, ph - 2*rad
        arc   = (math.pi * rad) / 2
        total = 2*(sw + sh) + 4*arc

        def get_pt(d):
            d %= total
            if d < sw:  return (px+rad+d, py)
            d -= sw
            if d < arc: a = (d/arc)*(math.pi/2)-math.pi/2; return (px+pw-rad+math.cos(a)*rad, py+rad+math.sin(a)*rad)
            d -= arc
            if d < sh:  return (px+pw, py+rad+d)
            d -= sh
            if d < arc: a = (d/arc)*(math.pi/2);            return (px+pw-rad+math.cos(a)*rad, py+ph-rad+math.sin(a)*rad)
            d -= arc
            if d < sw:  return (px+pw-rad-d, py+ph)
            d -= sw
            if d < arc: a = (d/arc)*(math.pi/2)+math.pi/2; return (px+rad+math.cos(a)*rad, py+ph-rad+math.sin(a)*rad)
            d -= arc
            if d < sh:  return (px, py+ph-rad-d)
            d -= sh
            a = (d/arc)*(math.pi/2)+math.pi; return (px+rad+math.cos(a)*rad, py+rad+math.sin(a)*rad)

        for i in range(50):
            p     = get_pt(self.light_pos - i)
            alpha = int(255 * (1 - i/50))
            glow  = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*PINK_GLOW, alpha // 6), (5, 5), 5)
            surface.blit(glow, (p[0]-5, p[1]-5))
            pygame.draw.circle(surface, PINK, p, 1)

    def draw(self, surface):
        self.ticks     += 1
        self.light_pos  = (self.light_pos + 8) % 2000

        if self.bg:
            surface.blit(pygame.transform.scale(self.bg, (self.W, self.H)), (0, 0))
        else:
            surface.fill(DARK_BG)

        # Bot — centered horizontally, vertically ~48% of design height
        shake_x = math.sin(self.ticks * 0.6) * 1.5
        shake_y = math.cos(self.ticks * 0.5) * 1.5
        angle   = math.sin(self.ticks * 0.1) * 2

        if self.bot_img:
            rotated  = pygame.transform.rotate(self.bot_img, angle)
            bot_rect = rotated.get_rect(
                center=(int(self.W * 0.5 + shake_x), int(self.H * 0.48 + shake_y)))
            surface.blit(rotated, bot_rect)

            pulse_color = PINK if (self.ticks // 20) % 2 == 0 else NEON_CYAN
            for tx, ty in [(-56, -170), (56, -170)]:
                ra  = math.radians(-angle)
                rx  = tx*math.cos(ra) - ty*math.sin(ra)
                ry  = tx*math.sin(ra) + ty*math.cos(ra)
                tpos= (bot_rect.centerx + rx, bot_rect.centery + ry)
                gs  = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(gs, (*pulse_color, 70), (30, 30), 25)
                if (self.ticks // 10) % 2 == 0:
                    pygame.draw.circle(gs, (255, 255, 255, 200), (30, 30), 8)
                surface.blit(gs, (tpos[0]-30, tpos[1]-30))

        m_pos = design_mouse_pos()
        if self.back_hb.collidepoint(m_pos): self._draw_hover_light(surface, self.back_hb)
        if self.play_hb.collidepoint(m_pos): self._draw_hover_light(surface, self.play_hb)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_hb.collidepoint(event.pos): 
                if self.button_sound: self.button_sound.play()
                return "menu"
            if self.play_hb.collidepoint(event.pos): 
                if self.button_sound: self.button_sound.play()
                return "nickname"
        return None

# ── NICKNAME SCENE ────────────────────────────────────────────────────────
class NicknameScene:
    W, H = DESIGN_W, DESIGN_H

    def __init__(self, button_sound=None):
        self.button_sound = button_sound
        self.current_nickname = ""
        self.players  = []
        self.ticks    = 0

        self.bg = None
        if asset_image_path("nickname_bg_new.png").exists():
            self.bg = pygame.image.load(asset_image_path("nickname_bg_new.png")).convert()

        self.holder_img = None
        if asset_image_path("nickname_holder.png").exists():
            self.holder_img = pygame.image.load(asset_image_path("nickname_holder.png")).convert_alpha()

        self.img_add_normal  = self._load_btn("add_player_normal.png",  (380, 100))
        self.img_add_pressed = self._load_btn("add_player_pressed.png", (380, 100))
        self.img_back_normal = self._load_btn("back_normal.png",  (150, 85))
        self.img_back_pressed= self._load_btn("back_pressed.png", (150, 85))
        self.img_done_normal = self._load_btn("done_normal.png",  (150, 85))
        self.img_done_pressed= self._load_btn("done_pressed.png", (150, 85))

        # Figma positions (design space):
        # Back  ≈ (205, 630)  → 15% W, 82% H
        # Done  ≈ (1161, 630) → 85% W, 82% H
        # Add   ≈ (683, 600)  → 50% W, 78% H
        self.back_hb = pygame.Rect(0, 0, 150,  85); self.back_hb.center = (int(self.W * 0.15), int(self.H * 0.82))
        self.done_hb = pygame.Rect(0, 0, 150,  85); self.done_hb.center = (int(self.W * 0.85), int(self.H * 0.82))
        self.add_hb  = pygame.Rect(0, 0, 380, 100); self.add_hb.center  = (int(self.W * 0.50), int(self.H * 0.78))

        self.pressing_add = self.pressing_back = self.pressing_done = False

    def _load_btn(self, path, size):
        if asset_image_path(path).exists():
            return pygame.transform.smoothscale(
                pygame.image.load(asset_image_path(path)).convert_alpha(), size)
        s = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(s, PINK, (0, 0, size[0], size[1]), border_radius=size[1]//2)
        return s

    def _draw_static_glow(self, surface, rect):
        rad = rect.height // 2
        for i in range(5):
            gs = pygame.Surface((rect.width+20, rect.height+20), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*PINK_GLOW, 100-(i*20)),
                (10-i, 10-i, rect.width+i*2, rect.height+i*2),
                width=2+(i*2), border_radius=rad+i)
            surface.blit(gs, (rect.x-10, rect.y-10))

    def draw(self, surface):
        self.ticks += 1

        if self.bg:
            surface.blit(pygame.transform.scale(self.bg, (self.W, self.H)), (0, 0))
        else:
            surface.fill(DARK_BG)

        # Input holder — Figma: ~683×369 center (50%, 48%)
        if self.holder_img:
            ih      = pygame.transform.smoothscale(self.holder_img, (600, 110))
            ih_rect = ih.get_rect(center=(self.W//2, int(self.H * 0.48)))
            surface.blit(ih, ih_rect)

            cursor = "|" if (self.ticks // 30) % 2 == 0 else ""
            txt = pygame.font.SysFont("georgia", 50).render(
                self.current_nickname + cursor, True, WHITE)
            surface.blit(txt, txt.get_rect(center=ih_rect.center))

            # Player name chips — up to 6 players, shown in 2 rows of 3
            if self.players:
                item_w, item_h = 140, 45
                gap     = 15
                per_row = 3
                for i, name in enumerate(self.players):
                    row     = i // per_row
                    col     = i %  per_row
                    row_count = min(per_row, len(self.players) - row * per_row)
                    total_w = row_count * item_w + (row_count - 1) * gap
                    start_x = (self.W - total_w) // 2
                    chip = pygame.transform.smoothscale(self.holder_img, (item_w, item_h))
                    cr   = chip.get_rect(
                        topleft=(start_x + col*(item_w+gap),
                                 int(self.H * 0.60) + row * (item_h + 10)))
                    surface.blit(chip, cr)
                    nt = pygame.font.SysFont("georgia", 18).render(name, True, WHITE)
                    surface.blit(nt, nt.get_rect(center=cr.center))

        # Buttons
        surface.blit(self.img_back_pressed if self.pressing_back else self.img_back_normal, self.back_hb)
        surface.blit(self.img_add_pressed  if self.pressing_add  else self.img_add_normal,  self.add_hb)
        surface.blit(self.img_done_pressed if self.pressing_done else self.img_done_normal, self.done_hb)

        m_pos = design_mouse_pos()
        for hb in [self.back_hb, self.add_hb, self.done_hb]:
            if hb.collidepoint(m_pos):
                self._draw_static_glow(surface, hb)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_hb.collidepoint(event.pos): self.pressing_back = True
            if self.add_hb.collidepoint(event.pos):  self.pressing_add  = True
            if self.done_hb.collidepoint(event.pos): self.pressing_done = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressing_back and self.back_hb.collidepoint(event.pos):
                self.pressing_back = False
                if self.button_sound: self.button_sound.play()
                return "selection"
            if self.pressing_done and self.done_hb.collidepoint(event.pos):
                if len(self.players) >= 3:
                    self.pressing_done = False
                    if self.button_sound: self.button_sound.play()
                    return ("ready", self.players)
            if self.pressing_add and self.add_hb.collidepoint(event.pos):
                if self.current_nickname and len(self.players) < 6:
                    self.players.append(self.current_nickname)
                    self.current_nickname = ""
                    if self.button_sound: self.button_sound.play()
            self.pressing_back = self.pressing_add = self.pressing_done = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.current_nickname = self.current_nickname[:-1]
            elif event.key == pygame.K_RETURN:
                if self.current_nickname and len(self.players) < 6:
                    self.players.append(self.current_nickname)
                    self.current_nickname = ""
            elif (len(self.current_nickname) < 12 and
                  (event.unicode.isalnum() or event.unicode == " ")):
                self.current_nickname += event.unicode.upper()
        return None

# ── READY SCENE ──────────────────────────────────────────────────────────
class ReadyScene:
    W, H = DESIGN_W, DESIGN_H

    def __init__(self, players, button_sound=None):
        self.button_sound = button_sound
        self.players = players
        self.bg = None
        if asset_image_path("gold_bg.png").exists():
            self.bg = pygame.image.load(asset_image_path("gold_bg.png")).convert()

    def draw(self, surface):
        if self.bg:
            surface.blit(pygame.transform.scale(self.bg, (self.W, self.H)), (0, 0))
        else:
            surface.fill((184, 129, 67))

        # Player names centered vertically around 50% H
        n     = len(self.players)
        start_y = (self.H // 2) - ((n - 1) * 35)
        for i, name in enumerate(self.players):
            y = start_y + i * 70
            draw_text_pixel(surface, name, 45, PINK_DARK, self.W//2 + 3, y + 3)
            draw_text_pixel(surface, name, 45, WHITE,     self.W//2,     y)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_sound: self.button_sound.play()
            return "voting_results"
        return None

# ── VOTING RESULTS SCENE ──────────────────────────────────────────────────
class VotingResultsScene:
    W, H = DESIGN_W, DESIGN_H

    def __init__(self, button_sound=None):
        self.button_sound = button_sound
        self.bg = None
        if asset_image_path("gold_bg.png").exists():
            self.bg = pygame.image.load(asset_image_path("gold_bg.png")).convert()

    def draw(self, surface):
        if self.bg:
            surface.blit(pygame.transform.scale(self.bg, (self.W, self.H)), (0, 0))
        else:
            surface.fill((184, 129, 67))
        draw_retro_text(surface, "VOTING RESULTS", 60, self.W//2, self.H//2)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_sound: self.button_sound.play()
            return "win"
        return None

# ── END GAME SCENE ────────────────────────────────────────────────────────
class EndGameScene:
    W, H = DESIGN_W, DESIGN_H

    def __init__(self, result, winner_sound, loser_sound, button_sound=None, ai_answer=None):
        self.result = result
        self.winner_sound = winner_sound
        self.loser_sound = loser_sound
        self.button_sound = button_sound
        self.ai_answer = ai_answer
        self.played = False
        self.fade_timer = 0
        if result == "win":
            self.logo_img = self._load_img("image 24.png")
            self.text_img = self._load_img("image 25.png")
        else:
            self.logo_img = self._load_img("image 26.png")
            self.text_img = self._load_img("image 27.png")

        # Scale images to more balanced size
        if self.logo_img:
            self.logo_img = pygame.transform.scale(self.logo_img, (self.logo_img.get_width() // 2, self.logo_img.get_height() // 2))
        if self.text_img:
            self.text_img = pygame.transform.scale(self.text_img, (self.text_img.get_width() // 2, self.text_img.get_height() // 2))

    def _load_img(self, name):
        if asset_image_path(name).exists():
            return pygame.image.load(asset_image_path(name)).convert_alpha()
        return None

    def draw(self, surface):
        if not self.played:
            sound = self.winner_sound if self.result == "win" else self.loser_sound
            if sound: sound.play()
            self.played = True
        if self.result == "win":
            top, bot = (242, 228, 151), (169, 125, 63)
        else:
            top, bot = (137, 113, 197), (62, 58, 68)
        for y in range(self.H):
            t = y / max(self.H - 1, 1)
            color = (
                int(top[0] + (bot[0] - top[0]) * t),
                int(top[1] + (bot[1] - top[1]) * t),
                int(top[2] + (bot[2] - top[2]) * t),
            )
            pygame.draw.line(surface, color, (0, y), (self.W, y))

        self.fade_timer += 1
        alpha = min(255, self.fade_timer * 10)  # Fade in over ~0.4 seconds at 60fps

        if self.logo_img:
            logo_surf = self.logo_img.copy()
            logo_surf.set_alpha(alpha)
            logo_r = self.logo_img.get_rect(center=(self.W // 2, self.H // 2 - 120))
            surface.blit(logo_surf, logo_r)
        if self.text_img:
            text_surf = self.text_img.copy()
            text_surf.set_alpha(alpha)
            text_r = self.text_img.get_rect(center=(self.W // 2, self.H // 2 + 180))
            surface.blit(text_surf, text_r)

        if self.ai_answer:
            label = "AI-generated choice:"
            draw_text_pixel(surface, label, 25, WHITE, self.W // 2, int(self.H * 0.82))
            draw_text_wrapped(
                surface,
                self.ai_answer,
                22,
                WHITE,
                self.W // 2,
                int(self.H * 0.86),
                self.W - 120,
            )

        if not self.logo_img and not self.text_img:
            label = "YOU WIN" if self.result == "win" else "YOU LOSE"
            draw_retro_text(surface, label, 55, self.W // 2, self.H // 2)

        draw_text_pixel(surface, "CLICK ANYWHERE TO CONTINUE",
                        15, WHITE, self.W // 2, int(self.H * 0.95))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_sound: self.button_sound.play()
            return "loss" if self.result == "win" else "menu"
        return None

# ── MENU SCENE ────────────────────────────────────────────────────────────
class MenuScene:
    W, H = DESIGN_W, DESIGN_H

    def __init__(self, button_sound=None):
        self.button_sound = button_sound
        # Sized to match the large 3D START button drawn in menu_bg.png
        # Button spans roughly 220 × 90 px at design resolution 1366x768
        self.btn_w, self.btn_h = 220, 90
        # Center: horizontally ~49% W, vertically ~93% H (sitting on desk surface)
        self.rect = pygame.Rect(0, 0, self.btn_w, self.btn_h)
        self.rect.center = (int(self.W * 0.485), int(self.H * 0.900))

        self.bg = None
        if asset_image_path("menu_bg.png").exists():
            self.bg = pygame.image.load(asset_image_path("menu_bg.png")).convert()

        self.img_normal  = self._load_img("start_normal.png")
        self.img_pressed = self._load_img("start_pressed.png")
        self.img_hover   = self.img_normal.copy()
        self.img_hover.fill((30, 30, 30), special_flags=pygame.BLEND_RGB_ADD)

        self.pressing         = False
        self.show_mechanics   = False
        self.has_viewed_rules = False

        # Modal centered in design canvas
        self.modal_rect = pygame.Rect(
            self.W//2 - 350, self.H//2 - 260, 700, 520)

    def _load_img(self, name):
        if not asset_image_path(name).exists():
            s = pygame.Surface((self.btn_w, self.btn_h)); s.fill(PINK); return s
        raw = pygame.image.load(asset_image_path(name)).convert_alpha()
        return pygame.transform.smoothscale(raw, (self.btn_w, self.btn_h))

    def handle_event(self, event):
        m_pos   = design_mouse_pos()
        hovered = self.rect.collidepoint(m_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if (self.show_mechanics
                    and not self.modal_rect.collidepoint(event.pos)
                    and not hovered):
                self.show_mechanics = False
            if hovered:
                self.pressing = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressing and hovered:
                if not self.show_mechanics:
                    if not self.has_viewed_rules:
                        self.show_mechanics = True
                        self.has_viewed_rules = True
                    else:
                        self.pressing = False
                        if self.button_sound: self.button_sound.play()
                        return "selection"
                else:
                    self.pressing = False
                    if self.button_sound: self.button_sound.play()
                    return "selection"
            self.pressing = False
        return None

    def draw(self, surface):
        if self.bg:
            surface.blit(pygame.transform.scale(self.bg, (self.W, self.H)), (0, 0))
        else:
            surface.fill(DARK_BG)

        m_pos = design_mouse_pos()
        if self.pressing:
            r = self.img_pressed.get_rect(center=self.rect.center); r.y += 10
            surface.blit(self.img_pressed, r)
        elif self.rect.collidepoint(m_pos):
            surface.blit(self.img_hover, self.rect)
        else:
            surface.blit(self.img_normal, self.rect)

        if self.show_mechanics:
            self._draw_mechanics(surface)

    def _draw_mechanics(self, surface):
        pw, ph = 700, 520
        px, py = self.modal_rect.x, self.modal_rect.y
        rad    = 70

        dim = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160)); surface.blit(dim, (0, 0))

        box_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        for y in range(ph):
            t  = y / ph
            r  = int(GRADIENT_TOP[0] + (GRADIENT_BOT[0]-GRADIENT_TOP[0])*t)
            gv = int(GRADIENT_TOP[1] + (GRADIENT_BOT[1]-GRADIENT_TOP[1])*t)
            b  = int(GRADIENT_TOP[2] + (GRADIENT_BOT[2]-GRADIENT_TOP[2])*t)
            pygame.draw.line(box_surf, (r, gv, b, 255), (0, y), (pw, y))

        mask = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, pw, ph), border_radius=rad)
        box_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(box_surf, (px, py))
        pygame.draw.rect(surface, PINK, (px, py, pw, ph), width=3, border_radius=rad)

        draw_retro_text(surface, "GAME MECHANICS", 45, self.W//2, py+60)

        lines = [
            "3-6 PLAYERS JOIN THE GAME",
            "EACH PLAYER ANSWERS ONE QUESTION (MIN 10 WORDS)",
            "ONE AI-GENERATED ANSWER IS ADDED SECRETLY",
            "PLAYERS CANNOT TALK OR SHARE ANSWERS",
            "ALL ANSWERS ARE SHUFFLED AND SHOWN ANONYMOUSLY",
            "PLAYERS TAKE TURNS VOTING WHICH ANSWER IS AI",
            "AFTER VOTING, VOTES ARE COUNTED",
            "",
            "WINNING CONDITION:",
            "PLAYERS WIN IF THEY SPOT THE AI",
            "AI WINS IF PLAYERS FAIL TO IDENTIFY IT",
        ]
        for i, line in enumerate(lines):
            color = PINK_GLOW if "CONDITION" in line else WHITE
            draw_text_pixel(surface, line, 14, color, self.W//2, py + 130 + i*28)

        draw_text_pixel(surface, "CLICK OUTSIDE TO CLOSE  |  CLICK START IF READY",
                        12, (200, 180, 220), self.W//2, py+ph-30)

# ── MAIN LOOP ──────────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.mixer.init()

    # Load sounds
    try:
        button_sound = pygame.mixer.Sound(asset_sound_path("button_sound.MP3"))
        if button_sound: button_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load button sound: {e}")
        button_sound = None
    try:
        winner_sound = pygame.mixer.Sound(asset_sound_path("winner_soudn.mp3"))
        if winner_sound: winner_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load winner sound: {e}")
        winner_sound = None
    try:
        loser_sound = pygame.mixer.Sound(asset_sound_path("loser_sound.mp3"))
        if loser_sound: loser_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load loser sound: {e}")
        loser_sound = None
    try:
        pygame.mixer.music.load(asset_sound_path("bgmusic.mp3"))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Failed to load background music: {e}")
    # pygame.SCALED stretches the fixed-resolution canvas to fill any monitor
    # while preserving aspect ratio and keeping all coordinate math in design space.
    screen = pygame.display.set_mode(
        (DESIGN_W, DESIGN_H),
        pygame.FULLSCREEN | pygame.SCALED
    )
    pygame.display.set_caption("\"AI\"mong Us")
    clock = pygame.time.Clock()
    
    # ── TITLE BAR AUTO-HIDE ───────────────────────────────────────────────
    hide_title_bar()  # Start with hidden title bar
    title_bar_active = 0.0  # Smooth animation value 0.0 to 1.0
    title_bar_target = 0.0
    title_bar_hide_delay = 0.0

    state   = "bounce"
    bounce  = BounceScene(screen)
    menu    = select = nick = ready = results = endgame = None
    flash_alpha = 0

    while True:
        clock.tick(60)
        
        # ── AUTO-HIDE TITLE BAR: Check mouse position with smooth animation ───
        mouse_y = pygame.mouse.get_pos()[1]
        title_bar_threshold = 30  # Show title bar if mouse is within 30px of top
        
        # Smooth transition to target state
        if mouse_y < title_bar_threshold:
            # Mouse near top: animate title bar in
            title_bar_target = 1.0
            title_bar_hide_delay = 0.0  # Reset hide delay
        else:
            # Mouse away: schedule smooth hide after delay
            title_bar_hide_delay += 1.0 / 60.0  # Convert to seconds
            if title_bar_hide_delay > 0.8:  # Hide after 0.8 seconds
                title_bar_target = 0.0
        
        # Smooth animation using easing
        easing_speed = 0.15  # Smooth transition speed
        title_bar_active += (title_bar_target - title_bar_active) * easing_speed
        
        # Apply title bar changes with threshold
        if title_bar_active > 0.1 and title_bar_active < 1.0:
            show_title_bar()  # Gradually showing
        elif title_bar_active >= 1.0:
            show_title_bar()  # Fully shown
        elif title_bar_active <= 0.1:
            hide_title_bar()  # Fully hidden

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

            # ── State event routing ──────────────────────────────────────
            if state == "menu" and menu:
                res = menu.handle_event(event)
                if res == "selection":
                    flash_alpha = 255; state = "selection"; select = SelectionScene(button_sound)
                    button_sound.play()

            elif state == "selection" and select:
                res = select.handle_event(event)
                if res == "menu":
                    state = "menu"; menu = MenuScene(button_sound)
                elif res == "nickname":
                    state = "nickname"; nick = NicknameScene(button_sound); flash_alpha = 255

            elif state == "nickname" and nick:
                res = nick.handle_event(event)
                if res == "selection":
                    state = "selection"; select = SelectionScene(button_sound)
                elif isinstance(res, tuple) and res[0] == "ready":
                    state = "ready"; ready = ReadyScene(res[1], button_sound); flash_alpha = 255

            elif state == "ready" and ready:
                res = ready.handle_event(event)
                if res == "voting_results":
                    state = "results"; results = VotingResultsScene(button_sound); flash_alpha = 255

            elif state == "results" and results:
                res = results.handle_event(event)
                if res == "win":
                    state = "end"; endgame = EndGameScene("win", winner_sound, loser_sound, button_sound); flash_alpha = 255

            elif state == "end" and endgame:
                res = endgame.handle_event(event)
                if res == "loss":
                    state = "end"; endgame = EndGameScene("loss", winner_sound, loser_sound, button_sound); flash_alpha = 255
                elif res == "menu":
                    state = "menu"; menu = MenuScene(button_sound); flash_alpha = 255

        # ── Drawing ───────────────────────────────────────────────────────
        if state == "bounce":
            bounce.update()
            bounce.draw_scene(screen)
            if bounce.done:
                state = "menu"; menu = MenuScene(button_sound)
        elif state == "menu":     menu.draw(screen)
        elif state == "selection": select.draw(screen)
        elif state == "nickname":  nick.draw(screen)
        elif state == "ready":     ready.draw(screen)
        elif state == "results":   results.draw(screen)
        elif state == "end":       endgame.draw(screen)

        # Flash transition overlay
        if flash_alpha > 0:
            f = pygame.Surface((DESIGN_W, DESIGN_H))
            f.fill(NEON_CYAN); f.set_alpha(flash_alpha)
            screen.blit(f, (0, 0))
            flash_alpha -= 15

        pygame.display.flip()

if __name__ == "__main__":
    main()