"""Shared chrome for the profile cards.

Both cards are drawn with the same frame, palette and type so they read as a
pair on the README. Colours are picked to stay legible on GitHub's light and
dark themes alike, since a card is a flat image and cannot follow the theme.
"""
WIDTH, PAD = 480, 24
ACCENT, MUTED, HAIRLINE = "#0366d6", "#8b949e", "#8b949e"
FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"


def open_svg(height, title, label):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{label}">',
        f'<style>.t{{font:600 15px {FONT};fill:{ACCENT}}}'
        f'.n{{font:600 24px {FONT};fill:{ACCENT}}}'
        f'.l{{font:400 12px {FONT};fill:{MUTED}}}'
        f'.s{{font:400 11px {FONT};fill:{MUTED}}}</style>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="6" '
        f'fill="none" stroke="{HAIRLINE}" stroke-opacity="0.35"/>',
        f'<text x="{PAD}" y="34" class="t">{title}</text>',
    ]


def close_svg(out):
    out.append('</svg>')
    return "\n".join(out) + "\n"
