import inspect
import pathlib
from enum import Enum
from typing import TYPE_CHECKING, Any
import re
from collections import defaultdict
from bisect import bisect_left


if TYPE_CHECKING:
    from davinci_resolve import *

def get_script_dir() -> pathlib.Path:
    if "__file__" in globals():
        return pathlib.Path(__file__).parent.absolute().parent
    return pathlib.Path(inspect.getfile(inspect.currentframe())).parent

def find_neighbors(n: int, _keys: list) -> tuple[int, int]:
    idx = bisect_left(_keys, n)
    left = None
    right = None
    # 左侧最近
    if idx > 0:
        k = _keys[idx - 1]
        left = k
    # 如果刚好命中
    if idx < len(_keys) and _keys[idx] == n:
        k = _keys[idx]
        return k,k
    # 右侧最近
    if idx < len(_keys):
        k = _keys[idx]
        right = k
    return left, right

def check_shot_name_rule(_rule: str) -> str:
    match = re.search(r"\[ShotIndex]", _rule)
    if match:
        remaining = _rule[match.end():]
        if re.search(r"\[.*?]", remaining):
            return "NotTail"
        else:
            return "Pass"
    return "NoContain"

def format_input(_string: str, _data: dict[str, Any]) -> str:
    def repl(match):
        key = match.group(1)  # 取 [] 内部内容
        if key in _data.keys(): return f"{_data[key]}"
        return f"[{key}]"
    ret = re.sub(r"\[(.*?)]", repl, _string)
    return ret

def get_shot_index(_rule: str, _shot_name: str) ->  int | None:
    shot_index_end = 0
    for match in re.finditer(r"\[ShotIndex]", _rule):
        shot_index_end = match.end()
    shot_index_range = (shot_index_end - len(_rule) - 4, shot_index_end - len(_rule))
    if shot_index_range[1] == 0:
        res = _shot_name[shot_index_range[0]: len(_shot_name)]
    else:
        res = _shot_name[shot_index_range[0]: shot_index_range[1]]
    try:
        return int(res)
    except ValueError:
        return None



def merge_intervals(items) -> list[dict[str, Any]]:
    # 1. 按 name 分组
    groups = defaultdict(list)
    for it in items:
        groups[it["name"]].append((it["in"], it["out"]))

    result = []

    # 2. 每个 name 内分别合并
    for name, intervals in groups.items():
        # 按起点排序
        intervals.sort(key=lambda x: x[0])

        merged = []
        cur_start, cur_end = intervals[0]

        for start, end in intervals[1:]:
            # 可合并（相接或重叠）
            if start <= cur_end:
                cur_end = max(cur_end, end)
            else:
                merged.append({
                    "name": name,
                    "in": cur_start,
                    "out": cur_end
                })
                cur_start, cur_end = start, end

        # 收尾
        merged.append({
            "name": name,
            "in": cur_start,
            "out": cur_end
        })

        result.extend(merged)

    return result

def clipinfo_of(_media_pool_item: "MediaPoolItem", _start_frame: int = 0, _end_frame: int = -1,  _media_type: int = 1, _track_index: int = 1, _record_frame: int = -1) -> dict[str, Any]:
    if _end_frame == -1 and _record_frame != -1: return {"mediaPoolItem": _media_pool_item, "startFrame": _start_frame, "trackIndex": _track_index, "recordFrame": _record_frame}
    if _end_frame == -1: return {"mediaPoolItem": _media_pool_item, "startFrame": _start_frame}
    if _record_frame == -1: return {"mediaPoolItem": _media_pool_item, "startFrame": _start_frame, "endFrame": _end_frame, "mediaType": _media_type}
    return {"mediaPoolItem": _media_pool_item, "startFrame": _start_frame, "endFrame": _end_frame, "trackIndex": _track_index, "mediaType": _media_type, "recordFrame": _record_frame}



def to_time_code(frames: int, fps = 24, hour_offset = 0) -> str:
    fr = frames % fps
    sec = frames // fps
    minute = sec // 60
    sec = sec % 60
    hour = minute // 60
    minute = minute % 60
    hour += hour_offset
    return "%02d:%02d:%02d:%02d" % (hour, minute, sec, fr)

def to_frame_count(TC: str, fps = 24) -> int:
    frm = 0
    tcs = TC.split(":")
    # TC = 01:22:42:10
    # tcs = [01,22,42,10]
    if len(tcs) != 4: return 0
    frm = int(tcs[3]) + fps * (int(tcs[2]) + 60 * (int(tcs[1]) + 60 * int(tcs[0])))
    return frm

def overlap(a: range, b: range) -> bool:
    return max(a.start, b.start) < min(a.stop, b.stop)

def get_clips_in_range(clip_list: list["TimelineItem"], r: range) -> list["TimelineItem"]:
    ret: list["TimelineItem"] = []
    for clip in clip_list:
        clip_range = range(clip.GetStart(), clip.GetEnd(), 1)
        if overlap(clip_range, r): ret.append(clip)
    return ret



class WorkTimeline:
    class TrackType(Enum):
        Drama = "Drama"
        Overlay = "Overlay"
        ResolveFX = "ResolveFX"
        Resize = "Resize"
        Reference = "Reference"
        FXSubclip = "VFXPlates"
        FXShot_mark = "VFXTitles"
        FXShot_premark = "VFXPreTitles"
        FXReturn = "VFXShots"

    def __init__(self, _timeline: "Timeline"):
        self.timeline = _timeline

    @property
    def video_track_count(self): return self.timeline.GetTrackCount("video")
    @property
    def audio_track_count(self): return self.timeline.GetTrackCount("audio")
    @property
    def video_tracks(self) -> list[str]:
        ret: list[str] = []
        for i in range(1, self.video_track_count + 1):
            tn = f"V{i}/{self.timeline.GetTrackName("video", i)}"
            ret.append(tn)
        return ret
    @property
    def audio_tracks(self) -> list[str]:
        ret: list[str] = []
        for i in range(1, self.audio_track_count + 1):
            tn = f"{self.timeline.GetTrackName("audio", i)}"
            ret.append(tn)
        return ret

    def get_track_index(self, track_name: str) -> int:
        count = self.timeline.GetTrackCount("video")
        for i in range(1, count + 1):
            if track_name == self.timeline.GetTrackName("video", i): return i
        return -1

    def save_current_track_enable_states(self) -> dict[int, bool]:
        ret = {}
        count = self.timeline.GetTrackCount("video")
        for i in range(1, count + 1):
            ret[i] = self.timeline.GetIsTrackEnabled("video", i)
        return ret

    def recover_track_enable_states(self, states: dict[int, bool]):
        ret = {}
        count = self.timeline.GetTrackCount("video")
        for i in range(1, count + 1):
            self.timeline.SetTrackEnable("video", i, states[i])

    def get_audio_clips(self) -> list["TimelineItem"]:
        ret: list["TimelineItem"] = []
        count = self.timeline.GetTrackCount("audio")
        for i in range(1, count + 1):
            ret += self.timeline.GetItemListInTrack("audio", i)
        return ret

    def get_track_clips_in_range(self, r: range, _tracks: list[int], _track_type = "video") -> list["TimelineItem"]:
        ret: list["TimelineItem"] = []
        for track in _tracks:
            clips: list["TimelineItem"] = self.timeline.GetItemListInTrack(_track_type, track)
            for clip in clips:
                clip_range = range(clip.GetStart(), clip.GetEnd(), 1)
                if overlap(clip_range, r): ret.append(clip)
        return ret
    def get_track_clips(self, _tracks: list[int], _track_type = "video") -> list["TimelineItem"]:
        ret: list["TimelineItem"] = []
        for track in _tracks:
            ret += self.timeline.GetItemListInTrack(_track_type, track)
        return ret
    def get_all_clips(self, _type = "all") -> list["TimelineItem"]:
        ret: list["TimelineItem"] = []
        vid: list["TimelineItem"] = []
        aud: list["TimelineItem"] = []
        for i in range(1, self.video_track_count + 1):
            vid += self.timeline.GetItemListInTrack("video", i)
        for i in range(1, self.audio_track_count + 1):
            aud += self.timeline.GetItemListInTrack("audio", i)

        if _type == "all": ret = vid + aud
        if _type == "video": ret = vid
        if _type == "audio": ret = aud
        return ret

    def get_tracks_via_name(self, _type: str, _track_type = "video") -> list[int]:
        ret: list[int] = []
        head_length = len(_type)
        for i in range(1, self.video_track_count + 1):
            track_head = self.timeline.GetTrackName(_track_type, i)[0:head_length]
            if track_head == _type: ret.append(i)
        return ret
    def get_tracks(self, _type: TrackType) -> list[int]:
        track_name = _type.value
        return self.get_tracks_via_name(track_name, "video")

    def get_fx_data(self, _target_tracks: list[int], _with_audio_clip: bool = True) -> dict[str, list["TimelineItem"]]:
        _fx_timeline = self
        title_tracks = _target_tracks
        titles = _fx_timeline.get_track_clips(title_tracks)
        clips = _fx_timeline.get_track_clips(_fx_timeline.get_tracks(WorkTimeline.TrackType.Drama))
        overlays = _fx_timeline.get_track_clips(_fx_timeline.get_tracks(WorkTimeline.TrackType.Overlay))
        refs = _fx_timeline.get_track_clips(_fx_timeline.get_tracks(WorkTimeline.TrackType.Reference))
        audios = _fx_timeline.get_all_clips("audio")

        ret: dict[str, list["TimelineItem"]] = {}
        # 扫描所需片段
        for title in titles:
            title_in = title.GetStart()
            title_out = title.GetEnd()
            title_range = range(title_in, title_out, 1)

            linked_clips: list["TimelineItem"] = []
            if len(clips) > 0:
                linked_clips += get_clips_in_range(clips, title_range)
            if len(audios) > 0 and _with_audio_clip:
                linked_clips += get_clips_in_range(audios, title_range)
            if len(overlays) > 0:
                linked_clips += get_clips_in_range(overlays, title_range)
            if len(refs) > 0:
                linked_clips += get_clips_in_range(refs, title_range)

            ret[title.GetName()] = linked_clips
        return ret

    def create_track(self, _type: TrackType) -> int:
        ret = -1
        match _type:
            case self.TrackType.Drama:
                tracks = self.get_tracks(self.TrackType.Drama)
                track_index = tracks[-1] + 1
                if self.timeline.AddTrack("video", {"index": track_index}):
                    ret = track_index
                    self.timeline.SetTrackName("video", track_index, _type.value)

            case self.TrackType.Overlay:
                tracks = self.get_tracks(self.TrackType.Drama) + self.get_tracks(self.TrackType.Overlay)
                track_index = tracks[-1] + 1
                if self.timeline.AddTrack("video", {"index": track_index}):
                    ret = track_index
                    self.timeline.SetTrackName("video", track_index, _type.value)

            case self.TrackType.Resize | self.TrackType.FXShot_mark | self.TrackType.FXShot_premark:
                tracks = self.get_tracks(self.TrackType.Drama) + self.get_tracks(self.TrackType.Overlay) + self.get_tracks(self.TrackType.Resize)
                track_index = tracks[-1] + 1
                if self.timeline.AddTrack("video", {"index": track_index}):
                    ret = track_index
                    self.timeline.SetTrackName("video", track_index, _type.value)
        return ret






class WorkMediaPool:
    class WorkFolderType(Enum):
        Source = "Source"
        Asset = "Asset"
        Reference = "Reference"
        Sequence = "Sequence"
        VFXTitle = "VFXTitles"
        Turnover = "Turnover"
        Deliverable = "Returns"
        Offline = "Offline"
        WorkFolder = ".ProTurnover"

    pt_source :dict[str, "MediaPoolItem"] = {}

    def __init__(self, _media_pool: "MediaPool"):
        self.media_pool = _media_pool
        self.root = self.media_pool.GetRootFolder()

    def get_folder(self, _folder: WorkFolderType) -> ("Folder" | None):
        for f in self.root.GetSubFolderList():
            if f.GetName() == _folder.value: return f
        return None
    def create_folder(self, _folder: WorkFolderType) -> "Folder":
        tgt = self.get_folder(_folder)
        if not tgt: return self.media_pool.AddSubFolder(self.root, _folder.value)
        return tgt

    def subfolder_of(self, folder: "Folder", _folder_name: str) -> ("Folder"|None):
        if len(folder.GetSubFolderList()) == 0: return None
        for f in folder.GetSubFolderList():
            if f.GetName() == _folder_name: return f
        return None

    def get_all_clip(self, _target: "Folder") -> list["MediaPoolItem"]:
        if len(_target.GetClipList()) == 0 and len(_target.GetSubFolderList()) == 0: return []
        if len(_target.GetSubFolderList()) == 0:
            return _target.GetClipList()
        else:
            ret: list["MediaPoolItem"] = _target.GetClipList()
            for sf in _target.GetSubFolderList():
                if sf.GetName() == self.work_folder_names[2] or sf.GetName() == self.work_folder_names[3] or sf.GetName() == self.work_folder_names[4]:
                    continue
                ret += self.get_all_clip(sf)
            return ret

    def register_source(self,alies: str, path: pathlib.Path) -> ("MediaPoolItem" | None):
        if not path.exists(): return None
        if alies in self.pt_source: return self.pt_source[alies]
        wf = self.get_folder(self.WorkFolderType.WorkFolder)
        wfs = self.subfolder_of(wf, "PTAsset")
        if not wfs: wfs = self.media_pool.AddSubFolder(wf, "PTAsset")

        wfs_src_list = wfs.GetClipList()
        for clip in wfs_src_list:
            clip_path = pathlib.Path(clip.GetClipProperty("Clip Directory")) / clip.GetClipProperty("Clip Name")
            if clip_path == path:
                self.pt_source[alies] = clip
                return clip

        mpi: "MediaPoolItem" = self.media_pool.ImportMedia([str(path)])[0]
        self.media_pool.MoveClips([mpi], wfs)
        self.pt_source[alies] = mpi
        return mpi

    def get_source(self, alies: str) -> ("MediaPoolItem" | None):
        keys = self.pt_source.keys()
        if alies not in keys: return None
        return self.pt_source[alies]


class EDL:
    class EDLDataType(Enum):
        index = "Index"
        reel_name = "ReelName"
        v = "V"
        c = "C"
        start = "Start"
        end = "End"
        record_start = "RecordStart"
        record_end = "RecordEnd"
        edl_clip_name = "EDLClipName"

    def __init__(self,_title: str = "untitled_timeline", _fps = 24, _fcm: str = "NON-DROP FRAME" ):
        self.title = _title
        self.fcm = _fcm
        self.fps = _fps
        self.items: list[dict[EDL.EDLDataType, str]] = []

    def parse_str(self, s: list[str]):
        """
        从 EDL 文本行解析当前对象
        """
        self.items.clear()
        current_item = None

        for line in s:
            line = line.rstrip()
            if not line:
                continue
            # TITLE:
            if line.startswith("TITLE:"):
                self.title = line.replace("TITLE:", "", 1).strip()
                continue
            # FCM:
            if line.startswith("FCM:"):
                self.fcm = line.replace("FCM:", "", 1).strip()
                continue
            # EDL 主行
            # 例:
            # 001  AX       V     C        00:00:00:00 00:00:10:00 00:00:00:00 00:00:10:00
            m = re.match(
                r"^\s*(\d+)\s+"
                r"(\S+)\s+"
                r"(\S+)\s+"
                r"(\S+)\s+"
                r"(\d\d:\d\d:\d\d:\d\d)\s+"
                r"(\d\d:\d\d:\d\d:\d\d)\s+"
                r"(\d\d:\d\d:\d\d:\d\d)\s+"
                r"(\d\d:\d\d:\d\d:\d\d)",
                line
            )

            if m:
                current_item = {
                    self.EDLDataType.index: m.group(1),
                    self.EDLDataType.reel_name: m.group(2),
                    self.EDLDataType.v: m.group(3),
                    self.EDLDataType.c: m.group(4),
                    self.EDLDataType.start: m.group(5),
                    self.EDLDataType.end: m.group(6),
                    self.EDLDataType.record_start: m.group(7),
                    self.EDLDataType.record_end: m.group(8),
                }
                self.items.append(current_item)
                continue
            # FROM CLIP NAME:
            if "FROM CLIP NAME:" in line and current_item is not None:
                clip_name = line.split("FROM CLIP NAME:", 1)[1].strip()
                current_item[self.EDLDataType.edl_clip_name] = clip_name

    def get_str(self) -> list[str]:
        """
        输出 EDL 文本行
        """
        lines: list[str] = [f"TITLE: {self.title}", f"FCM: {self.fcm}", ""]

        for item in self.items:
            line = (
                f"{item.get(self.EDLDataType.index, '000'):>003}  "
                f"{item.get(self.EDLDataType.reel_name, "AX"):<32} "
                f"{item.get(self.EDLDataType.v, 'V'):<5} "
                f"{item.get(self.EDLDataType.c, 'C'):<5} "
                f"{item.get(self.EDLDataType.start, '00:00:00:00')} "
                f"{item.get(self.EDLDataType.end, '00:00:00:00')} "
                f"{item.get(self.EDLDataType.record_start, '00:00:00:00')} "
                f"{item.get(self.EDLDataType.record_end, '00:00:00:00')}"
            )
            lines.append(line)

            if self.EDLDataType.edl_clip_name in item:
                lines.append(
                    f"* FROM CLIP NAME: {item[self.EDLDataType.edl_clip_name]}"
                )
            lines.append("")
        return lines

    def load_from(self, path):
        pass

    def save_to(self, path):
        tgt = open(path, "w")
        for line in self.get_str():
            tgt.write(line)
            tgt.write("\n")
        tgt.close()

    def append_item(self, item: dict[EDLDataType, Any]):
        last_item: dict[EDL.EDLDataType, str] = {}
        if len(self.items)>0: last_item = self.items[-1]
        ii: int = 1
        irs: int = 0
        ire: int = 0
        iv = "V"
        ic = "C"
        if len(last_item.keys())>0:
            ii = int(last_item[self.EDLDataType.index]) + 1
            irs = to_frame_count(last_item[self.EDLDataType.record_end], self.fps)

        if self.EDLDataType.index in item.keys(): ii = item[self.EDLDataType.index]
        if self.EDLDataType.v in item.keys(): iv = item[self.EDLDataType.v]
        if self.EDLDataType.c in item.keys(): ic = item[self.EDLDataType.c]
        if self.EDLDataType.record_start in item.keys(): irs = item[self.EDLDataType.record_start]
        if self.EDLDataType.record_end in item.keys(): ire = item[self.EDLDataType.record_end]
        else: ire = irs + item[self.EDLDataType.end] - item[self.EDLDataType.start]

        self.items.append({
            self.EDLDataType.index: f"{ii:03d}",
            self.EDLDataType.reel_name: item[self.EDLDataType.reel_name],
            self.EDLDataType.v: iv,
            self.EDLDataType.c: ic,
            self.EDLDataType.start: to_time_code(item[self.EDLDataType.start], self.fps),
            self.EDLDataType.end: to_time_code(item[self.EDLDataType.end], self.fps),
            self.EDLDataType.record_start: to_time_code(irs, self.fps),
            self.EDLDataType.record_end: to_time_code(ire, self.fps),
            self.EDLDataType.edl_clip_name: item[self.EDLDataType.edl_clip_name],
        })
