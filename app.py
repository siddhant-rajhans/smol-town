"""Smol Town - watch a whole town of tiny local AI minds live, gossip, and feud on your laptop.
Build Small Hackathon - Thousand Token Wood.

    pip install -r requirements.txt
    python app.py        # set OLLAMA_BASE_URL to your Ollama (qwen3:14b now, MiniCPM later)
"""
import os

import gradio as gr
from PIL import Image, ImageDraw, ImageFont

import town

if os.getenv("SPACE_ID"):          # on a Hugging Face Space -> load the model in-process (Off-the-Grid)
    import space_backend  # noqa: F401   (points town.GENERATE at a local ZeroGPU model)

CSS = """
.gradio-container{background:#1c1714;}
#hdr h1{font-family:Georgia,serif;color:#f4d9a0;}
.feed{font-family:Georgia,serif;font-size:1.02rem;line-height:1.6;
      background:#2a2118;border-radius:12px;padding:16px 20px;color:#efe3cf;max-height:560px;overflow:auto;}
.feed .ev{color:#d98c4a;font-style:italic;}
.feed .av{font-size:1.15rem;margin-right:3px;}
"""


def _render(state):
    rows = []
    for s, t in state.feed:
        if s == "📢":
            rows.append(f"<div class='ev'>📢 {t}</div>")
        else:
            rows.append(f"<div><span class='av'>{town.avatar(s)}</span> <b>{s}</b> — {t}</div>")
    return "<div class='feed'>" + "<br>".join(rows) + "</div>"


def start():
    state = town.TownState()
    town.inject(state, town.OPENING_HOOK)
    return state, _render(state)


def boot():
    """On page load: show the scandal hook instantly, then stream in a few beats of drama."""
    state = town.TownState()
    town.inject(state, town.OPENING_HOOK)
    yield state, _render(state)
    for _ in range(3):
        town.step(state)
        yield state, _render(state)


def beat(state):
    if state is None:
        state, _ = start()
    town.step(state)
    return state, _render(state)


def godpower(state, event):
    if state is None:
        state, _ = start()
    if event and event.strip():
        town.inject(state, event.strip())
    return state, _render(state), ""


def _font(sz):
    for p in ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap(draw, text, font, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out or [""]


def share_card(state):
    """Render the current scene as a shareable PNG card."""
    if state is None:
        return None
    W, pad, lh = 1080, 48, 40
    body_f, title_f, foot_f = _font(28), _font(46), _font(22)
    td = ImageDraw.Draw(Image.new("RGB", (W, 10)))
    blocks = []
    for s, t in state.feed[-7:]:
        txt = ("» " + t) if s == "📢" else f"{s}:  {t}"
        blocks.append((s == "📢", _wrap(td, txt, body_f, W - 2 * pad)))
    h = pad + 84 + sum(len(b) * lh + 12 for _, b in blocks) + 56
    img = Image.new("RGB", (W, h), (28, 23, 20))
    d = ImageDraw.Draw(img)
    d.text((pad, pad), "Smol Town  ·  Tinbury", font=title_f, fill=(244, 217, 160))
    y = pad + 84
    for is_ev, lines in blocks:
        col = (217, 140, 74) if is_ev else (239, 227, 207)
        for ln in lines:
            d.text((pad, y), ln, font=body_f, fill=col)
            y += lh
        y += 12
    d.text((pad, h - 42), "huggingface.co/spaces/build-small-hackathon/smol-town",
           font=foot_f, fill=(150, 120, 90))
    return img


with gr.Blocks(css=CSS, title="Smol Town") as demo:
    gr.Markdown(f"# 🏘️ Smol Town\nA whole town of tiny minds — alive on your laptop, offline. "
                f"Poke it. Watch the drama unfold.  \n_A cast of {len(town.CAST)} tiny local agents, running offline._",
                elem_id="hdr")
    state = gr.State()
    feed = gr.HTML()
    with gr.Row():
        beat_btn = gr.Button("⏭️ Next beat", variant="primary", scale=1)
        god = gr.Textbox(placeholder="⚡ Inject an event (god powers): 'a stranger rides into town'...",
                         scale=4, container=False)
        god_btn = gr.Button("⚡ Inject", scale=1)
    with gr.Row():
        share_btn = gr.Button("📸 Share this scene")
    card = gr.Image(label="Your shareable card (right-click → Save image)")
    demo.load(boot, outputs=[state, feed])
    share_btn.click(share_card, [state], [card])
    beat_btn.click(beat, [state], [state, feed])
    god_btn.click(godpower, [state, god], [state, feed, god])
    god.submit(godpower, [state, god], [state, feed, god])

if __name__ == "__main__":
    demo.launch()
