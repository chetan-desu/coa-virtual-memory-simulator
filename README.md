# 🧠 Virtual Memory & Page Fault Simulator

## COA Academic Project — Computer Organization & Architecture

> **Title:** Design and Implementation of Virtual Memory and Page Fault Simulation with Comparative Performance Analysis of Page Replacement Algorithms Using Python and Streamlit.

---

## 🌟 Overview & Key Features

This interactive web application is a single-page dashboard designed for students and educators in Computer Organization and Architecture (COA) and Operating Systems (OS):

1. **Virtual Memory & Physical Frame Allocation:**
   - Configure custom or randomly generated page reference strings (with locality of reference modeling).
   - Dynamically adjust physical memory frame allocation (1 to 8 frames).
   - Visual representation of physical RAM frame slots with real-time state changes.

2. **Core Page Replacement Algorithms:**
   - **FIFO (First In First Out):** Evicts the oldest loaded page. Demonstrates Bélády's anomaly.
   - **LRU (Least Recently Used):** Evicts the page unused for the longest duration (temporal locality).
   - **Optimal (Bélády's Algorithm):** Evicts the page that will not be referenced for the longest time in the future (theoretical benchmark).
   - **LFU (Least Frequently Used):** Evicts the least frequently referenced page with FIFO tie-breaking.

3. **Step-by-Step Page Fault Simulation & Playback:**
   - Play, Pause, Next Step, Previous Step, Reset, and Slider Scrubbing.
   - Instant detection and highlighting of **Page Hits** (🟢) vs. **Page Faults** (🔴).
   - Displays victim/replaced pages on eviction.

4. **Dynamic Page Table Management:**
   - Real-time tracking of Virtual Page Numbers (VPN) to Physical Frame Numbers (PFN).
   - Implementation of **Valid (1)** and **Invalid (0)** bits.
   - Updates synchronously at every step of simulation.

5. **Comparative Performance Analysis:**
   - Total hits, faults, hit ratio (%), fault ratio (%), and execution time (ms).
   - Interactive Plotly visualizations: Grouped Bar Charts, Fault Share Donut, Performance Radar Chart.
   - **Fault Sensitivity Curve:** Plots faults across 1 to 8 frames for all 4 algorithms to evaluate frame scaling and observe Bélády's anomaly.

6. **SQLite History & CSV Export:**
   - Automatically stores all simulation runs in an embedded SQLite database (`simulation_history.db`).
   - Filter history by algorithm and frame count.
   - 1-click CSV export.

---

## 🚀 Installation & Running

### 1. Prerequisites
Ensure Python 3.11+ is installed.

### 2. Install Dependencies
```bash
cd Virtual_Memory_Simulator
pip install -r requirements.txt
```

### 3. Launch the Single-Page Dashboard
```bash
streamlit run app.py
```
Open your browser and navigate to: https://coa-virtual-memory-simulator-fjb7arrv9j25wohikyge5n.streamlit.app/

---

## 📁 Project Architecture

```
Virtual_Memory_Simulator/
├── app.py                       ← Single-Page Streamlit Interactive Dashboard
├── requirements.txt             ← Python dependencies (streamlit, plotly, pandas, numpy)
├── README.md                    ← Project documentation & academic notes
├── simulation_history.db        ← Persistent SQLite database (auto-generated)
└── simulator/
    ├── __init__.py              ← Package marker
    ├── page_replacement.py      ← FIFO, LRU, Optimal, LFU simulation engines
    ├── page_table.py            ← OS Page Table data structure (valid/invalid bits)
    └── storage.py               ← SQLite persistence and CSV export
```

---

## 🎓 COA Theoretical Concepts

### 1. Virtual Memory & Physical Memory Frames
- **Virtual Memory** decouples program address space from physical RAM, allowing systems to run programs that exceed physical memory capacity.
- Program addresses are broken into **Pages**; physical RAM is divided into **Frames** of equal size.

### 2. Page Tables & Valid/Invalid Bits
- The **Page Table** maps Virtual Page Numbers (VPN) to Physical Frame Numbers (PFN).
- **Valid Bit = 1:** The virtual page is loaded into a physical RAM frame.
- **Valid Bit = 0:** The page resides on disk; referencing it triggers a hardware trap called a **Page Fault**.

### 3. Page Fault Lifecycle
1. CPU references an address with Valid Bit = 0.
2. Hardware triggers a page fault trap to the OS kernel.
3. OS saves process state and locates the page on disk/swap.
4. OS finds a free physical frame (or uses a replacement algorithm to evict a victim page).
5. The requested page is read from disk into the frame.
6. The page table entry is updated (PFN assigned, Valid Bit = 1).
7. The process instruction is restarted.

### 4. Bélády's Anomaly
- Under certain replacement policies (such as **FIFO**), increasing physical memory frames can paradoxically result in **more** page faults.
- You can test this in the simulator using the workload `1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5` with 3 frames vs. 4 frames!
