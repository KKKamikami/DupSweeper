"""Legacy responsive check updated for the card/tab interface."""
from pathlib import Path
import sys, tkinter as tk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dupsweeper import App

def main():
    root=tk.Tk(); app=App(root)
    for w,h in ((1280,850),(950,820),(900,780),(1240,850)):
        root.geometry(f'{w}x{h}');root.update()
        assert app.smart.winfo_ismapped() and app.trash.winfo_ismapped()
        assert app.tree.winfo_ismapped() and app.results_panel.winfo_ismapped()
        assert not hasattr(app,'settings_scroll')
        if app._layout_mode=='tabs':
            assert app.tabbar.winfo_ismapped()
            for i in range(4):
                app._select_card(i);root.update()
                assert (app.folder_frame,app.pref_frame,app.excludes_frame,app.opts_frame)[i].winfo_ismapped()
        else:
            assert all(f.winfo_ismapped() for f in (app.folder_frame,app.pref_frame,app.excludes_frame,app.opts_frame))
    root.destroy()
    print('Responsive cards and tabs OK')

if __name__=='__main__':main()
