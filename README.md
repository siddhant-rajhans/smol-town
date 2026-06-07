---
title: Smol Town
emoji: 🏘️
colorFrom: indigo
colorTo: yellow
sdk: gradio
app_file: app.py
pinned: false
license: apache-2.0
---

# 🏘️ Smol Town — Build Small Hackathon (Thousand Token Wood)

A whole town of tiny local AI minds — they live, gossip, fall in love, and feud. **Runs offline on a laptop.**
Poke it with god-powers and watch the drama unfold.

> Big labs need a datacenter to run one mind. Smol Town runs a whole cast of them on a gaming GPU.

## Run locally
```bash
pip install -r requirements.txt
python app.py        # set OLLAMA_BASE_URL to your Ollama (qwen3:14b now, MiniCPM5-1B later)
# or watch it headless:  python town.py 8
```

## How it works
Each villager is a small-model agent with a personality, a secret, and feelings about the others. A tick loop
picks who acts; agents react to recent events (a memory window) and to each other → emergent soap-opera. You
inject events ("a stranger rides in") as god-powers.

## Pools / badges
Vision/agents MiniCPM (central) = OpenBMB · FLUX villager portraits = BFL · Tiny Aya multilingual gossip = Cohere ·
built with Codex = OpenAI. Badges: 🔌 Off-the-Grid · 🦙 Llama Champion · 🎨 Off-Brand · 🤖 Best Agent.

Submission: demo video _TODO_ · social post _TODO_ · GitHub https://github.com/siddhant-rajhans/smol-town
