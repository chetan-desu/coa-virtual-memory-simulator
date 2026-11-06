"""
page_table.py
==============
Implements the Page Table data structure for Virtual Memory simulation.

CONCEPT (for COA):
  - In a paged virtual memory system, the CPU generates virtual (logical) page addresses.
  - The Page Table is maintained by the Operating System to map each Virtual Page Number (VPN)
    to a Physical Frame Number (PFN) in RAM.
  - Valid Bit = 1 (Valid): The page is currently present in physical RAM.
  - Valid Bit = 0 (Invalid): The page is not in RAM. An access triggers a PAGE FAULT.
"""

class PageTable:
    """
    Simulates an Operating System Page Table with Valid/Invalid bits.
    """

    def __init__(self, num_pages: int, num_frames: int):
        self.num_pages = max(1, num_pages)
        self.num_frames = max(1, num_frames)
        # Entry format: page_number -> {'frame': int | None, 'valid': bool}
        self.table = {
            page: {'frame': None, 'valid': False}
            for page in range(self.num_pages)
        }

    def load_page(self, page_number: int, frame_number: int):
        """Mark a page as present in a specific physical frame."""
        if page_number not in self.table:
            self.table[page_number] = {'frame': None, 'valid': False}
        self.table[page_number] = {'frame': frame_number, 'valid': True}

    def evict_page(self, page_number: int):
        """Mark a page as evicted from physical memory."""
        if page_number in self.table:
            self.table[page_number] = {'frame': None, 'valid': False}

    def lookup(self, page_number: int) -> dict:
        """Look up an entry in the page table."""
        return self.table.get(page_number, {'frame': None, 'valid': False})

    def get_all_entries(self) -> list[dict]:
        """Return all page table rows formatted for UI display."""
        entries = []
        for page in sorted(self.table.keys()):
            info = self.table[page]
            frame_disp = f"Frame {info['frame']}" if info['frame'] is not None else "—"
            valid_disp = "1 (Valid)" if info['valid'] else "0 (Invalid)"
            status_disp = "In Physical Memory" if info['valid'] else "On Disk / Unloaded"
            entries.append({
                "Page Number": page,
                "Frame Number": frame_disp,
                "Valid Bit": valid_disp,
                "Status": status_disp,
            })
        return entries

    def sync_from_frames(self, frames_state: list[int], all_known_pages: list[int]):
        """
        Synchronize the page table with the current state of physical frames.
        
        Parameters:
        -----------
        frames_state     : list of page numbers currently residing in frames (-1 for empty).
        all_known_pages  : collection of all distinct page numbers in the workload.
        """
        # Ensure all known pages are represented in the table
        for p in all_known_pages:
            if p not in self.table:
                self.table[p] = {'frame': None, 'valid': False}

        # Invalidate all entries initially
        for page in self.table:
            self.table[page] = {'frame': None, 'valid': False}

        # Set valid bit and frame number for pages currently in memory
        for frame_idx, page in enumerate(frames_state):
            if page != -1:
                self.table[page] = {'frame': frame_idx, 'valid': True}
