import multiprocessing as mp
import os
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from duplicate_finder import App


def main():
    messagebox.showinfo=lambda *args,**kw:None
    messagebox.showwarning=lambda *args,**kw:None
    messagebox.showerror=lambda *args,**kw:(_ for _ in ()).throw(AssertionError(args))
    with tempfile.TemporaryDirectory() as home:
        os.environ['XDG_DATA_HOME']=str(Path(home)/'local_state')
        root_folder=Path(home)/'scan';root_folder.mkdir()
        pref=root_folder/'prefer';pref.mkdir()
        low=pref/'best-kept.mov';high=root_folder/'other-name.mov'
        low.write_bytes(b'A'*200000)
        high.write_bytes(low.read_bytes())
        root=tk.Tk();root.withdraw()
        app=App(root)
        app.paths=[str(root_folder)]
        app._update_preferred([str(pref)])
        state={'phase':0}
        def advance():
            if app.mode: return root.after(70,advance)
            if state['phase']==0:
                assert app.result is not None
                assert not app.marks
                state['phase']=1
                app._start_history()
            elif state['phase']==1:
                assert app.result.history_info['unresolved_exact']==1
                assert app.marks=={str(high)},app.marks
                print('History GUI automatically marks non-preferred duplicate',flush=True)
                high.unlink()
                state['phase']=2
                app._start_history()
            elif state['phase']==2:
                assert app.result.history_info['processed_exact']==1
                assert not app.result.groups and not app.marks
                print('History GUI skips processed group with one remaining',flush=True)
                state['phase']=3
                root.destroy()
            else: assert False
            if state['phase'] < 3:
                root.after(150,advance)
        root.after(150,app._start_scan)
        root.after(500,advance)
        root.after(12000,lambda: (print('GUI history timeout',flush=True),root.destroy()))
        root.mainloop()
        assert state['phase']==3


if __name__=='__main__':
    mp.freeze_support()
    main()
