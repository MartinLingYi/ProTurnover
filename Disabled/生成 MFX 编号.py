import Utils.Libs
from Utils.python_get_resolve import GetResolve
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from davinci_resolve import *



def is_append_mark(seq: list[dict[int, "TimelineItem"]], target: dict[int, "TimelineItem"]) -> bool:
    # 找到 target 在列表中的位置
    try:
        idx = seq.index(target)
    except ValueError:
        return False

    # 提取所有 key（假设每个 dict 只有一个键）
    keys = [next(iter(d)) for d in seq]
    if keys[-1] < len(mfx_marks)-1: return False

    # 从 target 开始检查是否连续直到末尾
    for i in range(idx, len(keys) - 1):
        if keys[i + 1] != keys[i] + 1:
            return False
    return True

resolve = GetResolve()
projectManager = resolve.GetProjectManager()
project = projectManager.GetCurrentProject()
mediaPool = project.GetMediaPool()
timeline = project.GetCurrentTimeline()
tl_fr = int(timeline.GetSetting("timelineFrameRate"))

mfx_mark_track = Utils.Libs.getTrackIndex("MFX_MRK",timeline)
mfx_marks: list["TimelineItem"] = timeline.GetItemListInTrack("video", mfx_mark_track)

renameList: list[dict[int,"TimelineItem"]] = []
for mark in mfx_marks:
    mark_name = mark.GetName()
    if len(mark_name)<3 or mark_name[0:3] != "MFX":
        renameList.append({mfx_marks.index(mark):mark})

for item in renameList:
    if is_append_mark(renameList, item):
        if list(item.keys())[0] - 1 < 0 :
            index = 10
            new_name = f"MFX_A{index:04d}_MRK"
            list(item.values())[0].SetName(new_name)
        else:
            index = int(mfx_marks[list(item.keys())[0] - 1].GetName()[5:9]) + 10
            new_name = f"MFX_A{index:04d}_MRK"
            list(item.values())[0].SetName(new_name)
    else:
        index = int(mfx_marks[list(item.keys())[0] - 1].GetName()[5:9])
        index_max = (index // 10 + 1) * 10
        index += 1
        if index < index_max:
            new_name = f"MFX_A{index:04d}_MRK"
            list(item.values())[0].SetName(new_name)
        else:
            new_name = "OUT_OF_RANGE"
            list(item.values())[0].SetName(new_name)
            tc = Utils.Libs.toTimeCode(list(item.values())[0].GetStart(),tl_fr)
            timeline.SetCurrentTimecode(tc)
            exit(-1)
