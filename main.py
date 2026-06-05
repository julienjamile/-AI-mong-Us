import os
import sys
import multiprocessing
import queue
import threading
import random
import time


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ASSETS_IMAGES = os.path.join(ASSETS_DIR, "images")
ASSETS_SOUNDS = os.path.join(ASSETS_DIR, "sounds")
ASSETS_FONTS = os.path.join(ASSETS_DIR, "fonts")

GEN_AI_API_KEY = ""


def asset_path(*parts):
    return os.path.join(ASSETS_DIR, *parts)


def _assign_player_ids(nicknames):
    ids = list(range(1, len(nicknames) + 1))
    random.shuffle(ids)
    return {pid: nn for pid, nn in zip(ids, nicknames)}


def _patch_gen_ai_api_key(api_module, api_key):
    if not api_key:
        return

    api_module.GEN_AI_API_KEY = api_key


def _msgbox(title, message, kind="error"): 
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    pos = os.environ.get("SDL_VIDEO_WINDOW_POS")
    if pos:
        try:
            x, y = map(int, pos.split(","))
            root.geometry(f"+{x + 50}+{y + 50}")
        except Exception:
            pass
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    root.focus_force()
    if kind == "yesno":
        result = messagebox.askyesno(title, message)
    elif kind == "warning":
        messagebox.showwarning(title, message)
        result = None
    elif kind == "info":
        messagebox.showinfo(title, message)
        result = None
    else:
        messagebox.showerror(title, message)
        result = None
    root.destroy()
    return result


def run_window1(result_queue, w1_to_w2, w2_to_w1, w2_offset):
    os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"

    import pygame
    import sys
    import queue
    import window1 as w1
    try:
        import Back_End as be
    except ModuleNotFoundError as exc:
        if "google" in str(exc):
            _msgbox(
                "Missing Dependency",
                "The google-genai package is not installed. Install it with pip install google-genai and restart.",
                kind="error",
            )
        else:
            _msgbox("Import Error", str(exc), kind="error")
        pygame.quit()
        sys.exit()

    pygame.init()
    pygame.mixer.init()

    # Load sounds
    try:
        button_sound = pygame.mixer.Sound(asset_path("sounds", "button_sound.MP3"))
        if button_sound: button_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load button sound: {e}")
        button_sound = None
    try:
        winner_sound = pygame.mixer.Sound(asset_path("sounds", "winner_soudn.mp3"))
        if winner_sound: winner_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load winner sound: {e}")
        winner_sound = None
    try:
        loser_sound = pygame.mixer.Sound(asset_path("sounds", "loser_sound.mp3"))
        if loser_sound: loser_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load loser sound: {e}")
        loser_sound = None
    try:
        pygame.mixer.music.load(asset_path("sounds", "bgmusic.mp3"))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Failed to load background music: {e}")

    screen = pygame.display.set_mode(
        (w1.DESIGN_W, w1.DESIGN_H),
        pygame.FULLSCREEN | pygame.SCALED,
    )
    pygame.display.set_caption("Bot Game")
    clock = pygame.time.Clock()

    state = "bounce"
    game_ended = False
    turn_order = []
    current_turn_index = 0
    game_result = None
    players_data = []
    question = None

    bounce = w1.BounceScene(screen)
    menu = None
    select = None
    nick = None
    ready = None
    results = None
    endgame = None
    last_result = None
    last_ai_answer = None

    while True:
        clock.tick(60)

        try:
            msg = w2_to_w1.get_nowait()
            event_name = msg.get("event")

            if event_name == "answer_saved":
                current_turn_index += 1

            elif event_name == "voting_phase":
                state = "voting_display"
                current_turn_index = 0

            elif event_name == "vote_cast":
                current_turn_index += 1

            elif event_name == "voting_results":
                game_result = msg["result"]
                result_str = "win" if game_result == "players_win" else "loss"
                last_result = result_str
                last_ai_answer = msg.get("ai_answer")
                result_queue.put(result_str)
                endgame = w1.EndGameScene(result_str, winner_sound, loser_sound, button_sound, ai_answer=last_ai_answer)
                state = "end"

            elif event_name == "game_over":
                game_result = msg["result"]
                result_str = "win" if game_result == "players_win" else "loss"
                last_ai_answer = msg.get("ai_answer")
                endgame = w1.EndGameScene(result_str, winner_sound, loser_sound, button_sound, ai_answer=last_ai_answer)
                state = "end"

            elif event_name == "quit":
                pygame.quit()
                sys.exit()

        except queue.Empty:
            pass

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if state == "menu" and menu:
                res = menu.handle_event(event)
                if res == "selection":
                    state = "selection"
                    select = w1.SelectionScene()

            elif state == "selection" and select:
                res = select.handle_event(event)
                if res == "menu":
                    state = "menu"
                    menu = w1.MenuScene()
                elif res == "nickname":
                    state = "nickname"
                    nick = w1.NicknameScene()
                    w1_to_w2.put({"event": "go_nickname"})

            elif state == "nickname" and nick:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if nick.add_hb.collidepoint(event.pos):
                        nickname = nick.current_nickname.strip()
                        if nickname == "":
                            _msgbox("Invalid Nickname", "Nickname cannot be empty.", kind="error")
                            continue
                        if len(nickname) > 12:
                            _msgbox("Nickname Too Long", "Nickname must be 12 characters or fewer.", kind="error")
                            continue
                        if nickname in nick.players:
                            _msgbox("Duplicate Nickname", "That nickname is already taken. Choose another.", kind="error")
                            continue
                        if len(nick.players) >= 6:
                            _msgbox("Too Many Players", "Maximum 6 players allowed.", kind="error")
                            continue
                    if nick.done_hb.collidepoint(event.pos):
                        if len(nick.players) < 3:
                            _msgbox("Not Enough Players", "You need at least 3 players to start. Add more players.", kind="error")
                            continue
                        if len(nick.players) > 6:
                            _msgbox("Too Many Players", "Maximum 6 players allowed.", kind="error")
                            continue
                res = nick.handle_event(event)
                if isinstance(res, tuple) and res[0] == "ready":
                    nicknames = res[1]
                    id_map = _assign_player_ids(nicknames)
                    question = be.randomizeQuestion(be.questions)
                    player_objs = [be.Player(nickname=nn, id=pid, answer=None) for pid, nn in id_map.items()]
                    be.randomizePlayerOrder(player_objs)
                    turn_order = [p.id for p in player_objs]
                    players_data = [{"id": p.id, "nickname": p.nickname} for p in player_objs]
                    w1_to_w2.put(
                        {
                            "event": "start_collecting",
                            "players": players_data,
                            "question": question,
                            "turn_order": turn_order,
                        }
                    )
                    ready = w1.ReadyScene([p.nickname for p in player_objs])
                    state = "ready"

            elif state == "results" and results:
                res = results.handle_event(event)
                if res == "win":
                    endgame = w1.EndGameScene(last_result if last_result is not None else "loss")
                    state = "end"

            elif state == "end" and endgame:
                res = endgame.handle_event(event)
                if res == "menu":
                    game_ended = True
                    state = "menu"
                    menu = w1.MenuScene(button_sound)
                    ready = None
                    endgame = None

        if game_ended and state == "menu":
            break

        if state == "bounce":
            bounce.update()
            bounce.draw_scene(screen)
            if bounce.done:
                state = "menu"
                menu = w1.MenuScene()

        elif state == "menu" and menu:
            menu.draw(screen)

        elif state == "selection" and select:
            select.draw(screen)

        elif state == "nickname" and nick:
            nick.draw(screen)

        elif state == "ready" and ready:
            ready.draw(screen)
            if turn_order:
                if current_turn_index < len(turn_order):
                    current_id = turn_order[current_turn_index]
                    current_nn = next(p["nickname"] for p in players_data if p["id"] == current_id)
                    w1.draw_retro_text(
                        screen,
                        f"> {current_nn} <",
                        40,
                        w1.DESIGN_W // 2,
                        int(w1.DESIGN_H * 0.85),
                        color=w1.NEON_CYAN,
                    )
                else:
                    w1.draw_retro_text(
                        screen,
                        "Gen AI is thinking...",
                        35,
                        w1.DESIGN_W // 2,
                        int(w1.DESIGN_H * 0.85),
                        color=w1.PINK,
                    )

        elif state == "voting_display":
            bg_img = None
            if os.path.exists(asset_path("images", "gold_bg.png")):
                try:
                    bg_img = pygame.image.load(asset_path("images", "gold_bg.png")).convert()
                except Exception:
                    bg_img = None
            if bg_img:
                screen.blit(pygame.transform.scale(bg_img, (w1.DESIGN_W, w1.DESIGN_H)), (0, 0))
            else:
                screen.fill(w1.DARK_BG)
            w1.draw_retro_text(screen, "VOTING PHASE", 60, w1.DESIGN_W // 2, w1.DESIGN_H // 3)
            if current_turn_index < len(turn_order):
                current_id = turn_order[current_turn_index]
                current_nn = next(p["nickname"] for p in players_data if p["id"] == current_id)
                w1.draw_text_pixel(
                    screen,
                    f"{current_nn}'s turn to vote",
                    30,
                    w1.WHITE,
                    w1.DESIGN_W // 2,
                    int(w1.DESIGN_H * 0.6),
                )
            else:
                w1.draw_text_pixel(
                    screen,
                    "Counting votes...",
                    30,
                    w1.WHITE,
                    w1.DESIGN_W // 2,
                    int(w1.DESIGN_H * 0.6),
                )

        elif state == "results" and results:
            results.draw(screen)

        elif state == "end" and endgame:
            endgame.draw(screen)

        pygame.display.flip()


def run_window2(w1_to_w2, w2_to_w1, w2_offset):
    os.environ["SDL_VIDEO_WINDOW_POS"] = f"{w2_offset[0]},{w2_offset[1]}"

    import pygame
    import sys
    import queue
    import threading
    import window2
    try:
        import Back_End as be
    except ModuleNotFoundError as exc:
        if "google" in str(exc):
            _msgbox(
                "Missing Dependency",
                "The google-genai package is not installed. Install it with pip install google-genai and restart.",
                kind="error",
            )
        else:
            _msgbox("Import Error", str(exc), kind="error")
        pygame.quit()
        sys.exit()
    try:
        import gen_ai
    except ModuleNotFoundError as exc:
        print(f"[DEBUG] gen_ai import failed: {exc}")
        if "google" in str(exc):
            _msgbox(
                "Missing Dependency",
                "The google-genai package is not installed. Install it with pip install google-genai and restart.",
                kind="error",
            )
        else:
            _msgbox("Import Error", str(exc), kind="error")
        pygame.quit()
        sys.exit()
    _patch_gen_ai_api_key(gen_ai, GEN_AI_API_KEY)

    pygame.init()
    pygame.mixer.init()

    # Load sounds
    try:
        button_sound = pygame.mixer.Sound(asset_path("sounds", "button_sound.MP3"))
        if button_sound: button_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load button sound: {e}")
        button_sound = None
    try:
        voting_sound = pygame.mixer.Sound(asset_path("sounds", "voting_sound.mp3"))
        if voting_sound: voting_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load voting sound: {e}")
        voting_sound = None
    try:
        winner_sound = pygame.mixer.Sound(asset_path("sounds", "winner_soudn.mp3"))
        if winner_sound: winner_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load winner sound: {e}")
        winner_sound = None
    try:
        loser_sound = pygame.mixer.Sound(asset_path("sounds", "loser_sound.mp3"))
        if loser_sound: loser_sound.set_volume(1.0)
    except Exception as e:
        print(f"Failed to load loser sound: {e}")
        loser_sound = None
    try:
        pygame.mixer.music.load(asset_path("sounds", "bgmusic.mp3"))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Failed to load background music: {e}")

    STATE_COLLECTING = window2.STATE_COLLECTING
    STATE_VOTING = window2.STATE_VOTING
    STATE_RESULTS = window2.STATE_RESULTS
    STATE_PLAYER_WINS = window2.STATE_PLAYER_WINS
    STATE_GEN_AI_WINS = window2.STATE_GEN_AI_WINS
    SCREEN_WIDTH = window2.SCREEN_WIDTH
    SCREEN_HEIGHT = window2.SCREEN_HEIGHT
    FPS = window2.FPS
    RECT_WIDTH = window2.RECT_WIDTH
    RECT_TOP_Y = window2.RECT_TOP_Y
    SHARP_RADIUS = window2.SHARP_RADIUS
    BANNER_HEIGHT = window2.BANNER_HEIGHT
    HOVER_SPEED = window2.HOVER_SPEED
    RECT_HEIGHT_IN = window2.RECT_HEIGHT_IN
    RECT2_HEIGHT_IN = window2.RECT2_HEIGHT_IN
    RECT1_HEIGHT_VOTE = window2.RECT1_HEIGHT_VOTE
    ROW_GAP = window2.ROW_GAP
    BUTTON_MARGIN = window2.BUTTON_MARGIN
    BORDER_COLOR = window2.BORDER_COLOR
    RECT1_COLOR_L = window2.RECT1_COLOR_L
    RECT1_COLOR_R = window2.RECT1_COLOR_R
    RECT2_COLOR_T = window2.RECT2_COLOR_T
    RECT2_COLOR_B = window2.RECT2_COLOR_B
    TRAPEZOID_L = window2.TRAPEZOID_L
    TRAPEZOID_R = window2.TRAPEZOID_R
    BTN_L = window2.BTN_L
    BTN_R = window2.BTN_R
    BTN_HOVER_T = window2.BTN_HOVER_T
    BTN_HOVER_B = window2.BTN_HOVER_B
    TEXT_WHITE = window2.TEXT_WHITE
    GOLD_LIGHT = window2.GOLD_LIGHT
    GOLD_DARK = window2.GOLD_DARK

    font_body = window2.font_body
    font_results = window2.font_results

    img_next = window2.load_img("image 22.png")
    img_done = window2.load_img("image 15.png")
    img_win_logo = window2.load_img("image 24.png")
    img_win_text = window2.load_img("image 25.png")
    img_ai_win_logo = window2.load_img("image 26.png")
    img_ai_win_text = window2.load_img("image 27.png")

    bg = None
    if os.path.exists(window2.BACKGROUND_IMAGE_PATH):
        try:
            bg = pygame.transform.smoothscale(pygame.image.load(window2.BACKGROUND_IMAGE_PATH).convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            bg = None

    def draw_background():
        if bg:
            screen.blit(bg, (0, 0))
            return
        for y in range(SCREEN_HEIGHT):
            t = y / max(SCREEN_HEIGHT - 1, 1)
            color = window2.lerp_color(window2.GRADIENT_TOP, window2.GRADIENT_BOT, t)
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption('"Gen AI"mong Us - Window 2')
    clock = pygame.time.Clock()

    while True:
        waiting = True
        players_data = []
        question = ""
        turn_order = []

        while waiting:
            draw_background()
            title = font_body.render("Waiting for game to start...", True, (255, 255, 255))
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
            try:
                msg = w1_to_w2.get_nowait()
                if msg.get("event") == "start_collecting":
                    players_data = msg["players"]
                    question = msg["question"]
                    turn_order = msg["turn_order"]
                    waiting = False
            except queue.Empty:
                pass

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            pygame.display.flip()
            clock.tick(FPS)

        players = [be.Player(nickname=p["nickname"], id=p["id"], answer=None) for p in players_data]
        player_by_id = {p.id: p for p in players}
        current_turn_index = 0
        all_answers = []
        vote_options = {}
        vote_options_keys = []
        ai_display_id = None
        votes_list = []
        typed_text = ""
        selected_ans_idx = None
        scroll_y = 0
        hover_vals = [0.0, 0.0]
        ans_hover_vals = []
        waiting_for_ai = False
        ai_answer_result = [None]
        ai_done_flag = [False]
        input_error_msg = ""
        error_timer = 0
        results_timer = 0
        final_result = None
        state = STATE_COLLECTING
        game_active = True

        while game_active:
            clock.tick(FPS)
            mx, my = pygame.mouse.get_pos()
            cx, lx = SCREEN_WIDTH // 2, (SCREEN_WIDTH - RECT_WIDTH) // 2
            btn1_rect = pygame.Rect(0, 0, 0, 0)
            btn2_rect = pygame.Rect(0, 0, 0, 0)
            voting_rects = []

            if state == STATE_COLLECTING:
                draw_background()
                r1 = pygame.Rect(lx, RECT_TOP_Y, RECT_WIDTH, RECT_HEIGHT_IN)
                window2.draw_sharp_gradient_rect(screen, r1.x, r1.y, r1.width, r1.height, SHARP_RADIUS, RECT1_COLOR_L, RECT1_COLOR_R)
                r2 = pygame.Rect(lx, r1.bottom + 15, RECT_WIDTH, RECT2_HEIGHT_IN)
                window2.draw_sharp_gradient_rect(screen, r2.x, r2.y, r2.width, r2.height, SHARP_RADIUS, RECT2_COLOR_T, RECT2_COLOR_B, False)
                window2.draw_text_wrapped(screen, question, font_body, TEXT_WHITE, r1)
                window2.draw_text_wrapped(screen, typed_text + "|", font_body, (0, 0, 0), r2)
                window2.draw_banner(screen, player_by_id[turn_order[current_turn_index]].nickname)
                word_count = len([w for w in typed_text.split() if w.strip()])
                can_proceed = 10 <= word_count <= 20
                is_last = current_turn_index == len(turn_order) - 1
                if input_error_msg:
                    err_surf = font_body.render(input_error_msg, True, (255, 100, 100))
                    screen.blit(err_surf, err_surf.get_rect(center=(cx, r2.bottom + 55)))
                b_y = r2.bottom + 20
                if not is_last:
                    btn1_rect = window2.draw_pill_btn(screen, cx, b_y, window2.BTN1_WIDTH, window2.BTN1_HEIGHT, img_next, hover_vals[0])
                else:
                    btn2_rect = window2.draw_pill_btn(screen, cx, b_y, window2.BTN2_WIDTH, window2.BTN2_HEIGHT, img_done, hover_vals[1])

            elif state == STATE_VOTING:
                draw_background()
                content_h = 2000
                scroll_surf = pygame.Surface((SCREEN_WIDTH, content_h), pygame.SRCALPHA)
                rv = pygame.Rect(lx, RECT_TOP_Y, RECT_WIDTH, RECT1_HEIGHT_VOTE)
                window2.draw_sharp_gradient_rect(scroll_surf, rv.x, rv.y, rv.width, rv.height, SHARP_RADIUS, RECT1_COLOR_L, RECT1_COLOR_R)
                title = font_body.render("Which answer is the impostor?", True, TEXT_WHITE)
                scroll_surf.blit(title, title.get_rect(center=rv.center))
                curr_y = rv.bottom + 15
                while len(ans_hover_vals) < len(all_answers):
                    ans_hover_vals.append(0.0)
                for i, ans in enumerate(all_answers):
                    dyn_h = max(70, len(window2.get_wrapped_lines(ans, font_body, RECT_WIDTH)) * font_body.get_linesize() + 20)
                    row_r = pygame.Rect(lx, curr_y, RECT_WIDTH, dyn_h)
                    collision_r = pygame.Rect(lx, curr_y - scroll_y, RECT_WIDTH, dyn_h)
                    voting_rects.append(collision_r)
                    is_selected = selected_ans_idx == i
                    targ = 1.0 if collision_r.collidepoint(mx, my) or is_selected else 0.0
                    ans_hover_vals[i] += (targ - ans_hover_vals[i]) * min(HOVER_SPEED * (1 / FPS), 1)
                    c1 = window2.lerp_color(RECT2_COLOR_T, BTN_HOVER_T, ans_hover_vals[i])
                    c2 = window2.lerp_color(RECT2_COLOR_B, BTN_HOVER_B, ans_hover_vals[i])
                    window2.draw_sharp_gradient_rect(scroll_surf, row_r.x, row_r.y, row_r.width, row_r.height, SHARP_RADIUS, c1, c2, False)
                    window2.draw_text_wrapped(scroll_surf, ans, font_body, (0, 0, 0), row_r)
                    curr_y += dyn_h + ROW_GAP
                b_y_virt = curr_y + 20
                is_last = current_turn_index == len(turn_order) - 1
                btn1_rect_virt = window2.draw_pill_btn(scroll_surf, cx, b_y_virt, window2.BTN1_WIDTH, window2.BTN1_HEIGHT, img_next, hover_vals[0])
                btn2_rect_virt = window2.draw_pill_btn(scroll_surf, cx, b_y_virt + window2.BTN1_HEIGHT + BUTTON_MARGIN, window2.BTN2_WIDTH, window2.BTN2_HEIGHT, img_done, hover_vals[1])
                btn1_rect = pygame.Rect(btn1_rect_virt.x, btn1_rect_virt.y - scroll_y, btn1_rect_virt.w, btn1_rect_virt.h)
                btn2_rect = pygame.Rect(btn2_rect_virt.x, btn2_rect_virt.y - scroll_y, btn2_rect_virt.w, btn2_rect_virt.h)
                screen.blit(scroll_surf, (0, -scroll_y))
                max_scroll = max(0, btn2_rect_virt.bottom + 50 - SCREEN_HEIGHT)
                scroll_y = max(0, min(scroll_y, max_scroll))
                if input_error_msg:
                    err_surf = font_body.render(input_error_msg, True, (255, 100, 100))
                    screen.blit(err_surf, err_surf.get_rect(center=(cx, SCREEN_HEIGHT - 35)))
                window2.draw_banner(screen, player_by_id[turn_order[current_turn_index]].nickname)
                can_proceed = selected_ans_idx is not None
                is_last = current_turn_index == len(turn_order) - 1

            elif state == STATE_RESULTS:
                draw_background()
                txt = font_results.render("VOTING RESULTS", True, TEXT_WHITE)
                screen.blit(txt, txt.get_rect(center=(cx, SCREEN_HEIGHT // 2)))

            elif state == STATE_PLAYER_WINS:
                draw_background()
                logo_r = img_win_logo.get_rect(center=(cx, SCREEN_HEIGHT // 2 - 120))
                text_r = img_win_text.get_rect(center=(cx, SCREEN_HEIGHT // 2 + 180))
                screen.blit(img_win_logo, logo_r)
                screen.blit(img_win_text, text_r)

            elif state == STATE_GEN_AI_WINS:
                draw_background()
                ai_logo_r = img_ai_win_logo.get_rect(center=(cx, SCREEN_HEIGHT // 2 - 120))
                ai_text_r = img_ai_win_text.get_rect(center=(cx, SCREEN_HEIGHT // 2 + 180))
                screen.blit(img_ai_win_logo, ai_logo_r)
                screen.blit(img_ai_win_text, ai_text_r)

            if state == STATE_COLLECTING and not waiting_for_ai:
                word_count = len([w for w in typed_text.split() if w.strip()])
                hover_vals[0] += ((1.0 if btn1_rect.collidepoint(mx, my) else 0.0) - hover_vals[0]) * min(HOVER_SPEED * (1 / FPS), 1)
                hover_vals[1] += ((1.0 if btn2_rect.collidepoint(mx, my) else 0.0) - hover_vals[1]) * min(HOVER_SPEED * (1 / FPS), 1)
            elif state == STATE_VOTING:
                hover_vals[0] += ((1.0 if btn1_rect.collidepoint(mx, my) else 0.0) - hover_vals[0]) * min(HOVER_SPEED * (1 / FPS), 1)
                hover_vals[1] += ((1.0 if btn2_rect.collidepoint(mx, my) else 0.0) - hover_vals[1]) * min(HOVER_SPEED * (1 / FPS), 1)

            if waiting_for_ai:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                thinking = font_body.render("Gen AI is thinking...", True, (255, 255, 255))
                screen.blit(thinking, thinking.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
                if ai_done_flag[0]:
                    ai_text = ai_answer_result[0]
                    if not isinstance(ai_text, str) or not ai_text.strip() or ai_text.lower().strip() in (
                        "gen ai unavailable",
                        "sorry, the gen ai is temporarily unavailable.",
                        "sorry, could not connect to the gen ai.",
                    ):
                        print(f"[DEBUG] Gen AI response invalid: {ai_text!r}")
                        print(f"[DEBUG] Using GEN_AI_API_KEY: {'SET' if GEN_AI_API_KEY.strip() else 'EMPTY'}")
                        _msgbox(
                            "Gen AI Error",
                            "The Gen AI could not generate an answer. Check your API key and internet connection, then restart.",
                            kind="error",
                        )
                        pygame.quit()
                        sys.exit()
                    vote_options, ai_display_id = be.build_vote_options(players, ai_text)
                    if ai_display_id is None:
                        _msgbox(
                            "Gen AI Error",
                            "Unable to identify the Gen AI answer after randomization. Restart the game.",
                            kind="error",
                        )
                        pygame.quit()
                        sys.exit()
                    all_answers = list(vote_options.values())
                    vote_options_keys = list(vote_options.keys())
                    w2_to_w1.put({"event": "voting_phase"})
                    state = STATE_VOTING
                    current_turn_index = 0
                    waiting_for_ai = False

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEWHEEL and state == STATE_VOTING:
                    scroll_y -= event.y * 30
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if state == STATE_COLLECTING and not waiting_for_ai:
                        word_count = len([w for w in typed_text.split() if w.strip()])
                        can_proceed = 10 <= word_count <= 20
                        is_last = current_turn_index == len(turn_order) - 1
                        if not is_last and btn1_rect.collidepoint(event.pos):
                            if not can_proceed:
                                if word_count < 10:
                                    _msgbox("Invalid Answer", "Your answer must be at least 10 words. Keep typing!", kind="error")
                                else:
                                    _msgbox("Invalid Answer", "Your answer must be 20 words or fewer. Please shorten it.", kind="error")
                            else:
                                current_player = player_by_id[turn_order[current_turn_index]]
                                be.collect_player_answer(current_player, typed_text)
                                w2_to_w1.put({"event": "answer_saved", "player_id": current_player.id})
                                typed_text = ""
                                current_turn_index += 1
                        elif is_last and btn2_rect.collidepoint(event.pos):
                            if not can_proceed:
                                if word_count < 10:
                                    _msgbox("Invalid Answer", "Your answer must be at least 10 words. Keep typing!", kind="error")
                                else:
                                    _msgbox("Invalid Answer", "Your answer must be 20 words or fewer. Please shorten it.", kind="error")
                            else:
                                current_player = player_by_id[turn_order[current_turn_index]]
                                be.collect_player_answer(current_player, typed_text)
                                w2_to_w1.put({"event": "answer_saved", "player_id": current_player.id})
                                typed_text = ""
                                waiting_for_ai = True

                                def _gen_ai():
                                    try:
                                        pygame.mixer.init()
                                        sound = pygame.mixer.Sound(asset_path("sounds", "button_sound.MP3"))
                                        sound.set_volume(1.0)
                                        sound.play()
                                    except Exception as e:
                                        print(f"Failed to play Gen AI generation sound: {e}")
                                    time.sleep(1)  # Give a moment for UI to settle
                                    answers = be.get_player_answers(players)
                                    ai_answer_result[0] = gen_ai.generate_gen_ai_answer(answers, question, api_key=GEN_AI_API_KEY)
                                    ai_done_flag[0] = True

                                threading.Thread(target=_gen_ai, daemon=True).start()

                    elif state == STATE_VOTING:
                        for i, r in enumerate(voting_rects):
                            if r.collidepoint(event.pos):
                                selected_ans_idx = i
                                if button_sound: button_sound.play()
                        is_last = current_turn_index == len(turn_order) - 1
                        if not is_last and btn1_rect.collidepoint(event.pos):
                            if selected_ans_idx is None:
                                input_error_msg = "Please select an answer before moving to the next voter."
                                error_timer = FPS * 2
                            else:
                                voted_display_id = vote_options_keys[selected_ans_idx]
                                votes_list.append(voted_display_id)
                                w2_to_w1.put({"event": "vote_cast", "voter_id": turn_order[current_turn_index]})
                                selected_ans_idx = None
                                scroll_y = 0
                                current_turn_index += 1
                        elif is_last and btn2_rect.collidepoint(event.pos):
                            if selected_ans_idx is None:
                                input_error_msg = "Please select an answer before submitting your vote."
                                error_timer = FPS * 2
                            else:
                                voted_display_id = vote_options_keys[selected_ans_idx]
                                votes_list.append(voted_display_id)
                                w2_to_w1.put({"event": "vote_cast", "voter_id": turn_order[current_turn_index]})
                                totals = be.tally_votes(votes_list)
                                winner = be.determine_vote_winner(totals)
                                if isinstance(winner, list) or winner != ai_display_id:
                                    final_result = "gen_ai_wins"
                                else:
                                    final_result = "players_win"
                                w2_to_w1.put({
                                    "event": "voting_results",
                                    "result": final_result,
                                    "ai_answer": vote_options.get(ai_display_id),
                                })
                                game_active = False

                    elif state in (STATE_PLAYER_WINS, STATE_GEN_AI_WINS):
                        pygame.display.iconify()
                        play_again = _msgbox("Game Over", "Would you like to play again?", kind="yesno")
                        if play_again:
                            be.reset_game_state({})
                            w2_to_w1.put({"event": "restart"})
                            game_active = False
                        else:
                            w2_to_w1.put({"event": "quit"})
                            pygame.quit()
                            sys.exit()

                if event.type == pygame.KEYDOWN and state == STATE_COLLECTING and not waiting_for_ai:
                    if event.key == pygame.K_BACKSPACE:
                        typed_text = typed_text[:-1]
                    elif (len([w for w in typed_text.split() if w.strip()]) < 20) or (
                        event.unicode != " " and len([w for w in typed_text.split() if w.strip()]) == 20
                    ):
                        typed_text += event.unicode

            if error_timer > 0:
                error_timer -= 1
                if error_timer <= 0:
                    input_error_msg = ""

            pygame.display.flip()


def _detect_secondary_offset():
    try:
        import screeninfo

        monitors = screeninfo.get_monitors()
        if len(monitors) >= 2:
            return monitors[1].x, monitors[1].y
    except ImportError:
        pass
    return 1366, 0


if __name__ == "__main__":
    try:
        src = open("gen_ai.py").read()
        if 'GEN_AI_API_KEY = ""' in src or "GEN_AI_API_KEY = ''" in src:
            print("WARNING: gen_ai.py has an empty API key. Fill it in before playing.")
    except Exception:
        pass

    while True:
        w2_offset = _detect_secondary_offset()
        w1_to_w2 = multiprocessing.Queue()
        w2_to_w1 = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()

        p1 = multiprocessing.Process(target=run_window1, args=(result_queue, w1_to_w2, w2_to_w1, w2_offset), daemon=True)
        p2 = multiprocessing.Process(target=run_window2, args=(w1_to_w2, w2_to_w1, w2_offset), daemon=True)

        p1.start()
        p2.start()
        p1.join()
        p2.join()

        last_result = result_queue.get() if not result_queue.empty() else None
        if last_result:
            time.sleep(5)  # Wait 5 seconds after winner/loser declaration
            play_again = _msgbox("Game Over", f"You {'won' if last_result == 'win' else 'lost'}! Want to play again?", kind="yesno")
            if play_again:
                continue
            else:
                break
        else:
            break
