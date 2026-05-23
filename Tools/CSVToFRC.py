import csv
from Utils.PTLib import to_frame_count

# CSV文件路径
csv_path = r"MFXShotList.csv"

# 需要提取的列名
column_name = "录制时长"

# 帧率
fps = 24

with open(csv_path, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    for row in reader:
        tc = row[column_name].strip()

        if tc:
            try:
                frame_count = to_frame_count(tc, fps)
                print(frame_count)
            except Exception as e:
                print(f"转换失败: {tc} -> {e}")