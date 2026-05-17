import Utils.python_get_resolve
from Utils import *
from typing import TYPE_CHECKING

from Utils.Libs import WorkTimeline

if TYPE_CHECKING:
    from davinci_resolve import *

resolve: "Resolve" = Utils.python_get_resolve.GetResolve()
pm: "ProjectManager" = resolve.GetProjectManager()
project: "Project" = pm.GetCurrentProject()
current_timeline: "Timeline" = project.GetCurrentTimeline()

work_timeline = WorkTimeline(current_timeline)

vfx_ref_srcs: list["TimelineItem"] = []
keep_vfx_srcs: list["TimelineItem"] = []
disable_vfx_srcs: list["TimelineItem"] = []
vfx_connection_timeline: "Timeline" = None
# 扫描 VFX_REF
if work_timeline.vfx_ref_track != -1:
    vfx_connection_timeline = current_timeline.DuplicateTimeline(f"VFX_{current_timeline.GetName()}")
    work_timeline = WorkTimeline(vfx_connection_timeline)
    vfx_ref_clips = work_timeline.get_track_clips([work_timeline.vfx_ref_track])
    vfx_ref_srcs = (work_timeline.edit_online_clip_list +
                    work_timeline.get_track_clips(
                        work_timeline.get_tracks("EDT_OVL")
                    ))
    keep_vfx_srcs: list["TimelineItem"] = []
    for ref in vfx_ref_clips:
        if not ref.GetClipEnabled(): continue
        ref_range = range(ref.GetStart(), ref.GetEnd(), 1)
        keep_vfx_srcs += Utils.Libs.get_clips_in_range(vfx_ref_srcs, ref_range)

    disable_vfx_srcs: list["TimelineItem"] = [x for x in vfx_ref_srcs if x not in keep_vfx_srcs]

mfx_srcs: list["TimelineItem"] = []
keep_mfx_srcs: list["TimelineItem"] = []
disable_mfx_srcs: list["TimelineItem"] = []
mfx_connection_timeline: "Timeline" = None
# 扫描 MFX_MRK
if work_timeline.mfx_mark_track != -1:
    mfx_connection_timeline = current_timeline.DuplicateTimeline(f"MFX_{current_timeline.GetName()}")
    work_timeline = WorkTimeline(mfx_connection_timeline)
    mfx_mark_clips = work_timeline.get_track_clips([work_timeline.mfx_mark_track])
    mfx_srcs = (work_timeline.edit_online_clip_list +
                    work_timeline.get_track_clips(
                        work_timeline.get_tracks("EDT_OVL")
                    ))
    # MFX 额外需要视效参考片段
    if work_timeline.vfx_ref_track != -1: mfx_srcs += work_timeline.get_track_clips([work_timeline.vfx_ref_track])
    keep_mfx_srcs: list["TimelineItem"] = []
    for mrk in mfx_mark_clips:
        if not mrk.GetClipEnabled(): continue
        mrk_range = range(mrk.GetStart(), mrk.GetEnd(), 1)
        keep_mfx_srcs += Utils.Libs.get_clips_in_range(mfx_srcs, mrk_range)

    disable_mfx_srcs: list["TimelineItem"] = [x for x in mfx_srcs if x not in keep_mfx_srcs]

# 禁用片段
if vfx_ref_srcs:
    project.SetCurrentTimeline(vfx_connection_timeline)
    for clip in disable_vfx_srcs: clip.SetClipEnabled(False)
    if mfx_srcs: vfx_connection_timeline.DeleteTrack("video", WorkTimeline(vfx_connection_timeline).mfx_mark_track)

if mfx_srcs:
    project.SetCurrentTimeline(mfx_connection_timeline)
    for clip in disable_mfx_srcs: clip.SetClipEnabled(False)
