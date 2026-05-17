from typing import List

from Utils.Libs import *
from Utils.python_get_resolve import GetResolve
import tkinter as tk
from tkinter import simpledialog, messagebox

if TYPE_CHECKING:
    from davinci_resolve import *

def longest_common_prefix(strs: list[str]) -> str:
    if not strs:
        return ""

    strs.sort()
    first = strs[0]
    last = strs[-1]

    i = 0
    while i < len(first) and i < len(last) and first[i] == last[i]:
        i += 1

    return first[:i]


tk_root = tk.Tk()
tk_root.withdraw()

resolve: "Resolve" = GetResolve()
pm: "ProjectManager" = resolve.GetProjectManager()
proj: "Project" = pm.GetCurrentProject()
if not proj: exit(-1)

work_mp = WorkMediaPool(proj.GetMediaPool())
bin_folder = work_mp.subfolder_of(work_mp.source_folder, "Bin")
proj_path: str = ""

if bin_folder:
    sf_list = bin_folder.GetSubFolderList()
    clip_list = bin_folder.GetClipList()
    while len(clip_list) == 0:
        if len(sf_list) == 0: break
        next_folder = sf_list[0]
        clip_list = next_folder.GetClipList()
        sf_list = next_folder.GetSubFolderList()

    path_list: List[str] = []
    for clip in clip_list:
        path_list.append(clip.GetClipProperty("Clip Directory"))
    proj_path = longest_common_prefix(path_list)

proj_path = simpledialog.askstring("项目文件夹位置","将按照如下路径匹配项目文件夹。要终止匹配，请留空输入框。", initialvalue=proj_path)
if not proj_path or proj_path == "": exit(-1)


all_clips = work_mp.get_all_clip(work_mp.root)
to_move_clips: list["MediaPoolItem"] = []
for clip in all_clips:
    if proj_path not in clip.GetClipProperty("Clip Directory") and clip.GetClipProperty("Clip Directory") != "":
        to_move_clips.append(clip)

clips_name_display = ""
for clip in to_move_clips:
    clips_name_display += f"{clip.GetName()}\n"
    if len(clips_name_display) >=255:
        clips_name_display += "..."
        break

confirm_move = messagebox.askyesno("确认移动",f"共计{len(to_move_clips)}个片段将被移动。\n{clips_name_display}")

if confirm_move:
    extra_mf = work_mp.subfolder_of(work_mp.source_folder, "ExtraMedia")
    if not extra_mf: extra_mf = work_mp.media_pool.AddSubFolder(work_mp.source_folder, "ExtraMedia")
    work_mp.media_pool.MoveClips(to_move_clips, extra_mf)

tk_root.destroy()