"""Verify settings and post-scan allowlist affect visible rows and smart selection."""
from pathlib import Path
import sys, tempfile, tkinter as tk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dupsweeper as ui
from dupsweeper_engine import FileInfo, Group, Result, filtered_result


def run(language):
    from dupsweeper_i18n import set_language,T
    set_language(language)
    with tempfile.TemporaryDirectory() as temp:
        ui.storage_path=lambda:str(Path(temp)/'history.sqlite3')
        root=tk.Tk();app=ui.App(root)
        root.geometry('980x820');root.update()
        app._select_card(2);root.update()
        assert app.excludes_frame.winfo_ismapped()
        assert app.exclusion_skip_check.cget('text')==T('掃描前略過排除資料夾')
        skip=Path(temp)/'B';other=Path(temp)/'C'
        skip.mkdir();other.mkdir()
        a=FileInfo(str(skip/'same.mp4'),40,1,0,0)
        b=FileInfo(str(other/'same.mp4'),40,1,0,0)
        app.raw_result=Result([Group('exact',[a,b],key='fake')],2,0,0,[])
        app.result=app.raw_result
        app._render()
        assert app.result.groups
        app.marks.add(a.path)
        app._update_exclusions([str(skip)])
        assert not app.result.groups and not app.marks
        assert len(app.tree.get_children())==0
        assert app._plan() == []
        app.skip_excluded.set(False);app._exclusions_changed()
        assert app._scan_exclusions()==[]
        assert not app.result.groups
        app._update_exclusions([])
        assert len(app.result.groups)==1
        app._quit()
    print('Exclusion GUI OK',language)

if __name__=='__main__':
    run('zh-TW');run('en')
