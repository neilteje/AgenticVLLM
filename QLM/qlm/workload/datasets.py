"""
Load prompt datasets for QLM workload experiments: ShareGPT (local) and Hugging Face.
Each loader returns a list of dicts with at least "prompt" (str) and optional "prompt_length", "response_length".
"""

import json
import os
from typing import Any, Callable, List, Optional

# Hugging Face datasets is optional at import; we use it only when loading HF datasets.
try:
    from datasets import load_dataset
    _HF_AVAILABLE = True
except ImportError:
    _HF_AVAILABLE = False


# Default path for ShareGPT relative to QLM project root (data/ or ../data from benchmarks).
SHAREGPT_DEFAULT_PATH = "data/ShareGPT_V3_unfiltered_cleaned_split.json"

# Map dataset name to (HF path, split, prompt extraction strategy).
SUPPORTED_DATASETS = {
    "sharegpt": None,  # local file
    "lmsys/lmsys-chat-1m": ("lmsys/lmsys-chat-1m", "train", "lmsys"),
    "allenai/WildChat-4.8M": ("allenai/WildChat-4.8M", "train", "wildchat"),
    "OpenAssistant/oasst1": ("OpenAssistant/oasst1", "train", "oasst"),
    "HuggingFaceH4/ultrachat_200k": ("HuggingFaceH4/ultrachat_200k", "train_sft", "ultrachat"),
}


def _sharegpt_path(project_dir: Optional[str] = None) -> str:
    if project_dir:
        return os.path.join(project_dir, "data", "ShareGPT_V3_unfiltered_cleaned_split.json")
    return os.path.join(os.environ.get("QLMPROJDIR", "."), "data", "ShareGPT_V3_unfiltered_cleaned_split.json")


def load_sharegpt(
    path: Optional[str] = None,
    project_dir: Optional[str] = None,
    min_turns: int = 2,
    max_samples: Optional[int] = None,
) -> List[dict]:
    """
    Load ShareGPT from local JSON. Each item is {"prompt": str, "prompt_length": int (chars)}.
    """
    if path is None:
        path = _sharegpt_path(project_dir)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"ShareGPT file not found: {path}. "
            "Download with: wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json -O data/ShareGPT_V3_unfiltered_cleaned_split.json"
        )
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for item in data:
        conv = item.get("conversations") or []
        if len(conv) < min_turns:
            continue
        # First user message as prompt (same as basic_test.py)
        first_msg = conv[0].get("value") or ""
        if not first_msg.strip():
            continue
        out.append({
            "prompt": first_msg,
            "prompt_length": len(first_msg),
        })
        if max_samples and len(out) >= max_samples:
            break
    return out


def _extract_lmsys(example: dict) -> Optional[dict]:
    # lmsys-chat-1m: structure may have "conversation" or similar; use first user turn.
    conv = example.get("conversation") or example.get("conversations") or []
    if isinstance(conv, str):
        return {"prompt": conv[:10000], "prompt_length": len(conv)}
    for turn in conv:
        role = (turn.get("role") or turn.get("from") or "").lower()
        content = turn.get("content") or turn.get("value") or ""
        if role in ("user", "human") and content.strip():
            return {"prompt": content[:10000], "prompt_length": len(content)}
    return None


def _extract_wildchat(example: dict) -> Optional[dict]:
    # WildChat: "conversation" list of {"role", "content"}
    conv = example.get("conversation") or []
    for turn in conv:
        if (turn.get("role") or "").lower() in ("user", "human"):
            content = turn.get("content") or ""
            if content.strip():
                return {"prompt": content[:10000], "prompt_length": len(content)}
    return None


def _extract_oasst(example: dict) -> Optional[dict]:
    # OpenAssistant: "messages" or "text" / "parent_id" tree
    msg = example.get("text") or example.get("message") or ""
    if msg.strip():
        return {"prompt": msg[:10000], "prompt_length": len(msg)}
    for key in ("messages", "conversation"):
        val = example.get(key)
        if isinstance(val, list) and val:
            first = val[0]
            content = first.get("text") or first.get("content") or first.get("value") or ""
            if content.strip():
                return {"prompt": content[:10000], "prompt_length": len(content)}
    return None


def _extract_ultrachat(example: dict) -> Optional[dict]:
    # UltraChat: "messages" list of list [role, content]
    messages = example.get("messages") or example.get("data") or []
    for m in messages:
        if isinstance(m, (list, tuple)) and len(m) >= 2:
            role, content = m[0], m[1]
            if (str(role).lower() in ("user", "human")) and str(content).strip():
                return {"prompt": str(content)[:10000], "prompt_length": len(str(content))}
        if isinstance(m, dict):
            role = (m.get("role") or m.get("from") or "").lower()
            content = m.get("content") or m.get("value") or ""
            if role in ("user", "human") and content.strip():
                return {"prompt": content[:10000], "prompt_length": len(content)}
    return None


_EXTRACTORS = {
    "lmsys": _extract_lmsys,
    "wildchat": _extract_wildchat,
    "oasst": _extract_oasst,
    "ultrachat": _extract_ultrachat,
}


def load_hf_dataset(
    dataset_name: str,
    split: str = "train",
    max_samples: Optional[int] = None,
    extractor: Optional[str] = None,
    trust_remote_code: bool = True,
) -> List[dict]:
    """
    Load a Hugging Face dataset and return list of {"prompt", "prompt_length"}.
    dataset_name: e.g. "lmsys/lmsys-chat-1m", "allenai/WildChat-4.8M".
    extractor: one of lmsys, wildchat, oasst, ultrachat; auto-detected from SUPPORTED_DATASETS if None.
    """
    if not _HF_AVAILABLE:
        raise RuntimeError("Install 'datasets' to use Hugging Face datasets: pip install datasets")
    info = SUPPORTED_DATASETS.get(dataset_name)
    if info is None:
        if dataset_name == "sharegpt":
            raise ValueError("Use load_sharegpt() for ShareGPT")
        extractor = extractor or "lmsys"
        hf_path = dataset_name
    else:
        hf_path, default_split, extractor = info
        split = split or default_split
    # Use slice to avoid loading huge splits when max_samples is set
    split_spec = f"{split}[:{max_samples}]" if max_samples else split
    ds = load_dataset(hf_path, split=split_spec, trust_remote_code=trust_remote_code)
    extract_fn = _EXTRACTORS.get(extractor or "lmsys", _extract_lmsys)
    out = []
    for ex in ds:
        row = extract_fn(ex) if callable(extract_fn) else extract_fn(ex)
        if row:
            out.append(row)
    return out


def get_prompts_from_dataset(
    dataset_name: str,
    project_dir: Optional[str] = None,
    max_samples: Optional[int] = None,
    prompt_length_bucket: Optional[str] = None,
) -> List[dict]:
    """
    Unified loader: "sharegpt" loads from local file; otherwise load from Hugging Face.
    prompt_length_bucket: "short" (<=200 chars), "medium" (200–1000), "long" (>1000), or None for all.
    """
    if dataset_name.lower() == "sharegpt":
        items = load_sharegpt(project_dir=project_dir, max_samples=max_samples)
    else:
        items = load_hf_dataset(dataset_name, max_samples=max_samples)

    if prompt_length_bucket:
        def keep(item: dict) -> bool:
            L = item.get("prompt_length") or len(item.get("prompt", ""))
            if prompt_length_bucket == "short":
                return L <= 200
            if prompt_length_bucket == "medium":
                return 200 < L <= 1000
            if prompt_length_bucket == "long":
                return L > 1000
            return True
        items = [x for x in items if keep(x)]
    return items
