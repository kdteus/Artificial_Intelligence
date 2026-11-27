"""Visual theme, crisp typography, and vector drawing helpers for Search Studio."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pygame


@dataclass(frozen=True)
class Theme:
    name: str
    bg: tuple[int, int, int]
    card: tuple[int, int, int]
    card_alt: tuple[int, int, int]
    stage: tuple[int, int, int]
    stage_dot: tuple[int, int, int]
    shadow: tuple[int, int, int]
    shadow_soft: tuple[int, int, int]
    line: tuple[int, int, int]
    line_strong: tuple[int, int, int]
    ink: tuple[int, int, int]
    ink_soft: tuple[int, int, int]
    muted: tuple[int, int, int]
    tile: tuple[int, int, int]
    tile_edge: tuple[int, int, int]
    tile_shadow: tuple[int, int, int]
    empty_slot: tuple[int, int, int]
    pill_track: tuple[int, int, int]
    hover: tuple[int, int, int]
    key_bg: tuple[int, int, int]
    key_border: tuple[int, int, int]
    white: tuple[int, int, int]
    accents: dict[str, tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]]


LIGHT_THEME = Theme(
    name="light",
    bg=(241, 245, 250),
    card=(255, 255, 255),
    card_alt=(248, 250, 253),
    stage=(246, 249, 253),
    stage_dot=(222, 230, 242),
    shadow=(219, 226, 238),
    shadow_soft=(231, 236, 245),
    line=(226, 232, 240),
    line_strong=(203, 213, 225),
    ink=(15, 23, 42),
    ink_soft=(51, 65, 85),
    muted=(100, 116, 139),
    tile=(255, 255, 255),
    tile_edge=(214, 223, 236),
    tile_shadow=(209, 219, 233),
    empty_slot=(234, 240, 248),
    pill_track=(238, 242, 248),
    hover=(234, 240, 249),
    key_bg=(248, 250, 252),
    key_border=(203, 213, 225),
    white=(255, 255, 255),
    accents={
        "blue": ((37, 99, 235), (239, 246, 255), (191, 219, 254)),
        "purple": ((124, 58, 237), (245, 243, 255), (221, 214, 254)),
        "green": ((5, 150, 105), (236, 253, 245), (167, 243, 208)),
        "amber": ((217, 119, 6), (255, 251, 235), (253, 230, 138)),
        "red": ((225, 29, 72), (255, 241, 242), (254, 205, 211)),
    },
)

DARK_THEME = Theme(
    name="dark",
    bg=(13, 19, 33),
    card=(23, 32, 49),
    card_alt=(29, 40, 61),
    stage=(17, 24, 39),
    stage_dot=(36, 49, 74),
    shadow=(8, 12, 22),
    shadow_soft=(11, 16, 28),
    line=(42, 55, 79),
    line_strong=(64, 81, 112),
    ink=(241, 245, 249),
    ink_soft=(203, 213, 225),
    muted=(148, 163, 184),
    tile=(34, 47, 70),
    tile_edge=(59, 77, 109),
    tile_shadow=(12, 18, 30),
    empty_slot=(19, 28, 44),
    pill_track=(17, 24, 39),
    hover=(41, 55, 82),
    key_bg=(30, 41, 59),
    key_border=(64, 81, 112),
    white=(255, 255, 255),
    accents={
        "blue": ((96, 165, 250), (26, 44, 78), (59, 130, 246)),
        "purple": ((167, 139, 250), (43, 33, 74), (139, 92, 246)),
        "green": ((52, 211, 153), (19, 54, 46), (16, 185, 129)),
        "amber": ((251, 191, 36), (56, 41, 21), (217, 119, 6)),
        "red": ((251, 113, 133), (61, 24, 37), (225, 29, 72)),
    },
)


def _load_font(candidates: list[str], fallback_name: str, size: int, bold: bool = False) -> pygame.font.Font:
    for path_str in candidates:
        path = Path(path_str)
        if path.exists():
            try:
                return pygame.font.Font(str(path), size)
            except OSError:
                continue
    return pygame.font.SysFont(fallback_name, size, bold=bold)


class FontSet:
    """Curated font hierarchy with Windows Segoe UI Semibold/Bold and Cascadia Mono."""

    def __init__(self) -> None:
        win = Path(r"C:\Windows\Fonts")
        regular = [str(win / "segoeui.ttf")]
        semibold = [str(win / "seguisb.ttf"), str(win / "segoeui.ttf")]
        bold = [str(win / "segoeuib.ttf"), str(win / "seguisb.ttf")]
        mono = [str(win / "CascadiaMono.ttf"), str(win / "consolab.ttf"), str(win / "consola.ttf")]
        numeral = [str(win / "segoeuib.ttf"), str(win / "bahnschrift.ttf")]

        self.brand = _load_font(bold, "segoeui", 21, bold=True)
        self.h2 = _load_font(semibold, "segoeui", 17, bold=True)
        self.body = _load_font(regular, "segoeui", 15)
        self.body_sb = _load_font(semibold, "segoeui", 15, bold=True)
        self.small = _load_font(regular, "segoeui", 13)
        self.small_sb = _load_font(semibold, "segoeui", 13, bold=True)
        self.micro = _load_font(semibold, "segoeui", 11, bold=True)
        self.kpi = _load_font(bold, "segoeui", 24, bold=True)
        self.tile_sm = _load_font(bold, "segoeui", 24, bold=True)
        self.tile_lg = _load_font(numeral, "segoeui", 38, bold=True)
        self.mono = _load_font(mono, "consolas", 13)
        self.mono_sm = _load_font(mono, "consolas", 11)
        self.action_lg = _load_font(bold, "segoeui", 22, bold=True)


def blend(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def draw_rounded(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    radius: int = 12,
    outline: tuple[int, int, int] | None = None,
    width: int = 1,
) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if outline is not None:
        pygame.draw.rect(surface, outline, rect, width=width, border_radius=radius)


def draw_card(surface: pygame.Surface, rect: pygame.Rect, theme: Theme, radius: int = 18) -> None:
    shadow2 = pygame.Rect(rect.x, rect.y + 4, rect.width, rect.height)
    shadow1 = pygame.Rect(rect.x, rect.y + 2, rect.width, rect.height)
    draw_rounded(surface, shadow2, theme.shadow_soft, radius)
    draw_rounded(surface, shadow1, theme.shadow, radius)
    draw_rounded(surface, rect, theme.card, radius, outline=theme.line, width=1)


def draw_dashed_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    radius: int = 12,
    dash: int = 6,
    gap: int = 5,
) -> None:
    draw_rounded(surface, rect, color, radius)
    tick_color = blend(color, (148, 163, 184), 0.45)
    x0, y0, x1, y1 = rect.left + radius, rect.top, rect.right - radius, rect.bottom - 1
    x = x0
    while x < x1:
        end = min(x + dash, x1)
        pygame.draw.line(surface, tick_color, (x, y0), (end, y0), 1)
        pygame.draw.line(surface, tick_color, (x, y1), (end, y1), 1)
        x += dash + gap
    y = rect.top + radius
    y_end = rect.bottom - radius
    while y < y_end:
        end = min(y + dash, y_end)
        pygame.draw.line(surface, tick_color, (rect.left, y), (rect.left, end), 1)
        pygame.draw.line(surface, tick_color, (rect.right - 1, y), (rect.right - 1, end), 1)
        y += dash + gap


def draw_stage_grid(surface: pygame.Surface, rect: pygame.Rect, theme: Theme, radius: int = 16) -> None:
    draw_rounded(surface, rect, theme.stage, radius, outline=theme.line, width=1)
    spacing = 24
    for x in range(rect.left + 18, rect.right - 12, spacing):
        for y in range(rect.top + 18, rect.bottom - 12, spacing):
            pygame.draw.circle(surface, theme.stage_dot, (x, y), 1)


def draw_logo(surface: pygame.Surface, rect: pygame.Rect, accent: tuple[int, int, int], white: tuple[int, int, int]) -> None:
    draw_rounded(surface, rect, accent, 11)
    cx, cy = rect.center
    top = (cx, cy - 8)
    left = (cx - 8, cy + 7)
    right = (cx + 8, cy + 7)
    pygame.draw.line(surface, white, top, left, 2)
    pygame.draw.line(surface, white, top, right, 2)
    pygame.draw.line(surface, white, left, right, 1)
    for pt in (top, left, right):
        pygame.draw.circle(surface, white, pt, 3)


def draw_puzzle_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    s = 5
    g = 2
    x0 = cx - (2 * s + g) // 2
    y0 = cy - (2 * s + g) // 2
    for idx in range(3):
        r, c = divmod(idx, 2)
        pygame.draw.rect(surface, color, (x0 + c * (s + g), y0 + r * (s + g), s, s), border_radius=1)
    pygame.draw.rect(surface, color, (x0 + (s + g), y0 + (s + g), s, s), width=1, border_radius=1)


def draw_vacuum_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    pygame.draw.arc(surface, color, (cx - 7, cy - 6, 14, 12), 0, 3.14159, 2)
    pygame.draw.line(surface, color, (cx - 7, cy), (cx + 7, cy), 2)
    pygame.draw.circle(surface, color, (cx - 4, cy + 3), 2)
    pygame.draw.circle(surface, color, (cx + 4, cy + 3), 2)


def draw_play_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int], size: int = 5) -> None:
    pts = [(cx - size + 1, cy - size), (cx - size + 1, cy + size), (cx + size, cy)]
    pygame.draw.polygon(surface, color, pts)


def draw_pause_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    pygame.draw.rect(surface, color, (cx - 4, cy - 5, 3, 10), border_radius=1)
    pygame.draw.rect(surface, color, (cx + 1, cy - 5, 3, 10), border_radius=1)


def draw_step_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    pts = [(cx - 5, cy - 5), (cx - 5, cy + 5), (cx + 2, cy)]
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.rect(surface, color, (cx + 3, cy - 5, 2, 10), border_radius=1)


def draw_shuffle_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    pygame.draw.arc(surface, color, (cx - 6, cy - 6, 12, 12), 0.4, 5.2, 2)
    pygame.draw.polygon(surface, color, [(cx + 4, cy - 6), (cx + 7, cy - 2), (cx + 2, cy - 2)])


def draw_check_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    pygame.draw.lines(surface, color, False, [(cx - 4, cy), (cx - 1, cy + 3), (cx + 5, cy - 3)], 2)


def draw_chevron(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int], open_up: bool = False) -> None:
    if open_up:
        pts = [(cx - 4, cy + 2), (cx, cy - 2), (cx + 4, cy + 2)]
    else:
        pts = [(cx - 4, cy - 2), (cx, cy + 2), (cx + 4, cy - 2)]
    pygame.draw.lines(surface, color, False, pts, 2)


def draw_bfs_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    top = (cx, cy - 5)
    left = (cx - 5, cy + 4)
    right = (cx + 5, cy + 4)
    pygame.draw.line(surface, color, top, left, 2)
    pygame.draw.line(surface, color, top, right, 2)
    pygame.draw.line(surface, color, left, right, 1)
    for pt in (top, left, right):
        pygame.draw.circle(surface, color, pt, 2)


def draw_dfs_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    p1 = (cx - 4, cy - 6)
    p2 = (cx, cy)
    p3 = (cx + 4, cy + 6)
    pygame.draw.line(surface, color, p1, p2, 2)
    pygame.draw.line(surface, color, p2, p3, 2)
    for pt in (p1, p2, p3):
        pygame.draw.circle(surface, color, pt, 2)


def draw_ucs_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    pygame.draw.rect(surface, color, (cx - 6, cy - 5, 5, 3), border_radius=1)
    pygame.draw.rect(surface, color, (cx - 6, cy - 1, 9, 3), border_radius=1)
    pygame.draw.rect(surface, color, (cx - 6, cy + 3, 12, 3), border_radius=1)


def draw_popover(surface: pygame.Surface, rect: pygame.Rect, theme: Theme, radius: int = 16) -> None:
    s3 = pygame.Rect(rect.x, rect.y + 8, rect.width, rect.height)
    s2 = pygame.Rect(rect.x, rect.y + 4, rect.width, rect.height)
    draw_rounded(surface, s3, theme.shadow_soft, radius)
    draw_rounded(surface, s2, theme.shadow, radius)
    draw_rounded(surface, rect, theme.card, radius, outline=theme.line_strong, width=1)


def draw_cross_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    pygame.draw.line(surface, color, (cx - 3, cy - 3), (cx + 3, cy + 3), 2)
    pygame.draw.line(surface, color, (cx - 3, cy + 3), (cx + 3, cy - 3), 2)


def draw_theme_icon(surface: pygame.Surface, cx: int, cy: int, color: tuple[int, int, int], is_dark: bool) -> None:
    if is_dark:
        pygame.draw.circle(surface, color, (cx, cy), 4, 2)
        for dx, dy in ((0, -7), (0, 7), (-7, 0), (7, 0), (-5, -5), (5, -5), (-5, 5), (5, 5)):
            pygame.draw.line(surface, color, (cx + dx * 0.75, cy + dy * 0.75), (cx + dx, cy + dy), 1)
    else:
        pygame.draw.circle(surface, color, (cx, cy), 6, 2)
        pygame.draw.circle(surface, color, (cx + 2, cy - 2), 3)


def draw_direction_arrow(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    direction: str,
    color: tuple[int, int, int],
    radius: int = 12,
) -> None:
    if direction == "UP":
        pts = [(cx, cy - radius), (cx - radius + 2, cy + 2), (cx + radius - 2, cy + 2)]
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.rect(surface, color, (cx - 3, cy + 1, 6, radius - 2), border_radius=2)
    elif direction == "DOWN":
        pts = [(cx, cy + radius), (cx - radius + 2, cy - 2), (cx + radius - 2, cy - 2)]
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.rect(surface, color, (cx - 3, cy - radius + 1, 6, radius - 2), border_radius=2)
    elif direction == "LEFT":
        pts = [(cx - radius, cy), (cx + 2, cy - radius + 2), (cx + 2, cy + radius - 2)]
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.rect(surface, color, (cx + 1, cy - 3, radius - 2, 6), border_radius=2)
    elif direction == "RIGHT":
        pts = [(cx + radius, cy), (cx - 2, cy - radius + 2), (cx - 2, cy + radius - 2)]
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.rect(surface, color, (cx - radius + 1, cy - 3, radius - 2, 6), border_radius=2)
    elif direction == "SUCK":
        pygame.draw.circle(surface, color, (cx, cy), radius - 2, 2)
        pygame.draw.circle(surface, color, (cx, cy), 4)
    else:
        pygame.draw.circle(surface, color, (cx, cy), 6)


def draw_robot(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    accent: tuple[int, int, int],
    white: tuple[int, int, int],
    sucking: bool = False,
) -> None:
    pygame.draw.rect(surface, (45, 55, 72), (cx - 18, cy + 4, 36, 9), border_radius=4)
    pygame.draw.ellipse(surface, accent, (cx - 16, cy - 11, 32, 22))
    pygame.draw.rect(surface, accent, (cx - 16, cy - 1, 32, 7))
    pygame.draw.rect(surface, white, (cx - 9, cy - 4, 18, 5), border_radius=2)
    pygame.draw.circle(surface, accent, (cx - 4, cy - 2), 1)
    pygame.draw.circle(surface, accent, (cx + 4, cy - 2), 1)
    pygame.draw.line(surface, accent, (cx, cy - 11), (cx, cy - 17), 2)
    pygame.draw.circle(surface, accent, (cx, cy - 18), 3)
    if sucking:
        for r in (19, 24):
            pygame.draw.arc(surface, accent, (cx - r, cy - 8, r * 2, 26), 3.6, 5.8, 2)
