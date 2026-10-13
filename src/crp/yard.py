"""Yard state during solving: stacks, moves, and the relocation counter.

Mirrors cpp_reference/simulator/ContainerYard.cpp and BayFloor.cpp, including the
look-ahead window (MaximumKnownContainer, GetTopContainerId, GetContainerId).
"""
from __future__ import annotations

from crp.instance import Instance

INT_MAX = 2_147_483_647  # C++ INT_MAX: the minimum of an empty stack


class Yard:
    """Live, changing copy of an instance."""

    def __init__(self, instance: Instance, alpha: float, hidden: str) -> None:
        if hidden not in ("max", "ignore"):
            raise ValueError(f"hidden must be 'max' or 'ignore', got {hidden!r}")
        self.stacks: list[list[int]] = [list(s) for s in instance.stacks]  # bottom -> top
        self.max_height = instance.max_height
        self.n_containers = instance.n_containers
        self.alpha = alpha
        self.hidden = hidden
        self.next_target = 1  # ID of the next container to retrieve
        self.relocations = 0
        self._stack_of = {c: i for i, s in enumerate(self.stacks) for c in s}

    def target_stack(self) -> int:
        """Index of the stack that holds the next target."""
        return self._stack_of[self.next_target]

    def last_visible(self) -> int:
        """Highest visible ID: int(next_target + alpha * N), rounded down like the C++."""
        return int(self.next_target + self.alpha * self.n_containers)

    def value(self, container: int) -> int:
        """What rules see for a container: its ID if visible, else the hidden value."""
        last = self.last_visible()
        if container <= last:
            return container
        return last + 1 if self.hidden == "max" else -1

    def top_value(self, stack: int) -> int:
        """Visible value of the top container (C++ GetTopContainerId)."""
        return self.value(self.stacks[stack][-1])

    def min_value(self, stack: int) -> int:
        """Smallest visible value in a stack, INT_MAX if empty. Ignore's -1 is not skipped."""
        return min(map(self.value, self.stacks[stack]), default=INT_MAX)

    def is_full(self, stack: int) -> bool:
        return len(self.stacks[stack]) >= self.max_height

    def is_done(self) -> bool:
        return self.next_target > self.n_containers

    def relocate(self, src: int, dst: int) -> None:
        """Move the top container of src onto dst; counts as one relocation."""
        if src == dst:
            raise ValueError(f"cannot relocate stack {src} onto itself")
        if not self.stacks[src]:
            raise ValueError(f"stack {src} is empty")
        if self.is_full(dst):
            raise ValueError(f"stack {dst} is full")
        container = self.stacks[src].pop()
        self.stacks[dst].append(container)
        self._stack_of[container] = dst
        self.relocations += 1

    def retrieve(self) -> None:
        """Remove the next target from the yard. It must be on top; not counted."""
        stack = self.target_stack()
        if self.stacks[stack][-1] != self.next_target:
            raise ValueError(f"container {self.next_target} is not on top of stack {stack}")
        self.stacks[stack].pop()
        del self._stack_of[self.next_target]
        self.next_target += 1
