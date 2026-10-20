"""Adaptive layout and English/Chinese feature-access regression test."""
from pathlib import Path
import sys, tkinter as tk
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dupsweeper import App
from dupsweeper_i18n import set_language

for lang in ('zh-TW','en'):
    set_language(lang)
    root=tk.Tk()
    app=App(root)
    for w,h in ((780,720),(820,720),(950,760),(1180,810),(1440,900),(1600,1050),(950,1020)):
        root.geometry(f'{w}x{h}+10+10')
        root.update()
        assert root.winfo_width()>=780
        assert app.tree.winfo_height()>70,(lang,w,h,app.tree.winfo_height())
        assert app.tree.winfo_ismapped()
        assert app.smart.winfo_ismapped() and app.trash.winfo_ismapped()
        assert not hasattr(app,'settings_scroll')
        assert app._layout_mode==('grid' if w>=1180 and h>=1000 else 'tabs')
        if app._layout_mode=='tabs':
            assert app.tabbar.winfo_ismapped()
            for i,card in enumerate((app.folder_frame,app.pref_frame,app.excludes_frame,app.opts_frame)):
                app._select_card(i)
                root.update()
                assert card.winfo_ismapped(),(lang,w,h,i)
                assert card.winfo_width()<=root.winfo_width(),(lang,w,h,i)
        else:
            assert all(c.winfo_ismapped() for c in (app.folder_frame,app.pref_frame,app.excludes_frame,app.opts_frame))
            assert app.folder_frame.winfo_x()==app.excludes_frame.winfo_x()
        if app._layout_mode=='tabs':app._select_card(3);root.update()
        for row,label in app.media_rows:
            assert row.winfo_ismapped() and label.winfo_width()>=120,(lang,w,h,label.cget('text'))
            assert int(label.cget('wraplength')) <= app.opts_frame.winfo_width(),(lang,w,h,label.cget('wraplength'),app.opts_frame.winfo_width())
        app._select_card(0)
        root.update()
    app._quit()
    print('RESPONSIVE_OK',lang)
