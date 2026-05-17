from Utils.Libs import *
from Utils.python_get_resolve import GetResolve

if TYPE_CHECKING:
    from davinci_resolve import *

resolve: "Resolve" = GetResolve()
pm: "ProjectManager" = resolve.GetProjectManager()
proj: "Project" = pm.GetCurrentProject()
if not proj: exit(-1)


media_pool: "MediaPool" = proj.GetMediaPool()
work_mp = WorkMediaPool(media_pool)
if not work_mp.subfolder_of(work_mp.source_folder, "Bin"):
    work_mp.media_pool.AddSubFolder(work_mp.source_folder, "Bin")

