from Utils import Libs
from Utils.Libs import WorkTimeline
from Utils.python_get_resolve import GetResolve
from Utils.Libs import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from davinci_resolve import *

# 做什么：
# 1. 清理禁用的片段
# 2. 重新分配 SRC 名称
# 3. 生成 Online 素材 REF 时间线，生成 TMP 时间线用于整理复合片段，生成 OVL 拷贝时间线
# 4. 将带有声音的复合片段插入回主时间线


resolve: "Resolve" = GetResolve()
pm: "ProjectManager" = resolve.GetProjectManager()
proj: "Project" = pm.GetCurrentProject()
media_pool : "MediaPool" = proj.GetMediaPool()
timeline: "Timeline" = proj.GetCurrentTimeline()
timeline_name = timeline.GetName()

work_timeline = WorkTimeline(timeline)

# 1. 清理禁用片段
all_clips = work_timeline.get_all_clips()
delete_clips: list["TimelineItem"] = []
for clip in all_clips:
    if not clip.GetClipEnabled(): delete_clips.append(clip)
timeline.DeleteClips(delete_clips)
work_timeline = WorkTimeline(timeline)
all_clips = work_timeline.get_all_clips()

# MFX处理
mfx_mark_track = work_timeline.mfx_mark_track
if mfx_mark_track != -1:
    mfx_mark_clips: list["TimelineItem"] = timeline.GetItemListInTrack("video", mfx_mark_track)
    edt_onl_clips = Libs.getEditOnlineClipList(timeline)
    for clip in mfx_mark_clips:
        clip_range = range(clip.GetStart(), clip.GetEnd(),1)
        #重命名 VFX Clip
        rename_clips = get_clips_in_range(work_timeline.edit_online_clip_list, clip_range)
        onl_index = 1
        for onl_clip in rename_clips:
            onl_clip_range = range(onl_clip.GetStart(), onl_clip.GetEnd(),1)
            # MFX_A0000_
            # 0123456789
            new_name = f"{clip.GetName()[0:9]}__SRC-C{onl_index:03d}__{onl_clip.GetName()}"
            onl_clip.SetName(new_name)
            onl_index += 1
    # 3. 生成 TMP 整理复合片段
    tmp_timeline = WorkTimeline(timeline.DuplicateTimeline(f"{timeline_name}_REF"))
    proj.SetCurrentTimeline(tmp_timeline.timeline)
    mfx_mark_clips = tmp_timeline.get_track_clips([tmp_timeline.mfx_mark_track])
    all_clips = tmp_timeline.get_all_clips()
    ref_clip_names: list[str]= []
    for clip in mfx_mark_clips:
        clip_range = range(clip.GetStart(), clip.GetEnd(),1)
        to_pack_clips = get_clips_in_range(all_clips, clip_range)
        pack_name = f"{clip.GetName()[0:9]}_REF"
        tmp_timeline.timeline.CreateCompoundClip(to_pack_clips, {"startTimecode" : "00:00:00:00", "name" : pack_name})
        ref_clip_names.append(pack_name)
        all_clips[:] = [x for x in all_clips if x not in to_pack_clips]

    ref_clips: list["MediaPoolItem"] = []
    for clip in tmp_timeline.get_all_clips("video"):
        if clip.GetName() in ref_clip_names: ref_clips.append(clip.GetMediaPoolItem())

    for mpi in ref_clips: print(mpi.GetName())

    #插入回主时间线
    proj.SetCurrentTimeline(timeline)

    timeline.AddTrack("video", {"index":1})
    timeline.AddTrack("audio", {"index":1})
    timeline.SetTrackName("video",1, "REF_CLIPS")
    timeline.SetTrackName("audio",1, "REF_CLIPS")
    work_timeline = WorkTimeline(timeline)
    mfx_mark_clips = timeline.GetItemListInTrack("video", work_timeline.mfx_mark_track)
    insert_list: list[dict] = []
    for clip in mfx_mark_clips:
        ref_name = f"{clip.GetName()[0:9]}_REF"
        ref_clip: "MediaPoolItem"
        for rc in ref_clips:
            if rc.GetName() == ref_name:
                ref_clip = rc
                insert_list.append({"mediaPoolItem": ref_clip, "trackIndex": 1, "recordFrame": clip.GetStart()})
                break
    media_pool.AppendToTimeline(insert_list)
elif work_timeline.vfx_ref_track != -1:
    # VFX处理
    vfx_ref_clips = work_timeline.get_track_clips([work_timeline.vfx_ref_track], "video")
    edt_onl_clips = work_timeline.edit_online_clip_list
    for clip in vfx_ref_clips:
        clip_range = range(clip.GetStart(), clip.GetEnd(),1)
        #重命名 VFX Clip
        rename_clips = get_clips_in_range(work_timeline.edit_online_clip_list, clip_range)
        onl_index = 1
        for onl_clip in rename_clips:
            onl_clip_range = range(onl_clip.GetStart(), onl_clip.GetEnd(),1)
            new_name = f"{clip.GetName()[0:9]}__SRC-C{onl_index:03d}__{onl_clip.GetName()}"
            onl_clip.SetName(new_name)
            onl_index += 1
    # 3. 生成 TMP 整理复合片段
    tmp_timeline = WorkTimeline(timeline.DuplicateTimeline(f"{timeline_name}_REF"))
    proj.SetCurrentTimeline(tmp_timeline.timeline)
    vfx_ref_clips = tmp_timeline.get_track_clips([tmp_timeline.vfx_ref_track])
    all_clips = tmp_timeline.get_all_clips()
    ref_clip_names: list[str]= []
    for clip in vfx_ref_clips:
        clip_range = range(clip.GetStart(), clip.GetEnd(),1)
        to_pack_clips = get_clips_in_range(all_clips, clip_range)
        pack_name = f"{clip.GetName()[0:9]}_REF"
        tmp_timeline.timeline.CreateCompoundClip(to_pack_clips, {"startTimecode" : "00:00:00:00", "name" : pack_name})
        ref_clip_names.append(pack_name)
        all_clips[:] = [x for x in all_clips if x not in to_pack_clips]

    ref_clips: list["MediaPoolItem"] = []
    for clip in tmp_timeline.get_all_clips("video"):
        if clip.GetName() in ref_clip_names: ref_clips.append(clip.GetMediaPoolItem())

    for mpi in ref_clips: print(mpi.GetName())

    #插入回主时间线
    proj.SetCurrentTimeline(timeline)

    timeline.AddTrack("video", {"index":1})
    timeline.AddTrack("audio", {"index":1})
    timeline.SetTrackName("video",1, "REF_CLIPS")
    timeline.SetTrackName("audio",1, "REF_CLIPS")
    work_timeline = WorkTimeline(timeline)
    vfx_ref_clips = timeline.GetItemListInTrack("video", work_timeline.vfx_ref_track)
    insert_list: list[dict] = []
    for clip in vfx_ref_clips:
        ref_name = f"{clip.GetName()[0:9]}_REF"
        ref_clip: "MediaPoolItem"
        for rc in ref_clips:
            if rc.GetName() == ref_name:
                ref_clip = rc
                insert_list.append({"mediaPoolItem": ref_clip, "trackIndex": 1, "recordFrame": clip.GetStart()})
                break
    media_pool.AppendToTimeline(insert_list)

