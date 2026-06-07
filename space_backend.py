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


@spaces.GPU(duration=45)
def generate(system, user, num_predict=90, temperature=0.95):
    model = _model.to("cuda")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    ids = _tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                   return_tensors="pt", enable_thinking=False).to("cuda")
    out = model.generate(ids, max_new_tokens=num_predict, do_sample=True,
                         temperature=temperature, top_p=0.95)
    return _tok.decode(out[0][ids.shape[-1]:], skip_special_tokens=True).strip()


town.GENERATE = generate   # Smol Town now thinks with a local in-Space model
