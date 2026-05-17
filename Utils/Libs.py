from typing import TYPE_CHECKING
from unittest import case

if TYPE_CHECKING:
    from davinci_resolve import *

def getTrackIndex(trackName: str, timeline) -> int:
    count = timeline.GetTrackCount("video")
    for i in range(1, count+1):
        if trackName == timeline.GetTrackName("video", i): return i
    return -1

def saveCurrentTrackEnableStates(timeline) -> dict[int, bool]:
    ret = {}
    count = timeline.GetTrackCount("video")
    for i in range(1, count+1):
        ret[i] = timeline.GetIsTrackEnabled("video", i)
    return ret

def recoverTrackEnableStates(timeline, states: dict[int, bool]):
    ret = {}
    count = timeline.GetTrackCount("video")
    for i in range(1, count + 1):
        timeline.SetTrackEnable("video", i, states[i])

def disableOtherTracks(timeline):
    count = timeline.GetTrackCount("video")
    for i in range(1, count + 1):
        trackHead = timeline.GetTrackName("video", i)[0:7]
        if trackHead != "EDT_ONL" and trackHead != "EDT_OFL":
            timeline.SetTrackEnable("video", i, False)

def getEditTrackList(timeline, type = "ONL") -> list[int]:
    ret: list[int] = []
    count = timeline.GetTrackCount("video")
    for i in range(1, count + 1):
        if timeline.GetTrackName("video", i)[0:7] == f"EDT_{type}": ret.append(i)
    return ret

def getEditOnlineClipList(timeline) -> list["TimelineItem"]:
    ret: list["TimelineItem"] = []
    for i in getEditTrackList(timeline): ret += timeline.GetItemListInTrack("video", i)
    return ret

def toTimeCode(frames: int, fps = 24, hour_offset = 0) -> str:
    fr = frames % fps
    sec = frames // fps
    minute = sec // 60
    sec = sec % 60
    hour = minute // 60
    minute = minute % 60
    hour += hour_offset
    return "%02d:%02d:%02d:%02d" % (hour, minute, sec, fr)

def toFrameCount(TC: str, fps = 24) -> int:
    frm = 0
    tcs = TC.split(":")
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

def get_audio_clips(timeline: "Timeline") -> list["TimelineItem"]:
    ret: list["TimelineItem"] = []
    count = timeline.GetTrackCount("audio")
    for i in range(1, count + 1):
        ret += timeline.GetItemListInTrack("audio", i)
    return ret

class WorkTimeline:
    def __init__(self, _timeline: "Timeline"):
        self.timeline = _timeline
        self.video_track_count = self.timeline.GetTrackCount("video")
        self.audio_track_count = self.timeline.GetTrackCount("audio")
        self.vfx_ref_track = getTrackIndex("VFX_REF", self.timeline)
        self.mfx_mark_track = getTrackIndex("MFX_MRK", self.timeline)
        self.edit_online_track_list = getEditOnlineClipList(self.timeline)
        self.edit_online_clip_list = getEditOnlineClipList(self.timeline)
        self.audio_clip_list = get_audio_clips(self.timeline)

    def get_online_clips_in_range(self, r: range) -> list["TimelineItem"]:
        return get_clips_in_range(self.edit_online_clip_list, r)
    def get_audio_clips_in_range(self, r: range) -> list["TimelineItem"]:
        return get_clips_in_range(self.audio_clip_list, r)
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

    def get_tracks(self, _type: str, _track_type = "video") -> list[int]:
        ret: list[int] = []
        head_length = len(_type)
        for i in range(1, self.video_track_count + 1):
            track_head = self.timeline.GetTrackName(_track_type, i)[0:head_length]
            if track_head == _type: ret.append(i)
        return ret


class WorkMediaPool:
    work_folder_names = ["Source", "TIMELINE", "Connections", "Reference", "Offline"]
    source_folder: "Folder" = None
    timeline_folder: "Folder" = None
    connections_folder: "Folder" = None
    reference_folder: "Folder" = None
    offline_folder: "Folder" = None
    # Source: 放置所有 Online 素材。其中Bin为默认素材箱，ExtraMedia 为对不安全媒体的收集
    # TIMELINE 用于存放所有时间线
    # Connections 用于存放交接时间线与交接媒体。其中分为 SEND 与 RCV 两个子文件夹
    # Reference 用于存放参考媒体。参考媒体被视为项目外部文件，不会被添加到ExtraMedia中
    # Offline 用于存放离线剪辑素材，用于离线剪辑工作。
    def __init__(self, _media_pool: "MediaPool"):
        self.media_pool = _media_pool
        self.root = self.media_pool.GetRootFolder()
        self.search_and_build_folders()

    def search_and_build_folders(self):
        root: "Folder" = self.media_pool.GetRootFolder()
        if len(root.GetSubFolderList())>0:
            for folder in root.GetSubFolderList():
                if folder.GetName() in self.work_folder_names:
                    match folder.GetName():
                        case "Source": self.source_folder = folder
                        case "TIMELINE": self.timeline_folder = folder
                        case "Connections": self.connections_folder = folder
                        case "Reference": self.reference_folder = folder
                        case "Offline": self.offline_folder = folder

        if not self.source_folder: self.media_pool.AddSubFolder(root, self.work_folder_names[0])
        if not self.timeline_folder: self.media_pool.AddSubFolder(root, self.work_folder_names[1])
        if not self.connections_folder: self.media_pool.AddSubFolder(root, self.work_folder_names[2])
        if not self.reference_folder: self.media_pool.AddSubFolder(root, self.work_folder_names[3])
        if not self.offline_folder: self.media_pool.AddSubFolder(root, self.work_folder_names[4])
        for folder in root.GetSubFolderList():
            if folder.GetName() in self.work_folder_names:
                match folder.GetName():
                    case "Source":
                        self.source_folder = folder
                    case "TIMELINE":
                        self.timeline_folder = folder
                    case "Connections":
                        self.connections_folder = folder
                    case "Reference":
                        self.reference_folder = folder
                    case "Offline":
                        self.offline_folder = folder

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

