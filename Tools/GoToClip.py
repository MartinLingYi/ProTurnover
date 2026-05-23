from time import sleep

import Utils.PTLib
from Utils.PTLib import WorkTimeline
from Utils.python_get_resolve import GetResolve
from tkinter import simpledialog
from tkinter import messagebox
import threading

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from davinci_resolve import *

results: list["TimelineItem"] = []
search_finished = False

def find_clip(_tgt: str, seq: list["TimelineItem"]):
    global search_finished
    search_finished = False
    for item in seq:
        if _tgt in item.GetName():
            results.append(item)
    search_finished = True



tgt_clip_name = simpledialog.askstring("前往...","前往片段:")

resolve: "Resolve" = GetResolve()
pm: "ProjectManager" = resolve.GetProjectManager()
proj : "Project" = pm.GetCurrentProject()
tl: "Timeline" = proj.GetCurrentTimeline()

fps = proj.GetSetting("timelineFrameRate")

if not tl: exit(0)

work_tl = WorkTimeline(tl)
clips = work_tl.get_all_clips("video")
p = 0
search_thread = threading.Thread(target=find_clip, args=(tgt_clip_name, clips), daemon=True)
search_thread.start()

while True:
    # Wait if no result yet
    while (len(results) < p or len(results) == 0) and not search_finished:
        sleep(0.1)

    if len(results) == 0:
        messagebox.showinfo("没有搜索结果",f"没有找到任何包含{tgt_clip_name}的片段。")
        break

    p_clip = results[p]
    if p_clip:
        tl.SetCurrentTimecode(Utils.PTLib.to_time_code(p_clip.GetStart(), fps))
        p+=1
        s_stat ="已完成" if search_finished else "进行中"
        if not messagebox.askyesno("前往下一个匹配片段？", f"目前是第{p - 1}个匹配片段，目前搜索到{len(results)}个片段。搜索{s_stat}。"): break




