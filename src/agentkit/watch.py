from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from agentkit.lifecycle import render_reminder, sample_lifecycle


def watch_task(
    repo: Path,
    *,
    interval_seconds: float = 30.0,
    once: bool = False,
    output: Callable[[str], None] = print,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    while True:
        sample = sample_lifecycle(repo)
        output(render_reminder(sample))
        if once or sample.state in {"no_task", "completed", "blocked"}:
            return 0
        sleep(interval_seconds)
