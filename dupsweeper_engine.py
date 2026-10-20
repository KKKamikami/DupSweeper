#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone final engine. stdlib-only exact compare; Pillow/FFmpeg optional near-duplicate inspection.

No automatic deletion. SHA-256 groups are byte-identical; perceptual matches are suggestions only.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

CHUNK = 4 * 1024 * 1024
SAMPLE = 64 * 1024
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.gif', '.tif', '.tiff', '.heic', '.heif', '.avif', '.jfif'}
VIDEO_EXT = {'.mp4', '.mov', '.mkv', '.avi', '.wmv', '.m4v', '.flv', '.webm', '.mts', '.m2ts', '.mpg', '.mpeg', '.3gp', '.ts'}

class Cancelled(Exception): pass

@dataclass(frozen=True)
class FileInfo:
    path: str
    size: int
    mtime_ns: int
    dev: int
    ino: int

@dataclass
class Group:
    kind: str  # exact, similar_photo, similar_video, same_name
    files: list[FileInfo]
    key: str = ''
    note: str = ''

@dataclass
class Result:
    groups: list[Group]
    count: int
    hardlinks: int
    cache_hits: int
    errors: list[str]
    qualities: dict[str, dict] = field(default_factory=dict)
    signatures: dict[str, str] = field(default_factory=dict)
    sha: dict[str, str] = field(default_factory=dict)
    ffmpeg_available: bool = False
    pillow_available: bool = False
    history_info: dict = field(default_factory=dict)


def cancelled(event):
    if event.is_set(): raise Cancelled()


def norm(path): return os.path.normcase(os.path.abspath(path))


def snapshot(x: FileInfo):
    try:
        s = os.stat(x.path, follow_symlinks=False)
        return (stat.S_ISREG(s.st_mode) and not os.path.islink(x.path)
                and s.st_size == x.size and s.st_mtime_ns == x.mtime_ns
                and (not x.ino or (s.st_ino == x.ino and s.st_dev == x.dev)))
    except (OSError, ValueError): return False


def hash_file(x: FileInfo, event, partial: bool = False):
    cancelled(event)
    if not snapshot(x): raise OSError('檔案於掃描期間變更')
    h = hashlib.sha256()
    with open(x.path, 'rb', buffering=CHUNK) as f:
        if partial and x.size > SAMPLE * 3:
            h.update(f.read(SAMPLE))
            cancelled(event)
            f.seek(max(SAMPLE, x.size // 2 - SAMPLE // 2))
            h.update(f.read(SAMPLE))
            cancelled(event)
            f.seek(x.size - SAMPLE)
            h.update(f.read(SAMPLE))
        elif partial:
            while True:
                cancelled(event)
                block = f.read(CHUNK)
                if not block: break
                h.update(block)
        else:
            while True:
                cancelled(event)
                block = f.read(CHUNK)
                if not block: break
                h.update(block)
    if not snapshot(x): raise OSError('檔案於讀取期間變更')
    return h.hexdigest()


def cache_file():
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA') or str(Path.home())
    elif sys.platform == 'darwin': base = str(Path.home() / 'Library' / 'Caches')
    else: base = os.environ.get('XDG_CACHE_HOME') or str(Path.home() / '.cache')
    return os.path.join(base, 'DupSweeper', 'hash_cache.sqlite3')


class HashCache:
    def __init__(self):
        self.db = None
        try:
            dest = cache_file()
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            self.db = sqlite3.connect(dest, timeout=2)
            self.db.execute('''CREATE TABLE IF NOT EXISTS hashes (
               path TEXT PRIMARY KEY, size INTEGER, mtime INTEGER, dev INTEGER, ino INTEGER,
               quick TEXT, full TEXT)''')
            self.db.execute('''CREATE TABLE IF NOT EXISTS media (
               path TEXT PRIMARY KEY, size INTEGER, mtime INTEGER, dev INTEGER, ino INTEGER,
               kind TEXT, data TEXT)''')
            self.db.commit()
        except (sqlite3.Error, OSError):
            self.close()

    def get(self, x, col):
        if self.db is None: return None
        try:
            row = self.db.execute('SELECT size,mtime,dev,ino,quick,full FROM hashes WHERE path=?', (x.path,)).fetchone()
            if row and row[:4] == (x.size, x.mtime_ns, x.dev, x.ino):
                return row[4 if col == 'quick' else 5]
        except sqlite3.Error: pass
        return None

    def put(self, x, col, value):
        if self.db is None: return
        try:
            old = self.db.execute('SELECT size,mtime,dev,ino,quick,full FROM hashes WHERE path=?', (x.path,)).fetchone()
            if old and old[:4] == (x.size, x.mtime_ns, x.dev, x.ino):
                quick, full = old[4], old[5]
            else: quick = full = None
            if col == 'quick': quick = value
            else: full = value
            self.db.execute('REPLACE INTO hashes VALUES (?,?,?,?,?,?,?)', (x.path,x.size,x.mtime_ns,x.dev,x.ino,quick,full))
        except sqlite3.Error: pass

    def get_media(self, x, kind):
        if self.db is None: return None
        try:
            row=self.db.execute('SELECT size,mtime,dev,ino,kind,data FROM media WHERE path=?',(x.path,)).fetchone()
            if row and row[:5]==(x.size,x.mtime_ns,x.dev,x.ino,kind):
                return json.loads(row[5])
        except (sqlite3.Error, ValueError, TypeError): pass
        return None

    def put_media(self,x,kind,data):
        if self.db is None: return
        try:
            self.db.execute('REPLACE INTO media VALUES (?,?,?,?,?,?,?)',
                  (x.path,x.size,x.mtime_ns,x.dev,x.ino,kind,json.dumps(data,ensure_ascii=False)))
        except (sqlite3.Error, ValueError): pass

    def close(self):
        if self.db:
            try: self.db.commit()
            finally: self.db.close()
            self.db = None


def list_files(roots, event, progress, error):
    sizes, names = defaultdict(list), defaultdict(list)
    visited, inodes = set(), set()
    total = hardlinks = 0
    tick = time.monotonic()
    for root in roots:
        stack = [root]
        while stack:
            cancelled(event)
            path = stack.pop()
            try:
                with os.scandir(path) as items:
                    for item in items:
                        cancelled(event)
                        try:
                            if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()): continue
                            s = item.stat(follow_symlinks=False)
                            if stat.S_ISDIR(s.st_mode): stack.append(item.path); continue
                            if not stat.S_ISREG(s.st_mode): continue
                            p = os.path.abspath(item.path)
                            key = norm(p)
                            if key in visited: continue
                            visited.add(key)
                            if s.st_nlink > 1 and s.st_ino:
                                key_inode = (s.st_dev, s.st_ino)
                                if key_inode in inodes: hardlinks += 1; continue
                                inodes.add(key_inode)
                            x = FileInfo(p, s.st_size, s.st_mtime_ns, s.st_dev, s.st_ino)
                            sizes[x.size].append(x)
                            names[os.path.basename(p).casefold()].append(x)
                            total += 1
                        except (OSError, ValueError) as exc: error(f'{item.path}: {exc}')
                        if time.monotonic() - tick > .3:
                            progress('列舉資料夾', total, 0)
                            tick = time.monotonic()
            except (OSError, ValueError) as exc: error(f'{path}: {exc}')
    progress('列舉完成', total, total)
    return sizes, names, total, hardlinks


def file_kind(x):
    ext = Path(x.path).suffix.lower()
    return 'photo' if ext in IMAGE_EXT else 'video' if ext in VIDEO_EXT else None


def _dhash_gray(vals):
    out = 0
    for i in range(8):
        for j in range(8):
            out = (out << 1) | int(vals[i*9+j] > vals[i*9+j+1])
    return out


def photo_signature(x, Image, event):
    cancelled(event)
    with Image.open(x.path) as img:
        width, height = img.size
        if width < 20 or height < 20: raise ValueError('影像尺寸過小')
        img.seek(0)
        im = img.convert('L').resize((9,8), Image.Resampling.LANCZOS)
        pixels = im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata()
        h = _dhash_gray(list(pixels))
    cancelled(event)
    return {'hash': h, 'width': width, 'height': height, 'size': x.size, 'kind': 'photo'}


def ffmpeg_exe(name):
    # Windows bootstrap installs both tools into the per-user app data directory.
    base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    suffix = '.exe' if os.name == 'nt' else ''
    from_history = os.path.join(os.path.dirname(__import__('dupsweeper_history').storage_path()), 'bin', name + suffix)
    bundle_root = getattr(sys, '_MEIPASS', base)
    for loc in (os.path.join(bundle_root, name + suffix), os.path.join(base, name + suffix),
                from_history, shutil.which(name)):
        if loc and os.path.isfile(loc): return loc
    return None


def cancellable_cmd(cmd, event, timeout=35):
    cancelled(event)
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, creationflags=creationflags)
    t0 = time.monotonic()
    try:
        while True:
            if event.is_set() or time.monotonic() - t0 > timeout:
                raise Cancelled() if event.is_set() else TimeoutError('外部媒體解碼逾時')
            try: return proc.communicate(timeout=.2)[0]
            except subprocess.TimeoutExpired: continue
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()


def video_signature(x, ffprobe, ffmpeg, event):
    info = json.loads(cancellable_cmd([ffprobe, '-v','error','-show_entries',
           'format=duration,bit_rate:stream=index,codec_type,width,height,avg_frame_rate,bit_rate',
           '-of','json',x.path], event, timeout=20).decode('utf-8'))
    v = next((s for s in info.get('streams',[]) if s.get('codec_type') == 'video'), None)
    if v is None: raise ValueError('沒有影片影格')
    duration = float(info.get('format',{}).get('duration') or 0)
    if duration < 3: raise ValueError('影片過短，無法安全取樣')
    width, height = int(v.get('width') or 0), int(v.get('height') or 0)
    if width < 16 or height < 16: raise ValueError('無法辨認解析度')
    fraction = v.get('avg_frame_rate','0/1')
    try:
        a,b = fraction.split('/')
        fps = float(a)/float(b) if float(b) else 0
    except (ValueError, ZeroDivisionError): fps = 0
    bit_rate = int(v.get('bit_rate') or info.get('format',{}).get('bit_rate') or 0)
    hashes = []
    for f in (.16,.51,.84):
        t = min(duration-0.3, duration*f)
        data = cancellable_cmd([ffmpeg,'-nostdin','-hide_banner','-loglevel','error',
                      '-ss',f'{t:.3f}','-i',x.path,'-frames:v','1','-vf',
                      'scale=9:8,format=gray','-f','rawvideo','-pix_fmt','gray','pipe:1'], event)
        if len(data) < 72: raise ValueError('影格擷取失敗')
        hashes.append(_dhash_gray(data[:72]))
    return {'hashes': hashes, 'duration': duration, 'width': width, 'height': height,
            'fps': fps, 'bitrate': bit_rate, 'size': x.size, 'kind': 'video'}


def quality_value(x, q):
    if not q: return (0,0,0,0,x.size,-x.mtime_ns)
    # Pixel count first, then useful stream/image data density, then file size as tie-breaker.
    return (int(q.get('width',0))*int(q.get('height',0)),
            float(q.get('bitrate',0)), float(q.get('fps',0)),
            x.size, -x.mtime_ns, x.path.casefold())


def inside_folder(file_path, folder):
    """True for descendants only; commonpath avoids confusing C:\foo and C:\foobar."""
    if not folder: return False
    try:
        base = norm(folder)
        target = norm(file_path)
        return os.path.commonpath((target, base)) == base
    except (OSError, ValueError):
        return False


def normalize_preferred(preferred_folders):
    """Normalize one or many preferred directories."""
    if not preferred_folders: return []
    if isinstance(preferred_folders, (str, os.PathLike)):
        preferred_folders = [os.fspath(preferred_folders)]
    return [os.fspath(p) for p in preferred_folders if p]


def inside_any_folder(file_path, preferred_folders):
    return any(inside_folder(file_path, p) for p in normalize_preferred(preferred_folders))


def choose_keeper(files, qualities, preferred_folder=None):
    """All preferred directories have equal precedence; quality breaks ties."""
    if not files: raise ValueError('空的群組無法保留檔案')
    inside = [x for x in files if inside_any_folder(x.path, preferred_folder)]
    pool = inside if inside else files
    return max(pool, key=lambda x: quality_value(x, qualities.get(x.path)))


def smart_marks(result, preferred_folder=None, include_near=False, near_kinds=None):
    """Pure mark planner. near_kinds independently opts in photos/videos.

    The legacy include_near bool is supported for compatibility with existing tests;
    explicitly passing near_kinds overrides it. No files are deleted here.
    """
    exact=[g for g in result.groups if g.kind=='exact']
    allowed = ({'similar_photo', 'similar_video'} if include_near else set()) if near_kinds is None else set(near_kinds)
    allowed.intersection_update(('similar_photo','similar_video'))
    near=[g for g in result.groups if g.kind in allowed]
    marks=set()
    for g in near:
        keep=choose_keeper(g.files,result.qualities,preferred_folder)
        marks.update(x.path for x in g.files if x.path!=keep.path and not protected(x.path))
    for g in exact:
        rest=[x for x in g.files if x.path not in marks]
        if not rest:
            keeper=choose_keeper(g.files,result.qualities,preferred_folder)
            marks.discard(keeper.path)
            rest=[keeper]
        keeper=choose_keeper(rest,result.qualities,preferred_folder)
        marks.update(x.path for x in g.files if x.path!=keeper.path and not protected(x.path))
    for g in near:
        if all(x.path in marks for x in g.files):
            marks.discard(choose_keeper(g.files,result.qualities,preferred_folder).path)
    return marks


def bands(h): return tuple((h >> (16*i)) & 0xffff for i in range(4))


def close_visual(a, b, kind):
    if a['kind'] != b['kind']: return False
    aspect_a = a['width']/max(1,a['height'])
    aspect_b = b['width']/max(1,b['height'])
    if abs(aspect_a / aspect_b - 1) > .06: return False
    if kind == 'photo': return (a['hash'] ^ b['hash']).bit_count() <= 3
    if abs(a['duration']-b['duration']) > max(2, min(a['duration'],b['duration'])*.02): return False
    diffs = [(z ^ w).bit_count() for z,w in zip(a['hashes'], b['hashes'])]
    return diffs[1] <= 3 and max(diffs) <= 4 and sum(diffs) <= 9


def visually_similar_groups(metas, records, sha):
    """Single-anchor non-transitive grouping; buckets cut candidate explosion."""
    by_kind = defaultdict(list)
    for p, q in metas.items(): by_kind[q['kind']].append((p,q))
    groups = []
    for kind, entries in by_kind.items():
        # For 4 bands, <=3 Hamming errors must leave one exact 16-bit band.
        buckets = defaultdict(set)
        assigned = set()
        for p, meta in entries:
            if p in assigned: continue
            duration_bin = int(meta.get('duration',0)//12) if kind == 'video' else 0
            all_candidates = set()
            for j,b in enumerate(bands(meta['hash'] if kind == 'photo' else meta['hashes'][1])):
                for d in ((duration_bin-1,duration_bin,duration_bin+1) if kind == 'video' else (0,)):
                    all_candidates.update(buckets.get((kind,j,b,d),()))
            matching = []
            for other in all_candidates:
                if other in assigned: continue
                ometa = metas[other]
                if close_visual(meta, ometa, kind) and (sha.get(p) or p) != (sha.get(other) or other):
                    matching.append(other)
            # A visual family contains representatives of different exact-content identities.
            if matching:
                members = [p] + matching
                # Existing digest-identical copies may also be in a visual family.
                fingerprints = {sha.get(path) for path in members if sha.get(path)}
                for path2,q2 in entries:
                    if path2 not in assigned and path2 not in members and sha.get(path2) in fingerprints and sha.get(path2):
                        members.append(path2)
                group_records = sorted([records[path] for path in members],key=lambda f:f.path.casefold())
                groups.append(Group('similar_photo' if kind=='photo' else 'similar_video',
                          group_records, note='視覺相似，可能有不同音軌、字幕或內容；刪除須另外確認'))
                assigned.update(members)
            else:
                # Insert into bucket for comparisons with later files.
                for j,b in enumerate(bands(meta['hash'] if kind=='photo' else meta['hashes'][1])):
                    buckets[(kind,j,b,duration_bin)].add(p)
    return groups


def run_scan(roots, use_media, event, progress, error, use_cache=True):
    errors = []
    def err(msg):
        if len(errors) < 30: errors.append(msg)
        error(msg)
    sizes, names, count, hardlinks = list_files(roots, event, progress, err)
    cache = HashCache()
    hit_count = 0
    try:
        def cached_hash(x, col):
            nonlocal hit_count
            cancelled(event)
            value = cache.get(x, col) if use_cache else None
            if value and snapshot(x):
                hit_count += 1
                return value
            value = hash_file(x,event,partial=(col=='quick'))
            cache.put(x,col,value)
            return value

        # All same-name candidates require identity resolution even if quick samples differ.
        candidates = [x for s,items in sizes.items() if len(items)>1 for x in items]
        quick = defaultdict(list)
        for i,x in enumerate(candidates,1):
            try: quick[(x.size,cached_hash(x,'quick'))].append(x)
            except Cancelled: raise
            except (OSError, ValueError) as exc: err(f'略過 {x.path}: {exc}')
            if i%20==0 or i==len(candidates): progress('快速抽樣（首／中／尾）',i,len(candidates))
        full_candidates = {x.path: x for bucket in quick.values() if len(bucket)>1 for x in bucket}
        # Same-name groups with distinct bytes must also be resolvable.
        name_lookup = {x.path:x for items in names.values() if len(items)>1 for x in items}
        full_candidates.update(name_lookup)
        sha = {}
        pending = list(full_candidates.values())
        for i,x in enumerate(pending,1):
            try: sha[x.path] = cached_hash(x,'full')
            except Cancelled: raise
            except (OSError, ValueError) as exc: err(f'略過 {x.path}: {exc}')
            if i%3==0 or i==len(pending): progress('完整 SHA-256 驗證',i,len(pending))
        digest_map = defaultdict(list)
        for items in sizes.values():
            for x in items:
                if x.path in sha: digest_map[(x.size,sha[x.path])].append(x)
        exacts = [Group('exact',sorted(v,key=lambda x:(x.mtime_ns,x.path.casefold())),key=k[1])
                  for k,v in digest_map.items() if len(v)>1]
        # Same file name but different content is a warning only.
        samenames = []
        for name, items in names.items():
            if len(items)<2: continue
            sizes_seen={x.size for x in items}
            # If a same-size file was unreadable, don't mislabel it as proven different.
            different = len(sizes_seen)>1 or (
                all(x.path in sha for x in items) and len({sha[x.path] for x in items})>1)
            if different:
                samenames.append(Group('same_name',sorted(items,key=lambda x:x.path.casefold()),
                       note='僅同名，內容不相同；不可僅憑此項進行刪除'))
        qualities = {}
        signatures = {}
        pillow = False
        ff_available = bool(ffmpeg_exe('ffmpeg') and ffmpeg_exe('ffprobe'))
        medias = []
        if use_media:
            try:
                from PIL import Image
                pillow = True
            except ImportError:
                Image = None
            ffmpeg,ffprobe = ffmpeg_exe('ffmpeg'),ffmpeg_exe('ffprobe')
            all_media = [x for items in sizes.values() for x in items if file_kind(x)]
            for i,x in enumerate(all_media,1):
                cancelled(event)
                kind = file_kind(x)
                try:
                    if (kind == 'photo' and Image) or (kind == 'video' and ffmpeg and ffprobe):
                        saved=cache.get_media(x,kind) if use_cache else None
                        if saved and snapshot(x):
                            qualities[x.path]=saved
                            hit_count+=1
                        else:
                            if kind=='photo':
                                qualities[x.path]=photo_signature(x,Image,event)
                            else:
                                qualities[x.path]=video_signature(x,ffprobe,ffmpeg,event)
                            cache.put_media(x,kind,qualities[x.path])
                except Cancelled: raise
                except Exception as exc:
                    if len(errors)<30: err(f'相似比對略過 {x.path}: {exc}')
                if i%2==0 or i==len(all_media): progress('進階媒體分析（可略過）',i,len(all_media))
            records = {x.path:x for x in all_media}
            medias = visually_similar_groups(qualities,records,sha)
        # The exact groups are prominently first. Similarity groups may overlap with exact groups.
        exacts.sort(key=lambda g: g.files[0].size*(len(g.files)-1),reverse=True)
        medias.sort(key=lambda g:max(x.size for x in g.files),reverse=True)
        samenames.sort(key=lambda g:len(g.files),reverse=True)
        cancelled(event)
        return Result(exacts+medias+samenames,count,hardlinks,hit_count,errors,
                      qualities,signatures,sha,ff_available,pillow)
    finally:
        cache.close()


def run_history(roots, use_media, event, progress, error):
    """Replay *only* previously recorded duplicate groups. No directory walk.

    Group invalidated if any recorded, still existing file has changed; missing
    paths are expected after deletion. Zero surviving copies is NOT 'processed'.
    """
    from dupsweeper_history import HistoryStore
    with HistoryStore() as store:
        # Use an earlier scan made without media analysis when a new media supplement exists.
        if use_media:
            try:
                created, data = store.load_scan(roots,True)
                base_media = True
            except __import__('dupsweeper_history').HistoryMissing:
                created, data = store.load_scan(roots,False)
                base_media = False
        else:
            created, data = store.load_scan(roots,False)
            base_media = False
        supplement = store.load_media_resume(roots,created,base_media) if use_media else None
        if use_media and not base_media and not supplement:
            raise __import__('dupsweeper_history').HistoryMissing('此歷史尚未補做相似分析。請按「補做相似比對」。')
        if supplement:
            _, extra = supplement
            data = dict(data)
            # A fresh media pass supersedes prior similar groups, not exact/name groups.
            data['groups'] = [rec for rec in data['groups'] if not rec['kind'].startswith('similar')] + extra['groups']
            data['qualities'] = {**data.get('qualities',{}), **extra.get('qualities',{})}
        groups=[]
        stats={'mode':'history','recorded_at':created,'media_resume_available':bool(supplement),
               'media_not_checked':bool(use_media and not supplement and not base_media),
               'processed_exact':0,
               'unresolved_exact':0,'stale_groups':0,'missing_all':0,
               'processed_near':0,'same_name_warnings':0,'checked_paths':0,
               'new_files_checked':False}
        # Same path may appear in exact, visual, and name-warning groups.
        states={}
        all_groups=data.get('groups',[])
        for i,rec in enumerate(all_groups,1):
            cancelled(event)
            survivors=[]
            is_stale=False
            for d in rec['files']:
                x=FileInfo(**d)
                if x.path not in states:
                    if os.path.lexists(x.path):
                        states[x.path]='valid' if snapshot(x) else 'changed'
                    else:
                        states[x.path]='missing'
                status=states[x.path]
                if status=='changed': is_stale=True
                elif status=='valid': survivors.append(x)
            if is_stale:
                stats['stale_groups']+=1
                continue
            if len(survivors)==0:
                stats['missing_all']+=1
                continue
            kind=rec['kind']
            if len(survivors)==1:
                if kind=='exact': stats['processed_exact']+=1
                elif kind.startswith('similar'): stats['processed_near']+=1
                continue
            if kind=='exact': stats['unresolved_exact']+=1
            elif kind=='same_name': stats['same_name_warnings']+=1
            groups.append(Group(kind, survivors,rec.get('key',''),rec.get('note','')))
            if i%100==0 or i==len(all_groups): progress('核對歷史檔案',i,len(all_groups))
        stats['checked_paths']=len(states)
        cancelled(event)
        store.record_check(roots,base_media,stats)
    groups.sort(key=lambda g:(0 if g.kind=='exact' else (1 if g.kind.startswith('similar') else 2),
                              -max(x.size for x in g.files)))
    # Expose only currently surviving candidates, never stale paths or completed groups.
    kept_paths={x.path for g in groups for x in g.files}
    result=Result(groups,data.get('count',0),data.get('hardlinks',0),0,[],
                  {p:q for p,q in data.get('qualities',{}).items() if p in kept_paths},
                  {}, {p:h for p,h in data.get('sha',{}).items() if p in kept_paths},
                  bool(ffmpeg_exe('ffmpeg') and ffmpeg_exe('ffprobe')),False,stats)
    return result


def list_media_files(roots, event, progress, error):
    """Enumerate CURRENT media files only; 本版歷史 has no full file inventory."""
    unique_paths = set()
    unique_inodes = set()
    found = []
    scanned = 0
    for root in roots:
        stack = [root]
        while stack:
            cancelled(event)
            path = stack.pop()
            try:
                with os.scandir(path) as items:
                    for item in items:
                        cancelled(event)
                        try:
                            if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()): continue
                            if item.is_dir(follow_symlinks=False):
                                stack.append(item.path)
                                continue
                            if not item.is_file(follow_symlinks=False): continue
                            scanned += 1
                            if Path(item.name).suffix.lower() not in IMAGE_EXT | VIDEO_EXT: continue
                            st = item.stat(follow_symlinks=False)
                            full = os.path.abspath(item.path)
                            if norm(full) in unique_paths: continue
                            unique_paths.add(norm(full))
                            if st.st_nlink > 1 and st.st_ino:
                                inode = (st.st_dev, st.st_ino)
                                if inode in unique_inodes: continue
                                unique_inodes.add(inode)
                            found.append(FileInfo(full,st.st_size,st.st_mtime_ns,st.st_dev,st.st_ino))
                        except (OSError,ValueError) as ex: error(f'{item.path}: {ex}')
                        if scanned % 500 == 0: progress('補掃媒體檔案清單',scanned,0)
            except (OSError,ValueError) as ex: error(f'{path}: {ex}')
    progress('媒體檔案清單完成',len(found),len(found))
    return found, scanned


def run_media_recheck(roots, event, progress, error):
    """Fill in 先前跳過 visual analysis without rehashing every other file.

    A full directory walk IS required: Completed scan history stores duplicate groups, not every
    scanned file. Original scan remains intact; visual-only data is a supplement.
    """
    from dupsweeper_history import HistoryStore
    with HistoryStore() as store:
        base_media, base_created, base_data = store.load_latest_scan(roots)
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError('缺少 Pillow，請重新執行 Windows 啟動檔以安裝。') from exc
    ffmpeg, ffprobe = ffmpeg_exe('ffmpeg'), ffmpeg_exe('ffprobe')
    if not ffmpeg or not ffprobe:
        raise RuntimeError('缺少 FFmpeg 或 FFprobe。請重新執行 Windows 啟動檔安裝，再補掃。')

    msgs=[]
    def err(msg):
        if len(msgs)<50: msgs.append(msg)
        error(msg)
    files, enumerated = list_media_files(roots, event, progress, err)
    records={x.path:x for x in files}
    qualities={}
    cache_hits=0
    cache=HashCache()
    try:
        for i,x in enumerate(files,1):
            cancelled(event)
            kind=file_kind(x)
            try:
                meta=cache.get_media(x,kind)
                if meta and snapshot(x):
                    cache_hits += 1
                else:
                    meta=photo_signature(x,Image,event) if kind=='photo' else video_signature(x,ffprobe,ffmpeg,event)
                    cache.put_media(x,kind,meta)
                qualities[x.path]=meta
            except Cancelled: raise
            except (OSError, ValueError, TimeoutError, RuntimeError) as exc:
                err(f'相似比對略過 {x.path}: {exc}')
            if i % 2 == 0 or i == len(files):
                progress('補做相似照片／影片比對',i,len(files))
    finally:
        cache.close()
    sha=base_data.get('sha',{})
    near=visually_similar_groups(qualities,records,sha)
    near.sort(key=lambda g:max(x.size for x in g.files),reverse=True)
    cancelled(event)
    with HistoryStore() as store:
        store.save_media_resume(roots,base_media,base_created,near,qualities)
    # Replay the recorded exact groups; do not silently treat historical changes as valid.
    base=run_history(roots,True,event,progress,error)
    base.errors.extend(msgs)
    base.cache_hits=cache_hits
    base.ffmpeg_available=True
    base.pillow_available=True
    base.history_info['mode']='media_resume'
    base.history_info['media_enumerated']=len(files)
    base.history_info['media_signature_failures']=len(msgs)
    base.history_info['media_resumed_at']=time.time()
    return base


def protected(path):
    def within(parent):
        try: return os.path.commonpath([norm(parent), norm(path)]) == norm(parent)
        except ValueError: return False
    if sys.platform=='win32':
        dirs = [os.environ.get('WINDIR',r'C:\Windows'), os.environ.get('ProgramFiles',r'C:\Program Files'),
                os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'),os.environ.get('ProgramData',r'C:\ProgramData'),
                os.environ.get('APPDATA'),os.environ.get('LOCALAPPDATA')]
    elif sys.platform=='darwin': dirs=['/System','/Library','/Applications','/usr','/bin','/sbin','/private',str(Path.home()/'Library')]
    else: dirs=['/usr','/bin','/sbin','/etc','/lib','/lib64','/var/lib','/boot','/run',
                str(Path.home()/'.config'),str(Path.home()/'.local'/'share')]
    return any(within(x) for x in dirs if x)


def trash_worker(plan,event,progress):
    """For exact matches, recompute both full hashes. For near-duplicates, recheck signatures.
    Called only after user's explicit confirmation. Never permanently deletes.
    """
    try: from send2trash import send2trash
    except ImportError: raise RuntimeError('缺少 send2trash；請執行安裝套件批次檔')
    done, errors = [], []
    Image = None
    try:
        from PIL import Image
    except ImportError: pass
    ffmpeg,ffprobe = ffmpeg_exe('ffmpeg'),ffmpeg_exe('ffprobe')
    for n, entry in enumerate(plan,1):
        cancelled(event)
        x, keeper, kind, expected = entry
        try:
            if protected(x.path) or not snapshot(x) or not snapshot(keeper): raise OSError('檔案已改變或屬系統位置')
            if kind == 'exact':
                if hash_file(x,event) != expected or hash_file(keeper,event) != expected:
                    raise OSError('檔案與掃描時的 SHA-256 不同')
            else:
                media_kind = 'photo' if kind=='similar_photo' else 'video'
                if media_kind=='photo' and Image:
                    qa = photo_signature(x,Image,event); qb=photo_signature(keeper,Image,event)
                elif media_kind=='video' and ffmpeg and ffprobe:
                    qa=video_signature(x,ffprobe,ffmpeg,event); qb=video_signature(keeper,ffprobe,ffmpeg,event)
                else: raise OSError('未安裝媒體驗證所需工具')
                if not close_visual(qa,qb,media_kind): raise OSError('重算後不符合相似條件')
            cancelled(event)
            if not snapshot(x) or not snapshot(keeper): raise OSError('檔案於驗證期間變更')
            send2trash(x.path)
            done.append(x.path)
        except Cancelled: raise
        except Exception as exc: errors.append(f'{x.path}: {exc}')
        progress('移至回收桶',n,len(plan))
    return done,errors


def child_worker(which, payload, event, events):
    def emit(t, *a):
        try: events.put((t,*a))
        except (OSError, ValueError): pass
    try:
        if which=='scan':
            from dupsweeper_history import HistoryStore
            full_refresh = len(payload)>2 and bool(payload[2])
            result = run_scan(payload[0],payload[1],event,
                              lambda stage,n,total:emit('progress',stage,n,total),
                              lambda msg:emit('error',msg),use_cache=not full_refresh)
            # Only a complete scan writes a snapshot, never a cancelled scan.
            try:
                with HistoryStore() as store:
                    store.save_scan(payload[0],payload[1],result)
            except (OSError,ValueError,sqlite3.Error) as exc:
                result.errors.append('歷史紀錄儲存失敗：'+str(exc))
            emit('done_scan',result)
        elif which=='media_resume':
            result=run_media_recheck(payload[0], event,
                          lambda stage,n,total:emit('progress',stage,n,total),
                          lambda msg:emit('error',msg))
            emit('done_scan',result)
        elif which=='history':
            result=run_history(payload[0],payload[1],event,
                               lambda stage,n,total:emit('progress',stage,n,total),
                               lambda msg:emit('error',msg))
            emit('done_scan',result)
        else:
            removed,errors = trash_worker(payload,event,
                              lambda stage,n,total:emit('progress',stage,n,total))
            emit('done_trash',removed,errors)
    except Cancelled: emit('cancelled')
    except BaseException as exc: emit('fatal',f'{type(exc).__name__}: {exc}')
