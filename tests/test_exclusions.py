"""Multiple allowlisted folders must never become removal candidates."""
import os
import threading
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dupsweeper_engine as engine
import dupsweeper_history as history
from dupsweeper import App


def scan(roots, excluded=()):
    return engine.run_scan([str(p) for p in roots],False,threading.Event(),lambda *a:None,
                           lambda x:None,use_cache=False,excluded_folders=excluded)


def fixture_files(root):
    for name in ('B','C','D','BX'):
        (root/name).mkdir()
        (root/name/'copy.txt').write_bytes(b'SAME'*1000)
    return root/'B',root/'C',root/'D',root/'BX'


def test_skip_one_subtree_while_scan_others(tmp_path):
    b,c,d,bx=fixture_files(tmp_path)
    r=scan([tmp_path],[str(b)])
    assert r.count==3
    gs=[g for g in r.groups if g.kind=='exact']
    assert len(gs)==1
    assert {x.path for x in gs[0].files}=={str(c/'copy.txt'),str(d/'copy.txt'),str(bx/'copy.txt')}
    assert len(engine.smart_marks(r))==2


def test_nested_multiple_exclusions_and_prefix_collision(tmp_path):
    b,c,d,bx=fixture_files(tmp_path)
    r=scan([tmp_path],[str(b),str(d)])
    assert r.count==2
    assert {x.path for x in r.groups[0].files}=={str(c/'copy.txt'),str(bx/'copy.txt')}
    assert not engine.inside_any_folder(str(bx/'copy.txt'),[str(b)])


def test_filter_after_scan_clears_hidden_candidates_and_retention(tmp_path):
    b,c,d,bx=fixture_files(tmp_path)
    all_result=scan([tmp_path]); assert all_result.count==4
    filtered=engine.filtered_result(all_result,[str(b),str(d)])
    assert all_result.groups and all_result.count==4
    assert len([g for g in filtered.groups if g.kind=='exact'])==1
    paths={x.path for g in filtered.groups for x in g.files}
    assert not any(engine.inside_any_folder(x,[str(b),str(d)]) for x in paths)
    assert engine.smart_marks(filtered,preferred_folder=[str(b)]) <= paths
    assert engine.filtered_result(all_result,[str(b),str(c),str(d)]).groups == []


def test_history_tracks_exclusion_scope(tmp_path,monkeypatch):
    b,c,d,bx=fixture_files(tmp_path)
    monkeypatch.setattr(history,'storage_path',lambda:str(tmp_path/'local.db'))
    roots=[str(tmp_path)]
    r=scan(roots,[str(b)])
    with history.HistoryStore() as db:
        db.save_scan(roots,False,r,[str(b)])
        assert db.load_scan(roots,False,[str(b)])[1]['count']==3
        with pytest.raises(history.HistoryMissing):db.load_scan(roots,False)
        assert db.summaries()[0]['excluded']==[str(b)]
    replay=engine.run_history(roots,False,threading.Event(),lambda *a:None,lambda x:None,[str(b)])
    assert len(replay.groups)==1
    assert all(not engine.inside_any_folder(x.path,[str(b)]) for g in replay.groups for x in g.files)


def test_filtered_history_removes_group_if_one_survives(tmp_path):
    b,c,d,bx=fixture_files(tmp_path)
    full=scan([tmp_path]);f=engine.filtered_result(full,[str(b),str(c),str(d)])
    assert f.groups==[]
    assert engine.smart_marks(f)==set()


def test_trash_worker_defensive_block(tmp_path,monkeypatch):
    b,c,d,bx=fixture_files(tmp_path)
    r=scan([tmp_path]);g=next(g for g in r.groups if g.kind=='exact')
    import send2trash
    moved=[]
    monkeypatch.setattr(send2trash,'send2trash',lambda path:moved.append(path))
    block=next(x for x in g.files if engine.inside_any_folder(x.path,[str(b)]))
    keep=next(x for x in g.files if engine.inside_any_folder(x.path,[str(c)]))
    done,fail=engine.trash_worker([(block,keep,'exact',g.key)],threading.Event(),lambda *a:None,[str(b)])
    assert not done and len(fail)==1 and not moved
    done,fail=engine.trash_worker([(keep,block,'exact',g.key)],threading.Event(),lambda *a:None,[str(b)])
    assert not done and len(fail)==1 and not moved


def test_gui_plan_rejects_stale_mark_in_excluded(tmp_path):
    b,c,d,bx=fixture_files(tmp_path)
    r=scan([tmp_path])
    app=object.__new__(App)
    app.result=r
    app.excluded_paths=[str(b)]
    app.preferred_paths=[]
    app.marks={str(b/'copy.txt')}
    with pytest.raises(ValueError,match='禁止移除排除資料夾'):
        app._plan()


def test_english_exclusion_translation():
    from dupsweeper_i18n import set_language,T
    set_language('en')
    try:
        assert T('排除資料夾／白名單')=='Excluded folders / Allowlist'
        assert T('掃描前略過排除資料夾')=='Skip excluded folders during scan'
    finally:set_language('zh-TW')


def test_media_enumeration_skips_nested_folders(tmp_path):
    b,c,d,bx=fixture_files(tmp_path)
    for folder in (b,c,d,bx):
        (folder/'clip.mp4').write_bytes(b'fake media for listing')
    media,scanned=engine.list_media_files([str(tmp_path)],threading.Event(),lambda *a:None,
                                         lambda x:None,[str(b),str(d)])
    assert {Path(x.path).parent for x in media}=={c,bx}
    assert scanned==4 # two .txt and two .mp4 outside excluded subtrees


def test_migrate_existing_history_without_excluded_column(tmp_path,monkeypatch):
    import sqlite3
    dbfile=tmp_path/'legacy.sqlite3'
    monkeypatch.setattr(history,'storage_path',lambda:str(dbfile))
    db=sqlite3.connect(dbfile)
    db.execute('''CREATE TABLE scans (
        scope TEXT PRIMARY KEY, roots TEXT NOT NULL, media INTEGER NOT NULL,
        created REAL NOT NULL, count INTEGER NOT NULL, group_count INTEGER NOT NULL,
        format_version INTEGER NOT NULL, payload BLOB NOT NULL,
        last_check REAL, last_summary TEXT)''')
    db.commit();db.close()
    with history.HistoryStore() as store:
        cols={row[1] for row in store.db.execute('PRAGMA table_info(scans)')}
        assert 'excluded' in cols
        assert store.db.execute('SELECT COUNT(*) FROM scans').fetchone()[0]==0
