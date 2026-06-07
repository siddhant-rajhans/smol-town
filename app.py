"""Smol Town - watch a whole town of tiny local AI minds live, gossip, and feud on your laptop.
Build Small Hackathon - Thousand Token Wood.

    pip install -r requirements.txt
    python app.py        # set OLLAMA_BASE_URL to your Ollama (qwen3:14b now, MiniCPM later)
"""
import base64
import functools
import html
import io
import json
import math
import os
import tempfile

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


def _build_portraits():
    css, cls = [], {}
    pdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portraits")
    for name, key in town.PORTRAIT.items():
        p = os.path.join(pdir, key + ".png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB").resize((88, 88))
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=82)
            b64 = base64.b64encode(buf.getvalue()).decode()
            css.append(f".pav-{key}{{background-image:url(data:image/jpeg;base64,{b64})}}")
            cls[name] = key
    return "\n".join(css), cls


PORTRAIT_CSS, PORTRAIT_CLS = _build_portraits()
CSS += ("\n.pav{display:inline-block;width:34px;height:34px;border-radius:50%;"
        "background-size:cover;background-position:center top;vertical-align:middle;"
        "margin-right:8px;border:1px solid #5a4a36}\n"
        ".roster{display:flex;flex-wrap:wrap;gap:10px;margin:4px 0 14px}\n"
        ".rcard{text-align:center;width:78px}\n.roster .pav{width:62px;height:62px}\n"
        ".rname{font-size:.72rem;color:#cdbfa6;margin-top:3px}\n" + PORTRAIT_CSS)

ROSTER_HTML = "<div class='roster'>" + "".join(
    f"<div class='rcard'><span class='pav pav-{k}'></span>"
    f"<div class='rname'>{html.escape(n)}</div></div>"
    for n, k in PORTRAIT_CLS.items()) + "</div>"

RELATIONSHIPS = [
    ("Finn", "Marigold", "affection"),
    ("Marigold", "Bram", "conflict"),
    ("Mayor Doreen", "Finn", "affection"),
    ("Mayor Doreen", "Hazel", "conflict"),
    ("Pip", "Hazel", "affection"),
    ("Old Tom", "Mayor Doreen", "secret"),
    ("Pip", "Mayor Doreen", "secret"),
]


def _render(state):
    rows = []
    for s, t in state.feed:
        safe_s = html.escape(s)
        safe_t = html.escape(t)
        if s == "📢":
            rows.append(f"<div class='ev'>📢 {safe_t}</div>")
        else:
            key = PORTRAIT_CLS.get(s)
            av = (f"<span class='pav pav-{key}'></span>" if key
                  else f"<span class='av'>{town.avatar(s)}</span>")
            rows.append(f"<div>{av}<b>{safe_s}</b> — {safe_t}</div>")
    return "<div class='feed'>" + "".join(rows) + "</div>"


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


def chaos(state, event):
    if state is None:
        state, _ = start()
    town.inject(state, event)
    yield state, _render(state)
    for _ in range(2):
        town.step(state)
        yield state, _render(state)


def download_trace(state):
    """Write this session's agent traces to a temporary JSONL file."""
    if state is None:
        return None
    with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".jsonl", prefix="smol-town-trace-",
            delete=False) as trace_file:
        for trace in state.traces:
            trace_file.write(json.dumps(trace, ensure_ascii=False) + "\n")
        return trace_file.name


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


def _centered_text(draw, xy, text, font, fill):
    x, y = xy
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((x - (bbox[2] - bbox[0]) / 2, y), text, font=font, fill=fill)


def relationship_graph(state):
    W, H, cx, cy, R = 620, 640, 310, 330, 215
    img = Image.new("RGB", (W, H), (28, 23, 20))
    d = ImageDraw.Draw(img)
    title_f, name_f, legend_f = _font(30), _font(18), _font(16)
    _centered_text(d, (W / 2, 28), "The web of Tinbury", title_f, (244, 217, 160))

    names = list(town.PORTRAIT.keys())
    positions = {}
    for i, name in enumerate(names):
        angle = 2 * math.pi * i / len(names) - math.pi / 2
        positions[name] = (cx + R * math.cos(angle), cy + R * math.sin(angle))

    edge_cols = {
        "affection": (120, 200, 120),
        "conflict": (220, 90, 90),
        "secret": (230, 190, 90),
    }
    for a, b, kind in RELATIONSHIPS:
        d.line([positions[a], positions[b]], fill=edge_cols[kind], width=5)

    pdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portraits")
    last_speaker = state.feed[-1][0] if state is not None and state.feed else None
    node_size = 86
    mask = Image.new("L", (node_size, node_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, node_size - 1, node_size - 1), fill=255)

    for name in names:
        x, y = positions[name]
        box = (x - node_size / 2, y - node_size / 2,
               x + node_size / 2, y + node_size / 2)
        p = os.path.join(pdir, town.PORTRAIT[name] + ".png")
        if os.path.exists(p):
            with Image.open(p) as source:
                portrait = source.convert("RGB")
                side = min(portrait.size)
                left = (portrait.width - side) // 2
                top = (portrait.height - side) // 2
                portrait = portrait.crop((left, top, left + side, top + side))
                portrait = portrait.resize((node_size, node_size))
        else:
            portrait = Image.new("RGB", (node_size, node_size), (70, 58, 43))
        img.paste(portrait, (int(box[0]), int(box[1])), mask)
        ring = (244, 217, 160) if name == last_speaker else (90, 74, 54)
        width = 5 if name == last_speaker else 2
        d.ellipse(box, outline=ring, width=width)
        _centered_text(d, (x, y + node_size / 2 + 7), name, name_f, (205, 191, 166))

    legend = [("affection", (120, 200, 120)), ("conflict", (220, 90, 90)), ("secret", (230, 190, 90))]
    ly = 555
    for label, col in legend:
        d.rounded_rectangle((28, ly + 4, 54, ly + 16), radius=3, fill=col)
        d.text((64, ly), label, font=legend_f, fill=(205, 191, 166))
        ly += 24
    return img


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
    gr.HTML(ROSTER_HTML)
    graph = gr.Image(label="The web of Tinbury", show_label=False)
    state = gr.State()
    feed = gr.HTML()
    with gr.Row():
        beat_btn = gr.Button("⏭️ Next beat", variant="primary", scale=1)
        god = gr.Textbox(placeholder="⚡ Inject an event (god powers): 'a stranger rides into town'...",
                         scale=4, container=False)
        god_btn = gr.Button("⚡ Inject", scale=1)
    gr.Markdown("🎲 **Chaos events** — poke the town:")
    chaos_events = [
        ("🔥 Bakery fire",
         "A fire breaks out in Finn's bakery, and Bram is the only one close enough to help."),
        ("💌 Stolen letter",
         "Pip scrambles onto the well and reads a stolen love letter aloud to the whole square."),
        ("🧳 A stranger",
         "A hooded traveler arrives at dusk, asking for Hazel by a name only her family would know."),
        ("💰 Tax collector",
         "A tax collector rides in demanding the town hand over the missing treasury gold by sundown."),
        ("💍 Surprise wedding",
         "Mayor Doreen announces a surprise wedding at noon and refuses to say who the couple is."),
    ]
    with gr.Row():
        chaos_btns = [
            gr.Button(label, size="sm")
            for label, _ in chaos_events
        ]
    with gr.Row():
        share_btn = gr.Button("📸 Share this scene")
        trace_btn = gr.Button("Download town trace")
    card = gr.Image(label="Your shareable card (right-click → Save image)")
    trace_file = gr.File(label="Town agent trace")
    demo.load(boot, outputs=[state, feed]).then(relationship_graph, [state], [graph])
    share_btn.click(share_card, [state], [card])
    trace_btn.click(download_trace, [state], [trace_file])
    for chaos_btn, (_, event_text) in zip(chaos_btns, chaos_events):
        chaos_btn.click(functools.partial(chaos, event=event_text), [state], [state, feed]).then(
            relationship_graph, [state], [graph])
    beat_btn.click(beat, [state], [state, feed]).then(relationship_graph, [state], [graph])
    god_btn.click(godpower, [state, god], [state, feed, god]).then(relationship_graph, [state], [graph])
    god.submit(godpower, [state, god], [state, feed, god]).then(relationship_graph, [state], [graph])

if __name__ == "__main__":
    demo.launch()
