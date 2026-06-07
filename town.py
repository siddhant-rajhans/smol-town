"""Smol Town - a living town of tiny local AI minds. Build Small Hackathon (Thousand Token Wood).

Every villager is a small-model agent with a personality, a secret, and feelings about the others.
Self-contained (stdlib only). Watch the town come alive headless:
    python town.py 8
Point OLLAMA_BASE_URL at an Ollama serving a small model.
"""
import json
import os
import random
import re
import sys
import urllib.request
from dataclasses import dataclass, field

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
AGENT_MODEL = os.getenv("AGENT_MODEL", "qwen3:14b")     # later: MiniCPM5-1B (faster + OpenBMB pool)
AGENT_THINK = os.getenv("AGENT_THINK", "0") == "1"
MEMORY_WINDOW = int(os.getenv("MEMORY_WINDOW", "8"))
MAX_WORDS = int(os.getenv("MAX_WORDS", "30"))
TOWN = "Tinbury"


@dataclass
class Villager:
    name: str
    role: str
    traits: str
    secret: str
    feelings: str


CAST = [
    Villager("Mayor Doreen", "mayor", "pompous, image-obsessed, smiles too much",
             "the town treasury is empty - she blew it all on the marble fountain",
             "leans on Finn, distrusts the newcomer Hazel, finds Old Tom an embarrassment"),
    Villager("Finn", "baker", "sweet, anxious, desperate to please",
             "hopelessly in love with Marigold but too shy to say a single word",
             "adores Marigold, loyal to Mayor Doreen, intimidated by Bram"),
    Villager("Marigold", "florist", "fiery, proud, sharp-tongued",
             "still has feelings for her ex Bram and would rather die than admit it",
             "publicly feuding with Bram, totally oblivious to Finn's crush"),
    Villager("Bram", "blacksmith", "gruff, few words, secretly tender",
             "kept every letter Marigold ever wrote him, hidden in a tin box",
             "still pines for Marigold, quietly respects Old Tom"),
    Villager("Pip", "gossip kid", "nosy, gleeful, physically incapable of keeping a secret",
             "has overheard nearly everyone's secret and trades them like marbles",
             "idolizes Hazel, pesters everyone, terrified of Bram's hammer"),
    Villager("Hazel", "herbalist", "calm, watchful, quietly mysterious",
             "came to Tinbury to secretly find her birth mother, who may live here",
             "wary of Doreen, surprisingly gentle with Pip"),
    Villager("Old Tom", "philosopher-drunk", "blunt, funny, drops uncomfortable truths",
             "saw Doreen empty the treasury and blurts it out when he's had enough cider",
             "amused by all of them, fond of nobody and everybody at once"),
]

AVATAR = {"mayor": "🎩", "baker": "🥖", "florist": "🌹", "blacksmith": "🔨",
          "gossip kid": "🐤", "herbalist": "🌿", "philosopher-drunk": "🍺"}


def avatar(name):
    for v in CAST:
        if v.name == name:
            return AVATAR.get(v.role, "🧑")
    return "🧑"


PORTRAIT = {"Mayor Doreen": "mayor_doreen", "Finn": "finn", "Marigold": "marigold",
            "Bram": "bram", "Pip": "pip", "Hazel": "hazel", "Old Tom": "old_tom"}


OPENING_HOOK = ("The fountain fund is GONE - and Old Tom just stood up in the square "
                "and named the one who emptied it.")


@dataclass
class TownState:
    feed: list = field(default_factory=list)   # list of (speaker, text)
    tick: int = 0


def _ollama(system, user, temperature=0.95, num_predict=90):
    body = {"model": AGENT_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": num_predict, "top_p": 0.95}}
    if AGENT_MODEL.startswith("qwen3") or "minicpm" in AGENT_MODEL.lower():
        body["think"] = AGENT_THINK
    req = urllib.request.Request(OLLAMA_BASE_URL + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))["message"]["content"].strip()


GENERATE = _ollama   # swappable LLM backend; the HF Space overrides this with an in-process model


def _clean(name, text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)       # drop closed reasoning
    text = re.sub(r"<think>.*$", "", text, flags=re.S).strip()       # drop dangling reasoning
    text = next((ln.strip() for ln in text.split("\n") if ln.strip()), "")   # first real line
    text = re.sub(r'^["\']|["\']$', "", text).strip()               # strip wrapping quotes
    text = re.sub(rf"^{re.escape(name)}\s*[:\-]\s*", "", text, flags=re.I)   # strip "Name:" prefix
    return text


def _recent(state):
    lines = [f"{s}: {t}" for s, t in state.feed[-MEMORY_WINDOW:]]
    return "\n".join(lines) if lines else "(a quiet morning; nothing has happened yet)"


def act(state, villager):
    system = (f"You are {villager.name}, the {villager.role} in the small town of {TOWN}. "
              f"You are {villager.traits}. Your private secret: {villager.secret}. "
              f"How you feel about the others: {villager.feelings}. "
              f"Stay completely in character. Speak or act in ONE vivid line (max {MAX_WORDS} words). "
              f"You may react to others, spread gossip, confess, scheme, or stir up drama. "
              f"Do NOT narrate or use quotation marks - just speak or act as {villager.name}.")
    user = f"Recent happenings in {TOWN}:\n{_recent(state)}\n\nIt's your moment, {villager.name}. What do you do?"
    text = _clean(villager.name, GENERATE(system, user))
    state.feed.append((villager.name, text))
    return text


def _next_actor(state):
    if not state.feed:
        return random.choice(CAST)
    last_speaker, last_text = state.feed[-1]
    for v in CAST:                                       # someone named in the last line reacts
        if v.name != last_speaker and re.search(rf"\b{re.escape(v.name.split()[-1])}\b", last_text):
            if random.random() < 0.6:
                return v
    return random.choice([v for v in CAST if v.name != last_speaker])


def step(state):
    state.tick += 1
    return act(state, _next_actor(state))


def inject(state, event):
    state.feed.append(("📢", event))


def run(ticks=6):
    state = TownState()
    inject(state, OPENING_HOOK)
    print(f"=== {TOWN} (model: {AGENT_MODEL}) ===")
    print(f"📢: {state.feed[-1][1]}")
    for i in range(ticks):
        text = step(state)
        print(f"{state.feed[-1][0]}: {text}")
        if i == ticks // 2:
            inject(state, "Pip skids into the square waving a letter he definitely should not be holding.")
            print(f"📢: {state.feed[-1][1]}")
    return state


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 6)
