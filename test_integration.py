"""Quick integration test — run with python3.11 test_integration.py"""
import sys
sys.path.insert(0, '.')

print("=" * 50)
print("Integration Test: All Modules")
print("=" * 50)

# 1. Test page replacement
from simulator.page_replacement import compare_all
results = compare_all([7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1], 3)
print("\n[1] Page Replacement Algorithms:")
for r in results:
    print(f"    {r['algorithm']:8s} faults={r['faults']:2d}  hits={r['hits']:2d}  hit%={r['hit_ratio']:.1%}")

# 2. Test address translation
from simulator.address_translation import batch_translate
tr = batch_translate([512, 768, 1300, 256, 512], 256, [2, 5, 7], 8, 4)
print(f"\n[2] Address Translation:")
print(f"    TLB Hits={tr['tlb_hits']}  Misses={tr['tlb_misses']}  Faults={tr['page_faults']}")

# 3. Test storage
from simulator.storage import init_db, save_simulation, get_history
init_db()
rid = save_simulation(results[0], [7,0,1,2,0,3,0,4,2,3])
df  = get_history()
print(f"\n[3] Storage:")
print(f"    Saved row ID={rid}, History rows={len(df)}")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
