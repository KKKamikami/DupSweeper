"""Smoke test GUI trust settings and responsive layout in an actual Tk window."""
from pathlib import Path
import sys, tempfile, tkinter as tk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dupsweeper as ui

def main():
    with tempfile.TemporaryDirectory() as d:
        ui.storage_path=lambda:str(Path(d)/'scan_history.sqlite3')
        root=tk.Tk()
        app=ui.App(root)
        assert not app.trust_photo.get()
        assert not app.trust_video.get()
        app.trust_photo.set(True)
        app._trust_changed()
        app.trust_video.set(False)
        for width in (1240,950,780,720,1240):
            root.geometry(f'{width}x720')
            root.update()
            if width < 840:
                if not app.settings_panel.winfo_ismapped():
                    app._toggle_settings();root.update()
                assert app.opts_frame.grid_info()['row']==1
                assert app.opts_frame.grid_info()['columnspan']==3
            elif width < 1040:
                if not app.settings_panel.winfo_ismapped():
                    app._toggle_settings();root.update()
                assert app.opts_frame.grid_info()['row']==0
            else:
                assert app.opts_frame.grid_info()['row']==2
            assert app.smart.winfo_ismapped()
            assert app.trash.winfo_ismapped()
        root.destroy()
        root2=tk.Tk()
        second=ui.App(root2)
        assert second.trust_photo.get() and not second.trust_video.get()
        root2.destroy()
    print('GUI_TRUST_AND_RESIZE_OK')

if __name__=='__main__': main()
