"""Quick integration test — tests all simulator modules"""
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Integration Test: COA Virtual Memory Simulator")
print("=" * 60)

# 1. Test page replacement algorithms
from simulator.page_replacement import (
    run_fifo, run_lru, run_optimal, run_lfu, compare_all
)
ref_string = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
frames = 3
results = compare_all(ref_string, frames)

print("\n[1] Page Replacement Algorithms:")
for r in results:
    print(f"    {r['algorithm']:8s} | Faults: {r['faults']:2d} | Hits: {r['hits']:2d} | Hit Ratio: {r['hit_ratio']:.1%} | Time: {r['execution_time_ms']:.4f} ms")

assert len(results) == 4, "Expected 4 algorithms compared"
assert results[0]['faults'] == 15, f"Expected FIFO faults 15, got {results[0]['faults']}"
assert results[1]['faults'] == 12, f"Expected LRU faults 12, got {results[1]['faults']}"
assert results[2]['faults'] == 9,  f"Expected Optimal faults 9, got {results[2]['faults']}"

# 2. Test Page Table Management
from simulator.page_table import PageTable
pt = PageTable(num_pages=8, num_frames=3)
pt.sync_from_frames(frames_state=[2, 0, 1], all_known_pages=[0, 1, 2, 3, 4, 7])
entries = pt.get_all_entries()

print(f"\n[2] Page Table Management:")
print(f"    Total entries: {len(entries)}")
valid_entries = [e for e in entries if "1 (Valid)" in e["Valid Bit"]]
print(f"    Valid pages in RAM: {[e['Page Number'] for e in valid_entries]}")
assert len(valid_entries) == 3, f"Expected 3 valid pages, got {len(valid_entries)}"

# 3. Test Storage & SQLite Database
from simulator.storage import (
    init_db, save_simulation, save_all_results, get_history, get_summary_stats, export_csv
)
init_db()
row_id = save_simulation(results[0], ref_string)
df = get_history()
stats = get_summary_stats()
csv_bytes = export_csv(df)

print(f"\n[3] Storage & SQLite Persistence:")
print(f"    Saved simulation ID : {row_id}")
print(f"    Total history rows  : {len(df)}")
print(f"    CSV export size     : {len(csv_bytes)} bytes")
assert len(df) >= 1, "Expected at least 1 record in history"
assert len(csv_bytes) > 0, "Expected non-empty CSV bytes"

print("\n" + "=" * 60)
print("ALL MODULE TESTS PASSED SUCCESSFULLY! (100% OK)")
print("=" * 60)
