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
    state = gr.State()
    feed = gr.HTML()
    with gr.Row():
        beat_btn = gr.Button("⏭️ Next beat", variant="primary", scale=1)
        god = gr.Textbox(placeholder="⚡ Inject an event (god powers): 'a stranger rides into town'...",
                         scale=4, container=False)
        god_btn = gr.Button("⚡ Inject", scale=1)
    gr.Markdown("**Chaos events** — poke the town:")
    chaos_events = [
        ("Bakery fire",
         "A fire breaks out in Finn's bakery, and Bram is the only one close enough to help."),
        ("Stolen letter",
         "Pip scrambles onto the well and reads a stolen love letter aloud to the whole square."),
        ("A stranger",
         "A hooded traveler arrives at dusk, asking for Hazel by a name only her family would know."),
        ("Tax collector",
         "A tax collector rides in demanding the town hand over the missing treasury gold by sundown."),
        ("Surprise wedding",
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
    demo.load(boot, outputs=[state, feed])
    share_btn.click(share_card, [state], [card])
    trace_btn.click(download_trace, [state], [trace_file])
    for chaos_btn, (_, event_text) in zip(chaos_btns, chaos_events):
        chaos_btn.click(functools.partial(chaos, event=event_text), [state], [state, feed])
    beat_btn.click(beat, [state], [state, feed])
    god_btn.click(godpower, [state, god], [state, feed, god])
    god.submit(godpower, [state, god], [state, feed, god])

if __name__ == "__main__":
    demo.launch()
