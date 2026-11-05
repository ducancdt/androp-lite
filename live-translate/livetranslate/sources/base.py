from __future__ import annotations

from typing import Iterator

import numpy as np


class AudioSource:
    """Giao diện nguồn âm thanh. ``frames()`` sinh các khối float32 mono 16 kHz cho đến khi hết."""

    name = "source"

    def frames(self) -> Iterator[np.ndarray]:  # pragma: no cover - interface
        raise NotImplementedError

    def close(self) -> None:
        pass
