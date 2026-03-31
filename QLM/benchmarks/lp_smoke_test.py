import time

from qlm.queue.group import Group
from qlm.queue.request import Request
from qlm.queue.virtual_queue import VirtualQueue
from qlm.scheduler.scheduler import Scheduler


def make_group(model: str, slo: int, num_requests: int) -> Group:
    group = Group(model=model, slo=slo)
    now = time.time()
    for idx in range(num_requests):
        group.add_request(
            Request(
                prompt=f"request-{idx}",
                model=model,
                slo=slo,
                insertion_time=now,
            )
        )
    return group


def main() -> None:
    print("Running LP scheduler smoke test with Gurobi")
    scheduler = Scheduler(policy="lp")

    vq = VirtualQueue()
    vq.add_group(make_group("unsloth/Llama-3.2-1B-Instruct", slo=2000, num_requests=5))
    vq.add_group(make_group("unsloth/Llama-3.2-1B-Instruct", slo=5000, num_requests=3))
    vq.add_group(make_group("unsloth/Llama-3.2-1B-Instruct", slo=4000, num_requests=4))

    reordered = scheduler.reorder([vq])
    total_groups = sum(len(queue.groups) for queue in reordered)

    if total_groups != 3:
        raise RuntimeError(f"Expected 3 groups after LP reorder, found {total_groups}")

    print("LP smoke test succeeded.")


if __name__ == "__main__":
    main()
