"""Real Tk layout and language checks; run with xvfb-run when headless."""
import sys
from pathlib import Path
import tkinter as tk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dupsweeper import App
from dupsweeper_i18n import T, set_language

def inspect(lang):
    set_language(lang)
    root=tk.Tk()
    app=App(root)
    for width,height in ((1580,960),(1360,900),(1020,780),(840,740),(770,650),(1560,920)):
        root.geometry(f'{width}x{height}')
        root.update()
        assert app.results_panel.winfo_ismapped(), (width,height)
        assert app.tree.winfo_ismapped(), (width,height)
        assert app.smart.winfo_ismapped() and app.trash.winfo_ismapped()
        assert app.settings_panel.winfo_ismapped()
        assert not hasattr(app,'settings_scroll')
        assert app.exclusion_skip_check.winfo_exists()
        if width<1510:
            assert app.tabbar.winfo_ismapped(),width
            for j in range(4):
                app._select_card(j)
                root.update()
                assert (app.folder_frame,app.pref_frame,app.excludes_frame,app.opts_frame)[j].winfo_ismapped()
                assert app.results_panel.winfo_y() >= app.settings_panel.winfo_y()
        else:
            assert all(f.winfo_ismapped() for f in (app.folder_frame,app.pref_frame,app.excludes_frame,app.opts_frame))
    if lang=='en':
        assert 'Duplicate File Manager' in root.title()
        assert app.scan.cget('text')=='Full Rescan'
        assert app.trust_photo.get() in (True,False)
    else:
        assert app.scan.cget('text')=='完整重新掃描'
    print('Layout OK:',lang)
    app._quit()

if __name__=='__main__':
    inspect('zh-TW')
    inspect('en')
