"""Render the README TUI GIF by driving the real Textual app.

The app runs headless under Textual's test pilot; each key press is a real key
press, and every frame is the screen the app actually composed (read from its
compositor), painted cell by cell with its own colours.

    pip install -e ".[tui]" pillow
    python scripts/make_tui_gif.py

Writes ``docs/assets/tui.gif``. Dev tool, so it lives outside ``src/``.
"""

from __future__ import annotations

import asyncio

from make_demo_gifs import ASSETS, BAR, BG, CH, CW, FG, FONT, PAD, REPO
from PIL import Image, ImageDraw

SIZE = (100, 30)
TITLE = "docmax tui"
BAR_H = 34
W, H = CW * SIZE[0] + PAD * 2, CH * SIZE[1] + PAD * 2 + BAR_H


def paint(strips: list) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, BAR_H], fill=BAR)
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse([PAD + i * 22, 11, PAD + i * 22 + 12, 23], fill=c)
    d.text((W // 2, 17), TITLE, font=FONT, fill=(125, 133, 144), anchor="mm")
    for row, strip in enumerate(strips):
        x, y = PAD, BAR_H + PAD + row * CH
        for seg in strip:
            style = seg.style
            fg = style.color.get_truecolor() if style and style.color else None
            bg = style.bgcolor.get_truecolor() if style and style.bgcolor else None
            if style and style.reverse:
                fg, bg = bg, fg
            width = CW * len(seg.text)
            if bg:
                d.rectangle([x, y, x + width, y + CH], fill=tuple(bg))
            d.text((x, y), seg.text, font=FONT, fill=tuple(fg) if fg else FG)
            x += width
    return img


async def record() -> tuple[list[Image.Image], list[int]]:
    from docmax.tui.app import DocMaxApp

    frames: list[Image.Image] = []
    durs: list[int] = []
    app = DocMaxApp()
    async with app.run_test(size=SIZE) as pilot:

        async def snap(ms: int) -> None:
            await pilot.pause(0.3)
            frames.append(paint(app.screen._compositor.render_strips()))
            durs.append(ms)

        # The search box owns focus on launch, so typing filters straight away.
        await snap(1500)
        for ch in "comp":
            await pilot.press(ch)
            await snap(250)
        await snap(900)
        for _ in range(8):  # arrow down the way a user would, until compress is focused
            if getattr(app.focused, "id", "") == "tool-compress":
                break
            await pilot.press("down")
            await snap(350)
        await snap(1800)
        await pilot.press("enter")
        await snap(2800)
        await pilot.press("escape")
        await snap(1200)
    return frames, durs


def main() -> None:
    frames, durs = asyncio.run(record())
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / "tui.gif"
    pal = [f.quantize(colors=48, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=durs, loop=0, disposal=2)
    print(f"{out.relative_to(REPO)}  {len(frames)} frames  {out.stat().st_size // 1024} KiB")  # noqa: T201


if __name__ == "__main__":
    main()
