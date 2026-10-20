import os
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dupsweeper_engine as e
import dupsweeper_history as h


@pytest.fixture
def local_db(tmp_path,monkeypatch):
    monkeypatch.setattr(h,'storage_path',lambda:str(tmp_path/'private'/'history.sqlite3'))
    monkeypatch.setattr(e,'cache_file',lambda:str(tmp_path/'private'/'hashes.sqlite3'))
    return tmp_path


def do_scan(roots, use_cache=False):
    return e.run_scan(roots,False,threading.Event(),lambda *a:None,lambda x:None,use_cache=use_cache)


def save_then_replay(roots):
    result=do_scan(roots)
    with h.HistoryStore() as db:
        db.save_scan(roots,False,result)
    history=e.run_history(roots,False,threading.Event(),lambda *a:None,lambda x:None)
    return result,history


def test_preferred_folder_wins_over_better_quality(tmp_path):
    pref=tmp_path/'selected';pref.mkdir()
    other=tmp_path/'elsewhere';other.mkdir()
    a=e.FileInfo(str(pref/'small.mp4'),200,1,0,0)
    b=e.FileInfo(str(other/'big.mp4'),900,1,0,0)
    qualities={a.path:{'width':640,'height':360},b.path:{'width':3840,'height':2160}}
    assert e.choose_keeper([a,b],qualities,str(pref))==a
    assert e.choose_keeper([a,b],qualities,None)==b
    assert e.choose_keeper([a,b],qualities,str(tmp_path/'none'))==b
    assert not e.inside_folder(str(other/'big.mp4'),str(tmp_path/'else'))


def test_multiple_inside_preferred_keep_best_there(tmp_path):
    folder=tmp_path/'priority';folder.mkdir()
    other=tmp_path/'normal';other.mkdir()
    a=e.FileInfo(str(folder/'low.png'),100,1,0,0)
    b=e.FileInfo(str(folder/'high.png'),200,1,0,0)
    c=e.FileInfo(str(other/'ultra.png'),300,1,0,0)
    q={a.path:{'width':640,'height':480},b.path:{'width':1920,'height':1080},
       c.path:{'width':4000,'height':3000}}
    r=e.Result([e.Group('similar_photo',[a,b,c])],3,0,0,[],q)
    assert e.choose_keeper([a,b,c],q,str(folder))==b
    assert e.smart_marks(r,str(folder),True)=={a.path,c.path}


def test_exact_different_names_history_auto_marks(tmp_path,local_db):
    pref=tmp_path/'prefer';pref.mkdir()
    other=tmp_path/'other';other.mkdir()
    a=pref/'renamed.mp4'; b=other/'video.mov'
    a.write_bytes(b'video'*10000); b.write_bytes(a.read_bytes())
    roots=[str(tmp_path/'prefer'),str(tmp_path/'other')]
    full,hist=save_then_replay(roots)
    assert len([g for g in full.groups if g.kind=='exact'])==1
    assert hist.history_info['unresolved_exact']==1
    assert hist.history_info['processed_exact']==0
    assert e.smart_marks(hist,str(pref),False)=={str(b)}
    entries=[]
    with h.HistoryStore() as db: entries=db.summaries()
    assert len(entries)==1
    assert entries[0]['details']['unresolved_exact']==1


def test_history_processed_one_left_not_rehashed(tmp_path,local_db,monkeypatch):
    root=tmp_path/'docs';root.mkdir()
    a=root/'original.dat';b=root/'copy.dat'
    a.write_bytes(b'data'*50);b.write_bytes(a.read_bytes())
    save_then_replay([str(root)])
    b.unlink()
    def never_hash(*args,**kw):
        raise AssertionError('history replay must not rehash surviving files')
    monkeypatch.setattr(e,'hash_file',never_hash)
    history=e.run_history([str(root)],False,threading.Event(),lambda *a:None,lambda x:None)
    assert history.groups==[]
    assert history.history_info['processed_exact']==1
    assert history.history_info['unresolved_exact']==0
    assert history.history_info['checked_paths']==2


def test_history_changed_file_invalidates_group(tmp_path,local_db):
    root=tmp_path/'docs';root.mkdir()
    a=root/'a.bin';b=root/'b.bin'
    a.write_bytes(b'X'*450);b.write_bytes(a.read_bytes())
    save_then_replay([str(root)])
    b.write_bytes(b'Y'*470)
    history=e.run_history([str(root)],False,threading.Event(),lambda *a:None,lambda x:None)
    assert history.groups==[]
    assert history.history_info['stale_groups']==1
    assert history.history_info['processed_exact']==0
    assert e.smart_marks(history,None)==set()


def test_history_missing_all_never_counts_processed(tmp_path,local_db):
    root=tmp_path/'docs';root.mkdir()
    a=root/'a.bin';b=root/'b.bin'
    a.write_bytes(b'X'*450);b.write_bytes(a.read_bytes())
    save_then_replay([str(root)])
    a.unlink();b.unlink()
    history=e.run_history([str(root)],False,threading.Event(),lambda *a:None,lambda x:None)
    assert history.history_info['missing_all']==1
    assert history.history_info['processed_exact']==0


def test_full_scan_catches_new_files_while_history_only_replays(tmp_path,local_db):
    root=tmp_path/'docs';root.mkdir()
    (root/'a.bin').write_bytes(b'X'*420)
    (root/'b.bin').write_bytes(b'X'*420)
    save_then_replay([str(root)])
    (root/'c.txt').write_bytes(b'new data'*300)
    (root/'d.txt').write_bytes(b'new data'*300)
    history=e.run_history([str(root)],False,threading.Event(),lambda *a:None,lambda x:None)
    full=do_scan([str(root)])
    assert len([g for g in history.groups if g.kind=='exact'])==1
    assert len([g for g in full.groups if g.kind=='exact'])==2
    with h.HistoryStore() as db: db.save_scan([str(root)],False,full)
    updated=e.run_history([str(root)],False,threading.Event(),lambda *a:None,lambda x:None)
    assert len([g for g in updated.groups if g.kind=='exact'])==2


def test_history_scopes_separate(tmp_path,local_db):
    root=tmp_path/'docs';root.mkdir()
    (root/'a').write_bytes(b'X'*40)
    (root/'b').write_bytes(b'X'*40)
    save_then_replay([str(root)])
    with pytest.raises(h.HistoryMissing):
        e.run_history([str(root)],True,threading.Event(),lambda *a:None,lambda x:None)


def test_history_cancellation(tmp_path,local_db):
    root=tmp_path/'docs';root.mkdir()
    (root/'a').write_bytes(b'X'*40)
    (root/'b').write_bytes(b'X'*40)
    save_then_replay([str(root)])
    ev=threading.Event(); ev.set()
    with pytest.raises(e.Cancelled):
        e.run_history([str(root)],False,ev,lambda *a:None,lambda x:None)


def test_full_refresh_bypasses_stale_cache_even_with_unchanged_metadata(tmp_path,local_db):
    root=tmp_path/'data';root.mkdir()
    a=root/'same1.bin';b=root/'same2.bin'
    a.write_bytes(b'a'*120000)
    b.write_bytes(a.read_bytes())
    first=do_scan([str(root)],use_cache=True)
    assert len([g for g in first.groups if g.kind=='exact'])==1
    before=b.stat()
    b.write_bytes(b'z'*120000)
    os.utime(b,ns=(before.st_atime_ns,before.st_mtime_ns))
    # An attribute-only cache can be stale if another tool restores timestamps.
    # Full refresh must never rely on that cache.
    fresh=do_scan([str(root)],use_cache=False)
    assert not [g for g in fresh.groups if g.kind=='exact']


def test_history_same_filename_different_content_is_not_autoselected(tmp_path,local_db):
    root=tmp_path/'data';(root/'one').mkdir(parents=True);(root/'two').mkdir()
    (root/'one'/'same.mkv').write_bytes(b'a'*50)
    (root/'two'/'same.mkv').write_bytes(b'b'*50)
    _, history=save_then_replay([str(root)])
    assert len([g for g in history.groups if g.kind=='same_name'])==1
    assert e.smart_marks(history,None)==set()
