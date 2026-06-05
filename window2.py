import os
import pygame
import sys

pygame.init()
pygame.mixer.init()

# Load sounds
try:
    button_sound = pygame.mixer.Sound(os.path.join(ASSETS_SOUNDS, "button_sound.MP3"))
    if button_sound: button_sound.set_volume(1.0)
except Exception as e:
    print(f"Failed to load button sound: {e}")
    button_sound = None
try:
    voting_sound = pygame.mixer.Sound(os.path.join(ASSETS_SOUNDS, "voting_sound.mp3"))
    if voting_sound: voting_sound.set_volume(1.0)
except Exception as e:
    print(f"Failed to load voting sound: {e}")
    voting_sound = None
try:
    winner_sound = pygame.mixer.Sound(os.path.join(ASSETS_SOUNDS, "winner_soudn.mp3"))
    if winner_sound: winner_sound.set_volume(1.0)
except Exception as e:
    print(f"Failed to load winner sound: {e}")
    winner_sound = None
try:
    loser_sound = pygame.mixer.Sound(os.path.join(ASSETS_SOUNDS, "loser_sound.mp3"))
    if loser_sound: loser_sound.set_volume(1.0)
except Exception as e:
    print(f"Failed to load loser sound: {e}")
    loser_sound = None
try:
    pygame.mixer.music.load(os.path.join(ASSETS_SOUNDS, "bgmusic.mp3"))
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except Exception as e:
    print(f"Failed to load background music: {e}")

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

# -- Settings --
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60

BASE_DIR              = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR            = os.path.join(BASE_DIR, "assets")
ASSETS_IMAGES         = os.path.join(ASSETS_DIR, "images")
ASSETS_SOUNDS         = os.path.join(ASSETS_DIR, "sounds")
ASSETS_FONTS          = os.path.join(ASSETS_DIR, "fonts")
BACKGROUND_IMAGE_PATH = os.path.join(ASSETS_IMAGES, "Gemini_Generated_Image_9krgy89krgy89krg 2.png")

FONT_FILE = "EBGaramond-VariableFont_wght.ttf"
FONT_PATH = os.path.join(ASSETS_FONTS, FONT_FILE)

PLAYERS = ["Denni", "Zy", "Russel", "Aldrin", "Sam"]

# -- States --
STATE_COLLECTING   = 0
STATE_VOTING       = 1
STATE_RESULTS      = 2 
STATE_PLAYER_WINS  = 3 
STATE_AI_WINS      = 4 

# -- Fade Logic --
fade_alpha = 0
fade_speed = 5  
is_fading = False
next_state = None

# -- Layout Constants --
RECT_WIDTH, RECT_TOP_Y = 831, 60
SHARP_RADIUS = 10 
BANNER_HEIGHT = 38
HOVER_SPEED = 5 

RECT_HEIGHT_IN = 180
RECT2_HEIGHT_IN = 260
RECT1_HEIGHT_VOTE = 100
ROW_GAP           = 12

# -- BUTTON SPACING --
BUTTON_MARGIN = 10 

# -- Colors --
BORDER_COLOR = (240, 120, 160)
RECT1_COLOR_L, RECT1_COLOR_R = (186, 34, 111), (63, 21, 54)
RECT2_COLOR_T, RECT2_COLOR_B = (240, 120, 160), (137, 113, 197)
TRAPEZOID_L, TRAPEZOID_R = (186, 42, 146), (63, 21, 54)
BTN_L, BTN_R = (124, 72, 169), (71, 50, 63)
BTN_HOVER_T, BTN_HOVER_B = (186, 34, 111), (63, 21, 54)
TEXT_WHITE = (255, 255, 255)
GOLD_LIGHT, GOLD_DARK = (242, 228, 151), (169, 125, 63)

# --- DISPLAY SETUP ---
# Fullscreen scaling active
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)

# SET WINDOW NAME
pygame.display.set_caption("\"AI\"mong Us")

# SET WINDOW ICON
ICON_FILENAME = "Property 1=Default.png" 
icon_full_path = os.path.join(ASSETS_IMAGES, ICON_FILENAME)
if os.path.exists(icon_full_path):
    pygame.display.set_icon(pygame.image.load(icon_full_path))

clock = pygame.time.Clock()

# --- FONT LOADING ---
if os.path.exists(FONT_PATH):
    font_body = pygame.font.Font(FONT_PATH, 32)
    font_results = pygame.font.Font(FONT_PATH, 110) 
else:
    font_body = pygame.font.SysFont("georgia", 32)
    font_results = pygame.font.SysFont("georgia", 110)

# --- IMAGE LOADING ---
def load_img(name):
    p = os.path.join(ASSETS_IMAGES, name)
    return pygame.image.load(p).convert_alpha() if os.path.exists(p) else pygame.Surface((10,10))

img_next = load_img("image 22.png")
img_done = load_img("image 15.png")
img_win_logo = load_img("image 24.png")
img_win_text = load_img("image 25.png")
img_ai_win_logo = load_img("image 26.png")
img_ai_win_text = load_img("image 27.png")

BTN1_WIDTH, BTN1_HEIGHT = img_next.get_width() + 60, img_next.get_height() + 40
BTN2_WIDTH, BTN2_HEIGHT = img_done.get_width() + 30, img_done.get_height() + 20

# --- HELPERS ---
def get_wrapped_lines(text, font, max_width):
    words = text.split(' ')
    lines, current_line = [], ""
    for word in words:
        if font.size(current_line + word)[0] < max_width - 40:
            current_line += word + " "
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)
    return lines

def draw_text_wrapped(surface, text, font, color, rect):
    lines = get_wrapped_lines(text, font, rect.width)
    line_height = font.get_linesize()
    total_height = len(lines) * line_height
    start_y = rect.centery - (total_height // 2)
    for i, line in enumerate(lines):
        txt_surf = font.render(line.strip(), True, color)
        txt_rect = txt_surf.get_rect(center=(rect.centerx, start_y + (i * line_height) + (line_height // 2)))
        surface.blit(txt_surf, txt_rect)

def lerp_color(c1, c2, t): return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def draw_gradient_rect(surface, rect, col_t, col_b):
    for y in range(rect.height):
        t = y / max(rect.height - 1, 1)
        color = lerp_color(col_t, col_b, t)
        pygame.draw.line(surface, color, (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))

def draw_sharp_gradient_rect(surf_target, x, y, w, h, rad, col_a, col_b, horizontal=True):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    n = w if horizontal else h
    for i in range(n):
        t = i / max(n - 1, 1)
        color = lerp_color(col_a, col_b, t)
        if horizontal: pygame.draw.line(surf, (*color, 200), (i, 0), (i, h))
        else: pygame.draw.line(surf, (*color, 200), (0, i), (w, i))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255), (0, 0, w, h), border_radius=rad)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf_target.blit(surf, (x, y))
    pygame.draw.rect(surf_target, BORDER_COLOR, (x, y, w, h), 3, border_radius=rad)

def draw_banner(surface, name):
    cx, ty = SCREEN_WIDTH // 2, RECT_TOP_Y - (BANNER_HEIGHT // 2)
    pts = [(cx-110, ty), (cx+110, ty), (cx+141, ty+38), (cx-141, ty+38)]
    grad_surf = pygame.Surface((282, 38), pygame.SRCALPHA)
    for x in range(282):
        color = lerp_color(TRAPEZOID_L, TRAPEZOID_R, x/281)
        pygame.draw.line(grad_surf, color, (x, 0), (x, 38))
    mask = pygame.Surface((282, 38), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255,255,255), [(31,0), (251,0), (282,38), (0,38)])
    grad_surf.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(grad_surf, (cx-141, ty))
    pygame.draw.polygon(surface, BORDER_COLOR, pts, 2)
    txt = font_body.render(name, True, TEXT_WHITE)
    surface.blit(txt, txt.get_rect(center=(cx, ty + 19)))

def draw_pill_btn(surface, cx, top, w, h, img, hover_t):
    rect = pygame.Rect(cx - w//2, top, w, h)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        ty = y / max(h - 1, 1)
        color = lerp_color(lerp_color(BTN_L, BTN_R, ty), lerp_color(BTN_HOVER_T, BTN_HOVER_B, ty), hover_t)
        pygame.draw.line(surf, (*color, 255), (0, y), (w, y))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255,255,255), (0, 0, w, h), border_radius=h//2)
    surf.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(surf, rect.topleft)
    pygame.draw.rect(surface, BORDER_COLOR, rect, 3, border_radius=h//2)
    surface.blit(img, img.get_rect(center=rect.center))
    return rect

# --- MAIN LOOP ---
def main():
    global fade_alpha, is_fading, next_state
    
    # ── TITLE BAR AUTO-HIDE ───────────────────────────────────────────────
    hide_title_bar()  # Start with hidden title bar
    title_bar_active = 0.0  # Smooth animation value 0.0 to 1.0
    title_bar_target = 0.0
    title_bar_hide_delay = 0.0
    
    state, current_p_idx, typed_text = STATE_COLLECTING, 0, ""
    all_answers, hover_vals = [], [0.0, 0.0]
    ans_hover_vals = []
    selected_ans_idx = None
    scroll_y = 0

    bg = pygame.transform.smoothscale(pygame.image.load(BACKGROUND_IMAGE_PATH).convert(), (1280, 720)) if os.path.exists(BACKGROUND_IMAGE_PATH) else None
    fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surf.fill((0, 0, 0))

    while True:
        dt = clock.tick(FPS) / 1000.0
        mx, my = pygame.mouse.get_pos()
        cx, lx = SCREEN_WIDTH // 2, (SCREEN_WIDTH - RECT_WIDTH) // 2
        
        # ── AUTO-HIDE TITLE BAR: Check mouse position with smooth animation ──
        mouse_y = my
        title_bar_threshold = 30  # Show title bar if mouse is within 30px of top
        
        # Smooth transition to target state
        if mouse_y < title_bar_threshold:
            # Mouse near top: animate title bar in
            title_bar_target = 1.0
            title_bar_hide_delay = 0.0  # Reset hide delay
        else:
            # Mouse away: schedule smooth hide after delay
            title_bar_hide_delay += dt
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
        
        if state in [STATE_RESULTS, STATE_PLAYER_WINS, STATE_AI_WINS]:
            draw_gradient_rect(screen, screen.get_rect(), GOLD_LIGHT, GOLD_DARK)
        elif bg: screen.blit(bg, (0,0))
        else: screen.fill((62, 58, 68))

        word_count = len([w for w in typed_text.split() if w.strip()])
        can_proceed = (10 <= word_count <= 20) if state == STATE_COLLECTING else (selected_ans_idx is not None)
        btn1_rect, btn2_rect = pygame.Rect(0,0,0,0), pygame.Rect(0,0,0,0)
        voting_rects = []

        if state == STATE_COLLECTING:
            r1 = pygame.Rect(lx, RECT_TOP_Y, RECT_WIDTH, RECT_HEIGHT_IN)
            draw_sharp_gradient_rect(screen, r1.x, r1.y, r1.width, r1.height, SHARP_RADIUS, RECT1_COLOR_L, RECT1_COLOR_R)
            r2 = pygame.Rect(lx, r1.bottom + 15, RECT_WIDTH, RECT2_HEIGHT_IN)
            draw_sharp_gradient_rect(screen, r2.x, r2.y, r2.width, r2.height, SHARP_RADIUS, RECT2_COLOR_T, RECT2_COLOR_B, False)
            draw_text_wrapped(screen, "What is the ememememememememe?", font_body, TEXT_WHITE, r1)
            draw_text_wrapped(screen, typed_text + "|", font_body, (0,0,0), r2)
            b_y = r2.bottom + 20
        
        elif state == STATE_VOTING:
            content_h = 2000
            scroll_surf = pygame.Surface((SCREEN_WIDTH, content_h), pygame.SRCALPHA)
            
            rv = pygame.Rect(lx, RECT_TOP_Y, RECT_WIDTH, RECT1_HEIGHT_VOTE)
            draw_sharp_gradient_rect(scroll_surf, rv.x, rv.y, rv.width, rv.height, SHARP_RADIUS, RECT1_COLOR_L, RECT1_COLOR_R)
            title = font_body.render("Which answer is the impostor?", True, TEXT_WHITE)
            scroll_surf.blit(title, title.get_rect(center=rv.center))
            
            curr_y = rv.bottom + 15
            while len(ans_hover_vals) < len(all_answers): ans_hover_vals.append(0.0)

            for i, ans in enumerate(all_answers):
                dyn_h = max(70, len(get_wrapped_lines(ans, font_body, RECT_WIDTH)) * font_body.get_linesize() + 20)
                row_r = pygame.Rect(lx, curr_y, RECT_WIDTH, dyn_h)
                collision_r = pygame.Rect(lx, curr_y - scroll_y, RECT_WIDTH, dyn_h)
                voting_rects.append(collision_r)
                
                is_selected = (selected_ans_idx == i)
                targ = 1.0 if (collision_r.collidepoint(mx, my) or is_selected) else 0.0
                ans_hover_vals[i] += (targ - ans_hover_vals[i]) * min(HOVER_SPEED * dt, 1)
                
                c1 = lerp_color(RECT2_COLOR_T, BTN_HOVER_T, ans_hover_vals[i])
                c2 = lerp_color(RECT2_COLOR_B, BTN_HOVER_B, ans_hover_vals[i])
                
                draw_sharp_gradient_rect(scroll_surf, row_r.x, row_r.y, row_r.width, row_r.height, SHARP_RADIUS, c1, c2, False)
                draw_text_wrapped(scroll_surf, ans, font_body, (0,0,0), row_r)
                curr_y += dyn_h + ROW_GAP
            
            b_y_virt = curr_y + 20
            is_last = (current_p_idx == len(PLAYERS) - 1)
            
            btn1_rect_virt = draw_pill_btn(scroll_surf, cx, b_y_virt, BTN1_WIDTH, BTN1_HEIGHT, img_next, hover_vals[0])
            btn2_rect_virt = draw_pill_btn(scroll_surf, cx, b_y_virt + BTN1_HEIGHT + BUTTON_MARGIN, BTN2_WIDTH, BTN2_HEIGHT, img_done, hover_vals[1])
            
            btn1_rect = pygame.Rect(btn1_rect_virt.x, btn1_rect_virt.y - scroll_y, btn1_rect_virt.w, btn1_rect_virt.h)
            btn2_rect = pygame.Rect(btn2_rect_virt.x, btn2_rect_virt.y - scroll_y, btn2_rect_virt.w, btn2_rect_virt.h)

            screen.blit(scroll_surf, (0, -scroll_y))
            max_scroll = max(0, btn2_rect_virt.bottom + 50 - SCREEN_HEIGHT)
            scroll_y = max(0, min(scroll_y, max_scroll))

        elif state == STATE_PLAYER_WINS:
            logo_r = img_win_logo.get_rect(center=(cx, SCREEN_HEIGHT // 2 - 120))
            text_r = img_win_text.get_rect(center=(cx, SCREEN_HEIGHT // 2 + 180))
            screen.blit(img_win_logo, logo_r); screen.blit(img_win_text, text_r)
        elif state == STATE_AI_WINS:
            ai_logo_r = img_ai_win_logo.get_rect(center=(cx, SCREEN_HEIGHT // 2 - 120))
            ai_text_r = img_ai_win_text.get_rect(center=(cx, SCREEN_HEIGHT // 2 + 180))
            screen.blit(img_ai_win_logo, ai_logo_r); screen.blit(img_ai_win_text, ai_text_r)
        elif state == STATE_RESULTS:
            txt = font_results.render("VOTING RESULTS", True, TEXT_WHITE)
            screen.blit(txt, txt.get_rect(center=(cx, SCREEN_HEIGHT // 2)))

        if state in [STATE_COLLECTING, STATE_VOTING]:
            is_last = (current_p_idx == len(PLAYERS) - 1)
            if state == STATE_COLLECTING:
                btn1_rect = draw_pill_btn(screen, cx, b_y, BTN1_WIDTH, BTN1_HEIGHT, img_next, hover_vals[0])
                btn2_rect = draw_pill_btn(screen, cx, b_y + BTN1_HEIGHT + BUTTON_MARGIN, BTN2_WIDTH, BTN2_HEIGHT, img_done, hover_vals[1])
            
            for i, r in enumerate([btn1_rect, btn2_rect]):
                hover_vals[i] += ((1.0 if r.collidepoint(mx, my) else 0.0) - hover_vals[i]) * min(HOVER_SPEED * dt, 1)
            draw_banner(screen, PLAYERS[current_p_idx])

        if is_fading:
            fade_alpha += fade_speed
            if fade_alpha >= 255: state, is_fading = next_state, False
        elif fade_alpha > 0: fade_alpha -= fade_speed
        fade_surf.set_alpha(fade_alpha)
        screen.blit(fade_surf, (0,0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            if event.type == pygame.MOUSEWHEEL and state == STATE_VOTING:
                scroll_y -= event.y * 30

            if event.type == pygame.MOUSEBUTTONDOWN and not is_fading:
                if state == STATE_VOTING:
                    for i, r in enumerate(voting_rects):
                        if r.collidepoint(event.pos):
                            selected_ans_idx = i
                
                if state in [STATE_COLLECTING, STATE_VOTING]:
                    if btn1_rect.collidepoint(event.pos):
                        if button_sound: button_sound.play()
                        if not is_last and can_proceed:
                            if state == STATE_COLLECTING: 
                                all_answers.append(typed_text); typed_text = ""; current_p_idx += 1
                            elif state == STATE_VOTING: 
                                selected_ans_idx = None
                                scroll_y = 0
                                current_p_idx += 1
                    elif btn2_rect.collidepoint(event.pos):
                        if button_sound: button_sound.play()
                        if is_last and can_proceed:
                            if state == STATE_COLLECTING: 
                                all_answers.append(typed_text); typed_text = ""; current_p_idx = 0; state = STATE_VOTING
                            elif state == STATE_VOTING: 
                                if voting_sound: voting_sound.play()
                                is_fading, next_state = True, STATE_RESULTS
                
                elif state == STATE_RESULTS: 
                    if winner_sound: winner_sound.play()
                    is_fading, next_state = True, STATE_PLAYER_WINS 
                elif state == STATE_PLAYER_WINS: 
                    if loser_sound: loser_sound.play()
                    is_fading, next_state = True, STATE_AI_WINS

            if event.type == pygame.KEYDOWN:
                # Emergency exit for fullscreen
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                
                if state == STATE_COLLECTING:
                    if event.key == pygame.K_BACKSPACE: typed_text = typed_text[:-1]
                    elif word_count < 20 or (event.unicode != " " and word_count == 20): typed_text += event.unicode
        
        pygame.display.flip()

if __name__ == "__main__":
    main()