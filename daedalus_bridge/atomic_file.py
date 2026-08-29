"""Atomic filesystem replacement shared by bridge storage owners."""
import os
import time


_REPLACE_ATTEMPTS = 5
_REPLACE_RETRY_DELAY = 0.02


def retry_sharing_violation(action):
    """Call `action`, retrying a transient sharing violation.

    Windows refuses to open or replace a file while any handle is open on it,
    and that handle need not be the bridge's; a scanner that opens a file the
    moment it appears is enough. It clears on its own within milliseconds, so
    without a retry the bridge answers 500 for a write that was about to
    succeed and discards data a caller already produced.

    Only PermissionError is retried. A write refused because the volume is
    read-only or the disk is full is not going to start working, and waiting
    on it would delay the error that explains what happened instead of fixing
    anything.

    `action` takes no arguments; a caller with its own arguments to pass
    wraps them in a closure, so every retried write shares this one policy
    rather than each growing its own copy of it.
    """
    remaining = _REPLACE_ATTEMPTS
    while True:
        remaining -= 1
        try:
            return action()
        except PermissionError:
            if not remaining:
                raise
            time.sleep(_REPLACE_RETRY_DELAY)


def replace_atomically(src, dst):
    """Publish `src` over `dst`, retrying a transient sharing violation."""
    retry_sharing_violation(lambda: os.replace(src, dst))
