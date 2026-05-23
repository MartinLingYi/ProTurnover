import Utils.Libs
from Utils.Libs import *
from Utils.python_get_resolve import GetResolve
import datetime

if TYPE_CHECKING:
    from davinci_resolve import *

resolve: "Resolve" = GetResolve()
pm: "ProjectManager" = resolve.GetProjectManager()
proj: "Project" = pm.GetCurrentProject()
if not proj: exit(-1)


media_pool: "MediaPool" = proj.GetMediaPool()

mpi: list["MediaPoolItem"] = media_pool.GetSelectedClips()
pre_subclips: list[dict] = []

handler_frame = 8
fps = proj.GetSetting("timelineFrameRate")

for i in mpi:
    io: dict[str, dict[str, int]] = i.GetMarkInOut()
    si = int(i.GetClipProperty("Start"))
    so = int(i.GetClipProperty("End"))
    for item in io:
        if item == "video":
            for iop in io[item]:
                if iop == "in": si = io[item][iop]
                if iop == "out": so = io[item][iop]
        break
    max_o = int(i.GetClipProperty("End"))
    clip_i = max(0, si - handler_frame)
    clip_o = min(so + handler_frame + 1, max_o + 1)
    clip_info: dict = {
        "mediaPoolItem": i,
        "startFrame":clip_i,
        "endFrame":clip_o,
        "mediaType":1,
        "markIn": si,
        "markOut": so,
        "startTC": i.GetClipProperty("Start TC"),
        "name": i.GetName(),
        "reelName": i.GetClipProperty("Reel Name")
    }
    pre_subclips.append(clip_info)

work_timeline = media_pool.CreateEmptyTimeline(f"Subclips_{datetime.datetime.now().strftime('%m%d%H%M%S')}")
proj.SetCurrentTimeline(work_timeline)

for info in pre_subclips:
    clip_info = {
        "mediaPoolItem": info["mediaPoolItem"],
        "startFrame": info["startFrame"],
        "endFrame": info["endFrame"],
        "mediaType": info["mediaType"]
    }
    tl_items = media_pool.AppendToTimeline([clip_info])
    if len(tl_items) == 0: continue
    frm_count = Utils.Libs.toFrameCount(info["startTC"], fps) + info["startFrame"]

    pre_subclip: "TimelineItem" = work_timeline.CreateCompoundClip(tl_items, {"startTimecode" : Utils.Libs.toTimeCode(frm_count, fps), "name" : info["reelName"]})
    subclip: "MediaPoolItem" = pre_subclip.GetMediaPoolItem()
    mi = info["markIn"] - info["startFrame"]
    mo = mi + info["markOut"] - info["markIn"]
    subclip.SetMarkInOut(mi, mo)
    subclip.SetMetadata("VFX", info["name"])


