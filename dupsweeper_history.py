#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local, persistent snapshots of completed full scans. Not an inventory of new files.

History replay deliberately does *not* enumerate directories. Existing recorded files
are checked with lstat; changed files invalidate their entire group. Safe trashing
always rehashes exact matches and rechecks both keeper and candidate.
"""
from __future__ import annotations
import json
import os
import sqlite3
import sys
import time
import zlib
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

VERSION = 1


def storage_path():
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA') or str(Path.home())
    elif sys.platform == 'darwin':
        base = str(Path.home() / 'Library' / 'Application Support')
    else:
        base = os.environ.get('XDG_DATA_HOME') or str(Path.home() / '.local' / 'share')
    return os.path.join(base, 'DupSweeper', 'scan_history.sqlite3')


def scope_key(roots, use_media):
    import hashlib
    paths = sorted({os.path.normcase(os.path.abspath(p)) for p in roots})
    scope = json.dumps([paths, bool(use_media)], ensure_ascii=False)
    return hashlib.sha256(scope.encode('utf-8')).hexdigest()


class HistoryMissing(Exception):
    pass


class HistoryStore:
    def __init__(self):
        path = storage_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.db = sqlite3.connect(path, timeout=10)
        self.db.execute('''CREATE TABLE IF NOT EXISTS scans (
            scope TEXT PRIMARY KEY, roots TEXT NOT NULL, media INTEGER NOT NULL,
            created REAL NOT NULL, count INTEGER NOT NULL, group_count INTEGER NOT NULL,
            format_version INTEGER NOT NULL, payload BLOB NOT NULL,
            last_check REAL, last_summary TEXT)''')
        self.db.execute('''CREATE TABLE IF NOT EXISTS media_resumes (
            scope TEXT PRIMARY KEY, created REAL NOT NULL,
            base_created REAL NOT NULL, base_media INTEGER NOT NULL,
            payload BLOB NOT NULL)''')
        self.db.commit()

    def __enter__(self): return self

    def __exit__(self, *args): self.db.close()

    def save_scan(self, roots, use_media, result):
        # Only completed *full scans* can write this record; history reads never replace it.
        data = {
            'groups': [{'kind':g.kind, 'files':[asdict(x) for x in g.files],
                        'key':g.key, 'note':g.note} for g in result.groups],
            'qualities':result.qualities,
            'sha':result.sha,
            'count':result.count,
            'hardlinks':result.hardlinks,
        }
        blob=zlib.compress(json.dumps(data, ensure_ascii=False, separators=(',',':')).encode('utf-8'), level=6)
        with self.db:
            self.db.execute('''REPLACE INTO scans
                (scope,roots,media,created,count,group_count,format_version,payload,last_check,last_summary)
                VALUES (?,?,?,?,?,?,?,?,NULL,NULL)''',
                (scope_key(roots,use_media),json.dumps(sorted(roots),ensure_ascii=False),
                 int(bool(use_media)),time.time(),result.count,len(result.groups),VERSION,blob))

    def load_scan(self, roots, use_media):
        row = self.db.execute('''SELECT created,count,group_count,format_version,payload
                                 FROM scans WHERE scope=?''', (scope_key(roots,use_media),)).fetchone()
        if not row: raise HistoryMissing('目前選取的位置與進階模式沒有已儲存的完整掃描紀錄。請先執行「完整重新掃描」。')
        created,count,group_count,version,payload=row
        if version != VERSION: raise HistoryMissing('歷史紀錄版本已過期，請執行「完整重新掃描」。')
        try:
            data = json.loads(zlib.decompress(payload).decode('utf-8'))
        except (ValueError, TypeError, zlib.error) as exc:
            raise HistoryMissing('歷史紀錄無法讀取，請執行「完整重新掃描」。') from exc
        return created,data

    def load_latest_scan(self, roots):
        """Find existing 本版 scan for these roots, regardless of old media checkbox.

        本版 saved records only for detected groups, not a full manifest.
        """
        options = []
        for enabled in (False, True):
            try:
                when, data = self.load_scan(roots,enabled)
                options.append((enabled,when,data))
            except HistoryMissing:
                continue
        if not options:
            raise HistoryMissing('本版 歷史沒有這組掃描路徑，請先執行完整重新掃描。')
        return max(options,key=lambda row:row[1])

    def save_media_resume(self, roots, base_media, base_created, groups, qualities):
        """Media-only results live separately; they do NOT replace full-scan history."""
        data = {'groups': [{'kind':g.kind,'files':[asdict(x) for x in g.files],
                            'key':g.key,'note':g.note} for g in groups],
                'qualities':qualities}
        payload=zlib.compress(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode('utf-8'),6)
        with self.db:
            self.db.execute('REPLACE INTO media_resumes VALUES (?,?,?,?,?)',
                            (scope_key(roots,False),time.time(),base_created,int(base_media),payload))

    def load_media_resume(self, roots, base_created, base_media):
        row=self.db.execute('SELECT created,base_created,base_media,payload FROM media_resumes WHERE scope=?',
                            (scope_key(roots,False),)).fetchone()
        if not row: return None
        created, original_created, original_media, payload = row
        if original_created != base_created or bool(original_media) != bool(base_media):
            return None
        try:
            return created,json.loads(zlib.decompress(payload).decode('utf-8'))
        except (ValueError,TypeError,zlib.error): return None

    def record_check(self, roots, use_media, summary):
        with self.db:
            self.db.execute('UPDATE scans SET last_check=?,last_summary=? WHERE scope=?',
                            (time.time(),json.dumps(summary,ensure_ascii=False),scope_key(roots,use_media)))

    def summaries(self):
        rows=self.db.execute('''SELECT scope,roots,media,created,count,group_count,last_check,last_summary
                                FROM scans ORDER BY created DESC LIMIT 60''').fetchall()
        summaries=[]
        for scope,roots,media,created,count,groups,checked,details in rows:
            rootlist=json.loads(roots)
            supplement=self.load_media_resume(rootlist,created,bool(media))
            summaries.append({'roots':rootlist,'media':bool(media),
                'media_resumed_at':datetime.fromtimestamp(supplement[0]).strftime('%Y-%m-%d %H:%M:%S') if supplement else '',
                'created':datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M:%S'),
                'count':count, 'groups':groups,
                'last_check':datetime.fromtimestamp(checked).strftime('%Y-%m-%d %H:%M:%S') if checked else '',
                'details':json.loads(details) if details else {}})
        return summaries
