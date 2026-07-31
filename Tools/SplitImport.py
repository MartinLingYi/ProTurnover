# region Import_block
import copy
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

def get_discontinuous_ranges(csv_path):
    """
    返回不连续的FRAME区间
    例如:
    [(250, 260), (500, 520)]
    """

    ranges = []

    start = None
    last_frame = None

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            frame = int(row["FRAME"])
            file_value = row["FILE"].strip()

            # 判断是否连续
            continuous = (
                file_value != ""
                and file_value.isdigit()
                and int(file_value) == frame
            )

            if not continuous:
                if start is None:
                    start = frame

            else:
                if start is not None:
                    ranges.append((start, frame - 1))
                    start = None

            last_frame = frame


        # 文件结尾仍然断裂
        if start is not None:
            ranges.append((start, last_frame))


    return ranges
def split_datas_by_ranges(_split_datas, discontinuous_ranges):

    result = {}

    for in_str, data in _split_datas.items():

        in_frame = int(in_str)
        dur = int(data["Dur"])

        # split: [in_frame, end_frame)
        end_frame = in_frame + dur

        cuts = []

        for bad_start, bad_end in discontinuous_ranges:

            # bad: [bad_start, bad_end]
            # 判断相交
            if not (bad_end < in_frame or bad_start >= end_frame):
                cuts.append(
                    (
                        max(bad_start, in_frame),
                        min(bad_end, end_frame - 1)
                    )
                )

        if not cuts:
            result[in_str] = data
            continue


        # 关键：排序
        cuts.sort()


        # 关键：合并重叠坏帧
        merged = []

        for start, end in cuts:

            if not merged or start > merged[-1][1] + 1:
                merged.append([start, end])
            else:
                merged[-1][1] = max(
                    merged[-1][1],
                    end
                )


        current = in_frame

        for bad_start, bad_end in merged:

            if current < bad_start:

                new_data = copy.deepcopy(data)

                new_data["Dur"] = str(
                    bad_start - current
                )

                result[str(current)] = new_data


            # 跳过闭区间坏帧
            current = bad_end + 1


        # 尾部
        if current < end_frame:

            new_data = copy.deepcopy(data)

            new_data["Dur"] = str(
                end_frame - current
            )

            result[str(current)] = new_data


    return result

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

xsheet_path = Path(split_csv_path).parent.joinpath("xsheet.csv")
if xsheet_path.exists():
    discontinuous_ranges = get_discontinuous_ranges(xsheet_path)
    split_datas = split_datas_by_ranges(split_datas, discontinuous_ranges)


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