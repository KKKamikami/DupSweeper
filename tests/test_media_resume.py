import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duplicate_engine as e
import history_store as h


@pytest.fixture
def private(tmp_path,monkeypatch):
    monkeypatch.setattr(h,'storage_path',lambda:str(tmp_path/'private'/'scan_history.sqlite3'))
    monkeypatch.setattr(e,'cache_file',lambda:str(tmp_path/'private'/'hash_cache.sqlite3'))
    return tmp_path


def test_multiple_preferred_directories_tie_break_quality(tmp_path):
    folders=[tmp_path/'priority1',tmp_path/'priority2',tmp_path/'elsewhere']
    for folder in folders:folder.mkdir()
    infos=[e.FileInfo(str(folder/(f'{i}.mov')),i*50+100,1,1,i+1) for i,folder in enumerate(folders)]
    q={infos[0].path:{'width':640,'height':360},
       infos[1].path:{'width':1920,'height':1080},
       infos[2].path:{'width':4096,'height':2160}}
    pref=[str(folders[0]),str(folders[1])]
    assert e.choose_keeper(infos,q,pref) == infos[1]
    assert e.choose_keeper(infos,q,list(reversed(pref))) == infos[1]
    assert e.choose_keeper(infos,q,[str(tmp_path/'missing')]) == infos[2]
    result=e.Result([e.Group('similar_video',infos)],3,0,0,[],qualities=q)
    assert e.smart_marks(result,pref,True) == {infos[0].path,infos[2].path}
    assert e.normalize_preferred(str(folders[0])) == [str(folders[0])]
    assert not e.inside_any_folder(str(folders[2] / '3.mov'),pref)


def test_no_inventory_then_resume_recovers_skipped_photos(tmp_path,private):
    from PIL import Image
    root=tmp_path/'scan';root.mkdir()
    (root/'same.dat').write_bytes(b'duplicate-'*100)
    (root/'copy.dat').write_bytes(b'duplicate-'*100)
    # Different bytes; photos have same image content.
    im=Image.new('RGB',(70,50),(123,98,44))
    im.save(root/'portrait.png')
    im.save(root/'portrait-jpeg.jpg',quality=90)
    paths=[str(root)]
    event=threading.Event()
    on_progress=lambda *a:None
    on_error=lambda msg:None
    previous=e.run_scan(paths,False,event,on_progress,on_error,use_cache=False)
    assert len(previous.groups)==1
    with h.HistoryStore() as store:store.save_scan(paths,False,previous)
    with pytest.raises(h.HistoryMissing):
        e.run_history(paths,True,event,on_progress,on_error)
    rechecked=e.run_media_recheck(paths,event,on_progress,on_error)
    assert rechecked.history_info['mode']=='media_resume'
    assert rechecked.history_info['media_enumerated']==2
    assert len([g for g in rechecked.groups if g.kind=='exact'])==1
    visual=[g for g in rechecked.groups if g.kind=='similar_photo']
    assert len(visual)==1, rechecked.groups
    assert len(visual[0].files)==2
    # The original full scan must remain unchanged and scoped to False.
    with h.HistoryStore() as store:
        _,data=store.load_scan(paths,False)
        assert all(g['kind']=='exact' for g in data['groups'])
        with pytest.raises(h.HistoryMissing): store.load_scan(paths,True)
    historical=e.run_history(paths,True,event,on_progress,on_error)
    assert len([g for g in historical.groups if g.kind=='similar_photo'])==1
    assert historical.history_info['media_resume_available']
    assert len([g for g in e.run_history(paths,False,event,on_progress,on_error).groups if g.kind=='similar_photo'])==0
    (root/'portrait-jpeg.jpg').unlink()
    hist_after_delete=e.run_history(paths,True,event,on_progress,on_error)
    assert hist_after_delete.history_info['processed_near']==1
    assert len([g for g in hist_after_delete.groups if g.kind=='similar_photo'])==0


def test_replacing_base_scan_invalidates_resume(tmp_path,private):
    from PIL import Image
    root=tmp_path/'files';root.mkdir()
    im=Image.new('RGB',(100,60),'skyblue')
    im.save(root/'one.png');im.save(root/'two.jpg')
    paths=[str(root)]
    ev=threading.Event()
    first=e.run_scan(paths,False,ev,lambda *a:None,lambda x:None)
    with h.HistoryStore() as store:store.save_scan(paths,False,first)
    e.run_media_recheck(paths,ev,lambda *a:None,lambda x:None)
    with h.HistoryStore() as store:
        # Replacing with a full scan means supplemental visual results need refresh.
        store.save_scan(paths,False,first)
    with pytest.raises(h.HistoryMissing):
        e.run_history(paths,True,ev,lambda *a:None,lambda x:None)


def test_media_resume_cancel_preserves_original_history(tmp_path,private):
    root=tmp_path/'folder';root.mkdir()
    (root/'a.dat').write_bytes(b'X'*200)
    (root/'b.dat').write_bytes(b'X'*200)
    paths=[str(root)]
    full=e.run_scan(paths,False,threading.Event(),lambda *a:None,lambda x:None)
    with h.HistoryStore() as store:store.save_scan(paths,False,full)
    ev=threading.Event();ev.set()
    with pytest.raises(e.Cancelled):e.run_media_recheck(paths,ev,lambda *a:None,lambda x:None)
    with h.HistoryStore() as store:
        assert store.load_scan(paths,False)
        assert store.load_media_resume(paths,store.load_scan(paths,False)[0],False) is None


def test_video_resume_recovers_transcoded_movie(tmp_path,private):
    import shutil
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        pytest.skip('ffmpeg not installed')
    root=tmp_path/'videos';root.mkdir()
    for filename,quality in [('original.mp4','18'),('transcoded.mkv','30')]:
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i',
             'testsrc2=size=160x120:rate=10','-t','4.2','-c:v','libx264',
             '-crf',quality,'-pix_fmt','yuv420p',str(root/filename)]
        result=subprocess.run(cmd,capture_output=True,timeout=25)
        if result.returncode:pytest.skip('System FFmpeg has no libx264 encoder')
    paths=[str(root)]
    event=threading.Event()
    original=e.run_scan(paths,False,event,lambda *a:None,lambda s:None)
    with h.HistoryStore() as store:store.save_scan(paths,False,original)
    result=e.run_media_recheck(paths,event,lambda *a:None,lambda s:None)
    assert len([g for g in result.groups if g.kind=='similar_video'])==1
    assert result.history_info['media_enumerated']==2


