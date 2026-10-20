#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final standalone local file organizer. Safe, review-first workflow."""
from __future__ import annotations
import csv
import json
import multiprocessing as mp
import os
import queue
import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from duplicate_engine import (Group, Result, FileInfo, child_worker, choose_keeper, smart_marks,
                              file_kind, norm, inside_folder, inside_any_folder, protected, snapshot, ffmpeg_exe)
from history_store import HistoryStore, storage_path
try:
    from send2trash import send2trash
except ImportError:
    send2trash = None


def readable(n):
    n = float(n)
    for suffix in ('B','KB','MB','GB','TB','PB'):
        if n < 1024 or suffix=='PB': return f'{n:,.0f} {suffix}' if suffix=='B' else f'{n:,.2f} {suffix}'
        n /= 1024


def mtime(x):
    try: return datetime.fromtimestamp(x.mtime_ns/1e9).strftime('%Y-%m-%d %H:%M')
    except (OverflowError,OSError,ValueError): return ''


def stats_string(x, q):
    if not q: return ''
    base=f"{q.get('width',0)}×{q.get('height',0)}"
    if q.get('kind') == 'video':
        base += f"｜{q.get('duration',0):.1f} 秒｜{q.get('fps',0):.1f} fps"
        if q.get('bitrate'): base += f"｜{q['bitrate']/1000000:.2f} Mbps"
    return base


class App:
    def __init__(self,root):
        self.root=root
        root.title('檔案整理助手｜獨立最終版')
        root.geometry('1240x800')
        root.minsize(720,680)
        self.paths=[]
        self.preferred_paths=self._load_preferences()
        self.result=None
        self.marks=set()
        self.ctx=mp.get_context('spawn')
        self.proc=None
        self.event=None
        self.messages=None
        self.mode=None
        self.finished=False
        self.dead_ticks=0
        self.item_map={}
        self.row_groups={}
        self.filter_job=None
        self.dirty=False
        self.view_limit=200
        self._build()
        self.root.after(120,self._poll)
        self.root.protocol('WM_DELETE_WINDOW',self._quit)

    def _init_theme(self):
        # Muted pastel palette with high-contrast typography; do not recolor system dialogs.
        self.colors = {
            'bg':'#F6F7F5', 'surface':'#FFFFFF', 'sage':'#E1EDE5',
            'lavender':'#EAE5F2', 'blue':'#E3ECF2', 'peach':'#F3E6E1',
            'text':'#2D3842', 'muted':'#64717D', 'line':'#D8E0E2',
            'accent':'#527C72', 'warn':'#875F4C', 'red':'#915456'
        }
        c=self.colors
        self.root.configure(background=c['bg'])
        style=ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.',font=('Microsoft JhengHei UI' if sys.platform=='win32' else ('PingFang TC' if sys.platform=='darwin' else 'Noto Sans CJK TC'),10),
                        background=c['bg'],foreground=c['text'])
        style.configure('Base.TFrame',background=c['bg'])
        style.configure('Panel.TFrame',background=c['surface'])
        style.configure('Panel.TLabelframe',background=c['surface'],borderwidth=1,relief='solid')
        style.configure('Panel.TLabelframe.Label',background=c['surface'],foreground=c['text'],font=('',10,'bold'))
        style.configure('Panel.TLabel',background=c['surface'],foreground=c['text'])
        style.configure('Muted.TLabel',background=c['bg'],foreground=c['muted'])
        style.configure('PanelMuted.TLabel',background=c['surface'],foreground=c['muted'])
        style.configure('Header.TLabel',font=('',18,'bold'),background=c['bg'],foreground=c['text'])
        style.configure('TButton',padding=(12,8),borderwidth=1,background=c['blue'],
                        foreground=c['text'],relief='flat')
        style.map('TButton',background=[('active',c['sage']),('disabled','#F0F1F2')],
                  foreground=[('disabled','#9BA4AA')])
        style.configure('Primary.TButton',background=c['sage'],foreground='#25483E',font=('',10,'bold'))
        style.map('Primary.TButton',background=[('active','#D0E5D7')])
        style.configure('Danger.TButton',background=c['peach'],foreground='#80494B',font=('',10,'bold'))
        style.map('Danger.TButton',background=[('active','#EED6D2')])
        style.configure('TCheckbutton',background=c['surface'],foreground=c['text'],padding=3)
        style.map('TCheckbutton',background=[('active',c['surface'])])
        style.configure('Treeview',background=c['surface'],fieldbackground=c['surface'],
                        foreground=c['text'],rowheight=29,borderwidth=0)
        style.map('Treeview',background=[('selected',c['lavender'])],foreground=[('selected',c['text'])])
        style.configure('Treeview.Heading',background=c['blue'],foreground=c['text'],padding=7,
                        font=('',10,'bold'),relief='flat')
        style.configure('TEntry',padding=5,fieldbackground=c['surface'])
        style.configure('TProgressbar',background=c['accent'],troughcolor=c['blue'],borderwidth=0)

    def _build(self):
        self._init_theme()
        c=self.colors
        main=ttk.Frame(self.root,style='Base.TFrame',padding=(16,12))
        main.pack(fill='both',expand=True)
        main.columnconfigure(0,weight=1)
        main.rowconfigure(3,weight=1)
        header=ttk.Frame(main,style='Base.TFrame')
        header.grid(row=0,column=0,sticky='ew',pady=(0,9))
        header.columnconfigure(0,weight=1)
        ttk.Label(header,text='檔案整理助手',style='Header.TLabel').grid(row=0,column=0,sticky='w')
        ttk.Label(header,text='找重複、選保留、確認後移除',style='Muted.TLabel').grid(row=1,column=0,sticky='w',pady=(1,0))
        ttk.Label(header,text='獨立最終版  ·  本機處理',style='Muted.TLabel').grid(row=0,column=1,sticky='e')
        self.settings_expanded=False
        self.settings_toggle=ttk.Button(header,text='收合設定',command=self._toggle_settings)
        self.settings_toggle.grid(row=1,column=1,sticky='e')

        tools=ttk.Frame(main,style='Base.TFrame')
        tools.grid(row=1,column=0,sticky='ew',pady=(0,8))
        self.history_btn=ttk.Button(tools,text='歷史快速檢查',command=self._start_history)
        self.scan=ttk.Button(tools,text='完整重新掃描',style='Primary.TButton',command=self._start_scan)
        self.resume_btn=ttk.Button(tools,text='補做相似比對',command=self._start_media_resume)
        self.history_view=ttk.Button(tools,text='查看歷史',command=self._show_history)
        self.stop=ttk.Button(tools,text='安全停止',command=self._soft_stop,state='disabled')
        self.kill=ttk.Button(tools,text='強制停止',style='Danger.TButton',command=self._force_stop,state='disabled')
        self.toolbar_buttons=[self.history_btn,self.scan,self.resume_btn,self.history_view,self.stop,self.kill]
        for j,b in enumerate(self.toolbar_buttons): b.grid(row=0,column=j,sticky='ew',padx=(0,6))
        
        progress=ttk.Frame(main,style='Base.TFrame')
        progress.grid(row=2,column=0,sticky='ew',pady=(0,9))
        progress.columnconfigure(0,weight=1)
        self.progress_var=tk.StringVar(value='就緒：請加入掃描位置。')
        ttk.Label(progress,textvariable=self.progress_var,style='Muted.TLabel').grid(row=0,column=0,sticky='w')
        self.pb=ttk.Progressbar(progress,mode='determinate',maximum=100)
        self.pb.grid(row=1,column=0,sticky='ew',pady=(5,0))
        
        self.workspace=ttk.Frame(main,style='Base.TFrame')
        self.workspace.grid(row=3,column=0,sticky='nsew')
        self.workspace.rowconfigure(0,weight=1)
        self.workspace.columnconfigure(1,weight=1)
        
        settings=ttk.Frame(self.workspace,style='Panel.TFrame',padding=12)
        self.settings_panel=settings
        settings.grid(row=0,column=0,sticky='nsew',padx=(0,12))
        settings.columnconfigure(0,weight=1)
        
        # Both path pickers are intentionally visible; advanced controls are compact.
        folder_frame=ttk.LabelFrame(settings,text='掃描位置',padding=(9,8),style='Panel.TLabelframe')
        self.folder_frame=folder_frame
        folder_frame.grid(row=0,column=0,sticky='ew')
        folder_frame.columnconfigure(0,weight=1)
        self.folders=tk.Listbox(folder_frame,height=4,selectmode='extended',exportselection=False,
                  relief='flat',highlightthickness=1,highlightbackground=c['line'],
                  bg=c['bg'],fg=c['text'],selectbackground=c['lavender'],selectforeground=c['text'])
        self.folders.grid(row=0,column=0,columnspan=3,sticky='ew',pady=(0,7))
        self.folder_add=ttk.Button(folder_frame,text='+ 加入',command=self._add)
        self.folder_remove=ttk.Button(folder_frame,text='移除',command=self._remove)
        self.folder_clear=ttk.Button(folder_frame,text='清空',command=self._clear_roots)
        for j,b in enumerate([self.folder_add,self.folder_remove,self.folder_clear]):
            folder_frame.columnconfigure(j,weight=1)
            b.grid(row=1,column=j,sticky='ew',padx=(0,4) if j<2 else 0)

        pref=ttk.LabelFrame(settings,text='優先保留的資料夾（可多選）',padding=(9,8),style='Panel.TLabelframe')
        self.pref_frame=pref
        pref.grid(row=1,column=0,sticky='ew',pady=(11,0))
        pref.columnconfigure(0,weight=1)
        self.preferred_list=tk.Listbox(pref,height=3,selectmode='extended',exportselection=False,
                  relief='flat',highlightthickness=1,highlightbackground=c['line'],
                  bg=c['bg'],fg=c['text'],selectbackground=c['lavender'],selectforeground=c['text'])
        self.preferred_list.grid(row=0,column=0,columnspan=3,sticky='ew',pady=(0,7))
        for folder in self.preferred_paths:self.preferred_list.insert('end',folder)
        self.pref_add=ttk.Button(pref,text='+ 加入',command=self._choose_preferred)
        self.pref_remove=ttk.Button(pref,text='移除',command=self._remove_preferred)
        self.pref_clear=ttk.Button(pref,text='清空',command=self._clear_preferred)
        for j,b in enumerate([self.pref_add,self.pref_remove,self.pref_clear]):
            pref.columnconfigure(j,weight=1)
            b.grid(row=1,column=j,sticky='ew',padx=(0,4) if j<2 else 0)
        ttk.Label(pref,text='有優先資料夾時，先從其中挑品質最佳版本。',
                  style='PanelMuted.TLabel',wraplength=275).grid(row=2,column=0,columnspan=3,sticky='w',pady=(8,0))

        opts=ttk.LabelFrame(settings,text='相似照片與影片',padding=(9,8),style='Panel.TLabelframe')
        self.opts_frame=opts
        opts.grid(row=2,column=0,sticky='ew',pady=(11,0))
        self.media_opt=tk.BooleanVar(value=self._load_media_setting())
        ttk.Checkbutton(opts,text='啟用相似媒體分析',variable=self.media_opt,
                        command=self._save_preference).pack(anchor='w')
        self.allow_near=tk.BooleanVar(value=False)
        ttk.Checkbutton(opts,text='允許標記相似媒體（高風險）',variable=self.allow_near).pack(anchor='w',pady=(3,0))
        ttk.Label(opts,text='相似不代表相同；移除前請自行預覽。',
                  style='PanelMuted.TLabel',wraplength=275).pack(anchor='w',pady=(6,0))

        results=ttk.Frame(self.workspace,style='Panel.TFrame',padding=(11,10))
        self.results_panel=results
        results.grid(row=0,column=1,sticky='nsew')
        results.columnconfigure(0,weight=1)
        results.rowconfigure(1,weight=1)
        search=ttk.Frame(results,style='Panel.TFrame')
        search.grid(row=0,column=0,sticky='ew',pady=(0,7))
        search.columnconfigure(0,weight=1)
        self.summary=tk.StringVar(value='尚無掃描結果')
        ttk.Label(search,textvariable=self.summary,style='Panel.TLabel',wraplength=800).grid(row=0,column=0,sticky='w')
        self.filter=tk.StringVar()
        entry=ttk.Entry(search,textvariable=self.filter,width=22)
        entry.grid(row=0,column=1,sticky='e',padx=(7,0))
        entry.insert(0,'')
        self.filter.trace_add('write',lambda *_:self._schedule_filter())
        cols=('state','size','quality','path')
        self.tree=ttk.Treeview(results,columns=cols,show='tree headings',selectmode='extended')
        for k,t in [('#0','群組／檔案'),('state','建議'),('size','大小'),('quality','畫質'),('path','位置')]:
            self.tree.heading(k,text=t)
        self.tree.column('#0',width=215,minwidth=150,stretch=False)
        self.tree.column('state',width=135,minwidth=105,stretch=False)
        self.tree.column('size',width=90,minwidth=65,anchor='e',stretch=False)
        self.tree.column('quality',width=150,minwidth=85,stretch=False)
        self.tree.column('path',width=310,minwidth=110,stretch=True)
        self.tree.grid(row=1,column=0,sticky='nsew')
        sy=ttk.Scrollbar(results,orient='vertical',command=self.tree.yview)
        sx=ttk.Scrollbar(results,orient='horizontal',command=self.tree.xview)
        sy.grid(row=1,column=1,sticky='ns')
        sx.grid(row=2,column=0,sticky='ew')
        self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        self.tree.tag_configure('warn',foreground='#946947')
        self.tree.tag_configure('marked',foreground='#9A4E56')
        self.tree.tag_configure('keeper',foreground='#477B64')
        self.tree.tag_configure('protected',foreground='#69747D')
        self.tree.tag_configure('near',foreground='#587897')
        self.tree.bind('<Double-1>',self._double)
        self.tree.bind('<Control-c>',lambda ev:self._copy())
        self.more=ttk.Button(results,text='顯示更多結果',command=self._load_more)
        self.more.grid(row=3,column=0,sticky='e',pady=(5,0))
        self.more.grid_remove()

        actions=ttk.Frame(main,style='Base.TFrame')
        actions.grid(row=4,column=0,sticky='ew',pady=(10,4))
        self.smart=ttk.Button(actions,text='智慧選取',style='Primary.TButton',command=self._smart)
        self.mark=ttk.Button(actions,text='標記所選',command=self._mark)
        self.unmark=ttk.Button(actions,text='清除標記',command=self._unmark)
        self.trash=ttk.Button(actions,text='確認移至回收桶',style='Danger.TButton',command=self._trash)
        self.open_btn=ttk.Button(actions,text='開啟檔案位置',command=self._open)
        self.copy_btn=ttk.Button(actions,text='複製路徑',command=self._copy)
        self.csv_btn=ttk.Button(actions,text='匯出 CSV',command=self._csv)
        self.action_buttons=[self.smart,self.mark,self.unmark,self.trash,self.open_btn,self.copy_btn,self.csv_btn]
        for j,b in enumerate(self.action_buttons):b.grid(row=0,column=j,sticky='ew',padx=(0,6))
        self.marked_label=tk.StringVar(value='待移除：0 份')
        ttk.Label(main,textvariable=self.marked_label,style='Muted.TLabel').grid(row=5,column=0,sticky='w')
        self.root.bind('<Configure>',self._adapt,add='+')
        self._adapt_layout(self.root.winfo_width())

    def _adapt(self,event):
        if event.widget is self.root:self._adapt_layout(event.width)

    def _adapt_layout(self,width):
        compact = width < 1040
        tiny = width < 840
        if getattr(self,'_compact',None) != compact:
            self._compact=compact
            for x in (self.folder_frame,self.pref_frame,self.opts_frame):x.grid_forget()
            for j in range(3):self.settings_panel.columnconfigure(j,weight=0)
            self.settings_panel.grid_forget()
            self.results_panel.grid_forget()
            self.workspace.columnconfigure(0,weight=0)
            self.workspace.columnconfigure(1,weight=0)
            self.workspace.rowconfigure(0,weight=0)
            self.workspace.rowconfigure(1,weight=0)
            if compact:
                self.settings_panel.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,8))
                self.results_panel.grid(row=1,column=0,columnspan=2,sticky='nsew')
                self.workspace.columnconfigure(0,weight=1)
                self.workspace.rowconfigure(1,weight=1)
                # In compact mode minimize vertical space consumed by the settings.
                self.settings_panel.columnconfigure(0,weight=1)
                self.settings_panel.columnconfigure(1,weight=1)
                self.settings_panel.columnconfigure(2,weight=1)
                self.folder_frame.grid(row=0,column=0,sticky='nsew',padx=(0,6))
                self.pref_frame.grid(row=0,column=1,sticky='nsew',padx=(0,6))
                self.opts_frame.grid(row=0,column=2,sticky='nsew')
                self.folders.configure(height=3)
                self.preferred_list.configure(height=3)
            else:
                self.settings_panel.grid(row=0,column=0,sticky='nsw',padx=(0,12))
                self.results_panel.grid(row=0,column=1,sticky='nsew')
                self.workspace.columnconfigure(1,weight=1)
                self.workspace.rowconfigure(0,weight=1)
                self.folder_frame.grid(row=0,column=0,sticky='ew')
                self.pref_frame.grid(row=1,column=0,sticky='ew',pady=(11,0))
                self.opts_frame.grid(row=2,column=0,sticky='ew',pady=(11,0))
                self.folders.configure(height=4)
                self.preferred_list.configure(height=3)
        if getattr(self,'_tiny',None) != tiny:
            self._tiny=tiny
            for b in self.toolbar_buttons:b.grid_forget()
            for j,b in enumerate(self.toolbar_buttons):
                row,col=divmod(j,3 if tiny else 6)
                b.grid(row=row,column=col,sticky='ew',padx=(0,6),pady=(0,5))
            for b in self.action_buttons:b.grid_forget()
            for j,b in enumerate(self.action_buttons):
                row,col=divmod(j,4 if tiny else 7)
                b.grid(row=row,column=col,sticky='ew',padx=(0,6),pady=(0,5))
        self.tree.column('#0',width=175 if compact else 220)
        self.tree.column('quality',width=95 if compact else 155)
        self.settings_toggle.grid() if compact else self.settings_toggle.grid_remove()
        self._sync_settings_visible()

    def _toggle_settings(self):
        self.settings_expanded=not self.settings_expanded
        self._sync_settings_visible()

    def _sync_settings_visible(self):
        if not getattr(self,'_compact',False):return
        if self.settings_expanded:
            self.settings_panel.grid()
            self.results_panel.grid_configure(row=1)
            self.workspace.rowconfigure(0,weight=0)
            self.workspace.rowconfigure(1,weight=1)
            self.settings_toggle.configure(text='收合設定')
        else:
            self.settings_panel.grid_remove()
            self.results_panel.grid_configure(row=0)
            self.workspace.rowconfigure(0,weight=1)
            self.workspace.rowconfigure(1,weight=0)
            self.settings_toggle.configure(text='展開設定')

    def _load_preferences(self):
        try:
            with open(os.path.join(os.path.dirname(storage_path()), 'settings.json'), encoding='utf-8') as f:
                data=json.load(f)
            items=data.get('preferred_folders', [])
            return list(dict.fromkeys(os.path.abspath(p) for p in items if isinstance(p,str) and p))
        except (OSError, ValueError, TypeError):
            return []

    def _load_media_setting(self):
        try:
            with open(os.path.join(os.path.dirname(storage_path()),'settings.json'),encoding='utf-8') as f:
                return bool(json.load(f).get('media_enabled',False))
        except (OSError,ValueError,TypeError):return False

    def _save_preference(self):
        try:
            path=os.path.join(os.path.dirname(storage_path()),'settings.json')
            os.makedirs(os.path.dirname(path),exist_ok=True)
            with open(path,'w',encoding='utf-8') as f:
                json.dump({'preferred_folders':self.preferred_paths,
                           'media_enabled':bool(self.media_opt.get()) if hasattr(self,'media_opt') else False},
                          f,ensure_ascii=False,indent=2)
        except OSError as exc:
            messagebox.showwarning('偏好設定未儲存',str(exc))

    def _update_preferred(self, paths):
        if paths==self.preferred_paths: return
        self.preferred_paths=paths
        self.preferred_list.delete(0,'end')
        for path in paths:self.preferred_list.insert('end',path)
        self._save_preference()
        if self.marks:
            self.marks.clear()
            messagebox.showinfo('標記已清空','優先保留位置已改變，請重新執行智慧選取。')
        if self.result:self._refresh()

    def _choose_preferred(self):
        folder=filedialog.askdirectory(title='新增智慧保留優先資料夾',mustexist=True)
        if folder and norm(folder) not in {norm(x) for x in self.preferred_paths}:
            self._update_preferred(self.preferred_paths+[os.path.abspath(folder)])

    def _remove_preferred(self):
        indexes=set(self.preferred_list.curselection())
        if indexes:self._update_preferred([p for i,p in enumerate(self.preferred_paths) if i not in indexes])

    def _clear_preferred(self):
        self._update_preferred([])

    def _show_history(self):
        try:
            with HistoryStore() as store: items=store.summaries()
        except Exception as exc:
            messagebox.showerror('無法讀取歷史',str(exc)); return
        w=tk.Toplevel(self.root)
        w.title('完整掃描歷史')
        w.geometry('1020x470')
        frame=ttk.Frame(w,padding=12)
        frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='選擇本版完成的掃描紀錄，可載入掃描位置或補做相似媒體比對。',
                  wraplength=980).pack(anchor='w',pady=(0,8))
        cols=('date','media','resume','files','groups','paths')
        tree=ttk.Treeview(frame,columns=cols,show='headings',selectmode='browse')
        for name,label,width in [('date','完整掃描時間',170),('media','原進階模式',90),('resume','已補掃',95),('files','掃描份數',95),('groups','群組數',95),('paths','掃描位置',500)]:
            tree.heading(name,text=label)
            tree.column(name,width=width)
        tree.pack(fill='both',expand=True)
        for i,item in enumerate(items):
            tree.insert('','end',iid=str(i),values=(item['created'],'有' if item['media'] else '無',
                   '有' if item.get('media_resumed_at') else '無',item['count'],item['groups'],'；'.join(item['roots'])))
        def load_old(and_resume=False):
            chosen=tree.selection()
            if not chosen:
                messagebox.showinfo('先選擇紀錄','請先點選一筆歷史掃描紀錄。',parent=w);return
            old=items[int(chosen[0])]
            missing=[p for p in old['roots'] if not os.path.isdir(p)]
            if missing:
                messagebox.showwarning('有掃描路徑不存在','\n'.join(missing)+'\n請確認磁碟已連接且磁碟代號沒有變更。',parent=w)
                return
            self.paths=list(old['roots'])
            self.folders.delete(0,'end')
            for folder in self.paths:self.folders.insert('end',folder)
            self.media_opt.set(True)
            self._save_preference()
            w.destroy()
            if and_resume:self._start_media_resume()
            else:self.progress_var.set('已載入掃描位置；可按「補做上次跳過的相似比對」。')
        buttons=ttk.Frame(frame)
        buttons.pack(fill='x',pady=(8,0))
        ttk.Button(buttons,text='載入掃描位置',command=load_old).pack(side='left',padx=(0,8))
        ttk.Button(buttons,text='載入並立即補掃相似媒體',command=lambda:load_old(True)).pack(side='left')
        ttk.Button(buttons,text='關閉',command=w.destroy).pack(side='right')

    def _add(self):
        path=filedialog.askdirectory(title='選取硬碟或資料夾',mustexist=True)
        if path and norm(path) not in [norm(p) for p in self.paths]:
            self.paths.append(os.path.abspath(path))
            self.folders.insert('end',self.paths[-1])

    def _remove(self):
        for i in reversed(self.folders.curselection()):
            self.folders.delete(i)
            self.paths.pop(i)

    def _clear_roots(self):
        self.paths.clear()
        self.folders.delete(0,'end')

    def _setbusy(self,busy,mode=None):
        self.mode=mode if busy else None
        for x in [self.folder_add,self.folder_remove,self.folder_clear,self.pref_add,self.pref_remove,
                  self.pref_clear,self.scan,self.history_btn,self.resume_btn,self.history_view,self.smart,
                  self.mark,self.unmark,self.trash,self.csv_btn]:
            x.configure(state='disabled' if busy else 'normal')
        self.stop.configure(state='normal' if busy else 'disabled')
        self.kill.configure(state='normal' if busy else 'disabled')
        if not busy: self.pb['value']=0

    def _launch(self,mode,payload):
        self.event=self.ctx.Event()
        self.messages=self.ctx.Queue()
        self.finished=False
        self.dead_ticks=0
        self.proc=self.ctx.Process(target=child_worker,args=(mode,payload,self.event,self.messages),daemon=True)
        self.proc.start()
        self._setbusy(True,mode)
        if getattr(self,'_compact',False):
            self.settings_expanded=False
            self._sync_settings_visible()

    def _start_scan(self):
        roots=[x for x in self.paths if os.path.isdir(x)]
        if not roots:
            messagebox.showinfo('尚未指定掃描位置','請先加入至少一個資料夾或硬碟。')
            return
        self.result=None
        self.marks.clear()
        self._render()
        self.progress_var.set('完整重新掃描：不讀取歷史紀錄與 SHA 快取，檢查範圍內所有可存取檔案。')
        self._launch('scan',(roots,self.media_opt.get(),True))

    def _start_media_resume(self):
        roots=[x for x in self.paths if os.path.isdir(x)]
        if not roots:
            messagebox.showinfo('尚未設定掃描位置','請先選擇有完整掃描歷史的資料夾。')
            return
        try:
            with HistoryStore() as store: store.load_latest_scan(roots)
        except Exception as exc:
            messagebox.showwarning('尚無符合的歷史紀錄',str(exc));return
        if not messagebox.askyesno('補做上次跳過的相似分析',
                    '歷史未儲存完整檔案清單。\n\n程式將使用這筆歷史的路徑，重新找出照片與影片並補算視覺特徵。'
                    '\n一般檔案不重新計算完整 SHA-256，原本完整掃描歷史會保留。'
                    '\n\n這仍需要時間，且不代表全部新檔案已完成精確重複搜尋。是否繼續？',icon='question'):return
        self.media_opt.set(True)
        self._save_preference()
        self.result=None
        self.marks.clear()
        self._render()
        self.progress_var.set('正讀取本版歷史，補掃原磁碟中的照片／影片；可強制停止。')
        self._launch('media_resume',(roots,True))

    def _start_history(self):
        roots=[x for x in self.paths if os.path.isdir(x)]
        if not roots:
            messagebox.showinfo('尚未指定掃描位置','請先加入至少一個資料夾或硬碟。')
            return
        self.result=None
        self.marks.clear()
        self._render()
        self.progress_var.set('歷史檢查只核對已記錄群組；要補做先前未完成的照片／影片分析，請選擇補做相似比對。')
        self._launch('history',(roots,self.media_opt.get()))

    def _soft_stop(self):
        if self.mode:
            self.event.set()
            self.progress_var.set('已要求安全中斷，正在結束目前操作；如未及時停止可按「強制停止」。')

    def _force_stop(self):
        if not self.mode: return
        if not messagebox.askyesno('確認強制停止',
               '強制停止將立即終止掃描／移動程序。若正在移至回收桶，部分檔案可能已移動，必須重新掃描才能繼續。\n\n確定強制停止？',icon='warning'):
            return
        old=self.mode
        self.event.set()
        if self.proc and self.proc.is_alive():
            self.proc.terminate()
            self.proc.join(timeout=1.5)
            if self.proc.is_alive():
                self.proc.kill()
                self.proc.join(timeout=1.0)
        self._finished()
        if old=='trash':
            self.result=None
            self.marks.clear()
            self._render()
            self.progress_var.set('已強制停止移動程序；狀態可能部分更新，請重新掃描。')
            messagebox.showwarning('請重新掃描','移動中途被強制停止，結果已清空；請重新掃描確認檔案位置。')
        else: self.progress_var.set('已強制停止掃描，未進行任何刪除。')

    def _finished(self):
        self._setbusy(False)
        if self.proc:
            try: self.proc.join(timeout=.05)
            except Exception: pass
        self.proc=None
        if self.messages:
            try: self.messages.close()
            except Exception: pass
        self.messages=None
        self.event=None

    def _poll(self):
        try:
            if self.mode and self.messages:
                for _ in range(120):
                    try: kind,*args=self.messages.get_nowait()
                    except queue.Empty: break
                    if kind=='progress':
                        phase,done,total=args
                        self.progress_var.set(f'{phase}：{done:,}'+(f' / {total:,}' if total else ''))
                        if total:
                            self.pb['value']=100*done/max(1,total)
                        else:
                            self.pb['value']=0
                    elif kind=='error':
                        pass # errors are summarized in Result
                    elif kind=='done_scan':
                        was_history=self.mode=='history'
                        was_resume=self.mode=='media_resume'
                        self.result=args[0]
                        self.marks.clear()
                        if was_history or was_resume:
                            self.marks=smart_marks(self.result,self.preferred_paths,False)
                        self._render()
                        r=self.result
                        self._finished()
                        if was_history or was_resume:
                            info=r.history_info
                            when=datetime.fromtimestamp(info['recorded_at']).strftime('%Y-%m-%d %H:%M')
                            self.progress_var.set(('補掃媒體完成｜' if was_resume else '')+f'歷史紀錄（{when}）：未處理精確 {info["unresolved_exact"]} 組／已處理略過 {info["processed_exact"]} 組｜自動標記 {len(self.marks)} 份｜異動需重掃 {info["stale_groups"]} 組｜全部缺失 {info["missing_all"]} 組。'+('媒體已重列舉；新檔案的精確重複仍須完整掃描。' if was_resume else '新增檔案未檢查。'))
                            if was_resume:
                                self.progress_var.set(self.progress_var.get()+f'｜分析媒體 {info.get("media_enumerated",0)} 份；失敗 {info.get("media_signature_failures",0)} 份。')
                            if info['stale_groups'] or info['missing_all']:
                                messagebox.showwarning('部分歷史內容無法沿用',
                                    f'已變更的群組：{info["stale_groups"]}\n所有已知副本都消失的群組：{info["missing_all"]}\n\n這些群組已跳過，沒有自動標記。請使用「完整重新掃描」查清楚。')
                        else:
                            self.progress_var.set(f'完整掃描完成：{r.count:,} 份檔案｜'+('歷史儲存失敗' if any('歷史紀錄儲存失敗' in msg for msg in r.errors) else '已建立新歷史')+f'｜略過硬連結 {r.hardlinks:,}｜例外 {len(r.errors):,} 筆')
                            if any('歷史紀錄儲存失敗' in msg for msg in r.errors):
                                messagebox.showwarning('歷史紀錄未儲存', '\n'.join(r.errors))
                        if not was_history and self.media_opt.get() and (not r.pillow_available or not r.ffmpeg_available):
                            missing=[]
                            if not r.pillow_available: missing.append('Pillow（相似照片）')
                            if not r.ffmpeg_available: missing.append('FFmpeg＋FFprobe（相似影片）')
                            messagebox.showwarning('部分相似比對未執行', '缺少：'+', '.join(missing)+'。\n精確重複與同名警示仍正常。請參考 README.md 安裝。')
                        break
                    elif kind=='done_trash':
                        removed,failures=args
                        self._finished()
                        self.result=None
                        self.marks.clear()
                        self._render()
                        self.progress_var.set(f'已移至回收桶 {len(removed)} 份，失敗 {len(failures)} 份。為防止結果過期，請重新掃描。')
                        messagebox.showinfo('處理完成',f'已移至回收桶：{len(removed)} 份\n未成功：{len(failures)} 份\n\n請重新掃描。'+
                                            ('\n\n'+ '\n'.join(failures[:5]) if failures else ''))
                        break
                    elif kind in ('cancelled','fatal'):
                        self._finished()
                        self.progress_var.set('已停止。' if kind=='cancelled' else '錯誤：'+args[0])
                        if kind=='fatal': messagebox.showerror('作業錯誤',args[0])
                        break
                if self.mode and self.proc and not self.proc.is_alive():
                    self.dead_ticks += 1
                    if self.dead_ticks>12:
                        was=self.mode
                        self._finished()
                        if was=='trash':
                            self.result=None
                            self.marks.clear()
                            self._render()
                        self.progress_var.set('背景工作異常結束；如有移動操作，請重新掃描。')
                else: self.dead_ticks=0
        finally:
            self.root.after(130,self._poll)

    def _schedule_filter(self):
        self.view_limit=200
        if self.filter_job: self.root.after_cancel(self.filter_job)
        self.filter_job=self.root.after(230,self._render)

    def _load_more(self):
        self.view_limit+=200
        self._render()

    def _render(self):
        self.filter_job=None
        self.more.grid_remove()
        self.tree.delete(*self.tree.get_children())
        self.item_map.clear()
        self.row_groups.clear()
        if not self.result:
            self.summary.set('尚無掃描結果。')
            self.marked_label.set('待移除：0 份')
            return
        q=self.filter.get().casefold().strip()
        kind_name={'exact':'內容完全相同','same_name':'同名但內容不同！',
                   'similar_photo':'相似照片（人工判讀）','similar_video':'相似影片（人工判讀）'}
        filtered=[(n,g) for n,g in enumerate(self.result.groups,1)
                  if not q or any(q in x.path.casefold() for x in g.files) or q in kind_name[g.kind]]
        for n,g in filtered[:self.view_limit]:
            group_id=f'g{n}'
            note = (f'可省 {readable(sum(x.size for x in g.files)-max(x.size for x in g.files))}' if g.kind=='exact'
                    else g.note)
            self.tree.insert('', 'end',iid=group_id,
                             text=f'{n:04d}｜{kind_name[g.kind]}（{len(g.files)} 份）',
                             values=('', '', '', note), open=(len(self.result.groups)<160))
            self.row_groups[group_id]=g
            keeper=choose_keeper(g.files,self.result.qualities,self.preferred_paths)
            for j,x in enumerate(g.files):
                iid=f'f{n}-{j}'
                state,tag=self._state(x,g,keeper)
                self.tree.insert(group_id,'end',iid=iid,text=os.path.basename(x.path),
                       values=(state,readable(x.size),stats_string(x,self.result.qualities.get(x.path)),x.path),tags=(tag,))
                self.item_map[iid]=(g,x)
        exacts=[g for g in self.result.groups if g.kind=='exact']
        near=[g for g in self.result.groups if g.kind.startswith('similar')]
        names=[g for g in self.result.groups if g.kind=='same_name']
        extra=sum(len(g.files)-1 for g in exacts)
        space=sum(g.files[0].size*(len(g.files)-1) for g in exacts)
        prefix=('媒體補掃＋歷史結果（不包含新檔精確比對）｜' if self.result.history_info.get('mode')=='media_resume' else '歷史待處理（未包含新檔精確比對）｜') if self.result.history_info else '完整結果｜'
        self.summary.set(prefix+f'精確重複 {len(exacts)} 組／多餘 {extra} 份／可省 {readable(space)}｜相似媒體 {len(near)} 組｜同名不同內容警示 {len(names)} 組')
        if len(filtered)>self.view_limit:
            self.more.configure(text=f'載入更多群組（已顯示 {self.view_limit:,} / {len(filtered):,} 組）')
            self.more.grid(row=3,column=0,sticky='e',pady=(5,0))
        self._mark_count()

    def _state(self,x,g,keeper):
        if protected(x.path): return '系統位置（保護）','protected'
        if x.path in self.marks: return '✓ 待移至回收桶','marked'
        if g.kind=='same_name': return '⚠ 僅同名，不可推定重複','warn'
        if x.path==keeper.path:
            return ('★ 優先資料夾保留' if inside_any_folder(x.path,self.preferred_paths) else '★ 品質優先保留'),'keeper'
        if g.kind.startswith('similar'): return '△ 視覺近似，需確認','near'
        return '○ 精確重複副本',''

    def _refresh(self):
        for iid,(g,x) in self.item_map.items():
            keeper=choose_keeper(g.files,self.result.qualities,self.preferred_paths)
            state,tag=self._state(x,g,keeper)
            self.tree.set(iid,'state',state)
            self.tree.item(iid,tags=(tag,))
        self._mark_count()

    def _mark_count(self):
        # Prevent double-count of a path appearing in exact and near-similar groups.
        unique={x.path:x.size for g in self.result.groups for x in g.files if x.path in self.marks} if self.result else {}
        self.marked_label.set(f'待移除：{len(self.marks)} 份｜{readable(sum(unique.values()))}')

    def _eligible(self,g,x):
        if protected(x.path): return False,'系統或程式資料夾不允許刪除。'
        if g.kind=='same_name': return False,'同名不同內容只是警示，不能作為移除依據。'
        if g.kind.startswith('similar') and not self.allow_near.get():
            return False,'請先勾選「允許將相似媒體加入待移除清單」，並且仔細確認內容、音軌和字幕。'
        return True,''

    def _double(self,e):
        if self.mode:return
        iid=self.tree.identify_row(e.y)
        if iid not in self.item_map: return
        g,x=self.item_map[iid]
        valid,msg=self._eligible(g,x)
        if not valid:
            messagebox.showwarning('不允許標記',msg)
            return
        if x.path in self.marks:self.marks.remove(x.path)
        else:self.marks.add(x.path)
        self._refresh()

    def _mark(self):
        if not self.result:return
        invalid=[]
        for iid in self.tree.selection():
            if iid not in self.item_map:continue
            g,x=self.item_map[iid]
            valid,msg=self._eligible(g,x)
            if valid:self.marks.add(x.path)
            else:invalid.append(msg)
        self._refresh()
        if invalid: messagebox.showwarning('已略過部分選取', '\n'.join(sorted(set(invalid))))

    def _unmark(self):
        self.marks.clear()
        if self.result:self._refresh()

    def _smart(self):
        if not self.result:return
        groups=self.result.groups
        exact=[g for g in groups if g.kind=='exact']
        near=[g for g in groups if g.kind.startswith('similar')]
        use_near=bool(near and self.allow_near.get())
        if use_near and not messagebox.askyesno('相似影片與照片風險確認',
              '智慧選取將依解析度、位元率等資訊，對「視覺相似但位元組不同」的照片／影片保留品質優先版本。\n\n注意：不同影片可能有不同音軌、語言、字幕、片頭片尾或剪輯。這不是完全可靠的內容比對，請逐一預覽！\n\n是否將相似媒體也一起標記？',icon='warning'):
            use_near=False
        marks=smart_marks(self.result,self.preferred_paths,use_near)
        self.marks=marks
        self._refresh()
        messagebox.showinfo('智慧選取已完成',
             f'已標記 {len(marks)} 份候選檔案，尚未刪除。\n\n'
             + ('包含相似照片／影片，務必先開啟確認音軌與影像。' if use_near else '僅選取內容完全相同的檔案；同名不同內容不會被選取。')
             + '\n可逐筆取消標記後，再按「移至回收桶」。')

    def _plan(self):
        if not self.result:return None
        exact={x.path:g for g in self.result.groups if g.kind=='exact' for x in g.files}
        similar={x.path:g for g in self.result.groups if g.kind.startswith('similar') for x in g.files}
        files={x.path:x for g in self.result.groups for x in g.files}
        result=[]
        for path in sorted(self.marks):
            x=files.get(path)
            if not x: return None
            if protected(x.path): raise ValueError('禁止移除系統位置：'+path)
            g=exact.get(path)
            if g:
                available=[f for f in g.files if f.path not in self.marks]
                if not available: raise ValueError('至少保留一份內容相同的檔案：'+path)
                keeper=choose_keeper(available,self.result.qualities,self.preferred_paths)
                result.append((x,keeper,'exact',g.key))
            else:
                g=similar.get(path)
                if not g or not self.allow_near.get():
                    raise ValueError('不允許僅憑檔名判定可刪除：'+path)
                available=[f for f in g.files if f.path not in self.marks]
                if not available: raise ValueError('相似媒體群組必須至少保留一份：'+path)
                keeper=choose_keeper(available,self.result.qualities,self.preferred_paths)
                result.append((x,keeper,g.kind,''))
        # Extra precaution: all shared group memberships must retain one file.
        for g in self.result.groups:
            if g.kind=='same_name':continue
            if any(f.path in self.marks for f in g.files) and all(f.path in self.marks for f in g.files):
                raise ValueError('群組全部檔案被選取，請至少取消一份：'+g.files[0].path)
        return result

    def _trash(self):
        if not self.marks:
            messagebox.showinfo('尚未標記','請手動標記檔案或點選「智慧選取」。')
            return
        if send2trash is None:
            messagebox.showerror('缺少回收桶套件','未安裝必要元件 send2trash。請使用正式安裝包或參閱 README.md。\n不會改用永久刪除。')
            return
        try: plan=self._plan()
        except ValueError as exc:
            messagebox.showwarning('安全檢查未通過',str(exc))
            return
        near=[p for p in plan if p[2]!='exact']
        sz=sum(p[0].size for p in plan)
        prompt=f'即將把 {len(plan)} 份檔案（{readable(sz)}）移至作業系統回收桶。\n\n'
        if self.result.history_info:prompt+='目前為歷史結果，未檢查新加入檔案；移動前會重新驗證原始檔案的雜湊。\n\n'
        if near:prompt+=f'其中 {len(near)} 份僅屬視覺相似，可能有不同的音軌／字幕，無法保證是同一檔案。\n\n'
        prompt+='移動前會重新驗證來源與保留副本，且不會永久刪除。\n外接／網路磁碟不一定支援復原。確定嗎？'
        if not messagebox.askyesno('最後確認',prompt,icon='warning'):return
        if near:
            phrase=simpledialog.askstring('相似媒體二次驗證','若確認已自行檢查相似媒體差異，請輸入：確認相似\n\n否則請按取消。',parent=self.root)
            if phrase!='確認相似':return
        self.progress_var.set('準備重新驗證檔案並移至回收桶…')
        self._launch('trash',plan)

    def _selected(self):
        unique={}
        for iid in self.tree.selection():
            if iid in self.item_map:
                g,x=self.item_map[iid]
                unique[x.path]=x
        return list(unique.values())

    def _open(self):
        items=self._selected()
        if not items:return
        path=items[0].path
        if not os.path.isfile(path):
            messagebox.showwarning('找不到檔案','請重新掃描。')
            return
        try:
            if sys.platform=='win32': subprocess.Popen(['explorer','/select,',path])
            elif sys.platform=='darwin': subprocess.Popen(['open','-R',path])
            else: subprocess.Popen(['xdg-open',os.path.dirname(path)])
        except OSError as exc:messagebox.showerror('無法開啟',str(exc))

    def _copy(self):
        items=self._selected()
        if not items:return
        self.root.clipboard_clear()
        self.root.clipboard_append('\n'.join(x.path for x in items))
        self.progress_var.set(f'已複製 {len(items)} 條檔案路徑。')

    def _csv(self):
        if not self.result:return
        target=filedialog.asksaveasfilename(title='匯出所有結果',defaultextension='.csv',
                                      filetypes=[('CSV 檔案','*.csv')],initialfile='檔案整理清單.csv')
        if not target:return
        try:
            with open(target,'w',encoding='utf-8-sig',newline='') as f:
                w=csv.writer(f)
                w.writerow(['群組','類型','檔案名稱','狀態','大小(位元組)','畫質資訊','修改時間','完整路徑','精確SHA256'])
                for n,g in enumerate(self.result.groups,1):
                    keeper=choose_keeper(g.files,self.result.qualities,self.preferred_paths)
                    for x in g.files:
                        state,_=self._state(x,g,keeper)
                        w.writerow([n,g.kind,os.path.basename(x.path),state,x.size,
                                    stats_string(x,self.result.qualities.get(x.path)),mtime(x),x.path,
                                    self.result.sha.get(x.path,'')])
            self.progress_var.set('CSV 已儲存：'+target)
        except (OSError,UnicodeError) as exc:messagebox.showerror('無法匯出',str(exc))

    def _quit(self):
        if self.mode:
            if not messagebox.askyesno('背景作業正在執行','結束視窗將強制中止背景作業；若正在移動檔案，應重新掃描。\n\n確定結束？',icon='warning'):
                return
            if self.proc and self.proc.is_alive():
                self.proc.terminate()
                self.proc.join(timeout=1.0)
                if self.proc.is_alive(): self.proc.kill()
        self.root.destroy()


def self_test():
    """Packaging smoke test, runnable on actual target operating systems."""
    import tempfile
    import threading
    from duplicate_engine import run_scan, ffmpeg_exe
    from PIL import Image
    import send2trash
    assert Image is not None and send2trash is not None
    assert ffmpeg_exe('ffmpeg'), 'FFmpeg executable not bundled'
    assert ffmpeg_exe('ffprobe'), 'FFprobe executable not bundled'
    with tempfile.TemporaryDirectory() as d:
        a=Path(d)/'sample.txt'; b=Path(d)/'renamed.xyz'
        a.write_bytes(b'local duplicate test'*5000)
        b.write_bytes(a.read_bytes())
        outcome=run_scan([d], False, threading.Event(),lambda *_:None,lambda _:None, use_cache=False)
        assert len([g for g in outcome.groups if g.kind=='exact'])==1
    print('SELF_TEST_OK', flush=True)


def run_app():
    root=tk.Tk()
    App(root)
    root.mainloop()

if __name__=='__main__':
    mp.freeze_support()
    if '--self-test' in sys.argv:
        self_test()
    else:
        run_app()
