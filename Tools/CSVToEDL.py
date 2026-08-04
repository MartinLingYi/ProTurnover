import csv
import pathlib

from Utils.PTLib import EDL
from tkinter import filedialog

def csv_to_edl(csv_path, edl_path, fps=24):
    edl = EDL(
        _title="csv_convert",
        _fps=fps
    )

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:

            in_frame = int(row["In"])
            dur = int(row["Dur"])

            # 闭区间
            start_frame = in_frame
            end_frame = in_frame + dur - 1

            scene = row["Scene"].strip()
            shot = row["Shot"].strip()

            reel_name = f"{scene}_{shot}"

            edl.append_item({
                EDL.EDLDataType.reel_name: reel_name,

                EDL.EDLDataType.start: start_frame,
                EDL.EDLDataType.end: end_frame,

                EDL.EDLDataType.record_start: start_frame,
                EDL.EDLDataType.record_end: end_frame,

                EDL.EDLDataType.edl_clip_name: reel_name,
            })

    edl.save_to(edl_path)

s_url = filedialog.askopenfilename(
    filetypes=[("CSV File", "*.csv")],
    defaultextension=".csv"
)

t_url = pathlib.Path(s_url).parent.joinpath(s_url).with_suffix(".edl")

csv_to_edl(s_url, t_url)