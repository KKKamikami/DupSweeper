"""Validate layout adapts to different window sizes without hiding actions."""
from pathlib import Path
import tkinter as tk
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dupsweeper import App


def main():
    root=tk.Tk()
    app=App(root)
    for width,height in [(1280,850),(950,670),(790,650),(720,590),(1240,800)]:
        root.geometry(f'{width}x{height}')
        root.update()
        assert app.workspace.winfo_width() <= width
        assert app.trash.winfo_ismapped()
        assert app.smart.winfo_ismapped()
        assert app.tree.winfo_ismapped()
        if width < 1040:
            assert app.settings_toggle.winfo_ismapped()
            if app.settings_panel.winfo_ismapped():
                app._toggle_settings()
                root.update()
            assert not app.settings_panel.winfo_ismapped()
            assert app.results_panel.winfo_height() > 250
            app._toggle_settings()
            root.update()
            assert app.settings_panel.winfo_ismapped()
            app._toggle_settings()
            root.update()
        else:
            assert app.settings_panel.winfo_ismapped()
            assert app.results_panel.winfo_ismapped()
    print('Responsive layout OK')
    root.destroy()


if __name__=='__main__':main()
