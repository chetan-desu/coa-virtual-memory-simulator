"""
app.py — Virtual Memory & Page Fault Simulator
==============================================
Design and Implementation of Virtual Memory and Page Fault Simulation
with Comparative Performance Analysis of Page Replacement Algorithms
Using Python and Streamlit.

Single-Page Interactive COA Dashboard.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import random
import time
import sys
import os
import textwrap

# Ensure package directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from simulator.page_replacement import (
        run_fifo, run_lru, run_optimal, run_lfu, compare_all
    )
    from simulator.page_table import PageTable
    from simulator.storage import (
        init_db, save_simulation, save_all_results,
        get_history, export_csv, clear_history, get_summary_stats
    )
except ModuleNotFoundError:
    from page_replacement import (
        run_fifo, run_lru, run_optimal, run_lfu, compare_all
    )
    from page_table import PageTable
    from storage import (
        init_db, save_simulation, save_all_results,
        get_history, export_csv, clear_history, get_summary_stats
    )

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Virtual Memory & Page Fault Simulator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling — Modern Dark Theme with Vibrant Accents
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

code, .mono {
    font-family: 'JetBrains Mono', monospace;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 60%, #0f172a 100%);
    border-right: 1px solid #30363d;
}

/* Main background */
.main {
    background-color: #0b0f19;
}

/* Metric Cards */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #161e2e, #1f293d);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
}

/* Gradient Titles */
.gradient-title {
    background: linear-gradient(90deg, #818cf8 0%, #38bdf8 50%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.1rem;
    margin-bottom: 0.2rem;
}

.gradient-subtitle {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 1.2rem;
}

/* Info Cards */
.glass-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.7));
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 14px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.25);
}

/* Frame Slot Boxes */
.frame-box {
    background: #111827;
    border: 2px solid #374151;
    border-radius: 10px;
    padding: 14px 10px;
    text-align: center;
    transition: all 0.25s ease;
}
.frame-box.empty {
    border-color: #27272a;
    background: #09090b;
}
.frame-box.hit {
    border-color: #10b981;
    background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
    box-shadow: 0 0 16px rgba(16, 185, 129, 0.35);
}
.frame-box.fault {
    border-color: #f43f5e;
    background: linear-gradient(135deg, #881337 0%, #4c0519 100%);
    box-shadow: 0 0 16px rgba(244, 63, 94, 0.35);
}
.frame-box.normal {
    border-color: #6366f1;
    background: #1e1b4b;
}

/* Badges */
.badge-hit {
    background: #059669;
    color: #ffffff;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 9999px;
    display: inline-block;
}
.badge-fault {
    background: #e11d48;
    color: #ffffff;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 9999px;
    display: inline-block;
}
.badge-ref {
    padding: 4px 10px;
    border-radius: 6px;
    font-weight: 600;
    font-family: monospace;
    font-size: 0.85rem;
    display: inline-block;
    margin: 2px;
}
.badge-ref-active {
    background: #6366f1;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.8);
    transform: scale(1.15);
}
.badge-ref-hit {
    background: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
}
.badge-ref-fault {
    background: #881337;
    color: #fda4af;
    border: 1px solid #e11d48;
}
.badge-ref-pending {
    background: #1f2937;
    color: #9ca3af;
    border: 1px solid #374151;
}

/* Section Divider */
.section-div {
    height: 1px;
    background: linear-gradient(90deg, transparent, #334155, #6366f1, #334155, transparent);
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def render_html(html_str: str):
    """Render raw HTML cleanly without markdown parser mangling it."""
    clean_html = " ".join(line.strip() for line in html_str.strip().splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(clean_html)
    else:
        st.markdown(clean_html, unsafe_allow_html=True)

def safe_styler_map(styler, func, subset=None):
    """Compatible with both modern Pandas 2.1+ (map) and older Pandas (applymap)."""
    if hasattr(styler, "map"):
        return styler.map(func, subset=subset)
    return styler.applymap(func, subset=subset)

def parse_reference_string(raw: str) -> list[int]:
    """Parse comma or space separated numbers into list of ints."""
    clean = raw.replace(",", " ").replace("-", " ")
    parts = clean.split()
    return [int(p) for p in parts if p.strip().isdigit()]

def generate_random_workload(length: int, max_page: int, locality: bool = True) -> list[int]:
    """Generate realistic page reference string with optional locality of reference."""
    if not locality:
        return [random.randint(0, max_page) for _ in range(length)]
    
    # Locality of reference simulation (cluster accesses)
    pages = []
    current_focus = random.randint(0, max_page)
    for _ in range(length):
        if random.random() < 0.35:
            # Shift focus to a new locality cluster
            current_focus = random.randint(0, max_page)
        # 75% chance to access near the current locality focus
        if random.random() < 0.75:
            delta = random.choice([-1, 0, 1])
            page = max(0, min(max_page, current_focus + delta))
        else:
            page = random.randint(0, max_page)
        pages.append(page)
    return pages

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
def init_state():
    init_db()
    defaults = {
        "ref_input": "7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1",
        "num_frames": 3,
        "selected_algo": "FIFO",
        "sim_result": None,
        "sim_step": 0,
        "is_playing": False,
        "compare_results": None,
        "last_run_pages": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ---------------------------------------------------------------------------
# Ensure initial simulation is computed
# ---------------------------------------------------------------------------
parsed_initial = parse_reference_string(st.session_state["ref_input"])
if st.session_state["sim_result"] is None and parsed_initial:
    algo_fn = {
        "FIFO": run_fifo, "LRU": run_lru, "Optimal": run_optimal, "LFU": run_lfu
    }[st.session_state["selected_algo"]]
    st.session_state["sim_result"] = algo_fn(parsed_initial, st.session_state["num_frames"])
    st.session_state["last_run_pages"] = parsed_initial

# ---------------------------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 10px 0;'>
        <div style='font-size: 2.6rem;'>🧠</div>
        <div style='font-size: 1.15rem; font-weight: 700; color: #818cf8;'>COA SIMULATOR</div>
        <div style='font-size: 0.78rem; color: #94a3b8;'>Virtual Memory & Page Replacement</div>
    </div>
    <div class="section-div"></div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Workload Configuration")

    # Preset selection
    preset = st.selectbox(
        "Standard Test Cases",
        [
            "Custom Input",
            "Silberschatz OS (Classic 7,0,1,2...)",
            "Bélády's Anomaly Case (1,2,3,4,1...)",
            "High Locality Pattern",
            "Sequential Scan Pattern",
        ]
    )

    if preset == "Silberschatz OS (Classic 7,0,1,2...)":
        st.session_state["ref_input"] = "7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1"
    elif preset == "Bélády's Anomaly Case (1,2,3,4,1...)":
        st.session_state["ref_input"] = "1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5"
    elif preset == "High Locality Pattern":
        st.session_state["ref_input"] = "2, 2, 3, 2, 3, 4, 2, 3, 7, 7, 8, 7, 8, 2, 3, 2"
    elif preset == "Sequential Scan Pattern":
        st.session_state["ref_input"] = "0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5"

    ref_str = st.text_area(
        "Page Reference String (space or comma separated):",
        value=st.session_state["ref_input"],
        height=75,
        help="The ordered sequence of virtual page numbers accessed by the process."
    )
    st.session_state["ref_input"] = ref_str

    # Random generator expander
    with st.expander("🎲 Random String Generator", expanded=False):
        rlen = st.slider("String Length", 5, 30, 18)
        rmax = st.slider("Max Page Number", 3, 12, 7)
        r_loc = st.checkbox("Simulate Locality of Reference", value=True)
        if st.button("Generate Random Workload", use_container_width=True):
            rand_pages = generate_random_workload(rlen, rmax, r_loc)
            st.session_state["ref_input"] = ", ".join(map(str, rand_pages))
            st.rerun()

    # Frame count slider
    num_frames = st.slider(
        "Physical Memory Frames",
        min_value=1,
        max_value=8,
        value=st.session_state["num_frames"],
        help="Number of page slots available simultaneously in physical RAM."
    )
    st.session_state["num_frames"] = num_frames

    # Algorithm selector
    algo_name = st.selectbox(
        "Page Replacement Algorithm",
        ["FIFO", "LRU", "Optimal", "LFU"],
        index=["FIFO", "LRU", "Optimal", "LFU"].index(st.session_state["selected_algo"]),
        help="Eviction strategy when physical memory is full."
    )
    st.session_state["selected_algo"] = algo_name

    # Action buttons
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        run_sim_btn = st.button("🚀 Run Simulator", type="primary", use_container_width=True)
    with col_btn2:
        compare_btn = st.button("⚡ Compare All 4", use_container_width=True)

    if run_sim_btn:
        pages = parse_reference_string(st.session_state["ref_input"])
        if not pages:
            st.error("Please enter at least one valid page number.")
        else:
            fn = {"FIFO": run_fifo, "LRU": run_lru, "Optimal": run_optimal, "LFU": run_lfu}[algo_name]
            res = fn(pages, num_frames)
            st.session_state["sim_result"] = res
            st.session_state["last_run_pages"] = pages
            st.session_state["sim_step"] = 0
            st.session_state["is_playing"] = False
            save_simulation(res, pages)
            st.success(f"Simulation executed with {algo_name}!")
            st.rerun()

    if compare_btn:
        pages = parse_reference_string(st.session_state["ref_input"])
        if not pages:
            st.error("Please enter at least one valid page number.")
        else:
            results = compare_all(pages, num_frames)
            st.session_state["compare_results"] = results
            st.session_state["last_run_pages"] = pages
            save_all_results(results, pages)
            st.success("All 4 algorithms simulated and saved to history!")
            st.rerun()

    st.markdown("<div class='section-div'></div>", unsafe_allow_html=True)
    st.caption("COA Project • Virtual Memory & Page Replacement • Streamlit App")

# ---------------------------------------------------------------------------
# MAIN HEADER
# ---------------------------------------------------------------------------
st.markdown("<div class='gradient-title'>Design & Implementation of Virtual Memory & Page Fault Simulator</div>", unsafe_allow_html=True)
st.markdown("<div class='gradient-subtitle'>Computer Organization and Architecture • Interactive Page Replacement & Physical Frame Analysis</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TOP LEVEL TABS (All on 1 Page)
# ---------------------------------------------------------------------------
tab_sim, tab_compare, tab_table, tab_history = st.tabs([
    "🔄 Interactive Simulation & Playback",
    "📊 Comparative Algorithm Analysis",
    "📋 Page Table & Memory Frames",
    "🕒 Simulation History & SQLite",
])

# ===========================================================================
# TAB 1: INTERACTIVE SIMULATION & PLAYBACK
# ===========================================================================
with tab_sim:
    current_result = st.session_state.get("sim_result")
    
    if current_result is None or not current_result.get("steps"):
        st.info("👈 Enter reference string and click **Run Simulator** in the sidebar to start.")
    else:
        steps = current_result["steps"]
        num_steps = len(steps)
        step_idx = min(st.session_state.get("sim_step", 0), num_steps - 1)
        curr_step = steps[step_idx]
        prev_step = steps[step_idx - 1] if step_idx > 0 else None

        # Playback auto-advance
        if st.session_state.get("is_playing", False):
            if step_idx < num_steps - 1:
                time.sleep(0.65)
                st.session_state["sim_step"] = step_idx + 1
                st.rerun()
            else:
                st.session_state["is_playing"] = False

        # --- Reference String Visual Ribbon ---
        st.markdown("#### 📜 Page Reference String Sequence")
        ribbon_html = ["<div style='display:flex; flex-wrap:wrap; gap:4px; align-items:center; margin-bottom:12px;'>"]
        for idx, s in enumerate(steps):
            p = s["page"]
            if idx == step_idx:
                ribbon_html.append(f"<span class='badge-ref badge-ref-active' title='Current Step {idx+1}: Page {p}'>▶ {p}</span>")
            elif idx < step_idx:
                badge_type = "badge-ref-hit" if s["hit"] else "badge-ref-fault"
                label = "HIT" if s["hit"] else "FAULT"
                ribbon_html.append(f"<span class='badge-ref {badge_type}' title='Step {idx+1}: Page {p} ({label})'>{p}</span>")
            else:
                ribbon_html.append(f"<span class='badge-ref badge-ref-pending' title='Step {idx+1}: Pending'>{p}</span>")
        ribbon_html.append("</div>")
        st.markdown("".join(ribbon_html), unsafe_allow_html=True)

        # --- Playback Controls Bar ---
        st.markdown("#### 🎮 Simulation Step Controls")
        c_reset, c_prev, c_play, c_next, c_slider = st.columns([1, 1, 1.2, 1, 3.5])
        
        with c_reset:
            if st.button("⏮️ Reset", use_container_width=True):
                st.session_state["sim_step"] = 0
                st.session_state["is_playing"] = False
                st.rerun()
        with c_prev:
            if st.button("◀️ Prev", use_container_width=True):
                if st.session_state["sim_step"] > 0:
                    st.session_state["sim_step"] -= 1
                    st.session_state["is_playing"] = False
                    st.rerun()
        with c_play:
            play_label = "⏸️ Pause" if st.session_state["is_playing"] else "▶️ Auto Play"
            if st.button(play_label, use_container_width=True, type="secondary"):
                st.session_state["is_playing"] = not st.session_state["is_playing"]
                st.rerun()
        with c_next:
            if st.button("Next ▶️", use_container_width=True, type="primary"):
                if st.session_state["sim_step"] < num_steps - 1:
                    st.session_state["sim_step"] += 1
                    st.session_state["is_playing"] = False
                    st.rerun()
        with c_slider:
            new_step = st.slider(
                "Jump directly to step",
                min_value=1,
                max_value=num_steps,
                value=step_idx + 1,
                label_visibility="collapsed"
            )
            if new_step - 1 != step_idx:
                st.session_state["sim_step"] = new_step - 1
                st.session_state["is_playing"] = False
                st.rerun()

        st.progress((step_idx + 1) / num_steps, text=f"Step {step_idx + 1} of {num_steps} ({(step_idx+1)/num_steps*100:.0f}%)")

        st.markdown("<div class='section-div'></div>", unsafe_allow_html=True)

        # --- Current Step Detail Cards & Visual Frames ---
        col_status, col_frames = st.columns([1.1, 2])

        with col_status:
            is_fault = curr_step["fault"]
            status_color = "#f43f5e" if is_fault else "#10b981"
            status_text = "PAGE FAULT ❌" if is_fault else "PAGE HIT ✅"
            badge_class = "badge-fault" if is_fault else "badge-hit"

            hits_so_far = sum(1 for s in steps[:step_idx + 1] if s["hit"])
            faults_so_far = sum(1 for s in steps[:step_idx + 1] if s["fault"])
            total_so_far = hits_so_far + faults_so_far
            curr_hit_ratio = (hits_so_far / total_so_far * 100) if total_so_far > 0 else 0.0

            render_html(f"""
            <div class='glass-card'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                    <span style='color:#94a3b8; font-size:0.85rem;'>Algorithm: <strong style='color:#818cf8;'>{current_result['algorithm']}</strong></span>
                    <span class='{badge_class}'>{status_text}</span>
                </div>
                <div style='font-size:0.9rem; color:#94a3b8;'>Requested Virtual Page:</div>
                <div style='font-size:3rem; font-weight:800; color:{status_color}; line-height:1.1;'>
                    Page {curr_step['page']}
                </div>
                <div style='margin-top:12px; font-size:0.88rem; color:#cbd5e1;'>
                    <div>• <strong>Memory Action:</strong> {
                        "Allocated into free frame" if curr_step['replaced'] is None and is_fault else
                        (f"Evicted Page {curr_step['replaced']} to load Page {curr_step['page']}" if is_fault else "Referenced existing frame in RAM")
                    }</div>
                    <div>• <strong>Evicted Page:</strong> {
                        f"<span style='color:#f87171; font-weight:700;'>Page {curr_step['replaced']}</span>" if curr_step['replaced'] is not None else "<span style='color:#64748b;'>None</span>"
                    }</div>
                </div>
                <div class="section-div" style="margin:12px 0;"></div>
                <div style='display:flex; justify-content:space-between; font-size:0.85rem;'>
                    <span>Cumulative Hits: <strong style='color:#34d399;'>{hits_so_far}</strong></span>
                    <span>Cumulative Faults: <strong style='color:#f87171;'>{faults_so_far}</strong></span>
                </div>
                <div style='font-size:0.82rem; color:#94a3b8; margin-top:4px;'>
                    Current Hit Ratio: <strong>{curr_hit_ratio:.1f}%</strong>
                </div>
            </div>
            """)

        with col_frames:
            st.markdown("#### 🗄️ Physical Memory Frames State")
            frames_state = curr_step["frames"]
            num_f = len(frames_state)
            
            f_cols = st.columns(num_f)
            prev_f_state = prev_step["frames"] if prev_step else [-1] * num_f

            for i, (col, page) in enumerate(zip(f_cols, frames_state)):
                with col:
                    changed = (page != prev_f_state[i])
                    is_current_target = (page == curr_step["page"])

                    if page == -1:
                        cls_name = "frame-box empty"
                        title_label = "EMPTY"
                        color = "#64748b"
                    elif is_current_target and curr_step["fault"]:
                        cls_name = "frame-box fault"
                        title_label = f"Page {page}"
                        color = "#f43f5e"
                    elif is_current_target and curr_step["hit"]:
                        cls_name = "frame-box hit"
                        title_label = f"Page {page}"
                        color = "#10b981"
                    else:
                        cls_name = "frame-box normal"
                        title_label = f"Page {page}"
                        color = "#a5b4fc"

                    render_html(f"""
                    <div class='{cls_name}'>
                        <div style='font-size:0.75rem; color:#94a3b8; margin-bottom:6px;'>Frame {i}</div>
                        <div style='font-size:1.3rem; font-weight:700; color:{color};'>{title_label}</div>
                        <div style='font-size:0.7rem; color:#64748b; margin-top:4px;'>
                            { "★ Just Loaded" if (changed and page != -1) else ("✓ In Memory" if page != -1 else "Unallocated") }
                        </div>
                    </div>
                    """)

            # Compact Page Table Preview for current step
            st.markdown("#### 📋 Page Table (Valid / Invalid Bits at Step)")
            all_workload_pages = sorted(list(set(s["page"] for s in steps)))
            pt = PageTable(max(all_workload_pages) + 1 if all_workload_pages else 8, num_f)
            pt.sync_from_frames(frames_state, all_workload_pages)
            pt_rows = pt.get_all_entries()
            
            # Filter to pages present in this workload
            workload_pt_rows = [r for r in pt_rows if r["Page Number"] in all_workload_pages]
            pt_df = pd.DataFrame(workload_pt_rows)

            def style_pt(val):
                if "1 (Valid)" in str(val):
                    return "color: #34d399; font-weight: bold; background-color: rgba(16,185,129,0.15);"
                elif "0 (Invalid)" in str(val):
                    return "color: #f87171; background-color: rgba(244,63,94,0.1);"
                return ""

            styled_pt = safe_styler_map(pt_df.style, style_pt, subset=["Valid Bit"])
            st.dataframe(styled_pt, use_container_width=True, hide_index=True)

        # --- Complete Step-by-Step Execution Trace ---
        st.markdown("<div class='section-div'></div>", unsafe_allow_html=True)
        st.markdown("### 📑 Full Step-by-Step Simulation Trace Table")
        
        table_records = []
        for s in steps:
            f_str = " | ".join(str(p) if p != -1 else "—" for p in s["frames"])
            table_records.append({
                "Step": s["step"],
                "Page Accessed": s["page"],
                "Physical Frames [0..N-1]": f_str,
                "Result": "🔴 FAULT" if s["fault"] else "🟢 HIT",
                "Replaced Page": f"Page {s['replaced']}" if s["replaced"] is not None else "None",
            })
        
        full_df = pd.DataFrame(table_records)

        def highlight_trace(row):
            if row["Step"] == curr_step["step"]:
                return ["background-color: #312e81; font-weight: bold;"] * len(row)
            elif "FAULT" in row["Result"]:
                return ["background-color: #1e131d;"] * len(row)
            else:
                return ["background-color: #0b1e19;"] * len(row)

        st.dataframe(
            full_df.style.apply(highlight_trace, axis=1),
            use_container_width=True,
            hide_index=True,
            height=300
        )

# ===========================================================================
# TAB 2: COMPARATIVE ALGORITHM ANALYSIS
# ===========================================================================
with tab_compare:
    st.markdown("### 📊 Comparative Performance Analysis of All 4 Algorithms")
    st.markdown("Evaluates **FIFO**, **LRU**, **Optimal**, and **LFU** on the identical page reference string and frame count.")

    pages_to_compare = parse_reference_string(st.session_state["ref_input"])
    frames_to_compare = st.session_state["num_frames"]

    if not pages_to_compare:
        st.warning("Please configure a valid page reference string in the sidebar.")
    else:
        # Compute comparison results if not already computed for this exact workload
        if (
            st.session_state["compare_results"] is None or
            st.session_state.get("last_run_pages") != pages_to_compare
        ):
            comp_res = compare_all(pages_to_compare, frames_to_compare)
            st.session_state["compare_results"] = comp_res
            st.session_state["last_run_pages"] = pages_to_compare
        else:
            comp_res = st.session_state["compare_results"]

        # Metric cards row
        m_cols = st.columns(4)
        algo_palette = {"FIFO": "#f43f5e", "LRU": "#38bdf8", "Optimal": "#34d399", "LFU": "#fbbf24"}
        min_faults = min(r["faults"] for r in comp_res)

        for col, r in zip(m_cols, comp_res):
            aname = r["algorithm"]
            color = algo_palette.get(aname, "#818cf8")
            is_best = (r["faults"] == min_faults)
            best_tag = "<span style='color:#34d399; font-size:0.75rem; font-weight:700;'>★ BEST</span>" if is_best else ""

            card_html = (
                f"<div class='glass-card' style='border-top: 4px solid {color};'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>"
                f"<span style='font-size:1.3rem; font-weight:800; color:{color};'>{aname}</span>"
                f"{best_tag}"
                f"</div>"
                f"<div style='height:1px; background:#334155; margin:8px 0;'></div>"
                f"<div style='display:flex; justify-content:space-between; margin:4px 0;'><span style='color:#94a3b8;'>Page Faults:</span><strong style='color:#f87171;'>{r['faults']}</strong></div>"
                f"<div style='display:flex; justify-content:space-between; margin:4px 0;'><span style='color:#94a3b8;'>Page Hits:</span><strong style='color:#34d399;'>{r['hits']}</strong></div>"
                f"<div style='display:flex; justify-content:space-between; margin:4px 0;'><span style='color:#94a3b8;'>Hit Ratio:</span><strong style='color:#60a5fa;'>{r['hit_ratio']:.1%}</strong></div>"
                f"<div style='display:flex; justify-content:space-between; margin:4px 0;'><span style='color:#94a3b8;'>Fault Ratio:</span><strong style='color:#f43f5e;'>{r['fault_ratio']:.1%}</strong></div>"
                f"<div style='display:flex; justify-content:space-between; margin:4px 0;'><span style='color:#94a3b8;'>Exec Time:</span><span style='font-family:monospace; color:#cbd5e1;'>{r['execution_time_ms']:.3f} ms</span></div>"
                f"</div>"
            )
            with col:
                render_html(card_html)

        st.markdown("<div class='section-div'></div>", unsafe_allow_html=True)

        # Plotly Charts Row 1: Bar Chart & Fault Distribution Donut
        c_chart1, c_chart2 = st.columns([1.5, 1])

        with c_chart1:
            names = [r["algorithm"] for r in comp_res]
            fault_vals = [r["faults"] for r in comp_res]
            hit_vals = [r["hits"] for r in comp_res]

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="Page Faults",
                x=names,
                y=fault_vals,
                marker_color="#f43f5e",
                text=fault_vals,
                textposition="auto"
            ))
            fig_bar.add_trace(go.Bar(
                name="Page Hits",
                x=names,
                y=hit_vals,
                marker_color="#10b981",
                text=hit_vals,
                textposition="auto"
            ))
            fig_bar.update_layout(
                title="Page Faults vs. Page Hits by Algorithm",
                barmode="group",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#111827",
                font=dict(color="#e2e8f0"),
                height=330,
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_chart2:
            fig_donut = go.Figure(go.Pie(
                labels=names,
                values=fault_vals,
                hole=0.55,
                marker=dict(colors=[algo_palette[n] for n in names]),
                textinfo="label+value",
                hovertemplate="%{label}: %{value} faults (%{percent})<extra></extra>"
            ))
            fig_donut.update_layout(
                title="Fault Distribution Share",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                height=330,
                margin=dict(l=20, r=20, t=50, b=20),
                showlegend=False
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        # Plotly Charts Row 2: Radar Chart & Frame Sensitivity Curve
        c_radar, c_sens = st.columns([1, 1.5])

        with c_radar:
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[r["hit_ratio"] * 100 for r in comp_res],
                theta=names,
                fill="toself",
                name="Hit Ratio %",
                line=dict(color="#38bdf8", width=2),
                fillcolor="rgba(56, 189, 248, 0.25)"
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[r["fault_ratio"] * 100 for r in comp_res],
                theta=names,
                fill="toself",
                name="Fault Ratio %",
                line=dict(color="#f43f5e", width=2),
                fillcolor="rgba(244, 63, 94, 0.25)"
            ))
            fig_radar.update_layout(
                title="Performance Radar (Hit % vs Fault %)",
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], color="#94a3b8"),
                    bgcolor="#111827"
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                height=340,
                margin=dict(l=30, r=30, t=50, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with c_sens:
            # Multi-frame sensitivity analysis (1 to 8 frames)
            frame_axis = list(range(1, 9))
            fn_map = {"FIFO": run_fifo, "LRU": run_lru, "Optimal": run_optimal, "LFU": run_lfu}
            sensitivity_records = {algo: [] for algo in names}

            for f_count in frame_axis:
                for algo in names:
                    fault_count = fn_map[algo](pages_to_compare, f_count)["faults"]
                    sensitivity_records[algo].append(fault_count)

            fig_sens = go.Figure()
            for algo in names:
                fig_sens.add_trace(go.Scatter(
                    x=frame_axis,
                    y=sensitivity_records[algo],
                    mode="lines+markers",
                    name=algo,
                    line=dict(color=algo_palette[algo], width=2.5),
                    marker=dict(size=7)
                ))
            fig_sens.add_vline(
                x=frames_to_compare,
                line_dash="dash",
                line_color="#a855f7",
                annotation_text=f"Current: {frames_to_compare} Frames"
            )
            fig_sens.update_layout(
                title="Fault Sensitivity Curve: Faults vs. Frame Allocation (1 to 8 Frames)",
                xaxis_title="Physical Frames Allocated",
                yaxis_title="Total Page Faults",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#111827",
                font=dict(color="#e2e8f0"),
                height=340,
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_sens, use_container_width=True)

        # Comparison DataFrame
        st.markdown("#### 📋 Detailed Comparative Metrics Table")
        comp_summary_df = pd.DataFrame([
            {
                "Algorithm": r["algorithm"],
                "Total Accesses": r["total"],
                "Page Hits": r["hits"],
                "Page Faults": r["faults"],
                "Hit Ratio": f"{r['hit_ratio']:.2%}",
                "Fault Ratio": f"{r['fault_ratio']:.2%}",
                "Execution Time (ms)": f"{r['execution_time_ms']:.4f}",
                "Efficiency Ranking": "⭐ #1 (Optimal)" if r["algorithm"] == "Optimal" else (
                    "★ Best Practical" if r["faults"] == min(x["faults"] for x in comp_res if x["algorithm"] != "Optimal") else "Standard"
                ),
            }
            for r in comp_res
        ])
        st.dataframe(comp_summary_df, use_container_width=True, hide_index=True)

# ===========================================================================
# TAB 3: PAGE TABLE & MEMORY FRAMES
# ===========================================================================
with tab_table:
    st.markdown("### 📋 Page Table Management & Memory Mapping")
    st.markdown("Demonstrates how the Operating System's Page Table maintains Virtual Page Number (VPN) to Physical Frame Number (PFN) mapping along with the Valid/Invalid bit.")

    current_result = st.session_state.get("sim_result")
    if current_result is None:
        st.info("Run a simulation first to inspect the dynamic page table state.")
    else:
        steps = current_result["steps"]
        num_s = len(steps)
        pt_slider_val = st.slider("Inspect Page Table at Step:", 1, num_s, num_s, key="tab3_pt_slider")
        target_step = steps[pt_slider_val - 1]

        all_unique_pages = sorted(list(set(s["page"] for s in steps)))
        max_page_val = max(all_unique_pages) if all_unique_pages else 8
        pt_inst = PageTable(max_page_val + 1, len(target_step["frames"]))
        pt_inst.sync_from_frames(target_step["frames"], all_unique_pages)

        c_pt_left, c_pt_right = st.columns([1.2, 1])

        with c_pt_left:
            st.markdown(f"#### Page Table Snapshot at Step {pt_slider_val}")
            st.caption(f"Accessing Page {target_step['page']} • Event: {'🔴 PAGE FAULT' if target_step['fault'] else '🟢 PAGE HIT'}")

            table_entries = [r for r in pt_inst.get_all_entries() if r["Page Number"] in all_unique_pages]
            df_pt_inspect = pd.DataFrame(table_entries)

            def highlight_pt_inspect(val):
                if "1 (Valid)" in str(val):
                    return "color: #10b981; font-weight: bold; background-color: rgba(16, 185, 129, 0.15);"
                elif "0 (Invalid)" in str(val):
                    return "color: #f43f5e; background-color: rgba(244, 63, 94, 0.1);"
                return ""

            st.dataframe(
                safe_styler_map(df_pt_inspect.style, highlight_pt_inspect, subset=["Valid Bit"]),
                use_container_width=True,
                hide_index=True
            )

        with c_pt_right:
            st.markdown("#### Physical Memory Frames Content")
            for f_idx, pg in enumerate(target_step["frames"]):
                is_accessed = (pg == target_step["page"])
                border_clr = "#10b981" if is_accessed and target_step["hit"] else ("#f43f5e" if is_accessed else "#3b82f6")
                
                if pg != -1:
                    render_html(f"""
                    <div style='background:#111827; border-left: 5px solid {border_clr}; border-radius:8px; padding:12px 16px; margin-bottom:8px;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <strong style='color:#e2e8f0; font-size:1.05rem;'>Physical Frame {f_idx}</strong>
                            <span style='background:#1e293b; color:#38bdf8; font-size:0.8rem; padding:2px 8px; border-radius:4px;'>Page {pg}</span>
                        </div>
                        <div style='font-size:0.78rem; color:#94a3b8; margin-top:4px;'>
                            { "Currently Referenced" if is_accessed else "Allocated & Valid in RAM" }
                        </div>
                    </div>
                    """)
                else:
                    render_html(f"""
                    <div style='background:#09090b; border-left: 5px solid #4b5563; border-radius:8px; padding:12px 16px; margin-bottom:8px;'>
                        <strong style='color:#64748b;'>Physical Frame {f_idx}</strong> — <span style='color:#71717a;'>[ Free / Unallocated ]</span>
                    </div>
                    """)

        st.markdown("<div class='section-div'></div>", unsafe_allow_html=True)

        # Temporal chart of valid pages in physical memory
        valid_trend = [sum(1 for p in s["frames"] if p != -1) for s in steps]
        fig_valid = go.Figure()
        fig_valid.add_trace(go.Scatter(
            x=list(range(1, num_s + 1)),
            y=valid_trend,
            mode="lines+markers",
            name="Pages in Memory",
            line=dict(color="#38bdf8", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.15)"
        ))
        fig_valid.add_vline(x=pt_slider_val, line_dash="dash", line_color="#f43f5e", annotation_text=f"Step {pt_slider_val}")
        fig_valid.update_layout(
            title="Physical Memory Frame Occupancy Over Time",
            xaxis_title="Step Number",
            yaxis_title="Allocated Frames Count",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#111827",
            font=dict(color="#e2e8f0"),
            height=260,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_valid, use_container_width=True)

# ===========================================================================
# TAB 4: SIMULATION HISTORY & SQLITE
# ===========================================================================
with tab_history:
    st.markdown("### 🕒 Simulation History Database (SQLite)")
    st.markdown("Persists all simulation runs, allowing historical evaluation, filtering, and CSV export.")

    hist_df = get_history()

    if hist_df.empty:
        st.info("No past simulations stored in SQLite. Run a simulation to populate records!")
    else:
        # Quick stats cards
        stats = get_summary_stats()
        hc1, hc2, hc3, hc4 = st.columns(4)
        hc1.metric("Total Records Saved", stats["total_runs"])
        
        best_algo_name = max(
            stats["by_algorithm"].items(),
            key=lambda x: x[1]["avg_hit_ratio"],
            default=("N/A", {"avg_hit_ratio": 0})
        )[0]
        hc2.metric("Highest Avg Hit Ratio", best_algo_name)
        
        most_used = max(
            stats["by_algorithm"].items(),
            key=lambda x: x[1]["run_count"],
            default=("N/A", {"run_count": 0})
        )[0]
        hc3.metric("Most Tested Algorithm", most_used)
        hc4.metric("Storage Engine", "SQLite3")

        st.markdown("<div class='section-div'></div>", unsafe_allow_html=True)

        # Filters
        c_filt1, c_filt2 = st.columns(2)
        with c_filt1:
            sel_algos = st.multiselect(
                "Filter by Algorithm",
                ["FIFO", "LRU", "Optimal", "LFU"],
                default=["FIFO", "LRU", "Optimal", "LFU"]
            )
        with c_filt2:
            min_f = int(hist_df["Frames"].min())
            max_f = int(hist_df["Frames"].max())
            f_range = st.slider("Filter by Frame Count", min_f, max(min_f + 1, max_f), (min_f, max_f))

        filtered_history = hist_df[
            (hist_df["Algorithm"].isin(sel_algos)) &
            (hist_df["Frames"] >= f_range[0]) &
            (hist_df["Frames"] <= f_range[1])
        ]

        st.markdown(f"Displaying **{len(filtered_history)}** of **{len(hist_df)}** simulation records:")
        st.dataframe(filtered_history, use_container_width=True, hide_index=True)

        # Export & Clear buttons
        c_exp, c_clr = st.columns([2, 1])
        with c_exp:
            csv_data = export_csv(filtered_history)
            st.download_button(
                label="📥 Export Filtered History to CSV",
                data=csv_data,
                file_name="virtual_memory_simulation_history.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
        with c_clr:
            if st.button("🗑️ Clear Entire History", use_container_width=True):
                clear_history()
                st.success("History database successfully cleared!")
                st.rerun()
