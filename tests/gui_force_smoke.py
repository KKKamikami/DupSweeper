import multiprocessing as mp
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from duplicate_finder import App

def main():
    messagebox.askyesno=lambda *a,**kw:True
    with tempfile.TemporaryDirectory() as d:
        # Sparse files make it safe to create large candidates for mid-scan termination.
        for name in ('a.mov','b.mp4'):
            with open(Path(d)/name,'wb') as f:f.truncate(512*1024*1024)
        root=tk.Tk();root.withdraw()
        app=App(root)
        app.paths=[d]
        def start():
            app._start_scan()
            root.after(100,kill)
        def kill():
            app._force_stop()
            assert app.proc is None
            assert app.mode is None
            assert app.result is None
            print('Force stop terminated scanning process',flush=True)
            root.destroy()
        root.after(100,start)
        root.after(10000,lambda:root.destroy())
        root.mainloop()

if __name__=='__main__':
    mp.freeze_support()
    main()
