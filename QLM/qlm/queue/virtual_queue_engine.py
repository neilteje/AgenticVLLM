from bidict import bidict
import uuid
from qlm.queue.virtual_queue import VirtualQueue
from qlm.queue.group import Group
from qlm.queue.request import Request
from qlm.scheduler.scheduler import Scheduler
import random
import os


class VirtualQueueEngine:
    """
    VirtualQueueEngine is the main class that manages the virtual queues and groups.
    """

    def __init__(self):
        """
        Initializes the VirtualQueueEngine with empty virtual queues, request to group mapping, group to virtual queue
        mapping, virtual queue to worker mapping, model-slo to group mapping and a scheduler.
        """
        self.vqs = []
        self.request_to_group = {}
        self.group_to_vq = {}
        self.vq_worker_bimap = bidict({})
        self.model_slo_group_bimap = bidict({})
        scheduler_policy = os.environ.get("QLM_SCHEDULER_POLICY", "edf").lower()
        self.scheduler = Scheduler(policy=scheduler_policy)

    def add_worker(self, worker):
        """
        Adds a worker to the virtual queue engine. Creates a new virtual queue associated with the worker.
        :param worker: Worker object
        """
        new_vq = VirtualQueue()
        self.vqs.append(new_vq)
        self.vq_worker_bimap[new_vq] = worker

    def _group_in_any_vq(self, group) -> bool:
        """Returns True if the group is currently registered in any virtual queue."""
        return any(group in vq.groups for vq in self.vqs)

    def add_request(self, request):
        """
        Adds a request to the virtual queue engine. If a group with the same model and slo exists, adds the request to
        the group. Otherwise, creates a new group and adds the request to the new group.
        :param request: Request object
        """
        if (request.model, request.slo) in self.model_slo_group_bimap:
            existing_group = self.model_slo_group_bimap[(request.model, request.slo)]
            existing_group.add_request(request)
            self.request_to_group[request] = existing_group
            # The group is removed from its VQ when it becomes empty (see pop_request).
            # If a new request arrives after that, we must re-insert it so the queue
            # loop can see it again via has_request(). Without this, all requests after
            # the first complete group cycle are silently dropped.
            if not self._group_in_any_vq(existing_group):
                vq_idx = random.choice(range(len(self.vqs)))
                self.vqs[vq_idx].add_group(existing_group)
        else:
            new_group = Group(request.model, request.slo)
            print("Adding new group with model and slo", request.model, request.slo)
            new_group.add_request(request)

            self.model_slo_group_bimap[(request.model, request.slo)] = new_group
            self.request_to_group[request] = new_group

            # Select a random virtual queue to add the group to
            vq_idx = random.choice(range(len(self.vqs)))
            self.vqs[vq_idx].add_group(new_group)

    def pop_request(self, worker):
        """
        Pops a request from the virtual queue associated with the worker. If the group is empty, pops the group from the
        virtual queue.
        :param worker: Worker object
        :return: Request object
        """
        vq = self.vq_worker_bimap.inv[worker]
        group = vq.get_head_group()
        request = group.pop_request()

        if len(group.requests) == 0:
            vq.pop_group()

        return request

    def has_request(self, worker):
        """
        Checks if the virtual queue associated with the worker has any requests.
        :param worker: Worker object
        :return: Boolean
        """
        vq = self.vq_worker_bimap.inv[worker]
        return len(vq.groups) > 0

    def get_queue_length(self) -> int:
        """
        Total number of requests currently in all virtual queues (waiting, not yet dispatched).
        Used for workload experiment metrics.
        """
        total = 0
        for vq in self.vqs:
            for group in vq.groups:
                total += len(group.requests)
        return total

    def reorder_vqs(self):
        """
        Reorders the virtual queues based on the scheduler. If the scheduler detects an SLO violation, reorders the virtual
        queues. Else, keeps the queues as is.
        """
        if self.scheduler.check_violation(self.vqs):
            self.vqs = self.scheduler.reorder(self.vqs)
