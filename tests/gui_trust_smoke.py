"""Verify trust preferences persist and remain accessible in each responsive mode."""
from pathlib import Path
import sys, tempfile, tkinter as tk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dupsweeper as ui

def main():
    with tempfile.TemporaryDirectory() as d:
        ui.storage_path=lambda: str(Path(d)/'scan_history.sqlite3')
        root=tk.Tk();app=ui.App(root)
        assert not app.trust_photo.get() and not app.trust_video.get()
        app.trust_photo.set(True);app._trust_changed()
        for w in (1280,990,920,1280):
            root.geometry(f'{w}x820');root.update()
            if w<1120:app._select_card(2);root.update()
            assert app.opts_frame.winfo_ismapped()
            assert app.smart.winfo_ismapped() and app.trash.winfo_ismapped()
        root.destroy()
        root2=tk.Tk();second=ui.App(root2)
        assert second.trust_photo.get() and not second.trust_video.get()
        root2.destroy()
    print('Trust settings and responsive tabs OK')

if __name__=='__main__':main()
