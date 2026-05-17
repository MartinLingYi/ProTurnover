from Utils.xml_timeline import *

tl = XMLTimeline("/Users/martinly/数据/ResolveScriptTestENV/0329/Timeline 17.xml")

for clip in tl.clipitems:
    print(clip.name, clip.pathurl)