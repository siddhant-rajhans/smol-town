"""Smol Town - watch a whole town of tiny local AI minds live, gossip, and feud on your laptop.
Build Small Hackathon - Thousand Token Wood.

    pip install -r requirements.txt
    python app.py        # set OLLAMA_BASE_URL to your Ollama (qwen3:14b now, MiniCPM later)
"""
import os

import gradio as gr

import town

if os.getenv("SPACE_ID"):          # on a Hugging Face Space -> load the model in-process (Off-the-Grid)
    import space_backend  # noqa: F401   (points town.GENERATE at a local ZeroGPU model)

CSS = """
.gradio-container{background:#1c1714;}
#hdr h1{font-family:Georgia,serif;color:#f4d9a0;}
.feed{font-family:Georgia,serif;font-size:1.02rem;line-height:1.6;
      background:#2a2118;border-radius:12px;padding:16px 20px;color:#efe3cf;max-height:560px;overflow:auto;}
.feed .ev{color:#d98c4a;font-style:italic;}
"""


def _render(state):
    rows = []
    for s, t in state.feed:
        if s == "📢":
            rows.append(f"<div class='ev'>📢 {t}</div>")
        else:
            rows.append(f"<div><b>{s}</b> — {t}</div>")
    return "<div class='feed'>" + "<br>".join(rows) + "</div>"


def start():
    state = town.TownState()
    town.inject(state, f"Dawn breaks over {town.TOWN}. The marble fountain gurgles in the empty square.")
    return state, _render(state)


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
    demo.load(start, outputs=[state, feed])
    beat_btn.click(beat, [state], [state, feed])
    god_btn.click(godpower, [state, god], [state, feed, god])
    god.submit(godpower, [state, god], [state, feed, god])

if __name__ == "__main__":
    demo.launch()
