from Utils.PTLib import WorkTimeline
from Utils.python_get_resolve import GetResolve
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from davinci_resolve import *

def do_rename(_requirement: str):
    reqs = _requirement.split("|")
    if len(reqs) != 3 : return
    (_from, _to) = reqs[1].split("-")
    index = 1
    for i in range(int(_from), int(_to) + 1):
        work_tl.timeline.SetTrackName("audio", i, f"{reqs[2]}{index:02d}")
        index += 1

resolve: "Resolve" = GetResolve()
pm: "ProjectManager" = resolve.GetProjectManager()
proj : "Project" = pm.GetCurrentProject()
tl: "Timeline" = proj.GetCurrentTimeline()
work_tl = WorkTimeline(tl)

a_tracks = work_tl.audio_tracks
for track in a_tracks:
    if track[0] == '|': do_rename(track)