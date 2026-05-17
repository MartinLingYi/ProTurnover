import Utils.python_get_resolve
import tkinter as tk
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from davinci_resolve import *


def on_confirm():
    selection = listbox.curselection()
    if selection:
        _timeline = timelines[selection[0]]
        project.SetCurrentTimeline(_timeline)
        for mark in marks:
            _timeline.AddMarker(mark, marks[mark]["color"], marks[mark]["name"], marks[mark]["note"], marks[mark]["duration"], marks[mark]["customData"])

    tk_root.destroy()
    exit(0)



tk_root = tk.Tk()

resolve: "Resolve" = Utils.python_get_resolve.GetResolve()
pm: "ProjectManager" = resolve.GetProjectManager()
project: "Project" = pm.GetCurrentProject()
current_timeline: "Timeline" = project.GetCurrentTimeline()

marks: dict[int, dict] = current_timeline.GetMarkers()
timelines: list["Timeline"] = []
tl_count = project.GetTimelineCount()
for i in range(1, tl_count + 1):
    tl: "Timeline" = project.GetTimelineByIndex(i)
    timelines.append(tl)

# Label
label = tk.Label(tk_root, text="复制到:")
label.pack(pady=10)

# Listbox
listbox = tk.Listbox(tk_root, height=6)
listbox.pack(pady=5, fill=tk.BOTH, expand=True)

# 填充一些示例数据

for item in timelines:
    listbox.insert(tk.END, item.GetName())

# Confirm Button
confirm_button = tk.Button(tk_root, text="确认", command=on_confirm)
confirm_button.pack(pady=10)

tk_root.deiconify()
tk_root.mainloop()

