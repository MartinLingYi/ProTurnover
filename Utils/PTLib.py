import inspect
import pathlib
from enum import Enum
from typing import TYPE_CHECKING, Any
import re
from collections import defaultdict
from bisect import bisect_left, bisect_right


if TYPE_CHECKING:
    from davinci_resolve import *

#region Static Methods

def require_start_offset(clip: TimelineItem) -> bool:
    """
    What the f--k?
    非常奇怪的特性。对于StartTC不为0的mediaPoolItem，如果其timelineItem的Start也不为0，就需要给其Start补1帧的偏置。
    """
    clip_start = clip.GetSourceStartFrame()
    clip_s_tc = clip.GetMediaPoolItem().GetClipProperty("Start TC")
    return (clip_s_tc != "00:00:00:00") and (clip_start != 0)

def get_script_dir() -> pathlib.Path:
    """取得脚本所在目录，用于定位 PTAsset 等随脚本分发的资源。

    常规运行时返回项目根目录，没有 __file__ 的环境下回退到调用栈所在目录。
    """
    if "__file__" in globals():
        return pathlib.Path(__file__).parent.absolute().parent
    return pathlib.Path(inspect.getfile(inspect.currentframe())).parent

def find_neighbors(n: int, _keys: list) -> tuple[int, int]:
    """在升序列表中找出与 n 相邻的左右两个元素。

    n 与某元素相同时返回 (n, n)，某一侧不存在时为 None。
    """
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
    """检查视效镜头命名规则是否可用。

    规则须包含 [ShotIndex] 且其后没有其他字段，返回 "Pass"/"NotTail"/"NoContain"。
    """
    match = re.search(r"\[ShotIndex]", _rule)
    if match:
        remaining = _rule[match.end():]
        if re.search(r"\[.*?]", remaining):
            return "NotTail"
        else:
            return "Pass"
    return "NoContain"

def format_input(_string: str, _data: dict[str, Any]) -> str:
    """按 _data 填充字符串中的 [字段] 占位符。

    _data 中没有的字段保留原样，便于发现缺失数据。
    """
    def repl(match):
        key = match.group(1)  # 取 [] 内部内容
        if key in _data.keys(): return f"{_data[key]}"
        return f"[{key}]"
    ret = re.sub(r"\[(.*?)]", repl, _string)
    return ret

def get_shot_index(_rule: str, _shot_name: str) ->  int | None:
    """从视效镜头名中取出镜头编号。

    依据 [ShotIndex] 在命名规则中的位置，截取镜头名中的对应内容并转为整数。
    """
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
    """按名称分组，合并重叠或首尾相接的帧区间。

    传入与返回的都是含 "name"、"in"、"out" 的字典列表，同一名称的区间互不相交。
    """
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
    """构造 MediaPool.AppendToTimeline 所需的片段信息字典。

    -1 表示该参数不指定：仅给 _record_frame 时按记录位置插入，仅给源出入点时按源时间插入。
    """
    if _end_frame == -1 and _record_frame != -1: return {"mediaPoolItem": _media_pool_item, "startFrame": _start_frame, "trackIndex": _track_index, "recordFrame": _record_frame}
    if _end_frame == -1: return {"mediaPoolItem": _media_pool_item, "startFrame": _start_frame}
    if _record_frame == -1: return {"mediaPoolItem": _media_pool_item, "startFrame": _start_frame, "endFrame": _end_frame, "mediaType": _media_type}
    return {"mediaPoolItem": _media_pool_item, "startFrame": _start_frame, "endFrame": _end_frame, "trackIndex": _track_index, "mediaType": _media_type, "recordFrame": _record_frame}



def to_time_code(frames: int, fps = 24, hour_offset = 0) -> str:
    """把帧数换算为 HH:MM:SS:FF 时间码。

    hour_offset 用于补偿项目起始时间码，fps 默认 24。
    """
    fr = frames % fps
    sec = frames // fps
    minute = sec // 60
    sec = sec % 60
    hour = minute // 60
    minute = minute % 60
    hour += hour_offset
    return "%02d:%02d:%02d:%02d" % (hour, minute, sec, fr)

def to_frame_count(TC: str, fps = 24) -> int:
    """把 HH:MM:SS:FF 时间码换算为帧数。

    不是四段式时间码时返回 0，fps 默认 24。
    """
    frm = 0
    tcs = TC.split(":")
    # TC = 01:22:42:10
    # tcs = [01,22,42,10]
    if len(tcs) != 4: return 0
    frm = int(tcs[3]) + fps * (int(tcs[2]) + 60 * (int(tcs[1]) + 60 * int(tcs[0])))
    return frm

def overlap(a: range, b: range) -> bool:
    """判断两个帧范围是否相交。

    区间按左闭右开处理。
    """
    return max(a.start, b.start) < min(a.stop, b.stop)

def get_clips_in_range(clip_list: list["TimelineItem"], r: range) -> list["TimelineItem"]:
    """筛选出与给定帧范围有交集的片段。

    返回顺序与传入列表一致。
    """
    ret: list["TimelineItem"] = []
    for clip in clip_list:
        clip_range = range(clip.GetStart().__round__(), clip.GetEnd().__round__(), 1)
        if overlap(clip_range, r): ret.append(clip)
    return ret

#endregion

class WorkTimeline:
    """达芬奇时间线（Timeline）的封装。

    按 ProTurnover 的轨道命名约定（TrackType）提供轨道查找、片段扫描与轨道创建功能。

    方法:
        __init__: 记录被封装的时间线。
        video_track_count: 视频轨道数量。
        audio_track_count: 音频轨道数量。
        video_tracks: 视频轨道名称列表，形如 "V1/Drama"。
        audio_tracks: 音频轨道名称列表。
        get_track_index: 按名称查找视频轨道序号。
        save_current_track_enable_states: 记录各视频轨道的启用状态。
        recover_track_enable_states: 恢复各视频轨道的启用状态。
        get_audio_clips: 取得所有音频片段。
        get_track_clips_in_range: 取得指定轨道上落入帧范围的片段。
        get_track_clips: 取得指定轨道上的全部片段。
        get_all_clips: 取得整条时间线的片段，可按视频或音频过滤。
        get_tracks_via_name: 按轨道名前缀查找轨道序号。
        get_tracks: 按 TrackType 查找轨道序号。
        get_fx_data: 收集与各视效标注片段相关的剪辑、音频、叠加与参考片段。
        create_track: 按 TrackType 新建视频轨道并返回轨道序号。
    """
    class TrackType(Enum):
        """ProTurnover 的轨道命名约定，枚举值即轨道名。

        枚举值与轨道名不同的成员：FXSubclip 为 VFXPlates、FXShot_mark 为 VFXTitles、
        FXShot_premark 为 VFXPreTitles、FXReturn 为 VFXShots。
        """
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
    """媒体池（MediaPool）的封装。

    负责 ProTurnover 约定文件夹的创建与查找，以及帧计数素材等外部资源的登记。

    类属性:
        pt_source: 别名到 MediaPoolItem 的登记表，由所有实例共享。

    方法:
        __init__: 记录媒体池对象并取得根文件夹。
        get_folder: 按 WorkFolderType 查找根目录下的文件夹。
        create_folder: 取得约定的文件夹，不存在时创建。
        subfolder_of: 按名称查找子文件夹。
        get_all_clip: 递归收集文件夹内的片段。
        register_source: 登记磁盘文件，已登记过则直接返回。
        get_source: 按别名取出已登记的 MediaPoolItem。
    """
    class WorkFolderType(Enum):
        """ProTurnover 的媒体池文件夹命名约定，枚举值即文件夹名。

        枚举值与文件夹名不同的成员：VFXTitle 为 VFXTitles、Deliverable 为 Returns、
        WorkFolder 为 .ProTurnover。
        """
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
                if sf.GetName() == self.WorkFolderType.Reference or sf.GetName() == self.WorkFolderType.WorkFolder or sf.GetName() == self.WorkFolderType.Sequence:
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
    """EDL 文件的读写容器。

    以条目为单位维护 EDL 数据，支持文本解析、生成 EDL 文本、写入文件与逐条追加条目。

    方法:
        __init__: 设定标题、帧率与 FCM。
        parse_str: 从 EDL 文本行解析标题与各条目。
        get_str: 输出 EDL 文本行。
        load_from: 预留的读取接口，尚未实现。
        save_to: 将 EDL 写入指定文件。
        append_item: 追加条目，自动编号并按帧数换算时间码。
    """
    class EDLDataType(Enum):
        """EDL 条目的字段名。

        含序号、卷名、通道、剪辑方式、源入出点、记录入出点与源片段名（FROM CLIP NAME）。
        """
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


class Marker:
    at_clip_frame: int
    payload: MarkerInfo
    def __init__(self, at_clip_frame: int, payload: MarkerInfo):
        self.at_clip_frame = at_clip_frame
        self.payload = payload

    def content_equal_to(self, marker: Marker) -> bool:
        t_pl = marker.payload
        s_pl = self.payload
        return (s_pl["color"] == t_pl["color"]) and (s_pl["name"] == t_pl["name"]) and (s_pl["note"] == t_pl["note"]) and (s_pl["duration"] == t_pl["duration"])

class ClipMarkerSyncer:
    clip: TimelineItem
    def __init__(self, clip: TimelineItem):
        self.clip: TimelineItem = clip

    def get(self) -> dict[int, Marker]:
        ret: dict[int, Marker] = {}
        clip_in = round(self.clip.GetStart())
        clip_s_in: int = self.clip.GetSourceStartFrame()
        if require_start_offset(self.clip): clip_s_in += 1
        markers = self.clip.GetMarkers()
        for m in markers:
            fi = clip_in + m - clip_s_in
            ret[fi] = Marker(m, markers[m])

        return ret

    def set(self, markers: dict[int, Marker]):
        original_dict = self.get()
        original_markers = {m.at_clip_frame: m for m in original_dict.values()}
        now_markers = {m.at_clip_frame: m for m in markers.values()}
        diff = original_markers.keys() ^ now_markers.keys()
        same = original_markers.keys() & now_markers.keys()

        for fi in diff:
            if fi not in now_markers: self.clip.DeleteMarkerAtFrame(fi)
            if fi not in original_markers:
                new_marker = now_markers[fi].payload
                self.clip.AddMarker(fi, new_marker["color"],new_marker["name"], new_marker["note"], new_marker["duration"])

        for fi in same:
            if not original_markers[fi].content_equal_to(now_markers[fi]):
                new_marker = now_markers[fi].payload
                self.clip.DeleteMarkerAtFrame(fi)
                self.clip.AddMarker(fi, new_marker["color"], new_marker["name"], new_marker["note"],
                                    new_marker["duration"])


class MarkerSequence:
    # m_seq: {v_track_index: {in_frame: Marker} }
    m_seq: dict[int, dict[int, Marker]] = {}
    wt: WorkTimeline
    def __init__(self, _timeline: WorkTimeline):
        self.wt = _timeline

    def load(self):
        for p in range(1, self.wt.video_track_count + 1):
            current: dict[int, Marker] = {}
            clips = self.wt.get_track_clips([p],"video")
            for clip in clips:
                current |= ClipMarkerSyncer(clip).get()

            self.m_seq[p] = current

    def to_tsv(self, fps) -> list[str]:
        tsv: list[str] = ["RecordStart\tDuration\tVTrack\tName\tNote\tColor"]
        for v_track in self.m_seq:
            for (fi, marker) in self.m_seq[v_track].items():
                pl: MarkerInfo = marker.payload
                _dur = pl["duration"]
                _name = pl["name"]
                _note = pl["note"]
                _color = pl["color"]
                tsv.append(f"{to_time_code(fi,fps)}\t{_dur}\t{v_track}\t{_name}\t{_note}\t{_color}")

        return tsv

    def get_clip_of(self, tfi:int, v:int) -> TimelineItem|None:
        clips = self.wt.get_track_clips([v], "video")
        clip_ins = [c.GetStart().__round__() for c in clips]
        p = max(bisect_right(clip_ins, tfi) - 1, 0)
        if len(clips) > p >= 0 and tfi <= clips[p].GetEnd().__round__(): return clips[p]
        else:
            print(tfi, v, clip_ins, p, clip_ins[p])
            return None

    def get_source_frame_in(self, tfi: int, v: int) -> int:
        clip = self.get_clip_of(tfi, v)
        require_start_offset(clip)
        if clip is None: return -1
        clip_start = clip.GetStart().__round__()
        clip_source_start = clip.GetSourceStartFrame()
        if require_start_offset(clip): clip_source_start += 1
        sfi = tfi - clip_start + clip_source_start
        return sfi



    def parse_from(self, tsv: list[str], fps: int):
        if not tsv:
            print("Empty TSV.")
            return

        parsed: list[dict[str, Any]] = []
        header = tsv[0].split("\t")
        for v in tsv[1:]:
            values = v.split("\t")
            parsed_dict: dict[str, Any] = {}
            for index in range(len(values)):
                value = values[index]
                parsed_dict[header[index]] = value

            parsed.append(parsed_dict)


        self.m_seq = {}
        for marker_info in parsed:
            fi = 0
            v_track: int = 0
            resolve_marker_info: MarkerInfo = {}
            for (k,v) in marker_info.items():
                match k:
                    case "RecordStart":
                        fi = to_frame_count(v,fps)
                    case "Duration":
                        resolve_marker_info["duration"] = int(v)
                    case "VTrack":
                        v_track = int(v)
                    case "Name":
                        resolve_marker_info["name"] = v
                    case "Note":
                        resolve_marker_info["note"] = v
                    case "Color":
                        resolve_marker_info["color"] = v

            if v_track == 0 or fi == 0: continue
            sfi = self.get_source_frame_in(fi,v_track)
            if v_track not in self.m_seq: self.m_seq[v_track] = {}
            self.m_seq[v_track][fi] = Marker(sfi, resolve_marker_info)

    def write(self):
        for v_track in self.m_seq:
            fis = list(self.m_seq[v_track].keys())
            markers = list(self.m_seq[v_track].values())
            i = 0
            while i < len(fis):
                current_clip_markers: dict[int, Marker] = {}
                fi = fis[i]
                clip = self.get_clip_of(fi,v_track)
                if clip is None:
                    print(f"Dropped invalid marker at {fi}")
                    i += 1
                    continue
                clip_range = range(clip.GetStart().__round__(), clip.GetEnd().__round__())
                for j in range(i, len(fis)):
                    fi = fis[j]
                    marker = markers[j]
                    if fi in clip_range:
                        current_clip_markers[fi] = marker
                        i = j

                ClipMarkerSyncer(clip).set(current_clip_markers)
                i+=1
