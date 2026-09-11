import Utils.PTLib
from Utils.python_get_resolve import GetResolve, GetBMD
from Utils.PTLib import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

if TYPE_CHECKING:
    from davinci_resolve import DaVinciResolveScript

import tkinter as tk


#region Initialize Resolve
resolve: Resolve = GetResolve()
print("Got Resolve API.")
if not resolve:
    messagebox.showinfo("无法连接到Davinci Resolve","请启动Davinci Resolve，并进入一个项目工程，然后才能使用ProTurnover。")
    exit(-1)
pm: ProjectManager = resolve.GetProjectManager()
proj: Project = pm.GetCurrentProject()
if not proj:
    messagebox.showinfo("无法连接到Davinci Resolve","请启动Davinci Resolve，并进入一个项目工程，然后才能使用ProTurnover。")
    exit(-1)

media_pool: "MediaPool" = proj.GetMediaPool()
fps = proj.GetSettings()["timelineFrameRate"]
current_timeline = proj.GetCurrentTimeline()
if not current_timeline:
    messagebox.showinfo("无法加载时间线",
                        "请打开一个时间线，然后才能使用ProTurnover。")
    exit(-1)
#endregion

#region Initialize UI

'''
------------------------------------------
| ProMarker                              |
|----------------------------------------|
||                                      ||
||                                      ||
||           (TextBox)                  ||
||                                      ||
||                                      ||
||                                      ||
------------------------------------------
| [Refresh]                    [Apply]   |
------------------------------------------

'''

# 标记序列数据源：从当前时间线的所有视频轨道读取标记
work_timeline = WorkTimeline(current_timeline)
ms = MarkerSequence(work_timeline)
ms.load()

# 达芬奇内置 UI API：UIManager 描述窗口与控件，UIDispatcher 负责事件循环
bmd = GetBMD()
ui = resolve.Fusion().UIManager
dispatcher = bmd.UIDispatcher(ui)

text_box_id = "ProMarker.TextBox"
copy_buffer_id = "ProMarker.CopyBuffer"

m_seq_tsv: list[str] = []

def refresh_text_box():
    """按当前时间线标记刷新文本框内容。"""
    global m_seq_tsv
    m_seq_tsv = ms.to_tsv(fps)
    text_box.SetPlainText("\n".join(m_seq_tsv))

def on_refresh(ev):
    """[Refresh] 按钮点击回调：重新扫描时间线标记并刷新文本框。"""
    ms.load()
    refresh_text_box()

def on_copy(ev):
    """[Copy] 按钮点击回调：把文本框内容以纯文本写入系统剪贴板。

    文本框控件复制时总要附带一份 HTML 格式，而富文本目标（Excel/Word 等）
    会优先采用它，HTML 又会把 tab 当作普通空白吞掉。因此改由隐藏的单行
    文本框做一次纯文本复制：剪贴板里只留 text/plain，tab 与换行都完整保留。
    """
    copy_buffer.SetText(text_box.GetPlainText())
    copy_buffer.SelectAll()
    copy_buffer.Copy()


def on_apply(ev):
    """[Apply] 按钮点击回调：读取文本框中被编辑过的标记序列。"""
    global m_seq_tsv
    m_seq_tsv = text_box.GetPlainText().splitlines()
    ms.parse_from(m_seq_tsv,int(fps))
    print("Writing...")
    ms.write()
    refresh_text_box()


def on_close(ev):
    """窗口关闭回调：结束事件循环并隐藏窗口。

    先结束循环再隐藏，避免 Hide 抛错时事件循环无法退出，导致窗口卡死无法关闭。
    """
    dispatcher.ExitLoop()
    window.Hide()

# 上方为多行文本框，下方左 [Refresh] [Copy]，右 [Apply]
window_layout = ui.VGroup({"Spacing": 8}, [
    ui.TextEdit({"ID": text_box_id, "Text": "", "ReadOnly": False, "AcceptRichText": False}),
    ui.HGroup({"Spacing": 6, "Weight": 0}, [
        ui.Button({"ID": "Refresh", "Text": "从时间线同步", "Weight": 0}),
        ui.Button({"ID": "Copy", "Text": "复制到剪贴板", "Weight": 0}),
        ui.HGap(0, 1.0),
        ui.Button({"ID": "Apply", "Text": "同步到时间线", "Weight": 0}),
    ]),
    # 隐藏的纯文本复制缓冲，仅由 [Copy] 使用
    ui.LineEdit({"ID": copy_buffer_id, "Hidden": True}),
])

window = dispatcher.AddWindow({
    "ID": "ProMarker",
    "WindowTitle": "ProMarker",
    "Geometry": [200, 200, 720, 520],
}, [window_layout])

# 暴露两个按钮的点击回调
window.On.Refresh.Clicked = on_refresh
window.On.Apply.Clicked = on_apply
window.On.Copy.Clicked = on_copy
window.On.ProMarker.Close = on_close

text_box = window.Find(text_box_id)
copy_buffer = window.Find(copy_buffer_id)

#endregion

# 填充初始内容并进入事件循环
refresh_text_box()
window.Show()
dispatcher.RunLoop()
