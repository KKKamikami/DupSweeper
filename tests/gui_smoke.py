import tempfile
import multiprocessing as mp
from pathlib import Path
import tkinter as tk
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from duplicate_finder import App
from tkinter import messagebox


def main():
    messagebox.showinfo=lambda *a,**k:None
    messagebox.showwarning=lambda *a,**k:None
    with tempfile.TemporaryDirectory() as d:
        (Path(d)/'a.mp4').write_bytes(b'abc'*5000)
        (Path(d)/'renamed.mov').write_bytes(b'abc'*5000)
        (Path(d)/'other.mp4').write_bytes(b'X'*5000)
        root=tk.Tk()
        root.withdraw()
        app=App(root)
        app.paths=[d]
        def check():
            if app.result:
                print('GUI scan complete',len(app.result.groups),flush=True)
                assert len([g for g in app.result.groups if g.kind=='exact'])==1
                app._smart()
                assert len(app.marks)==1
                print('GUI smart-selection okay',flush=True)
                root.destroy()
            else: root.after(100,check)
        root.after(100,app._start_scan)
        root.after(150,check)
        root.after(10000,lambda:(print('GUI timed out',flush=True),root.destroy()))
        root.mainloop()

if __name__=='__main__':
    mp.freeze_support()
    main()
