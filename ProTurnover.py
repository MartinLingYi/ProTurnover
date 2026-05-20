import math
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from typing import Any
import datetime

import Utils.PTLib
from Utils.python_get_resolve import GetResolve
from Utils.PTLib import *

if TYPE_CHECKING:
    from davinci_resolve import *


def get_fx_data(_fx_timeline: WorkTimeline, _with_audio_clip: bool = True) -> dict[str, list["TimelineItem"]]:
    title_tracks = _fx_timeline.get_tracks(WorkTimeline.TrackType.FXShot_mark)
    titles = _fx_timeline.get_track_clips(title_tracks)
    clips = _fx_timeline.get_track_clips(_fx_timeline.get_tracks(WorkTimeline.TrackType.Drama))
    overlays = _fx_timeline.get_track_clips(_fx_timeline.get_tracks(WorkTimeline.TrackType.Overlay))
    audios = _fx_timeline.get_all_clips("audio")

    ret: dict[str, list["TimelineItem"]] = {}
    # 扫描所需片段
    for title in titles:
        title_in = title.GetStart()
        title_out = title.GetEnd()
        title_range = range(title_in, title_out, 1)

        linked_clips: list["TimelineItem"] = []
        if len(clips) >0 :
            linked_clips += Utils.PTLib.get_clips_in_range(clips, title_range)
        if len(audios)>0 and _with_audio_clip :
            linked_clips += Utils.PTLib.get_clips_in_range(audios, title_range)
        if len(overlays)>0 :
            linked_clips += Utils.PTLib.get_clips_in_range(overlays, title_range)

        ret[title.GetName()] = linked_clips
    return ret

# 达芬奇初始化
resolve: "Resolve" = GetResolve()
if not resolve:
    messagebox.showinfo("无法连接到Davinci Resolve","请启动Davinci Resolve，并进入一个项目工程，然后才能使用ProTurnover。")
    exit(-1)
pm: "ProjectManager" = resolve.GetProjectManager()
proj: "Project" = pm.GetCurrentProject()
if not proj:
    messagebox.showinfo("无法连接到Davinci Resolve","请启动Davinci Resolve，并进入一个项目工程，然后才能使用ProTurnover。")
    exit(-1)

media_pool: "MediaPool" = proj.GetMediaPool()
fps = proj.GetSetting("timelineFrameRate")
current_timeline = proj.GetCurrentTimeline()
if not current_timeline:
    messagebox.showinfo("无法加载时间线",
                        "请打开一个时间线，然后才能使用ProTurnover。")
    exit(-1)
work_timeline = WorkTimeline(current_timeline)
# 初始化媒体池并创建工作目录
work_mp = WorkMediaPool(media_pool)
for f in WorkMediaPool.WorkFolderType:
    work_mp.create_folder(f)
# 加载资源
env_path = Utils.PTLib.get_script_dir()
print(f"Script at {env_path}")
sys.path.append(str(env_path))
work_mp.register_source("FrameCounter_24P", env_path / "PTAsset" /"FrameCount_2KDCI_24P.mov")
print("Loaded PT Source:")
print(work_mp.pt_source)



# =========================
# 右侧按钮
# =========================

def on_pre_mark():
    # 预标注视效镜头
    drama_clip_tracks = work_timeline.get_tracks(WorkTimeline.TrackType.Drama)
    drama_clips: list["TimelineItem"] = work_timeline.get_track_clips(drama_clip_tracks)
    marked_clips: list["TimelineItem"] = []
    # 扫描 Drama Track中的 clips，并将片段颜色为 紫色 的片段视为预标注片段
    for drama_clip in drama_clips:
        if drama_clip.GetClipColor() == "Purple": marked_clips.append(drama_clip)
    marked_clip_sets: list[dict[str, Any]] = []
    for marked_clip in marked_clips:
        marked_clip_sets.append({"name": marked_clip.GetName(), "in": marked_clip.GetStart(), "out": marked_clip.GetEnd()})

    premark_range = Utils.PTLib.merge_intervals(marked_clip_sets)
    tgt_track = work_timeline.create_track(WorkTimeline.TrackType.FXShot_premark)
    for r in premark_range:
        cut_in = 1001 + handle_var.get()
        pmi = work_mp.media_pool.AppendToTimeline([Utils.PTLib.clipinfo_of(work_mp.get_source("FrameCounter_24P"), cut_in, cut_in + r["out"] - r["in"], 1,tgt_track, r["in"])])
        if len(pmi) != 0:
            pmi[0].SetName("PM_FXType=")


def on_mark_shot():
    name_rule = name_rule_var.get()
    if check_shot_name_rule(name_rule) != "Pass":
        match check_shot_name_rule(name_rule):
            case "NotTail":
                messagebox.showerror("需要修改命名规则", "目前尚不支持将[ShotIndex]字段置于其他字段之前。请确保[ShotIndex]之后没有其他字段。")
                return
            case "NoContain":
                messagebox.showerror("需要修改命名规则",
                                     "视效命名规则中应当包含[ShotIndex]字段，这用于告知ProTurnover在何处插入镜头编号。")
                return
            case _:
                messagebox.showerror("需要修改命名规则",
                                     f"规则检查器抛出了\"{check_shot_name_rule(name_rule)}\"错误。请提交issue。")
                return

    vfx_title_tracks = work_timeline.get_tracks(WorkTimeline.TrackType.FXShot_mark)
    vfx_premark_tracks = work_timeline.get_tracks(WorkTimeline.TrackType.FXShot_premark)
    print(vfx_title_tracks, vfx_premark_tracks)
    vfx_title_idict: dict[int, int] = {}
    vfx_title_ikeys: list[int] = []
    if len(vfx_title_tracks) != 0:
        # 扫描已有VFXTitles，并尝试读取ShotIndex
        vfx_titles = work_timeline.get_track_clips(vfx_title_tracks)

        for vt in vfx_titles:
            if not vt.GetClipEnabled(): continue
            shot_index = Utils.PTLib.get_shot_index(name_rule, vt.GetName())
            if not shot_index:
                messagebox.showerror("无法识别此片段",
                                     f"{vt.GetName()}不是与命名规则一致的视效镜头标记。请重命名此片段后重试。")
                return
            vfx_title_idict[vt.GetStart()] = shot_index
        # 排序后的in point keys
        vfx_title_ikeys = sorted(vfx_title_idict.keys())

    vfx_premarks = work_timeline.get_track_clips(vfx_premark_tracks)
    last_shot_index = 0
    for premark in vfx_premarks:
        pm_name = premark.GetName()
        # 跳过已标注镜头号的片段
        if pm_name[0:2] != "PM":
            last_shot_index = Utils.PTLib.get_shot_index(name_rule, premark.GetName())
            if not last_shot_index:
                messagebox.showerror("无法识别此片段",f"{premark.GetName()}不是与命名规则一致的视效镜头标记，也不是有效的预标记片段。请重命名此片段后重试。")
                return
            continue

        # 读取镜头数据
        pm_data = dict(
            item.split("=")
            for item in pm_name.removeprefix("PM_").split("_")
        )
        # 如果预标注了镜头，直接采用用户标注的镜头号
        if "ShotIndex" in pm_data.keys():
            shot_index = int(pm_data["ShotIndex"])
            shot_name = Utils.PTLib.format_input(name_rule, pm_data)
            premark.SetName(shot_name)
            last_shot_index = shot_index
            continue

        # 否则开始推理镜头号
        shot_index: int
        lc, nc = Utils.PTLib.find_neighbors(premark.GetStart(), vfx_title_ikeys)
        if not nc or not lc: shot_index = last_shot_index + 10 # 前后没有片段，说明是新增镜头
        else:
        # 否则视为插入镜头
            if nc == lc : shot_index = vfx_title_idict[nc] + 1
            if last_shot_index < vfx_title_idict[lc]: last_shot_index = vfx_title_idict[lc]

            if nc - last_shot_index <= 1:
                messagebox.showinfo("没有足够的镜头编号",f"在镜头号{vfx_title_idict[lc]:04d}与{last_shot_index:04d}之间无法插入新的镜头编号。")
                return
            d_index = max(math.floor((vfx_title_idict[nc] - last_shot_index) / 2), 1)
            shot_index = last_shot_index + d_index

        pm_data["ShotIndex"] = f"{shot_index:04d}"
        shot_name = Utils.PTLib.format_input(name_rule, pm_data)
        premark.SetName(shot_name)
        last_shot_index = shot_index


def on_generate_subclip():
    pt_tracks = work_timeline.get_tracks(WorkTimeline.TrackType.FXShot_premark)
    if len(pt_tracks) == 0:
        messagebox.showinfo(f"没有检测到{WorkTimeline.TrackType.FXShot_premark.value}轨道","请在预标注视效镜头后重试。")
        return
    pts: list["TimelineItem"] = work_timeline.get_track_clips(pt_tracks)
    vfx_title_edl = EDL(f"VFX_ID_{fps}P")
    index = 1
    for pt in pts:
        pt_ss = pt.GetSourceStartFrame()
        pt_se = pt.GetSourceEndFrame()
        vfx_title_edl.items.append({EDL.EDLDataType.index: f"{index:03d}",
                                    EDL.EDLDataType.reel_name: f"{pt.GetName()}",
                                    EDL.EDLDataType.v: "V",
                                    EDL.EDLDataType.c: "C",
                                    EDL.EDLDataType.start: Utils.PTLib.to_time_code(pt_ss, fps),
                                    EDL.EDLDataType.end: Utils.PTLib.to_time_code(pt_se, fps),
                                    EDL.EDLDataType.record_start: Utils.PTLib.to_time_code(pt.GetStart(), fps),
                                    EDL.EDLDataType.record_end: Utils.PTLib.to_time_code(pt.GetEnd(), fps),
                                    EDL.EDLDataType.edl_clip_name: f"{pt.GetName()}",
                                    })
        index += 1

    tgt_path = filedialog.asksaveasfilename(
        filetypes=[("带卷名的VFXTitle", ".edl")],
        defaultextension=".edl"
    )
    vfx_title_edl.save_to(tgt_path)


def on_extract_timeline():
    fx_timeline = WorkTimeline(work_timeline.timeline.DuplicateTimeline(f"FXTurnover_{datetime.datetime.now().strftime('%m%d%H%M')}"))
    tgt_folder = work_mp.media_pool.AddSubFolder(work_mp.get_folder(WorkMediaPool.WorkFolderType.Turnover), f"{datetime.datetime.now().strftime('%m%d%H%M')}_ToFX")
    work_mp.media_pool.MoveClips([fx_timeline.timeline.GetMediaPoolItem()], tgt_folder)
    proj.SetCurrentTimeline(fx_timeline)

    if not messagebox.askyesno("现在扫描片段？","选择继续将立刻扫描并禁用不必要的片段。"): return

    title_tracks = fx_timeline.get_tracks(WorkTimeline.TrackType.FXShot_mark)
    if len(title_tracks) == 0:
        messagebox.showinfo(f"没有检测到{WorkTimeline.TrackType.FXShot_mark}轨道",f"ProTurnover需要从{WorkTimeline.TrackType.FXShot_mark}中读取VFX Title信息。")
        return

    fx_datas = get_fx_data(fx_timeline)

    all_linked_clips_uuid = []
    for data in fx_datas:
        for clip in fx_datas[data]:
            all_linked_clips_uuid.append(clip.GetUniqueId())

    for clip in fx_timeline.get_all_clips():
        if clip.GetUniqueId() not in all_linked_clips_uuid:
            if clip.GetName() not in fx_datas.keys(): clip.SetClipEnabled(False)

    if not messagebox.askyesno("确认扫描结果", "选择继续将立刻删除不必要的片段。"): return

    to_delete: list["TimelineItem"] = []
    for clip in fx_timeline.get_all_clips():
        if not clip.GetClipEnabled(): to_delete.append(clip)
    fx_timeline.timeline.DeleteClips(to_delete)

    fx_datas = get_fx_data(fx_timeline, False)
    for data in fx_datas:
        index = 1
        for clip in fx_datas[data]:
            new_name = f"{data}_SRC{index:03d}"
            clip.SetName(new_name)
            index += 1

    if offline_var.get():
        di_edl = EDL("SourceList", fps)

        for data in fx_datas:
            for clip in fx_datas[data]:
                offset = to_frame_count(clip.GetMediaPoolItem().GetClipProperty("Start TC"), fps)
                csi = clip.GetSourceStartFrame() - handle_var.get() + offset
                cso = clip.GetSourceEndFrame() + handle_var.get() + offset
                di_edl.append_item({
                    EDL.EDLDataType.edl_clip_name: clip.GetName(),
                    EDL.EDLDataType.reel_name: clip.GetMediaPoolItem().GetClipProperty("Reel Name"),
                    EDL.EDLDataType.start: csi,
                    EDL.EDLDataType.end: cso,
                })

        tgt_path = filedialog.asksaveasfilename(
            defaultextension=".edl",
            filetypes=[(f"发送给DI的素材EDL（带{handle_var.get()}帧余量）", ".edl")],
        )
        di_edl.save_to(tgt_path)



def on_pack_selected_clips():
    mpi = work_mp.media_pool.GetSelectedClips()
    if len(mpi) == 0:
        messagebox.showinfo("未选中任何片段", "在媒体池中选择需要包裹的片段，然后再使用此功能。")
        return

    mp_root = work_mp.media_pool.GetCurrentFolder()
    for mp in mpi:
        tgt = work_mp.media_pool.AddSubFolder(mp_root, f"{mp.GetName()}")
        work_mp.media_pool.MoveClips([mp], tgt)


def on_export_shotlist():
    exp_timeline = WorkTimeline(proj.GetCurrentTimeline())
    title_tracks = exp_timeline.get_tracks(WorkTimeline.TrackType.FXShot_mark)
    if len(title_tracks) == 0:
        messagebox.showinfo("当前时间线没有视效镜头数据", f"选择一个有{WorkTimeline.TrackType.FXShot_mark.value}轨道的时间线，然后ProTurnover才能读取视效镜头数据。")
        return

    shotlist: dict[str, dict[str, Any]]  = {}
    vfx_titles = exp_timeline.get_track_clips(title_tracks)
    for vt in vfx_titles:
        mark_inout = vt.GetMediaPoolItem().GetMarkInOut()
        mi = mark_inout["video"]["in"]
        mo = mark_inout["video"]["out"] + 1
        shotlist[vt.GetName()] = {
            "Mark In": mi,
            "Mark Out": mo,
            "Cut In": vt.GetSourceStartFrame(),
            "Cut Out": vt.GetSourceEndFrame(),
            "Comments": vt.GetMediaPoolItem().GetClipProperty("Comments"),
            "VFX Shot": vt.GetMediaPoolItem().GetClipProperty("VFX Shot"),
            "VFX Markers": vt.GetMediaPoolItem().GetClipProperty("VFX Markers"),
            "VFX Notes": vt.GetMediaPoolItem().GetClipProperty("VFX Notes")
        }


    tgt_path = filedialog.asksaveasfilename(
        defaultextension=".md",
        filetypes=([("简要报告", ".md"),("全部镜头数据",".csv")])
    )

    with open(tgt_path, "w", encoding="utf-8") as shotlist_report:
        if tgt_path.endswith(".md"):
            output: list[str] = [f"# VFX Shot List of {exp_timeline.timeline.GetName()}", "|VFX ID|Description|Cut In|VFX Start|VFX End|Cut Out|", "|:---|:---|:---|:---|:---|:---|"]
            for vt in shotlist: output.append(f"|**{vt}**|{shotlist[vt]["Comments"]}|{shotlist[vt]["Cut In"]}|{shotlist[vt]["Mark In"]}|{shotlist[vt]["Mark Out"]}|{shotlist[vt]["Cut Out"]}|")
            output += ["---", f"Total Shot Count: **{len(vfx_titles)}**"]
        if tgt_path.endswith(".csv"):
            messagebox.showinfo("尚未支持","ProTurnover尚未添加对 CSV 的支持。")
            shotlist_report.close()
            return
        for line in output:
            shotlist_report.write(f"{line}\n")
        shotlist_report.close()






# UI初始化
root = tk.Tk()
root.title(f"ProTurnover - Timeline: {work_timeline.timeline.GetName()}")
root.geometry("520x320")

# 锁定窗体大小
root.resizable(False, False)


# =========================
# 主布局
# =========================
main_frame = ttk.Frame(root, padding=15)
main_frame.pack(fill="both", expand=True)

left_frame = ttk.Frame(main_frame)
left_frame.pack(side="left", fill="y", padx=(0, 30))

right_frame = ttk.Frame(main_frame)
right_frame.pack(side="right", fill="y")


# =========================
# 左侧内容
# =========================

# 视效子片段命名规则
name_rule_label = ttk.Label(
    left_frame,
    text="视效镜头命名规则"
)
name_rule_label.pack(anchor="w", pady=(0, 5))


name_rule_var = tk.StringVar(value="XXX_[FXType]_[ShotIndex]")
name_rule_entry = ttk.Entry(
    left_frame,
    width=28,
    textvariable=name_rule_var
)
name_rule_entry.pack(anchor="w", pady=(0, 15))



# 预留帧余量
handle_label = ttk.Label(
    left_frame,
    text="预留帧余量"
)
handle_label.pack(anchor="w", pady=(0, 5))

handle_var = tk.IntVar(value=8)

handle_spinbox = ttk.Spinbox(
    left_frame,
    from_=0,
    to=999,
    textvariable=handle_var,
    width=10
)
handle_spinbox.pack(anchor="w", pady=(0, 15))


# 抽取离线EDL
offline_var = tk.BooleanVar(value=False)

offline_check = ttk.Checkbutton(
    left_frame,
    text="使用离线流程",
    variable=offline_var
)
offline_check.pack(anchor="w")





btn_width = 18

pre_mark_btn = ttk.Button(
    right_frame,
    text="预标注视效镜头",
    width=btn_width,
    command=on_pre_mark
)
pre_mark_btn.pack(pady=(0, 10))


mark_shot_btn = ttk.Button(
    right_frame,
    text="标注镜头号",
    width=btn_width,
    command=on_mark_shot
)
mark_shot_btn.pack(pady=(0, 10))


generate_subclip_btn = ttk.Button(
    right_frame,
    text="获取VFXTitle",
    width=btn_width,
    command=on_generate_subclip
)
generate_subclip_btn.pack(pady=(0, 10))


extract_timeline_btn = ttk.Button(
    right_frame,
    text="抽取时间线",
    width=btn_width,
    command=on_extract_timeline
)
extract_timeline_btn.pack(pady=(0, 40))

pack_selected_clip_btn = ttk.Button(
    right_frame,
    text="使用媒体夹包裹所选",
    width=btn_width,
    command=on_pack_selected_clips
)
pack_selected_clip_btn.pack(pady=(0, 10))

export_shotlist_btn = ttk.Button(
    right_frame,
    text="导出视效镜头数据",
    width=btn_width,
    command=on_export_shotlist
)
export_shotlist_btn.pack()

root.mainloop()