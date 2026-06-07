# Build Small Hackathon — Plan (Siddhant Rajhans / @SID2000)
> Deadline **Jun 15**. Org **CONFIRMED**. Priority: **CASH > GPU > compute**.

## Concept (LOCKED + VALIDATED): 🏘️ Smol Town — Thousand Token Wood
A living town of tiny local AI agents (personalities, secrets, relationships, memory) that produce emergent drama;
the user injects events ("god powers"). Runs offline.

✅ **PROVEN 2026-06-06** — a 7-beat run on live `qwen3:14b` produced in-character, interconnected drama (Old Tom
spilled the treasury secret; Marigold called her ex Bram "lover" and threw thorns; Bram silently pocketed them).
The atom works on real hardware.

## Why it wins (cash logic)
- The pitch IS the thesis-flex: "a whole town of minds, offline, on a gaming GPU."
- Inherently watchable / screenshot-able → Community Choice + likes + NVIDIA community-vote GPU.
- Proven winning patterns: council-of-minds (consilium 133), immersive game (Immersia won), AI-NPCs.
- Honest 4-pool stack + **Best Agent** near-lock.

## Cash pools (honest fit)
OpenBMB $10k (MiniCPM agents, central) · BFL $5k (FLUX villager portraits) · Cohere $5k (Tiny Aya multilingual
gossip) · OpenAI $10k + ChatGPT Pro (Codex) · TTW placement ≤$4k · Community Choice $2k · Best Agent $1k ·
Best Demo $1k · Bonus Quest Champion $2k.

## Badges
- [ ] 🔌 Off-the-Grid — all agents local, no cloud APIs
- [ ] 🦙 Llama Champion — serve via llama.cpp
- [ ] 🎨 Off-Brand — cozy custom town UI
- [ ] 🎯 Well-Tuned — fine-tune a small "villager" persona model / LoRA; publish to HF
- [ ] 📡 Sharing is Caring — publish the town's agent trace as a dataset
- [ ] 📓 Field Notes — blog the build

## Build status
- [x] Engine: personas + memory + tick loop + god-power injection (`town.py`) — VALIDATED on live model.
- [x] Gradio feed UI with god-powers (`app.py`).
- [ ] Run/iterate the UI (tunnel to Ollama, or run on sid-ml).
- [ ] Swap agents → **MiniCPM5-1B** (faster + OpenBMB pool); decide prompt style (stage-play vs strict dialogue).
- [ ] **FLUX** villager portraits (BFL) + cozy pixel UI (Off-Brand).
- [ ] **Tiny Aya** multilingual gossip (Cohere).
- [ ] Affinity/relationship tracking + day/night cycle for deeper emergence.
- [ ] Codex public repo; publish agent trace (Sharing); deploy **ZeroGPU** Space; demo video + blog + social.

## 30-sec demo script
Open town → click a few beats (drama escalates) → inject "a stranger arrives with a secret" → town erupts →
"every one of these minds is a small model, running offline on this laptop."

## Tuning notes (first run)
- Agents sometimes narrate first-person with quotes despite the rule → either tighten to dialogue-only, or lean
  into the charming "stage play" style. Decide during polish.
- Pacing is good; the name-mention actor bias creates real back-and-forth.

## Access
`ssh sidml` · Ollama `:11434` · models on `/mnt/shared` (root disk full).
