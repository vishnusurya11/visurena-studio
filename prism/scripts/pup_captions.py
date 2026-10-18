"""Run BFL's FLUX 3 Klein prompt upsampler (PUP) over Prism requests -> whole captions.

Runs under ComfyUI's embedded python (CUDA torch + transformers with Qwen3.5); the project venv
has neither.  Free ComfyUI's models first (POST /free): the PUP is 18.8 GB in bf16.

    python_embeded/python.exe -s prism/scripts/pup_captions.py <requests.json> <captions.json> <pup dir>
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

GENERATE = {"max_new_tokens": 3584, "do_sample": False}
"""BFL's model card: greedy decoding, thinking off, 3584 new tokens."""


def messages(prompts: dict, request: str) -> list[dict]:
    return [{"role": "system", "content": prompts["t2i"]}, {"role": "user", "content": request}]


def pending_rows(rows: list[dict], done: list[dict]) -> list[dict]:
    held = {(d["style"], d["subject"]) for d in done}
    return [r for r in rows if (r["style"], r["subject"]) not in held]


def caption(model, processor, prompts: dict, request: str) -> str:
    import torch
    inputs = processor.apply_chat_template(messages(prompts, request), add_generation_prompt=True, tokenize=True,
                                           return_dict=True, return_tensors="pt",
                                           enable_thinking=False).to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, **GENERATE)
    return processor.decode(out[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def main(argv: list[str]) -> int:
    import torch
    from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration
    rows, out, pup = json.loads(Path(argv[0]).read_text(encoding="utf-8")), Path(argv[1]), Path(argv[2])
    done = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
    prompts = json.loads((pup / "system_prompts.json").read_text(encoding="utf-8"))
    processor = AutoProcessor.from_pretrained(pup)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(pup, dtype=torch.bfloat16, device_map="cuda").eval()
    for row in pending_rows(rows, done):
        started = time.monotonic()
        done.append({**row, "caption": caption(model, processor, prompts, row["request"]),
                     "seconds": round(time.monotonic() - started, 1)})
        out.write_text(json.dumps(done, indent=1, ensure_ascii=False), encoding="utf-8")
        print(row["style"], row["subject"], done[-1]["seconds"], "s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
