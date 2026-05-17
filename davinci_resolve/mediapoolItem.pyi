class MediaPoolItem:
  def GetName(self) -> str:...     # Returns the clip name.
  def SetName(self, name:str)-> bool:...               # Sets the clip's name to name(str). Returns True if successful
  def GetMetadata(self, metadataType)-> str|dict:...        # Returns the metadata value for the key 'metadataType'.
                                                                         # If no argument is specified, a dict of all set metadata properties is returned.
  def SetMetadata(self, metadataType, metadataValue)-> bool:...            # Sets the given metadata to metadataValue (str). Returns True if successful.
  def SetMetadata(self, metadata:dict)                         -> bool:...               # Sets the item metadata with specified 'metadata' dict. Returns True if successful.
  def GetThirdPartyMetadata(self, metadataType)        -> str|dict   :...     # Returns the third party metadata value for the key 'metadataType'.
                                                                         # If no argument is specified, a dict of all set third party metadata properties is returned.
  def SetThirdPartyMetadata(self, metadataType, metadataValue:str) -> bool  :...          # Sets/Add the given third party metadata to metadataValue (str). Returns True if successful.
  def SetThirdPartyMetadata(self, metadata:dict)               -> bool :...              # Sets/Add the item third party metadata with specified 'metadata' dict. Returns True if successful.
  def GetMediaId(self)                                    -> str :...            # Returns the unique ID for the MediaPoolItem.
  def AddMarker(self, frameId, color, name, note, duration,customData)  -> bool :...              # Creates a new marker at given frameId position and with given marker information. 'customData' is optional and helps to attach user specific data to the marker.

  def GetMarkers(self)                                    -> dict:...      # Returns a dict (frameId -> {information}) of all markers and dicts with their information.
                                                                         # Example of output format: {96.0: {'color': 'Green', 'duration': 1.0, 'note': '', 'name': 'Marker 1', 'customData': ''}, ...}
                                                                         # In the above example - there is one 'Green' marker at offset 96 (position of the marker)
  def GetMarkerByCustomData(self, customData)               -> dict:...      # Returns marker {information} for the first matching marker with specified customData.
  def UpdateMarkerCustomData(self, frameId, customData)     -> bool :...              # Updates customData (str) for the marker at given frameId position. CustomData is not exposed via UI and is useful for scripting developer to attach any user specific data to markers.
  def GetMarkerCustomData(self, frameId)                    -> str  :...           # Returns customData str for the marker at given frameId position.
  def DeleteMarkersByColor(self, color)                     -> bool  :...             # Delete all markers of the specified color from the media pool item. "All" as argument deletes all color markers.
  def DeleteMarkerAtFrame(self, frameNum)                   -> bool  :...             # Delete marker at frame number from the media pool item.
  def DeleteMarkerByCustomData(self, customData)            -> bool:...               # Delete first matching marker with specified customData.
  def AddFlag(self, color)                                  -> bool:...               # Adds a flag with given color (str).
  def GetFlagList(self)                                   -> list:...        # Returns a list of flag colors assigned to the item.
  def ClearFlags(self, color)                               -> bool :...              # Clears the flag of the given color if one exists. An "All" argument is supported and clears all flags.
  def GetClipColor(self)                                  -> str   :...          # Returns the item color as a str.
  def SetClipColor(self, colorName)                         -> bool  :...             # Sets the item color based on the colorName (str).
  def ClearClipColor(self)                                -> bool  :...             # Clears the item color.
  def GetClipProperty(self, propertyName=None)              -> str|dict :...       # Returns the property value for the key 'propertyName'.
                                                                         # If no argument is specified, a dict of all clip properties is returned. Check the section below for more information.
  def SetClipProperty(self, propertyName, propertyValue)    -> bool :...              # Sets the given property to propertyValue (str). Check the section below for more information.
  def LinkProxyMedia(self, proxyMediaFilePath)              -> bool :...              # Links proxy media located at path specified by arg 'proxyMediaFilePath' with the current clip. 'proxyMediaFilePath' should be absolute clip path.
  def LinkFullResolutionMedia(self, fullResMediaPath)       -> bool :...              # Links proxy media to full resolution media files specified via its path.
  def UnlinkProxyMedia(self)                              -> bool  :...             # Unlinks any proxy media associated with clip.
  def ReplaceClip(self, filePath)                           -> bool  :...             # Replaces the underlying asset and metadata of MediaPoolItem with the specified absolute clip path.
  def ReplaceClipPreserveSubClip(self, filePath)            -> bool  :...             # Replaces the underlying asset and metadata of a video or audio clip with the specified absolute clip path, preserving original sub clip extents.
  def GetUniqueId(self)                                   -> str  :...           # Returns a unique ID for the media pool item
  def TranscribeAudio(self)                               -> bool  :...             # Transcribes audio of the MediaPoolItem. Returns True if successful; False otherwise
  def ClearTranscription(self)                            -> bool   :...            # Clears audio transcription of the MediaPoolItem. Returns True if successful; False otherwise.
  def GetAudioMapping(self)                               -> str:... # Returns a str with MediaPoolItem's audio mapping information. Check 'Audio Mapping' section below for more information.
  def GetMarkInOut(self)                                  -> dict:...             # Returns dict of in/out marks set (keys omitted if not set), example:
                                                                         # {'video': {'in': 0, 'out': 134}, 'audio': {'in': 0, 'out': 134}}
  def SetMarkInOut(self, _in, _out, type="all")               -> bool  :...             # Sets mark in/out of type "video", "audio" or "all" (default).
  def ClearMarkInOut(self, type="all")                      -> bool :...              # Clears mark in/out of type "video", "audio" or "all" (default).
  def MonitorGrowingFile(self)                            -> bool  :...             # Monitor a file as long as it keeps growing (stops if the file does not grow for some time).