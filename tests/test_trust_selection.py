"""Independent opt-in test suite: visual photos and videos, no surprise trash."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dupsweeper_engine as eng
import dupsweeper as ui


class Var:
    def __init__(self, value=False): self.value=value
    def get(self): return self.value
    def set(self, value): self.value=value


def fixture_result():
    def f(n,s):
        return eng.FileInfo('/tmp/dupsweeper-trust-tests/'+n,s,1,0,0)
    p1,p2=f('image_low.png',100),f('image_high.png',300)
    v1,v2=f('film_low.mp4',800),f('film_high.mp4',1500)
    x1,x2=f('exact-a.txt',15),f('exact-b.txt',15)
    n1,n2=f('same-a/NAME.dat',20),f('same-b/NAME.dat',20)
    groups=[
        eng.Group('similar_photo',[p1,p2]),
        eng.Group('similar_video',[v1,v2]),
        eng.Group('exact',[x1,x2],key='hash'),
        eng.Group('same_name',[n1,n2])
    ]
    r=eng.Result(groups,8,0,0,[],{}, {}, {x1.path:'hash',x2.path:'hash'})
    return r, {'photo':p1.path,'video':v1.path, 'exact':x1.path, 'name':n1.path}


@pytest.mark.parametrize('photo,video',[(False,False),(True,False),(False,True),(True,True)])
def test_smart_marks_respect_two_switches(photo, video):
    result, paths=fixture_result()
    allowed={k for k,v in [('similar_photo',photo),('similar_video',video)] if v}
    marks=eng.smart_marks(result,near_kinds=allowed)
    assert len(marks)==1+int(photo)+int(video)
    assert any('exact-' in path for path in marks)
    assert ('photo' in str(marks)) == False   # files use "image", not "photo"
    assert (paths['photo'] in marks)==photo
    assert (paths['video'] in marks)==video
    assert paths['name'] not in marks


def test_marking_untrusted_media_is_blocked():
    result, paths=fixture_result()
    app=object.__new__(ui.App)
    app.trust_photo=Var(False);app.trust_video=Var(True)
    app.allow_near=Var(False)
    ok,msg=app._eligible(result.groups[0],result.groups[0].files[0])
    assert not ok
    assert app._eligible(result.groups[1],result.groups[1].files[0])[0]
    assert '未啟用' in msg


def test_smart_ui_does_not_show_risk_popup_each_time(monkeypatch):
    result, paths=fixture_result()
    app=object.__new__(ui.App)
    app.result=result
    app.trust_photo=Var(True);app.trust_video=Var(False)
    app.preferred_paths=[]
    app.marks=set()
    app._refresh=Mock()
    spy=Mock()
    monkeypatch.setattr(ui.messagebox,'showinfo',spy)
    monkeypatch.setattr(ui.messagebox,'askyesno',lambda *a,**k: (_ for _ in ()).throw(AssertionError('Unexpected modal')))
    app._smart()
    assert paths['photo'] in app.marks
    assert paths['video'] not in app.marks
    assert spy.called


def test_untrusted_near_cannot_be_in_trash_plan():
    result, paths=fixture_result()
    app=object.__new__(ui.App)
    app.result=result
    app.preferred_paths=[]
    app.trust_photo=Var(True);app.trust_video=Var(False)
    app.allow_near=Var(False)
    app.marks={paths['video']}
    with pytest.raises(ValueError):
        app._plan()


def test_trusted_near_allows_trash_plan():
    result, paths=fixture_result()
    app=object.__new__(ui.App)
    app.result=result
    app.preferred_paths=[]
    app.trust_photo=Var(True);app.trust_video=Var(False)
    app.allow_near=Var(False)
    app.marks={paths['photo']}
    plan=app._plan()
    assert len(plan)==1
    assert plan[0][2]=='similar_photo'


def test_single_final_confirmation_for_trusted(monkeypatch):
    result, paths=fixture_result()
    app=object.__new__(ui.App)
    app.result=result
    app.preferred_paths=[]
    app.trust_photo=Var(True);app.trust_video=Var(False)
    app.allow_near=Var(False)
    app.marks={paths['photo']}
    app.progress_var=Var()
    app._launch=Mock()
    monkeypatch.setattr(ui,'send2trash',lambda _: None)
    asked=Mock(return_value=True)
    monkeypatch.setattr(ui.messagebox,'askyesno',asked)
    monkeypatch.setattr(ui.simpledialog,'askstring',lambda *a,**k: (_ for _ in ()).throw(AssertionError('Unexpected typed confirmation')))
    app._trash()
    assert asked.call_count == 1
    assert app._launch.call_count==1
    assert app._launch.call_args.args[0]=='trash'


def test_untrusted_manual_trash_needs_typed_phrase(monkeypatch):
    result,paths=fixture_result()
    app=object.__new__(ui.App)
    app.root=None
    app.result=result
    app.preferred_paths=[]
    app.trust_photo=Var(False);app.trust_video=Var(False)
    app.allow_near=Var(True)
    app.marks={paths['video']}
    app.progress_var=Var()
    app._launch=Mock()
    monkeypatch.setattr(ui,'send2trash',lambda _: None)
    monkeypatch.setattr(ui.messagebox,'askyesno',lambda *a,**k: True)
    spy=Mock(return_value=None)
    monkeypatch.setattr(ui.simpledialog,'askstring',spy)
    app._trash()
    assert spy.called
    app._launch.assert_not_called()
