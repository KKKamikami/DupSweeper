import os
import sys
import threading
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duplicate_engine as e


def test_identical_different_names_and_extensions(tmp_path):
    (tmp_path/'video.mp4').write_bytes(b'MOVIE' * 25000)
    (tmp_path/'renamed.zip').write_bytes(b'MOVIE' * 25000)
    (tmp_path/'other.zip').write_bytes(b'different')
    r=e.run_scan([str(tmp_path)],False,threading.Event(),lambda *x:None,lambda x:None)
    exact=[g for g in r.groups if g.kind=='exact']
    assert len(exact)==1
    assert sorted(x.path.split('/')[-1] for x in exact[0].files)==['renamed.zip','video.mp4']


def test_same_name_different_bytes_and_sizes(tmp_path):
    p=tmp_path/'a';p.mkdir()
    q=tmp_path/'b';q.mkdir()
    (p/'same.txt').write_bytes(b'123')
    (q/'same.txt').write_bytes(b'xyz')
    (p/'same.MP4').write_bytes(b'abc')
    (q/'same.MP4').write_bytes(b'abc2')
    r=e.run_scan([str(tmp_path)],False,threading.Event(),lambda *x:None,lambda x:None)
    assert len([g for g in r.groups if g.kind=='same_name'])==2
    assert not [g for g in r.groups if g.kind=='exact']


def test_sample_collision_resolved_by_full_hash(tmp_path):
    # First/middle/last 64KB equal but content at an unsampled position differs.
    a=bytearray(b'X'*(1024*1024))
    b=bytearray(a)
    b[200_000]=77
    (tmp_path/'A.mkv').write_bytes(a)
    (tmp_path/'B.mkv').write_bytes(b)
    r=e.run_scan([str(tmp_path)],False,threading.Event(),lambda *x:None,lambda x:None)
    assert not [g for g in r.groups if g.kind=='exact']


def test_cached_hashes(tmp_path,monkeypatch):
    monkeypatch.setattr(e,'cache_file',lambda:str(tmp_path/'cache'/'db.sqlite'))
    p=tmp_path/'d';p.mkdir()
    (p/'1.mov').write_bytes(b'hello'*1000)
    (p/'2.mov').write_bytes(b'hello'*1000)
    a=e.run_scan([str(p)],False,threading.Event(),lambda *x:None,lambda x:None)
    b=e.run_scan([str(p)],False,threading.Event(),lambda *x:None,lambda x:None)
    assert a.cache_hits==0
    assert b.cache_hits>=4
    assert len([g for g in b.groups if g.kind=='exact'])==1


def test_cancellation(tmp_path):
    (tmp_path/'test.mp4').write_bytes(b'x'*5000)
    flag=threading.Event(); flag.set()
    try: e.run_scan([str(tmp_path)],False,flag,lambda *x:None,lambda x:None)
    except e.Cancelled: pass
    else: assert False, 'must cancel'


def test_visual_comparison_same_content_different_names(tmp_path):
    r1=e.FileInfo(str(tmp_path/'abc.png'),300,1,0,1)
    r2=e.FileInfo(str(tmp_path/'xyz.png'),200,2,0,2)
    a={'kind':'photo','hash':0x1234567890abcdef,'width':1920,'height':1080,'size':300}
    b={'kind':'photo','hash':a['hash']^3,'width':1280,'height':720,'size':200}
    gs=e.visually_similar_groups({r1.path:a,r2.path:b},{r1.path:r1,r2.path:r2},{})
    assert len(gs)==1
    assert gs[0].kind=='similar_photo'


def test_video_signature_different_duration_rejected():
    a={'kind':'video','hashes':[123,234,345],'duration':60.0,'width':1280,'height':720}
    b={'kind':'video','hashes':[123,234,345],'duration':90.0,'width':1280,'height':720}
    assert not e.close_visual(a,b,'video')


def test_reject_all_selected_even_with_multi_membership(tmp_path):
    import duplicate_finder as ui
    a=e.FileInfo(str(tmp_path/'1.mp4'),3,1,0,0)
    b=e.FileInfo(str(tmp_path/'2.mp4'),3,1,0,0)
    group=e.Group('exact',[a,b],key='dummy')
    app=object.__new__(ui.App)
    app.result=e.Result([group],2,0,0,[],{},{},{a.path:'dummy',b.path:'dummy'})
    app.marks={a.path,b.path}
    app.allow_near=type('Var',(),{'get':lambda self:False})()
    import pytest
    with pytest.raises(ValueError):app._plan()


def test_trash_worker_revalidates_full_hash(tmp_path,monkeypatch):
    import send2trash
    p=tmp_path/'a.mov'; q=tmp_path/'b.mov'
    p.write_bytes(b'abcd'*1000)
    q.write_bytes(b'abcd'*1000)
    r=e.run_scan([str(tmp_path)],False,threading.Event(),lambda *x:None,lambda x:None)
    group=next(g for g in r.groups if g.kind=='exact')
    calls=[]
    monkeypatch.setattr(send2trash,'send2trash',lambda path:calls.append(path))
    plan=[(group.files[0],group.files[1],'exact',group.key)]
    done,errors=e.trash_worker(plan,threading.Event(),lambda *x:None)
    assert done==calls and not errors
    # Modify the file after scan: stale results must not move anything.
    p.write_bytes(b'evil'*1000)
    calls.clear()
    done,errors=e.trash_worker(plan,threading.Event(),lambda *x:None)
    assert not done and len(errors)==1 and not calls


def test_quality_prefers_higher_resolution(tmp_path):
    a=e.FileInfo(str(tmp_path/'high.mp4'),8000,1,0,1)
    b=e.FileInfo(str(tmp_path/'low.mp4'),5000,1,0,2)
    quality={a.path:{'width':1920,'height':1080,'bitrate':5000,'fps':30},
             b.path:{'width':1280,'height':720,'bitrate':9000,'fps':30}}
    assert e.choose_keeper([a,b],quality)==a
