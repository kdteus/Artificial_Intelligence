"""Interactive search-algorithm visualizer.

Run from the repository root with ``python src/main.py``.
"""

from __future__ import annotations

import ctypes
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

try:
    import pygame
except ImportError as exc:
    raise SystemExit("Thiếu Pygame") from exc

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.registry import ALGORITHMS
from algorithms.search import SearchResult
from games import eight_puzzle, vacuum
from ui_theme import (
    DARK_THEME,
    LIGHT_THEME,
    FontSet,
    Theme,
    blend,
    draw_bfs_icon,
    draw_card,
    draw_check_icon,
    draw_chevron,
    draw_cross_icon,
    draw_dashed_rect,
    draw_dfs_icon,
    draw_direction_arrow,
    draw_logo,
    draw_pause_icon,
    draw_play_icon,
    draw_popover,
    draw_puzzle_icon,
    draw_robot,
    draw_rounded,
    draw_shuffle_icon,
    draw_stage_grid,
    draw_step_icon,
    draw_theme_icon,
    draw_ucs_icon,
    draw_vacuum_icon,
)

WIDTH, HEIGHT = 1280, 820
FPS = 60

ACTION_LABELS = {
    "UP": "LÊN",
    "DOWN": "XUỐNG",
    "LEFT": "TRÁI",
    "RIGHT": "PHẢI",
    "SUCK": "HÚT BỤI",
    "START": "BẮT ĐẦU",
}

ACTION_SHORT = {
    "UP": "LÊN",
    "DOWN": "XUỐNG",
    "LEFT": "TRÁI",
    "RIGHT": "PHẢI",
    "SUCK": "HÚT",
    "START": "BĐ",
}

ALGO_NOTES = {
    "BFS": "Mở rộng theo từng tầng độ sâu, đảm bảo tìm thấy lời giải có số bước ít nhất.",
    "DFS": "Đi sâu hết nhánh hiện tại rồi quay lui; tốn ít bộ nhớ hơn nhưng không đảm bảo ngắn nhất.",
    "UCS": "Luôn mở rộng trạng thái có tổng chi phí thấp nhất từ gốc, đảm bảo tối ưu theo trọng số.",
}

ALGO_BADGES = {
    "BFS": "Ngắn nhất",
    "DFS": "Tìm sâu",
    "UCS": "Chi phí tối ưu",
}

GAME_OPTIONS = [
    ("puzzle", "8 Puzzle", "3×3", "Sắp xếp các số về trạng thái đích.", "puzzle", "blue"),
    ("vacuum", "Máy hút bụi", "2–10 phòng", "Điều khiển robot dọn sạch các phòng bẩn.", "vacuum", "purple"),
]


class SearchStudio:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Search Studio · Trực quan hóa thuật toán tìm kiếm")

        info = pygame.display.Info()
        scale = min((info.current_w - 72) / WIDTH, (info.current_h - 96) / HEIGHT, 1.0)
        if scale >= 0.99:
            win_size = (WIDTH, HEIGHT)
        else:
            win_size = (max(960, int(WIDTH * scale)), max(620, int(HEIGHT * scale)))

        self.window = pygame.display.set_mode(win_size, pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = FontSet()
        self.theme: Theme = LIGHT_THEME

        self.game = "puzzle"
        self.selected_algorithm = next(iter(ALGORITHMS))
        self.algorithm_offset = 0

        self.puzzle_state = eight_puzzle.scramble(10)
        self.puzzle_selected: int | None = None
        self.vacuum_count = 5
        self.vacuum_dirty = [True] * self.vacuum_count
        self.vacuum_start = 0

        self.results: dict[str, SearchResult | None] = {name: None for name in ALGORITHMS}
        self.elapsed_by_algorithm = {name: 0.0 for name in ALGORITHMS}
        self.frame_index = 0
        self.playing = False
        self.step_delay = 0.48
        self.elapsed = 0.0
        self.anim_time = 0.0
        self.notice = "BFS · Chọn trò chơi, tùy chỉnh đầu vào rồi nhấn Chạy."
        self.future: Future | None = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.job_version = 0

        self.buttons: list[tuple[pygame.Rect, str, object, str, str | None]] = []
        self.puzzle_cells: list[pygame.Rect] = []
        self.room_cells: list[pygame.Rect] = []
        self.step_chips: list[tuple[pygame.Rect, int]] = []
        self.open_menu: str | None = None
        self.menu_rect: pygame.Rect | None = None
        self.menu_items: list[tuple[pygame.Rect, object]] = []
        self._current_cursor = pygame.SYSTEM_CURSOR_ARROW

    def _accent(self, theme_key: str | None = None):
        key = theme_key or ALGORITHMS[self.selected_algorithm].get("theme", "blue")
        return self.theme.accents.get(key, self.theme.accents["blue"])

    def _toggle_theme(self):
        self.theme = DARK_THEME if self.theme.name == "light" else LIGHT_THEME

    def _invalidate(self, notice: str | None = None):
        self.job_version += 1
        if self.future is not None:
            self.future.cancel()
            self.future = None
        self.results = {name: None for name in ALGORITHMS}
        self.elapsed_by_algorithm = {name: 0.0 for name in ALGORITHMS}
        self.frame_index = 0
        self.playing = False
        if notice:
            self.notice = notice

    def _toggle_menu(self, menu_name: str):
        self.open_menu = None if self.open_menu == menu_name else menu_name

    def _set_game(self, game: str):
        self.open_menu = None
        if self.game != game:
            self.game = game
            self.puzzle_selected = None
            self._invalidate("Đã chuyển bài toán. Nhấn Chạy để biểu diễn thuật toán.")

    def _set_algorithm(self, algorithm: str):
        self.open_menu = None
        if algorithm != self.selected_algorithm:
            self.selected_algorithm = algorithm
            self._invalidate(f"Đã chọn thuật toán {algorithm}.")

    def _active_algorithms(self):
        return [self.selected_algorithm]

    def _scroll_algorithms(self, delta: int):
        max_offset = max(0, len(ALGORITHMS) - 2)
        self.algorithm_offset = max(0, min(max_offset, self.algorithm_offset + delta * 2))

    @staticmethod
    def _is_solvable(state: tuple[int, ...]) -> bool:
        values = [value for value in state if value]
        inversions = sum(values[i] > values[j] for i in range(len(values)) for j in range(i + 1, len(values)))
        return inversions % 2 == 0

    def _run_search(self):
        if self.future and not self.future.done():
            return
        self.playing = False
        self.frame_index = 0
        if self.game == "puzzle":
            if not self._is_solvable(self.puzzle_state):
                self._invalidate("Bảng này không giải được. Hãy đổi vị trí hai ô hoặc xáo trộn lại.")
                return
            start = tuple(self.puzzle_state)
            goal = eight_puzzle.GOAL
            next_states = eight_puzzle.successors
            is_goal = lambda state: state == goal
            cost_fn = eight_puzzle.action_cost
        else:
            start = vacuum.make_start(self.vacuum_count, tuple(self.vacuum_dirty), self.vacuum_start)
            next_states = vacuum.successors
            is_goal = vacuum.is_goal
            cost_fn = vacuum.action_cost

        self.job_version += 1
        version = self.job_version
        self.results = {name: None for name in ALGORITHMS}
        self.elapsed_by_algorithm = {name: 0.0 for name in ALGORITHMS}
        selected = self._active_algorithms()
        self.notice = f"Đang chạy {selected[0]}…"

        def run_algorithm():
            results = {}
            durations = {}
            for name in selected:
                started = time.perf_counter()
                cfg = ALGORITHMS[name]
                if cfg.get("uses_cost"):
                    res = cfg["search"](start, is_goal, next_states, cost_fn=cost_fn)
                else:
                    res = cfg["search"](start, is_goal, next_states)
                if res is not None and res.total_cost is None:
                    res.total_cost = sum(cost_fn(action) for action in res.actions)
                results[name] = res
                durations[name] = time.perf_counter() - started
            return version, results, durations

        self.future = self.executor.submit(run_algorithm)

    def _poll_search(self):
        if not self.future or not self.future.done():
            return
        future, self.future = self.future, None
        try:
            version, results, durations = future.result()
        except Exception as exc:
            self.notice = f"Không thể chạy tìm kiếm: {exc}"
            return
        if version != self.job_version:
            return
        self.results.update(results)
        self.elapsed_by_algorithm.update(durations)
        if all(result is None for result in results.values()):
            self.notice = "Không tìm thấy lời giải trong không gian trạng thái này."
        else:
            algo_name = next(iter(results))
            res = results[algo_name]
            steps = len(res.actions) if res else 0
            self.notice = f"{algo_name} đã tìm xong lời giải gồm {steps} bước. Nhấn Phát hoặc → để xem."

    def _play(self):
        active = [self.results[name] for name in self._active_algorithms()]
        if not any(active):
            self._run_search()
            return
        max_steps = max(len(result.actions) for result in active if result is not None)
        if not self.playing and self.frame_index >= max_steps:
            self.frame_index = 0
        self.playing = not self.playing
        self.elapsed = 0.0
        self.notice = "Đang phát hoạt ảnh lời giải." if self.playing else "Đã tạm dừng."

    def _step(self, delta: int = 1):
        active = [self.results[name] for name in self._active_algorithms()]
        if not any(active):
            if delta > 0:
                self._run_search()
            return
        max_steps = max(len(result.actions) for result in active if result is not None)
        self.frame_index = max(0, min(max_steps, self.frame_index + delta))
        if self.frame_index >= max_steps:
            self.playing = False
            self.notice = "Đã đi hết lời giải."

    def _jump_to(self, step_idx: int):
        result = self.results.get(self.selected_algorithm)
        if result is None:
            return
        self.playing = False
        self.frame_index = max(0, min(len(result.actions), step_idx))
        self.notice = f"Đang xem bước {self.frame_index} / {len(result.actions)}."

    def _shuffle(self):
        if self.game == "puzzle":
            self.puzzle_state = eight_puzzle.scramble(10)
            self.puzzle_selected = None
            self._invalidate("Đã tạo bảng 8 Puzzle mới có lời giải.")
        else:
            self.vacuum_dirty = [True] * self.vacuum_count
            self.vacuum_start = 0
            self._invalidate("Đã làm bẩn tất cả phòng và đưa robot về phòng 1.")

    def _toggle_speed(self):
        self.step_delay = 0.20 if self.step_delay > 0.25 else 0.48

    def _set_room_count(self, delta: int):
        count = max(2, min(10, self.vacuum_count + delta))
        if count == self.vacuum_count:
            return
        old_dirty = self.vacuum_dirty
        self.vacuum_count = count
        self.vacuum_dirty = (old_dirty[:count] + [True] * count)[:count]
        self.vacuum_start = min(self.vacuum_start, count - 1)
        self._invalidate(f"Đã đổi số phòng thành {count}.")

    def _cycle_start(self):
        self.vacuum_start = (self.vacuum_start + 1) % self.vacuum_count
        self._invalidate(f"Robot bắt đầu tại phòng {self.vacuum_start + 1}.")

    def _click_puzzle_cell(self, index: int):
        if self.puzzle_selected is None:
            self.puzzle_selected = index
            return
        if self.puzzle_selected != index:
            board = list(self.puzzle_state)
            board[index], board[self.puzzle_selected] = board[self.puzzle_selected], board[index]
            self.puzzle_state = tuple(board)
            self._invalidate("Đã đổi vị trí hai ô.")
        self.puzzle_selected = None

    def _handle_click(self, position):
        if self.open_menu is not None:
            for rect, callback in self.menu_items:
                if rect.collidepoint(position):
                    callback()
                    return
            if self.menu_rect and self.menu_rect.collidepoint(position):
                return
            for rect, _label, callback, style, _icon in self.buttons:
                if style.startswith("dropdown") and rect.collidepoint(position):
                    callback()
                    return
            self.open_menu = None
            return

        for rect, _label, callback, _style, _icon in self.buttons:
            if rect.collidepoint(position):
                callback()
                return
        for rect, step_idx in self.step_chips:
            if rect.collidepoint(position):
                self._jump_to(step_idx)
                return
        if self.game == "puzzle":
            for index, rect in enumerate(self.puzzle_cells):
                if rect.collidepoint(position):
                    self._click_puzzle_cell(index)
                    return
        else:
            for index, rect in enumerate(self.room_cells):
                if rect.collidepoint(position):
                    self.vacuum_dirty[index] = not self.vacuum_dirty[index]
                    state_txt = "Bẩn" if self.vacuum_dirty[index] else "Sạch"
                    self._invalidate(f"Phòng {index + 1} đã chuyển sang {state_txt}.")
                    return

    def _update_cursor(self, mouse_pos):
        if self.open_menu is not None:
            interactive = any(rect.collidepoint(mouse_pos) for rect, _ in self.menu_items) or any(
                rect.collidepoint(mouse_pos) for rect, _l, _cb, style, _i in self.buttons if style.startswith("dropdown")
            )
        else:
            interactive = (
                any(rect.collidepoint(mouse_pos) for rect, *_ in self.buttons)
                or any(rect.collidepoint(mouse_pos) for rect, _ in self.step_chips)
                or (
                    any(rect.collidepoint(mouse_pos) for rect in self.puzzle_cells)
                    if self.game == "puzzle"
                    else any(rect.collidepoint(mouse_pos) for rect in self.room_cells)
                )
            )
        desired = pygame.SYSTEM_CURSOR_HAND if interactive else pygame.SYSTEM_CURSOR_ARROW
        if desired != self._current_cursor:
            self._current_cursor = desired
            pygame.mouse.set_cursor(desired)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            self.elapsed += dt
            self.anim_time += dt
            self._poll_search()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    w = max(900, event.w)
                    h = max(580, event.h)
                    self.window = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self._handle_click(self._to_canvas(event.pos))
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.open_menu is not None:
                            self.open_menu = None
                        else:
                            running = False
                    elif event.key == pygame.K_SPACE:
                        self._play()
                    elif event.key == pygame.K_RIGHT:
                        self._step(1)
                    elif event.key == pygame.K_LEFT:
                        self._step(-1)
                    elif event.key == pygame.K_r:
                        self._shuffle()
                    elif event.key == pygame.K_1:
                        self._set_game("puzzle")
                    elif event.key == pygame.K_2:
                        self._set_game("vacuum")

            if self.playing and self.elapsed >= self.step_delay:
                self.elapsed = 0.0
                self._step(1)

            mouse_pos = self._to_canvas(pygame.mouse.get_pos())
            self._draw(mouse_pos)
            self._update_cursor(mouse_pos)

            if self.window.get_size() == (WIDTH, HEIGHT):
                self.window.blit(self.screen, (0, 0))
            else:
                self.window.blit(pygame.transform.smoothscale(self.screen, self.window.get_size()), (0, 0))
            pygame.display.flip()

        self.executor.shutdown(wait=False, cancel_futures=True)
        pygame.quit()

    def _to_canvas(self, point):
        win_w, win_h = self.window.get_size()
        return (int(point[0] * WIDTH / max(1, win_w)), int(point[1] * HEIGHT / max(1, win_h)))

    def _draw(self, mouse_pos):
        self.screen.fill(self.theme.bg)
        self.buttons = []
        self.step_chips = []
        self.menu_rect = None
        self.menu_items = []
        self._draw_topbar(mouse_pos)
        self._draw_left_panel(mouse_pos)
        self._draw_right_panel(mouse_pos)
        self._draw_footer()
        if self.open_menu is not None:
            self._draw_dropdown_popover(mouse_pos)

    def _add_button(self, rect, label, callback, style="neutral", icon=None):
        self.buttons.append((pygame.Rect(rect), label, callback, style, icon))

    @staticmethod
    def _algo_icon(algo: str) -> str:
        if algo == "BFS":
            return "bfs"
        if algo == "DFS":
            return "dfs"
        if algo == "UCS":
            return "ucs"
        return f"dot_{ALGORITHMS[algo].get('theme', 'blue')}"

    def _draw_topbar(self, mouse_pos):
        bar = pygame.Rect(24, 18, 1232, 74)
        draw_card(self.screen, bar, self.theme, radius=18)

        accent, _, _ = self._accent()
        draw_logo(self.screen, pygame.Rect(40, 35, 40, 40), accent, self.theme.white)
        self._text("Search Studio", self.fonts.brand, self.theme.ink, (90, 29))
        self._text("Trực quan hóa thuật toán", self.fonts.small, self.theme.muted, (91, 56))

        algo_icon = self._algo_icon(self.selected_algorithm)
        self._add_button(
            (278, 35, 134, 40),
            self.selected_algorithm,
            lambda: self._toggle_menu("algorithm"),
            "dropdown_open_algo" if self.open_menu == "algorithm" else "dropdown_algo",
            algo_icon,
        )

        game_label = "8 Puzzle" if self.game == "puzzle" else "Máy hút bụi"
        game_icon = "puzzle" if self.game == "puzzle" else "vacuum"
        self._add_button(
            (424, 35, 174, 40),
            game_label,
            lambda: self._toggle_menu("game"),
            "dropdown_open_game" if self.open_menu == "game" else "dropdown_game",
            game_icon,
        )

        self._add_button((678, 35, 130, 40), f"Chạy {self.selected_algorithm}", self._run_search, "primary", "play")
        self._add_button(
            (818, 35, 108, 40),
            "Tạm dừng" if self.playing else "Phát",
            self._play,
            "soft_accent",
            "pause" if self.playing else "play",
        )
        self._add_button((936, 35, 104, 40), "Bước tiếp", lambda: self._step(1), "neutral", "step")
        self._add_button((1050, 35, 98, 40), "Xáo trộn", self._shuffle, "neutral", "shuffle")
        self._add_button((1158, 35, 44, 40), "2×" if self.step_delay < 0.25 else "1×", self._toggle_speed, "neutral")
        self._add_button((1210, 35, 34, 40), "", self._toggle_theme, "ghost", "theme")

        self._render_buttons(mouse_pos)

    def _solid_fill(self, key: str) -> tuple[int, int, int]:
        if self.theme.name == "dark":
            return {
                "blue": (37, 99, 235),
                "purple": (124, 58, 237),
                "green": (5, 150, 105),
                "amber": (217, 119, 6),
                "red": (225, 29, 72),
            }.get(key, (37, 99, 235))
        return self._accent(key)[0]

    def _render_buttons(self, mouse_pos):
        accent, pale, border = self._accent()
        primary_fill = self._solid_fill("green")
        for rect, label, _cb, style, icon in self.buttons:
            hovered = rect.collidepoint(mouse_pos)
            outline = None
            radius = 11

            if style == "primary":
                fill = blend(primary_fill, self.theme.white, 0.12) if hovered else primary_fill
                ink = self.theme.white
            elif style == "soft_accent":
                fill = blend(pale, accent, 0.14) if hovered else pale
                ink = accent
                outline = border
            elif style == "ghost":
                fill = self.theme.hover if hovered else self.theme.card
                ink = self.theme.ink_soft
                radius = 9
            elif style.startswith("dropdown"):
                is_open = style.startswith("dropdown_open")
                fill = self.theme.hover if (hovered or is_open) else self.theme.card_alt
                ink = self.theme.ink
                outline = accent if is_open else (self.theme.line_strong if hovered else self.theme.line)
                radius = 14
            elif style == "purple":
                p_accent, p_pale, p_border = self.theme.accents["purple"]
                fill = blend(p_pale, p_accent, 0.12) if hovered else p_pale
                ink = p_accent
                outline = p_border
            else:
                fill = self.theme.hover if hovered else self.theme.card_alt
                ink = self.theme.ink
                outline = self.theme.line_strong if hovered else self.theme.line

            draw_rounded(self.screen, rect, fill, radius, outline=outline)

            if icon:
                icon_x = rect.x + 16 if label else rect.centerx
                icon_y = rect.centery
                icon_color = accent if style.startswith("dropdown") and style.endswith("algo") else (
                    self._accent("blue" if self.game == "puzzle" else "purple")[0]
                    if style.startswith("dropdown") and style.endswith("game")
                    else ink
                )
                if icon == "play":
                    draw_play_icon(self.screen, icon_x, icon_y, icon_color, size=4)
                elif icon == "pause":
                    draw_pause_icon(self.screen, icon_x, icon_y, icon_color)
                elif icon == "step":
                    draw_step_icon(self.screen, icon_x, icon_y, icon_color)
                elif icon == "shuffle":
                    draw_shuffle_icon(self.screen, icon_x, icon_y, icon_color)
                elif icon == "puzzle":
                    draw_puzzle_icon(self.screen, icon_x + 1, icon_y, icon_color)
                elif icon == "vacuum":
                    draw_vacuum_icon(self.screen, icon_x + 1, icon_y, icon_color)
                elif icon == "bfs":
                    draw_bfs_icon(self.screen, icon_x + 1, icon_y, icon_color)
                elif icon == "dfs":
                    draw_dfs_icon(self.screen, icon_x + 1, icon_y, icon_color)
                elif icon == "ucs":
                    draw_ucs_icon(self.screen, icon_x + 1, icon_y, icon_color)
                elif icon == "theme":
                    draw_theme_icon(self.screen, icon_x, icon_y, icon_color, self.theme.name == "dark")
                elif icon.startswith("dot_"):
                    dot_accent, _, _ = self._accent(icon.removeprefix("dot_"))
                    pygame.draw.circle(self.screen, dot_accent, (icon_x + 2, icon_y), 4)

                if label:
                    text_surf = self.fonts.small_sb.render(label, True, ink)
                    if style.startswith("dropdown"):
                        self.screen.blit(text_surf, (rect.x + 34, rect.centery - text_surf.get_height() // 2))
                        draw_chevron(self.screen, rect.right - 16, rect.centery, self.theme.muted, open_up=style.startswith("dropdown_open"))
                    else:
                        tx = rect.x + 27 + (rect.width - 31 - text_surf.get_width()) // 2
                        self.screen.blit(text_surf, (tx, rect.centery - text_surf.get_height() // 2))
            elif label:
                self._center(label, self.fonts.small_sb, ink, rect.center)

    def _draw_dropdown_popover(self, mouse_pos):
        if self.open_menu == "algorithm":
            options = []
            for algo, cfg in ALGORITHMS.items():
                icon_type = self._algo_icon(algo)
                options.append(
                    (
                        algo,
                        ALGO_BADGES.get(algo),
                        cfg["subtitle"],
                        icon_type,
                        cfg.get("theme", "blue"),
                        self.selected_algorithm == algo,
                        lambda v=algo: self._set_algorithm(v),
                    )
                )
            menu_x, menu_w, header_text = 278, 372, "Thuật toán tìm kiếm"
        else:
            options = [
                (
                    title,
                    badge,
                    desc,
                    icon_type,
                    theme_key,
                    self.game == key,
                    lambda g=key: self._set_game(g),
                )
                for key, title, badge, desc, icon_type, theme_key in GAME_OPTIONS
            ]
            menu_x, menu_w, header_text = 424, 360, "Chọn trò chơi"

        row_h = 62
        row_gap = 4
        header_h = 36
        pad = 10
        menu_h = pad + header_h + len(options) * row_h + max(0, len(options) - 1) * row_gap + pad
        menu_rect = pygame.Rect(menu_x, 84, menu_w, menu_h)
        self.menu_rect = menu_rect
        draw_popover(self.screen, menu_rect, self.theme, radius=16)

        self._text(header_text, self.fonts.small_sb, self.theme.muted, (menu_rect.x + 18, menu_rect.y + 14))

        y = menu_rect.y + pad + header_h
        for title, badge, desc, icon_type, theme_key, selected, callback in options:
            row_rect = pygame.Rect(menu_rect.x + 8, y, menu_rect.width - 16, row_h)
            self.menu_items.append((row_rect, callback))
            hovered = row_rect.collidepoint(mouse_pos)
            opt_accent, opt_pale, opt_border = self._accent(theme_key)

            if hovered or selected:
                row_fill = self.theme.hover if hovered else self.theme.card_alt
                draw_rounded(self.screen, row_rect, row_fill, 12)

            icon_cx = row_rect.x + 22
            icon_cy = row_rect.y + 22
            icon_col = opt_accent if (selected or hovered) else self.theme.ink_soft
            if icon_type == "bfs":
                draw_bfs_icon(self.screen, icon_cx, icon_cy, icon_col)
            elif icon_type == "dfs":
                draw_dfs_icon(self.screen, icon_cx, icon_cy, icon_col)
            elif icon_type == "ucs":
                draw_ucs_icon(self.screen, icon_cx, icon_cy, icon_col)
            elif icon_type == "puzzle":
                draw_puzzle_icon(self.screen, icon_cx, icon_cy, icon_col)
            elif icon_type == "vacuum":
                draw_vacuum_icon(self.screen, icon_cx, icon_cy, icon_col)
            elif icon_type.startswith("dot_"):
                pygame.draw.circle(self.screen, opt_accent, (icon_cx, icon_cy), 5)

            title_surf = self.fonts.body_sb.render(title, True, self.theme.ink)
            tx = row_rect.x + 44
            self.screen.blit(title_surf, (tx, row_rect.y + 10))

            if badge:
                badge_surf = self.fonts.micro.render(badge, True, opt_accent if selected else self.theme.muted)
                bw = badge_surf.get_width() + 16
                bx = tx + title_surf.get_width() + 10
                b_rect = pygame.Rect(bx, row_rect.y + 11, bw, 20)
                draw_rounded(
                    self.screen,
                    b_rect,
                    opt_pale if selected else self.theme.pill_track,
                    10,
                    outline=opt_border if selected else self.theme.line,
                )
                self.screen.blit(badge_surf, (bx + 8, row_rect.y + 13))

            self._text(desc, self.fonts.small, self.theme.muted, (tx, row_rect.y + 34))

            if selected:
                draw_check_icon(self.screen, row_rect.right - 18, row_rect.centery, opt_accent)

            y += row_h + row_gap

    def _draw_left_panel(self, mouse_pos):
        card = pygame.Rect(24, 108, 416, 660)
        draw_card(self.screen, card, self.theme, radius=18)

        self._text("THIẾT LẬP ĐẦU VÀO", self.fonts.micro, self.theme.muted, (46, 128))
        if self.game == "puzzle":
            self._draw_puzzle_setup(mouse_pos)
        else:
            self._draw_vacuum_setup(mouse_pos)

        self._draw_algo_info_box()

    def _draw_puzzle_setup(self, mouse_pos):
        self._text("8 Puzzle · Bảng 3×3", self.fonts.h2, self.theme.ink, (46, 146))

        solvable = self._is_solvable(self.puzzle_state)
        status_key = "green" if solvable else "red"
        s_accent, s_pale, s_border = self._accent(status_key)
        badge = pygame.Rect(274, 142, 144, 28)
        draw_rounded(self.screen, badge, s_pale, 14, outline=s_border)
        if solvable:
            draw_check_icon(self.screen, badge.x + 22, badge.centery, s_accent)
            self._text("Có lời giải", self.fonts.micro, s_accent, (badge.x + 34, badge.y + 6))
        else:
            draw_cross_icon(self.screen, badge.x + 16, badge.centery, s_accent)
            self._text("Không giải được", self.fonts.micro, s_accent, (badge.x + 26, badge.y + 6))

        self.puzzle_cells = []
        size, gap = 76, 10
        x0 = 24 + (416 - (3 * size + 2 * gap)) // 2
        y0 = 192
        b_accent, b_pale, _ = self._accent("blue")

        for idx, value in enumerate(self.puzzle_state):
            row, col = divmod(idx, 3)
            tile = pygame.Rect(x0 + col * (size + gap), y0 + row * (size + gap), size, size)
            self.puzzle_cells.append(tile)
            selected = idx == self.puzzle_selected
            hovered = tile.collidepoint(mouse_pos)

            if value == 0:
                if selected:
                    draw_rounded(self.screen, tile, b_pale, 14, outline=b_accent, width=2)
                    self._center("□", self.fonts.h2, b_accent, tile.center)
                else:
                    draw_dashed_rect(self.screen, tile, self.theme.empty_slot, 14)
                    if hovered:
                        self._center("□", self.fonts.small, self.theme.muted, tile.center)
            else:
                if not selected:
                    lip = pygame.Rect(tile.x, tile.y + 3, tile.width, tile.height)
                    draw_rounded(self.screen, lip, self.theme.tile_shadow, 14)
                fill = b_pale if selected else (self.theme.hover if hovered else self.theme.tile)
                outline = b_accent if selected else (self.theme.line_strong if hovered else self.theme.tile_edge)
                draw_rounded(self.screen, tile, fill, 14, outline=outline, width=2 if selected else 1)
                self._center(str(value), self.fonts.tile_sm, b_accent if selected else self.theme.ink, tile.center)

        if self.puzzle_selected is not None:
            sel_val = self.puzzle_state[self.puzzle_selected]
            hint = f"Đang chọn ô {sel_val if sel_val else 'trống'} · nhấn ô thứ hai để đổi chỗ"
            self._center(hint, self.fonts.small_sb, b_accent, (232, 456))
        else:
            self._center("Nhấn hai ô bất kỳ để đổi vị trí", self.fonts.small, self.theme.muted, (232, 456))

        pygame.draw.line(self.screen, self.theme.line, (46, 478), (418, 478), 1)

        self._text("TRẠNG THÁI ĐÍCH", self.fonts.micro, self.theme.muted, (46, 494))
        g_size, g_gap = 30, 4
        gx0, gy0 = 46, 516
        for idx, value in enumerate(eight_puzzle.GOAL):
            r, c = divmod(idx, 3)
            g_rect = pygame.Rect(gx0 + c * (g_size + g_gap), gy0 + r * (g_size + g_gap), g_size, g_size)
            if value:
                draw_rounded(self.screen, g_rect, self.theme.card_alt, 7, outline=self.theme.line)
                self._center(str(value), self.fonts.small_sb, self.theme.ink, g_rect.center)
            else:
                draw_rounded(self.screen, g_rect, self.theme.empty_slot, 7)

        self._text("Mục tiêu chuẩn", self.fonts.body_sb, self.theme.ink, (164, 514))
        self._text("Sắp xếp các số từ 1 đến 8", self.fonts.small, self.theme.muted, (164, 539))
        self._text("theo thứ tự và ô trống ở cuối.", self.fonts.small, self.theme.muted, (164, 558))
        self._text("Hệ thống tự kiểm tra tính giải được.", self.fonts.small, self.theme.muted, (164, 579))

    def _draw_vacuum_setup(self, mouse_pos):
        self._text("Máy hút bụi · Thiết lập nhà", self.fonts.h2, self.theme.ink, (46, 146))

        stepper_box = pygame.Rect(46, 186, 150, 38)
        draw_rounded(self.screen, stepper_box, self.theme.card_alt, 11, outline=self.theme.line)
        self._add_button((50, 190, 32, 30), "−", lambda: self._set_room_count(-1), "neutral")
        self._center(f"{self.vacuum_count} phòng", self.fonts.small_sb, self.theme.ink, stepper_box.center)
        self._add_button((160, 190, 32, 30), "+", lambda: self._set_room_count(1), "neutral")

        self._add_button(
            (206, 186, 212, 38),
            f"Robot bắt đầu · Phòng {self.vacuum_start + 1}",
            self._cycle_start,
            "purple",
        )
        self._render_buttons(mouse_pos)

        self.room_cells = []
        cols = self.vacuum_count if self.vacuum_count <= 4 else (self.vacuum_count + 1) // 2
        rows = 1 if self.vacuum_count <= 4 else 2
        gap = 10
        avail_w = 372
        room_w = min(84, (avail_w - (cols - 1) * gap) // cols)
        room_h = 120 if rows == 1 else 108

        g_accent, g_pale, g_border = self._accent("green")
        a_accent, a_pale, a_border = self._accent("amber")
        p_accent, _, _ = self._accent("purple")

        y_start = 310 if rows == 1 else 258
        for i in range(self.vacuum_count):
            row_idx = 0 if rows == 1 else i // cols
            col_idx = i if rows == 1 else i % cols
            row_count = cols if row_idx == 0 else (self.vacuum_count - cols)
            row_w = row_count * room_w + (row_count - 1) * gap
            x0 = 24 + (416 - row_w) // 2
            x = x0 + col_idx * (room_w + gap)
            y = y_start + row_idx * (room_h + 24)

            tile = pygame.Rect(x, y, room_w, room_h)
            self.room_cells.append(tile)
            hovered = tile.collidepoint(mouse_pos)
            clean = not self.vacuum_dirty[i]

            fill = g_pale if clean else a_pale
            if hovered:
                fill = blend(fill, self.theme.ink, 0.04)
            outline = g_accent if hovered and clean else (a_accent if hovered else (g_border if clean else a_border))
            draw_rounded(self.screen, tile, fill, 13, outline=outline, width=2 if hovered else 1)

            self._center(f"P{i + 1}", self.fonts.h2, self.theme.ink, (tile.centerx, tile.y + 28))

            if clean:
                pygame.draw.circle(self.screen, g_accent, (tile.centerx, tile.y + 56), 5, 2)
            else:
                for dx, dy in ((-7, 54), (0, 58), (7, 53)):
                    pygame.draw.circle(self.screen, a_accent, (tile.centerx + dx, tile.y + dy), 2)

            pill = pygame.Rect(tile.centerx - 24, tile.bottom - 32, 48, 22)
            draw_rounded(self.screen, pill, self._solid_fill("green" if clean else "amber"), 8)
            self._center("Sạch" if clean else "Bẩn", self.fonts.micro, self.theme.white, pill.center)

            if self.vacuum_start == i:
                r_badge = pygame.Rect(tile.centerx - 13, tile.y - 11, 26, 20)
                draw_rounded(self.screen, r_badge, p_accent, 7)
                self._center("R", self.fonts.micro, self.theme.white, r_badge.center)

        self._center("Nhấn vào phòng bất kỳ để đổi Sạch / Bẩn", self.fonts.small, self.theme.muted, (232, 574))

    def _draw_algo_info_box(self):
        box = pygame.Rect(46, 616, 372, 130)
        draw_rounded(self.screen, box, self.theme.card_alt, 14, outline=self.theme.line)
        accent, pale, border = self._accent()
        pygame.draw.rect(self.screen, accent, (box.x + 12, box.y + 16, 4, box.height - 32), border_radius=2)

        pill = pygame.Rect(box.x + 26, box.y + 16, 54, 24)
        draw_rounded(self.screen, pill, pale, 8, outline=border)
        self._center(self.selected_algorithm, self.fonts.micro, accent, pill.center)
        self._text("Thuật toán đang chọn", self.fonts.small_sb, self.theme.ink, (box.x + 90, box.y + 19))

        subtitle = ALGORITHMS[self.selected_algorithm]["subtitle"]
        self._text(subtitle, self.fonts.small, self.theme.ink_soft, (box.x + 26, box.y + 48))

        if self.selected_algorithm == "UCS":
            if self.game == "puzzle":
                note = "Trọng số 8 Puzzle: Lên / Xuống = 1 · Trái / Phải = 2. Luôn chọn đường có tổng chi phí nhỏ nhất."
            else:
                note = "Trọng số Máy hút bụi: Trái / Phải = 1 · Hút bụi = 2. Luôn chọn đường có tổng chi phí nhỏ nhất."
        else:
            note = ALGO_NOTES.get(
                self.selected_algorithm,
                "Thuật toán tìm kiếm từ registry sẽ duyệt không gian trạng thái từ điểm bắt đầu.",
            )
        self._wrapped_text(note, self.fonts.small, self.theme.muted, pygame.Rect(box.x + 26, box.y + 74, 330, 48))

    def _draw_right_panel(self, mouse_pos):
        card = pygame.Rect(458, 108, 798, 660)
        draw_card(self.screen, card, self.theme, radius=18)

        name = self.selected_algorithm
        config = ALGORITHMS[name]
        accent, pale, border = self._accent()
        result = self.results.get(name)
        elapsed = self.elapsed_by_algorithm.get(name, 0.0)

        pill = pygame.Rect(480, 126, 58, 28)
        draw_rounded(self.screen, pill, pale, 10, outline=border)
        self._center(name, self.fonts.small_sb, accent, pill.center)
        self._text(config["subtitle"], self.fonts.body, self.theme.ink_soft, (550, 130))

        if self.future and not self.future.done():
            dots = "." * (int(self.anim_time * 3) % 4)
            status_txt, s_key = f"Đang chạy{dots}", "blue"
        elif result is None:
            status_txt, s_key = "Chờ chạy", "neutral"
        elif self.frame_index >= len(result.actions):
            status_txt, s_key = "Hoàn tất", "green"
        else:
            status_txt, s_key = f"Bước {self.frame_index} / {len(result.actions)}", config.get("theme", "blue")

        st_rect = pygame.Rect(1108, 126, 126, 28)
        if s_key == "neutral":
            draw_rounded(self.screen, st_rect, self.theme.card_alt, 14, outline=self.theme.line)
            self._center(status_txt, self.fonts.micro, self.theme.muted, st_rect.center)
        else:
            sa, sp, sb = self._accent(s_key)
            draw_rounded(self.screen, st_rect, sp, 14, outline=sb)
            if status_txt == "Hoàn tất":
                draw_check_icon(self.screen, st_rect.x + 28, st_rect.centery, sa)
                self._text(status_txt, self.fonts.micro, sa, (st_rect.x + 40, st_rect.y + 6))
            else:
                self._center(status_txt, self.fonts.micro, sa, st_rect.center)

        cost_val = "—"
        if result is not None:
            total_cost = result.total_cost
            if total_cost is None:
                cost_fn = eight_puzzle.action_cost if self.game == "puzzle" else vacuum.action_cost
                total_cost = sum(cost_fn(a) for a in result.actions)
            cost_val = f"{total_cost:,}"

        metrics = [
            ("MỞ RỘNG", f"{result.expanded:,}" if result else "—", "trạng thái đã xét"),
            ("ĐÃ THẤY", f"{result.discovered:,}" if result else "—", "trạng thái đã sinh"),
            ("SỐ BƯỚC", str(len(result.actions)) if result else "—", "độ dài lời giải"),
            ("CHI PHÍ", cost_val, "tổng trọng số"),
            ("THỜI GIAN", f"{elapsed * 1000:.1f} ms" if result else "—", "thời gian xử lý"),
        ]
        for idx, (label, val, hint) in enumerate(metrics):
            mx = 480 + idx * 153
            m_rect = pygame.Rect(mx, 168, 142, 86)
            draw_rounded(self.screen, m_rect, self.theme.card_alt, 14, outline=self.theme.line)
            pygame.draw.rect(self.screen, accent, (mx + 14, 168, 36, 3), border_radius=2)
            self._text(label, self.fonts.micro, self.theme.muted, (mx + 14, 178))
            self._text(val, self.fonts.kpi, accent if result else self.theme.muted, (mx + 14, 198))
            self._text(hint, self.fonts.micro, self.theme.muted, (mx + 14, 232))

        stage = pygame.Rect(480, 268, 754, 374)
        draw_stage_grid(self.screen, stage, self.theme, radius=16)

        if self.game == "puzzle":
            self._draw_puzzle_stage(stage, result, accent, pale, border)
        else:
            self._draw_vacuum_stage(stage, result, accent, pale, border)

        self._draw_timeline(result, accent, pale, border, mouse_pos)

    def _draw_puzzle_stage(self, stage: pygame.Rect, result: SearchResult | None, accent, pale, border):
        state = self.puzzle_state if result is None else result.states[min(self.frame_index, len(result.states) - 1)]
        prev_state = (
            result.states[self.frame_index - 1]
            if result is not None and self.frame_index > 0
            else None
        )
        moved_value = None
        if prev_state is not None:
            blank_prev = prev_state.index(0)
            moved_value = state[blank_prev]

        size, gap = 96, 10
        board_w = 3 * size + 2 * gap
        x0 = stage.x + 42
        y0 = stage.y + (stage.height - board_w) // 2

        g_accent, _, _ = self.theme.accents["green"]
        for idx, value in enumerate(state):
            r, c = divmod(idx, 3)
            tile = pygame.Rect(x0 + c * (size + gap), y0 + r * (size + gap), size, size)
            if value == 0:
                draw_dashed_rect(self.screen, tile, self.theme.empty_slot, 16)
            else:
                just_moved = value == moved_value
                in_goal = value == eight_puzzle.GOAL[idx]
                lip = pygame.Rect(tile.x, tile.y + 4, tile.width, tile.height)
                draw_rounded(self.screen, lip, blend(accent, self.theme.tile_shadow, 0.5) if just_moved else self.theme.tile_shadow, 16)
                fill = pale if just_moved else self.theme.tile
                outline = accent if just_moved else (border if in_goal else self.theme.tile_edge)
                draw_rounded(self.screen, tile, fill, 16, outline=outline, width=2 if just_moved else 1)
                self._center(str(value), self.fonts.tile_lg, accent if just_moved else self.theme.ink, tile.center)
                if in_goal:
                    pygame.draw.circle(self.screen, g_accent, (tile.right - 13, tile.top + 13), 4)

        panel = pygame.Rect(x0 + board_w + 36, y0, 326, board_w)
        draw_rounded(self.screen, panel, self.theme.card, 16, outline=self.theme.line)

        self._text("HÀNH ĐỘNG HIỆN TẠI", self.fonts.micro, self.theme.muted, (panel.x + 22, panel.y + 20))
        if result is None:
            action_code = "START"
            action_text = "Chưa mô phỏng"
            sub_text = f"Nhấn Chạy {self.selected_algorithm} để tìm lời giải"
        elif self.frame_index == 0:
            action_code = "START"
            action_text = "BẮT ĐẦU"
            sub_text = f"Tìm thấy lời giải gồm {len(result.actions)} bước"
        else:
            action_code = str(result.actions[min(self.frame_index, len(result.actions)) - 1])
            action_text = ACTION_LABELS.get(action_code, action_code)
            step_w = eight_puzzle.action_cost(action_code)
            sub_text = (
                f"Ô số {moved_value} di chuyển (+{step_w})"
                if moved_value
                else f"Bước {self.frame_index} (+{step_w})"
            )

        icon_box = pygame.Rect(panel.x + 22, panel.y + 50, 56, 56)
        draw_rounded(self.screen, icon_box, pale, 14, outline=border)
        draw_direction_arrow(self.screen, icon_box.centerx, icon_box.centery, action_code, accent, radius=13)

        self._text(action_text, self.fonts.action_lg, accent if result else self.theme.ink, (panel.x + 92, panel.y + 53))
        self._text(sub_text, self.fonts.small, self.theme.muted, (panel.x + 92, panel.y + 84))

        pygame.draw.line(self.screen, self.theme.line, (panel.x + 22, panel.y + 128), (panel.right - 22, panel.y + 128), 1)

        correct_count = sum(1 for i, v in enumerate(state) if v != 0 and v == eight_puzzle.GOAL[i])
        self._text("ĐỘ KHỚP MỤC TIÊU", self.fonts.micro, self.theme.muted, (panel.x + 22, panel.y + 146))
        self._text(f"{correct_count} / 8 ô đúng vị trí", self.fonts.body_sb, self.theme.ink, (panel.x + 22, panel.y + 168))

        meter_bg = pygame.Rect(panel.x + 22, panel.y + 198, panel.width - 44, 10)
        draw_rounded(self.screen, meter_bg, self.theme.pill_track, 5)
        if correct_count > 0:
            fill_w = max(10, int(meter_bg.width * (correct_count / 8)))
            draw_rounded(self.screen, pygame.Rect(meter_bg.x, meter_bg.y, fill_w, meter_bg.height), g_accent, 5)

        pygame.draw.circle(self.screen, g_accent, (panel.x + 28, panel.y + 240), 4)
        self._text("Chấm xanh: ô đã đúng vị trí đích", self.fonts.small, self.theme.muted, (panel.x + 40, panel.y + 231))
        pygame.draw.rect(self.screen, pale, (panel.x + 22, panel.y + 260, 12, 12), border_radius=3)
        pygame.draw.rect(self.screen, accent, (panel.x + 22, panel.y + 260, 12, 12), width=1, border_radius=3)
        self._text("Viền màu: ô vừa di chuyển", self.fonts.small, self.theme.muted, (panel.x + 40, panel.y + 258))

    def _draw_vacuum_stage(self, stage: pygame.Rect, result: SearchResult | None, accent, pale, border):
        state = (
            vacuum.make_start(self.vacuum_count, tuple(self.vacuum_dirty), self.vacuum_start)
            if result is None
            else result.states[min(self.frame_index, len(result.states) - 1)]
        )
        position, dirty = state
        count = len(dirty)

        action_code = "START"
        if result is not None and self.frame_index > 0:
            action_code = str(result.actions[min(self.frame_index, len(result.actions)) - 1])

        gap = 10
        room_w = min(88, (stage.width - 64 - gap * (count - 1)) // count)
        total_w = room_w * count + gap * (count - 1)
        x0 = stage.centerx - total_w // 2
        y0 = stage.y + 106
        room_h = 154

        pygame.draw.line(self.screen, self.theme.line_strong, (x0 - 16, y0 + room_h + 12), (x0 + total_w + 16, y0 + room_h + 12), 2)

        g_accent, g_pale, g_border = self._accent("green")
        a_accent, a_pale, a_border = self._accent("amber")

        for i, is_dirty in enumerate(dirty):
            x = x0 + i * (room_w + gap)
            tile = pygame.Rect(x, y0, room_w, room_h)
            clean = not is_dirty
            is_robot = i == position

            fill = g_pale if clean else a_pale
            outline = accent if is_robot else (g_border if clean else a_border)
            draw_rounded(self.screen, tile, fill, 14, outline=outline, width=2 if is_robot else 1)

            self._center(f"Phòng {i + 1}" if room_w >= 72 else f"P{i + 1}", self.fonts.small_sb, self.theme.ink, (tile.centerx, tile.y + 24))

            if clean:
                pygame.draw.circle(self.screen, g_accent, (tile.centerx, tile.y + 72), 11, 2)
                pygame.draw.line(self.screen, g_accent, (tile.centerx - 4, tile.y + 72), (tile.centerx - 1, tile.y + 75), 2)
                pygame.draw.line(self.screen, g_accent, (tile.centerx - 1, tile.y + 75), (tile.centerx + 5, tile.y + 68), 2)
            else:
                for dx, dy, rad in ((-10, 68, 4), (0, 74, 5), (10, 66, 3), (-5, 81, 3), (7, 79, 4)):
                    pygame.draw.circle(self.screen, a_accent, (tile.centerx + dx, tile.y + dy), rad)

            pill_w = min(56, room_w - 12)
            pill = pygame.Rect(tile.centerx - pill_w // 2, tile.bottom - 34, pill_w, 22)
            draw_rounded(self.screen, pill, self._solid_fill("green" if clean else "amber"), 8)
            self._center("Sạch" if clean else "Bẩn", self.fonts.micro, self.theme.white, pill.center)

            if is_robot:
                draw_robot(self.screen, tile.centerx, tile.y - 22, accent, self.theme.white, sucking=(action_code == "SUCK"))

        action_label = ACTION_LABELS.get(action_code, action_code)
        step_w = vacuum.action_cost(action_code) if action_code != "START" else 0
        cap_text = (
            f"Vị trí hiện tại: Phòng {position + 1} · Sẵn sàng mô phỏng"
            if result is None
            else (
                f"Hành động: {action_label} (+{step_w}) · Robot ở Phòng {position + 1}"
                if step_w
                else f"Hành động: {action_label} · Robot ở Phòng {position + 1}"
            )
        )
        cap_pill = pygame.Rect(stage.centerx - 220, stage.bottom - 52, 440, 34)
        draw_rounded(self.screen, cap_pill, self.theme.card, 12, outline=border if result else self.theme.line)
        draw_direction_arrow(self.screen, cap_pill.x + 22, cap_pill.centery, action_code, accent if result else self.theme.muted, radius=8)
        self._center(cap_text, self.fonts.small_sb, accent if result else self.theme.ink_soft, (cap_pill.centerx + 10, cap_pill.centery))

    def _draw_timeline(self, result: SearchResult | None, accent, pale, border, mouse_pos):
        self._text("LỘ TRÌNH HÀNH ĐỘNG", self.fonts.micro, self.theme.muted, (480, 656))
        solid_accent = self._solid_fill(ALGORITHMS[self.selected_algorithm].get("theme", "blue"))

        if result is None:
            info_surf = self.fonts.small.render(f"Chưa có dữ liệu · nhấn Chạy {self.selected_algorithm}", True, self.theme.muted)
            self.screen.blit(info_surf, (1234 - info_surf.get_width(), 654))
            bar = pygame.Rect(480, 678, 754, 6)
            draw_rounded(self.screen, bar, self.theme.pill_track, 3)
            empty_msg = pygame.Rect(480, 696, 754, 48)
            draw_rounded(self.screen, empty_msg, self.theme.card_alt, 12, outline=self.theme.line)
            self._center("Các bước lời giải sẽ hiển thị tại đây để bạn theo dõi hoặc nhảy đến từng bước.", self.fonts.small, self.theme.muted, empty_msg.center)
            return

        total = len(result.actions)
        idx = min(self.frame_index, total)
        prog_surf = self.fonts.small.render(f"Tiến trình: {idx} / {total} bước (nhấn vào bước để xem)", True, self.theme.muted)
        self.screen.blit(prog_surf, (1234 - prog_surf.get_width(), 654))

        bar = pygame.Rect(480, 678, 754, 6)
        draw_rounded(self.screen, bar, self.theme.pill_track, 3)
        if total > 0 and idx > 0:
            fill_w = max(8, int(bar.width * (idx / total)))
            draw_rounded(self.screen, pygame.Rect(bar.x, bar.y, fill_w, bar.height), accent, 3)
        elif total == 0:
            draw_rounded(self.screen, bar, accent, 3)

        all_steps = list(range(total + 1))
        max_visible = 9
        if len(all_steps) <= max_visible:
            visible = all_steps
        else:
            start = max(0, min(idx - max_visible // 2, len(all_steps) - max_visible))
            visible = all_steps[start : start + max_visible]

        chip_w, chip_gap = 78, 6
        x = 480
        y = 698
        for step_i in visible:
            c_rect = pygame.Rect(x, y, chip_w, 42)
            self.step_chips.append((c_rect, step_i))
            hovered = c_rect.collidepoint(mouse_pos)
            is_curr = step_i == idx
            is_past = step_i < idx

            if is_curr:
                fill, ink, out = solid_accent, self.theme.white, solid_accent
            elif is_past:
                fill, ink, out = pale, accent, border
            else:
                fill = self.theme.hover if hovered else self.theme.card_alt
                ink = self.theme.ink if hovered else self.theme.muted
                out = self.theme.line_strong if hovered else self.theme.line

            draw_rounded(self.screen, c_rect, fill, 10, outline=out)
            if step_i == 0:
                title = "BĐ"
                sub = "Gốc"
            else:
                act = str(result.actions[step_i - 1])
                title = ACTION_SHORT.get(act, act[:5])
                sub = f"#{step_i}"

            self._center(sub, self.fonts.mono_sm, ink if is_curr else self.theme.muted, (c_rect.centerx, c_rect.y + 12))
            self._center(title, self.fonts.micro, ink, (c_rect.centerx, c_rect.y + 28))
            x += chip_w + chip_gap

    def _draw_footer(self):
        notice_low = self.notice.lower()
        if "không giải được" in notice_low or "không thể" in notice_low or "không tìm thấy" in notice_low:
            dot_color, text_color = self._accent("red")[0], self._accent("red")[0]
        elif "đang chạy" in notice_low:
            dot_color, text_color = self._accent("blue")[0], self._accent("blue")[0]
        elif "tìm xong" in notice_low or "hoàn tất" in notice_low or "hết lời giải" in notice_low:
            dot_color, text_color = self._accent("green")[0], self.theme.ink_soft
        else:
            dot_color, text_color = self.theme.muted, self.theme.ink_soft

        pygame.draw.circle(self.screen, dot_color, (34, 793), 4)
        self._text(self.notice[:92], self.fonts.small_sb, text_color, (46, 783))

        shortcuts = [
            ("Space", "Phát/Dừng"),
            ("←/→", "Bước"),
            ("R", "Xáo trộn"),
            ("1/2", "Đổi game"),
            ("Esc", "Thoát"),
        ]
        rendered_items = []
        total_w = 0
        for key, desc in shortcuts:
            key_surf = self.fonts.mono_sm.render(key, True, self.theme.ink)
            desc_surf = self.fonts.small.render(desc, True, self.theme.muted)
            kw = key_surf.get_width() + 12
            item_w = kw + 5 + desc_surf.get_width()
            rendered_items.append((key_surf, desc_surf, kw, item_w))
            total_w += item_w
        total_w += 14 * (len(rendered_items) - 1)

        x = 1256 - total_w
        y = 782
        for key_surf, desc_surf, kw, item_w in rendered_items:
            k_rect = pygame.Rect(x, y, kw, 22)
            draw_rounded(self.screen, k_rect, self.theme.key_bg, 6, outline=self.theme.key_border)
            self.screen.blit(key_surf, (x + 6, y + 4))
            self.screen.blit(desc_surf, (x + kw + 5, y + 2))
            x += item_w + 14

    def _wrapped_text(self, text: str, font: pygame.font.Font, color, rect: pygame.Rect):
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= rect.width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        y = rect.y
        line_h = font.get_linesize() + 1
        for line in lines:
            if y + line_h > rect.bottom:
                break
            self._text(line, font, color, (rect.x, y))
            y += line_h

    def _text(self, value, font: pygame.font.Font, color, position):
        self.screen.blit(font.render(str(value), True, color), position)

    def _center(self, value, font: pygame.font.Font, color, position):
        surface = font.render(str(value), True, color)
        self.screen.blit(surface, surface.get_rect(center=position))


if __name__ == "__main__":
    SearchStudio().run()
