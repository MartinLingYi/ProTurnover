# region Import_block
import csv
from csv import DictReader
from pathlib import Path

from Utils.python_get_resolve import GetResolve
from typing import TYPE_CHECKING
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog

if TYPE_CHECKING:
    from davinci_resolve import *
# endregion

# region Init_Resolve
resolve: "Resolve" = GetResolve()
pm: "ProjectManager" = resolve.GetProjectManager()
proj: "Project" = pm.GetCurrentProject()
media_pool: "MediaPool" = proj.GetMediaPool()

# endregion

# region LoadCSV
split_csv_path = filedialog.askopenfilename(
    defaultextension=".csv",
    filetypes=[("Shot Split CSV", "*.csv")],
)
split_datas :dict[str, dict[str, str]] = {}

with open(split_csv_path, "r", encoding="utf-8-sig") as f:
    csv_dict_reader = csv.DictReader(f)
    for item in csv_dict_reader:
        if "In" not in item.keys():
            messagebox.showinfo("无法解析Split info", f"{item}不含有序列入点")
            exit(-1)
        split_data: dict[str, str] = {}
        for k in item:
            if k == "In": continue
            split_data[k] = item[k]
        split_datas[item["In"]] = split_data
# endregion

# region LinkMedia
media_path = Path(split_csv_path).parent
media_filename = ""
media_extension = ""
for ext in ["*.jpg", "*.jpeg", "*.arw", "*.dng", "*.tiff", "*.tif", "*.exr"]:
    for img in media_path.glob(ext):
        media_filename = simpledialog.askstring("确认媒体名称格式",  f"Example: filename_%04d.exr -> filename_[0001].exr", initialvalue=img.name)
        if media_filename: break
    if media_filename:
        media_extension = ext.split(".")[-1]
        break


for clip_in in split_datas:
    to_import = {
        "FilePath": f"{media_path.joinpath(f"{media_filename}")}",
        "StartIndex": int(clip_in),
        "EndIndex": int(clip_in) + int(split_datas[clip_in]["Dur"]) - 1,
    }
    mpi: list["MediaPoolItem"] = media_pool.ImportMedia([to_import])
    if len(mpi) > 0:
        mpi[0].SetMetadata("Scene", split_datas[clip_in]["Scene"])
        mpi[0].SetMetadata("Shot", split_datas[clip_in]["Shot"])



# endregion