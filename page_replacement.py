"""
page_replacement.py
====================
Implements four classic page replacement algorithms:
  1. FIFO  - First In, First Out
  2. LRU   - Least Recently Used
  3. Optimal - Best possible replacement (uses future knowledge)
  4. LFU   - Least Frequently Used

CONCEPT (for beginners):
  - Pages: numbered chunks of a program that live in virtual memory.
  - Frames: slots in physical RAM that can hold one page at a time.
  - Page Fault: when a needed page is NOT in any frame → OS must load it.
  - Page Hit  : when a needed page IS already in a frame → no loading needed.

Each algorithm decides WHICH page to evict when all frames are full and a new
page needs to be loaded. Different strategies give different fault counts.
"""

import time
from collections import deque, Counter


# ---------------------------------------------------------------------------
# Helper: build a standardised result dictionary
# ---------------------------------------------------------------------------
def _make_result(algorithm: str, steps: list, hits: int, faults: int,
                 exec_ms: float) -> dict:
    """
    Returns a standard result dict used by every algorithm.
    
    Parameters
    ----------
    algorithm : str   - Algorithm name (e.g. "FIFO")
    steps     : list  - Step-by-step trace (see format below)
    hits      : int   - Total page hits
    faults    : int   - Total page faults
    exec_ms   : float - Execution time in milliseconds
    
    Each step in 'steps' looks like:
    {
        "step"      : 1,          # step number (1-based)
        "page"      : 3,          # page being accessed
        "frames"    : [3, 1, -1], # frame contents (-1 = empty)
        "fault"     : True,       # True if page fault occurred
        "replaced"  : None,       # page evicted (None if no eviction)
        "hit"       : False,      # True if page hit occurred
    }
    """
    total = hits + faults
    return {
        "algorithm":      algorithm,
        "steps":          steps,
        "hits":           hits,
        "faults":         faults,
        "total":          total,
        "hit_ratio":      round(hits  / total, 4) if total > 0 else 0.0,
        "fault_ratio":    round(faults / total, 4) if total > 0 else 0.0,
        "execution_time_ms": round(exec_ms, 4),
    }


# ---------------------------------------------------------------------------
# 1. FIFO — First In, First Out
# ---------------------------------------------------------------------------
def run_fifo(pages: list[int], num_frames: int) -> dict:
    """
    FIFO Page Replacement Algorithm.

    IDEA: The page that arrived FIRST in memory is the first to be replaced.
    Think of frames as a queue — oldest page leaves first.

    Parameters
    ----------
    pages      : list of page numbers to access (the reference string)
    num_frames : number of physical memory frames available

    Returns
    -------
    Standard result dictionary (see _make_result)
    """
    start = time.perf_counter()

    frames   = []          # current pages in memory (ordered by arrival)
    queue    = deque()     # tracks insertion order for FIFO eviction
    steps    = []
    hits     = 0
    faults   = 0

    for i, page in enumerate(pages):
        replaced = None
        fault    = False
        hit      = False

        if page in frames:
            # PAGE HIT — page already in memory, nothing to do
            hit  = True
            hits += 1
        else:
            # PAGE FAULT — need to load the page
            fault  = True
            faults += 1

            if len(frames) < num_frames:
                # Frames not full yet — just add the page
                frames.append(page)
                queue.append(page)
            else:
                # Frames full — evict the oldest page (front of queue)
                replaced = queue.popleft()
                frames[frames.index(replaced)] = page
                queue.append(page)

        # Pad frame list to fixed width with -1 (represents empty slot)
        frame_snapshot = frames[:] + [-1] * (num_frames - len(frames))

        steps.append({
            "step":     i + 1,
            "page":     page,
            "frames":   frame_snapshot,
            "fault":    fault,
            "hit":      hit,
            "replaced": replaced,
        })

    exec_ms = (time.perf_counter() - start) * 1000
    return _make_result("FIFO", steps, hits, faults, exec_ms)


# ---------------------------------------------------------------------------
# 2. LRU — Least Recently Used
# ---------------------------------------------------------------------------
def run_lru(pages: list[int], num_frames: int) -> dict:
    """
    LRU Page Replacement Algorithm.

    IDEA: Replace the page that was used LEAST RECENTLY.
    Uses the past — pages not used for a long time are likely not needed soon.

    Parameters
    ----------
    pages      : list of page numbers to access
    num_frames : number of physical memory frames

    Returns
    -------
    Standard result dictionary
    """
    start = time.perf_counter()

    frames        = []    # current pages in memory
    recent_order  = []    # tracks recency (index 0 = least recently used)
    steps         = []
    hits          = 0
    faults        = 0

    for i, page in enumerate(pages):
        replaced = None
        fault    = False
        hit      = False

        if page in frames:
            # PAGE HIT — update recency: move page to most-recently-used end
            hit  = True
            hits += 1
            recent_order.remove(page)
            recent_order.append(page)
        else:
            # PAGE FAULT
            fault  = True
            faults += 1

            if len(frames) < num_frames:
                # Frames not full — just add
                frames.append(page)
                recent_order.append(page)
            else:
                # Evict the least recently used page (index 0)
                replaced = recent_order.pop(0)
                frames[frames.index(replaced)] = page
                recent_order.append(page)

        frame_snapshot = frames[:] + [-1] * (num_frames - len(frames))

        steps.append({
            "step":     i + 1,
            "page":     page,
            "frames":   frame_snapshot,
            "fault":    fault,
            "hit":      hit,
            "replaced": replaced,
        })

    exec_ms = (time.perf_counter() - start) * 1000
    return _make_result("LRU", steps, hits, faults, exec_ms)


# ---------------------------------------------------------------------------
# 3. Optimal Page Replacement (Bélády's Algorithm)
# ---------------------------------------------------------------------------
def run_optimal(pages: list[int], num_frames: int) -> dict:
    """
    Optimal (Bélády's) Page Replacement Algorithm.

    IDEA: Replace the page that will NOT be used for the LONGEST time in
    the future. This requires knowing the entire future reference string
    upfront — that's why it's called "optimal" (best possible, but not
    implementable in real OS; used as a benchmark).

    Parameters
    ----------
    pages      : list of page numbers to access
    num_frames : number of physical memory frames

    Returns
    -------
    Standard result dictionary
    """
    start = time.perf_counter()

    frames = []
    steps  = []
    hits   = 0
    faults = 0

    for i, page in enumerate(pages):
        replaced = None
        fault    = False
        hit      = False

        if page in frames:
            hit  = True
            hits += 1
        else:
            fault  = True
            faults += 1

            if len(frames) < num_frames:
                frames.append(page)
            else:
                # Look into the future for each frame page
                # Find next use index; if never used again → infinity
                future = pages[i + 1:]  # pages after current position
                farthest_idx  = -1
                page_to_evict = None

                for fp in frames:
                    if fp in future:
                        next_use = future.index(fp)
                    else:
                        next_use = float('inf')   # never used again → evict this

                    if next_use > farthest_idx:
                        farthest_idx  = next_use
                        page_to_evict = fp

                replaced = page_to_evict
                frames[frames.index(replaced)] = page

        frame_snapshot = frames[:] + [-1] * (num_frames - len(frames))

        steps.append({
            "step":     i + 1,
            "page":     page,
            "frames":   frame_snapshot,
            "fault":    fault,
            "hit":      hit,
            "replaced": replaced,
        })

    exec_ms = (time.perf_counter() - start) * 1000
    return _make_result("Optimal", steps, hits, faults, exec_ms)


# ---------------------------------------------------------------------------
# 4. LFU — Least Frequently Used
# ---------------------------------------------------------------------------
def run_lfu(pages: list[int], num_frames: int) -> dict:
    """
    LFU Page Replacement Algorithm.

    IDEA: Replace the page that has been used the FEWEST times overall.
    Pages used rarely in the past are considered less important.
    Tie-breaking: if two pages have equal frequency, evict the one that
    arrived FIRST (FIFO tie-breaking) for deterministic behaviour.

    Parameters
    ----------
    pages      : list of page numbers to access
    num_frames : number of physical memory frames

    Returns
    -------
    Standard result dictionary
    """
    start = time.perf_counter()

    frames     = []          # pages currently in memory
    freq       = Counter()   # access frequency for each page
    order      = []          # insertion order for tie-breaking (FIFO)
    steps      = []
    hits       = 0
    faults     = 0

    for i, page in enumerate(pages):
        replaced = None
        fault    = False
        hit      = False

        # Always increment frequency regardless of hit or fault
        freq[page] += 1

        if page in frames:
            hit  = True
            hits += 1
        else:
            fault  = True
            faults += 1

            if len(frames) < num_frames:
                frames.append(page)
                order.append(page)
            else:
                # Find page with minimum frequency; use insertion order for ties
                min_freq   = min(freq[f] for f in frames)
                candidates = [f for f in order if freq[f] == min_freq]
                # candidates are in insertion order → pick the first (oldest)
                replaced   = candidates[0]

                idx = frames.index(replaced)
                frames[idx] = page
                order.remove(replaced)
                order.append(page)

        frame_snapshot = frames[:] + [-1] * (num_frames - len(frames))

        steps.append({
            "step":     i + 1,
            "page":     page,
            "frames":   frame_snapshot,
            "fault":    fault,
            "hit":      hit,
            "replaced": replaced,
        })

    exec_ms = (time.perf_counter() - start) * 1000
    return _make_result("LFU", steps, hits, faults, exec_ms)


# ---------------------------------------------------------------------------
# Compare all four algorithms on the same input
# ---------------------------------------------------------------------------
def compare_all(pages: list[int], num_frames: int) -> list[dict]:
    """
    Run all four algorithms and return a list of their result dicts.
    Used by the Algorithm Comparison dashboard page.

    Parameters
    ----------
    pages      : reference string
    num_frames : number of frames

    Returns
    -------
    List of 4 result dicts (FIFO, LRU, Optimal, LFU)
    """
    results = [
        run_fifo(pages, num_frames),
        run_lru(pages, num_frames),
        run_optimal(pages, num_frames),
        run_lfu(pages, num_frames),
    ]
    return results


# ---------------------------------------------------------------------------
# Quick self-test (run this file directly: python page_replacement.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Classic textbook test: Silberschatz OS textbook example
    # Reference string: 7,0,1,2,0,3,0,4,2,3,0,3,0,3,2,1,2,0,1,7,0,1
    # Frames: 3
    # Expected FIFO faults: 15
    test_pages  = [7,0,1,2,0,3,0,4,2,3,0,3,0,3,2,1,2,0,1,7,0,1]
    test_frames = 3

    print("=" * 60)
    print(f"Test Reference String : {test_pages}")
    print(f"Number of Frames      : {test_frames}")
    print("=" * 60)

    for result in compare_all(test_pages, test_frames):
        print(f"\n{result['algorithm']}")
        print(f"  Faults    : {result['faults']}")
        print(f"  Hits      : {result['hits']}")
        print(f"  Hit Ratio : {result['hit_ratio']:.2%}")
        print(f"  Time (ms) : {result['execution_time_ms']}")
