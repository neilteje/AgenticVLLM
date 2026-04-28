from hyperagent import HyperAgent
from argparse import ArgumentParser
from hyperagent.tasks.github_issue_resolve import SWEBench
from hyperagent.continuum import build_continuum_llm_configs
import json
import os
import json
import subprocess

def get_args():
    parser = ArgumentParser()
    parser.add_argument("--split", type=str, default="verified")
    parser.add_argument("--output_folder", type=str, default="outputs/")
    parser.add_argument("--model_nick_name", type=str, default="claude-mini")
    parser.add_argument(
        "--backend",
        choices=["anthropic", "continuum"],
        default="anthropic",
        help="Use the original Anthropic config or a vLLM-Continuum server.",
    )
    parser.add_argument(
        "--continuum_base_url",
        type=str,
        default=os.environ.get("HYPERAGENT_CONTINUUM_BASE_URL",
                               "http://127.0.0.1:8000/v1"),
    )
    parser.add_argument(
        "--continuum_model",
        type=str,
        default=os.environ.get("HYPERAGENT_CONTINUUM_MODEL",
                               "Qwen/Qwen2.5-Coder-14B-Instruct"),
    )
    parser.add_argument(
        "--continuum_metrics_folder",
        type=str,
        default="results/hyperagent_continuum_metrics",
        help="Folder for per-instance live HyperAgent LLM metrics JSON.",
    )
    parser.add_argument(
        "--instance_ids",
        type=str,
        default="",
        help="Comma-separated SWE-bench instance ids to run, e.g. "
        "astropy__astropy-12907,django__django-10097.",
    )
    return parser.parse_args()


def build_anthropic_config():
    return {
        "name": "claude",
        "nav": [{
            "model": "claude-3-haiku-20240307",
            "api_key": os.environ.get("ANTHROPIC_API_KEY"),
            "stop_sequences": ["\nObservation:"],
            "base_url": "https://api.anthropic.com",
            "api_type": "anthropic",
        }],
        "edit": [{
            "model": "claude-3-5-sonnet-20240620",
            "api_key": os.environ.get("ANTHROPIC_API_KEY"),
            "stop_sequences": ["\nObservation:"],
            "price": [0.003, 0.015],
            "base_url": "https://api.anthropic.com",
            "api_type": "anthropic",
        }],
        "exec": [{
            "model": "claude-3-5-sonnet-20240620",
            "api_type": os.environ.get("ANTHROPIC_API_KEY"),
            "stop_sequences": ["\nObservation:"],
            "price": [0.003, 0.015],
            "base_url": "https://api.anthropic.com",
            "api_type": "anthropic",
        }],
        "plan": [{
            "model": "claude-3-5-sonnet-20240620",
            "api_type": os.environ.get("ANTHROPIC_API_KEY"),
            "price": [0.003, 0.015],
            "base_url": "https://api.anthropic.com",
            "api_type": "anthropic",
        }],
        "type": "patch"
    }


def selected_indices(task, instance_ids: str):
    requested = {item.strip() for item in instance_ids.split(",") if item.strip()}
    if not requested:
        return list(range(len(task)))

    indices = []
    seen = set()
    for idx in range(len(task)):
        _, _, instance_id, _ = task[idx]
        if instance_id in requested:
            indices.append(idx)
            seen.add(instance_id)

    missing = sorted(requested - seen)
    if missing:
        print(f"[warn] requested instance ids not found in split/images: {missing}")
    return indices


def main():
    args = get_args()
    os.makedirs(args.output_folder, exist_ok=True)
    if args.backend == "continuum":
        os.makedirs(args.continuum_metrics_folder, exist_ok=True)

    subprocess.run(["sudo", "rm", "-rf", "data/repos"])
    subprocess.run(["sudo", "mkdir", "-p", "data/repos"])
    subprocess.run(["sudo", "chmod", "777", "data/repos"])

    if args.backend == "continuum":
        os.environ["HYPERAGENT_CONTINUUM_ENABLED"] = "1"
        config = build_continuum_llm_configs(
            model=args.continuum_model,
            base_url=args.continuum_base_url,
        )
    else:
        config = build_anthropic_config()
    
    task = SWEBench(logdir="results/swe_bench", split=args.split)
    indices = selected_indices(task, args.instance_ids)
    print(f"[info] running {len(indices)} SWE-bench instance(s)")

    for idx in indices:
        repo_link, commit, instance_id, image_name = task[idx]
        success = False
        retry = 0
        while success != True:
            continuum_metrics_path = None
            if args.backend == "continuum":
                continuum_metrics_path = os.path.join(
                    args.continuum_metrics_folder,
                    f"{instance_id}.retry{retry}.metrics.json",
                )

            pilot = HyperAgent(
                repo_path=repo_link,
                commit=commit,
                language="python",
                clone_dir="data/repos",
                llm_configs=config,
                image_name=image_name,
                verbose=1,
                continuum_job_id=instance_id,
                continuum_metrics_path=continuum_metrics_path,
            )
            try:
                patch = task.run(pilot, idx)
            except Exception as e:
                print(e)
                patch = ""
            if len(patch) > 0:
                success = True
            retry += 1

            if retry > 3:
                break

        output_dict = {}

        output_dict["model_patch"] = patch
        output_dict["instance_id"] = instance_id
        output_dict["model_name_or_path"] = "hyperagent"

        output_file = os.path.join(args.output_folder, f"{args.model_nick_name}.jsonl")
        with open(output_file, "a+") as f:
            json.dump(output_dict, f)
            f.write("\n")

if __name__ == "__main__":
    main()