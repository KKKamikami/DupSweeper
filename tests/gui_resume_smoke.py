import multiprocessing as mp
import os
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dupsweeper import App


def main():
    messagebox.askyesno=lambda *a,**kw:True
    messagebox.showinfo=lambda *a,**kw:None
    messagebox.showwarning=lambda *a,**kw:None
    messagebox.showerror=lambda *a,**kw:(_ for _ in ()).throw(AssertionError(a))
    with tempfile.TemporaryDirectory() as d:
        os.environ['XDG_DATA_HOME']=str(Path(d)/'local_data')
        os.environ['XDG_CACHE_HOME']=str(Path(d)/'local_cache')
        folder=Path(d)/'scan';folder.mkdir()
        pref1=folder/'pref1';pref1.mkdir()
        pref2=folder/'pref2';pref2.mkdir()
        (pref1/'a.bin').write_bytes(b'a'*5000)
        (pref2/'b.bin').write_bytes(b'a'*5000)
        img=Image.new('RGB',(90,60),(110, 88, 52))
        img.save(folder/'photo.png')
        img.save(folder/'photo-copy.jpg')
        root=tk.Tk();root.withdraw()
        app=App(root)
        app.paths=[str(folder)]
        app._update_preferred([str(pref1),str(pref2)])
        phase=[0]
        def next_step():
            if app.mode:
                return root.after(90,next_step)
            if phase[0]==0:
                assert len([g for g in app.result.groups if g.kind=='similar_photo'])==0
                phase[0]=1
                app._start_media_resume()
                return root.after(100,next_step)
            if phase[0]==1:
                assert len([g for g in app.result.groups if g.kind=='similar_photo'])==1
                assert len([g for g in app.result.groups if g.kind=='exact'])==1
                assert len(app.preferred_paths)==2
                phase[0]=2
                app._start_history()
                return root.after(100,next_step)
            if phase[0]==2:
                assert len([g for g in app.result.groups if g.kind=='similar_photo'])==1
                assert app.result.history_info['media_resume_available']
                assert len(app.marks)==1
                print('GUI: full scan > media resume > history and smart selection OK',flush=True)
                phase[0]=3
                root.destroy()
        root.after(140,app._start_scan)
        root.after(360,next_step)
        root.after(30000,lambda:(print('TIMEOUT',flush=True),root.destroy()))
        root.mainloop()
        assert phase[0]==3

if __name__=='__main__':
    mp.freeze_support()
    main()
