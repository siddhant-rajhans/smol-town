"""In-Space LLM backend for Smol Town.

Runs a small model in-process on ZeroGPU (no cloud APIs -> 🔌 Off-the-Grid).
Importing this module points town.GENERATE at the local model. Only used on a
Hugging Face Space (app.py imports it when SPACE_ID is set).
"""
import os

import spaces
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import town

MODEL_ID = os.getenv("SPACE_MODEL", "Qwen/Qwen3-4B")   # small + ZeroGPU-friendly; thinking disabled below

_tok = AutoTokenizer.from_pretrained(MODEL_ID)
_model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16)   # to GPU inside the call


@spaces.GPU(duration=60)
def generate(system, user, num_predict=120, temperature=0.95):
    try:
        model = _model.to("cuda")
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        text = _tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                        enable_thinking=False)
        inputs = _tok(text, return_tensors="pt").to("cuda")
        out = model.generate(**inputs, max_new_tokens=num_predict, do_sample=True,
                             temperature=temperature, top_p=0.95)
        gen = out[0][inputs["input_ids"].shape[-1]:]
        return _tok.decode(gen, skip_special_tokens=True).strip()
    except Exception as e:
        return "[GEN_ERROR] " + repr(e)[:400]


town.GENERATE = generate   # Smol Town now thinks with a local in-Space model
