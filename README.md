# 关于ProScripts
原`ProTurnover`现在隆重升级为`ProScripts`。`ProScripts`预计带来包括`ProMarkers`、`ProGoto`、`ProTimelineIO`等全新脚本，分别对应片段标记管理、时间线跳转和更完善的 EDL IO 功能。

## 注意
达芬奇21.1的API有较多修改。目前不确定旧版API是否可用、也不确定旧版API何时会停用。已经完成对ProTurnover使用API的调整工作。但是**其依赖库PTLib仍然在使用许多旧版API的调用方法**，目前**无法评估这是否会影响ProTurnover的相关功能**。请谨慎更新达芬奇21.1。

已经探明达芬奇21.1存在一种对`TimelineItem.GetSourceStartFrame()`的计算bug。在FPS = 24的时间线下，当源入点帧计数i满足`(i - 1) mod 3 == 0`时，`TimelineItem.GetSourceStartFrame()`会出现`-1`帧的偏置。目前已将所有`TimelineItem.GetSourceStartFrame()`改为`Timeline.GetLeftOffset()`。


## 写在开头
达芬奇在 21.1 版本中添加了内置 MCP 服务器，同时在 script 目录中添加了完整的 pyi 和开发文档。从此，Agent 也将具有完善的达芬奇脚本开发能力。更进一步的， Agent 也极有可能代替一名剪辑助理。

~~这简直令人瘫坐眩晕~~。不过我想在这里说，如果剪助的一部分工作是机械、重复的劳动，那么它更应该被脚本完成，而不是一边烧 token 一边还有犯错可能的 Agent。本套脚本在编写时依然尽量使用古法手搓编程。仅在代码文档/注释、parse、设计复杂算法方面让 AI 介入。这是为了可维护性，为了真正知道这个脚本在干什么。我个人的观点就是这样：在一个没有 Git 管理的剪辑软件中，只有我清晰地知道这个脚本会做什么，我才能放心地将它用于生产环境。

## ProMarker
现在你可以像 Avid 一样，以轨道为依据，轻松从时间线上获取并修改片段标记。

仍在测试阶段。发现 bug 请提交 issue。

## ProTurnover

ProTurnover是基于Davinci Resolve API开发的一套Python脚本。它可以快速完成视效镜头标注、在离线工作流程下抽取VFX ID与VFX Plate EDL等常见视效交接工作。

要开始使用，请首先在```PTAsset```目录下创建你自己的帧计数素材。创建方式可以参考[这个视频](https://www.bilibili.com/video/BV12z411b7uL/)。帧计数素材的文件名应该为```FrameCount_2KDCI_24P.mov```。目前尚未支持其他规格的帧计数素材。

---

ProTurnover预设了一些轨道和媒体池文件夹的命名规则。其含义如下：

**时间线轨道命名规则**

|          轨道名 | 用途                    |
|-------------:|:----------------------|
|    VFXPlates | 存放视效子片段               |
| VFXPreTitles | 预标注的视效镜头              |
|    VFXTitles | 标注视效镜头                |
|    Reference | 效果参考                  |
|     VFXShots | 视效镜头                  |
|    ResolveFX | 调整图层、在Davinci中制作的视觉效果 |
|       Resize | 控制素材缩放的调整图层           |
|      Overlay | 带透明通道的素材叠加层           |
|        Drama | 剪辑                    |


**媒体池文件夹名称**

|           名称 | 用途                                 |
|-------------:|:-----------------------------------|
|       Source | 存放原始素材                             |
|        Asset | 存放美术资产                             |
|    Reference | 存放效果参考、离线参考                        |
|     Sequence | 存放剪辑时间线                            |
|     VFXTitle | 存放视效镜头号的子片段                        |
|      Returns | 存放自视音效团队发送回来的媒体文件                  |
|      Offline | 存放离线剪辑使用的媒体，可以视为离线的```Source```文件夹 |
| .ProTurnover | ProTurnover的工作文件夹                  |

这些定义存储于```Utils\PTLib.py```中```WorkTimeline```和```WorkMediaPool```两个类中。你**应该根据所在团队的工作流程修改这些定义**。

---

另外，在```Disabled```文件夹下存放了一些过时的脚本文件。请勿在不了解其具体功能的状况下将其用于生产环境。你也**不应该在完全不了解Turnover流程的前提下将ProTurnover用于生产环境**。

关于Turnover流程，你可参考[剪辑小常老师的视效剪辑不完全操作指南](https://space.bilibili.com/24461148/lists/1457126?type=series)。此脚本是基于这个指南开发的。出于Davinci Resolve的API限制，此脚本无法创建与操作指南中完全一致的```VFXTitle```和```VFXPlate```。但与之关联的EDL文件，ProTurnover均可直接输出。

---

要反馈Bug，请提交Issue。你可以自行Fork此项目，并基于此开发你所需要的特定功能。~~其中package```davinci_resolve```已经整理出了多数API中提供的方法。```PTLib.py```也对常用功能做了封装。~~（已经没必要了，请参考达芬奇官方的 API 文档。）

**碍于个人精力，ProTurnover不保证及时修复Issue中的Bug。在使用ProTurnover的代码时，你应当遵守项目中标注的GPL协议。**

如果你希望就视效交接流程、Davinci Resolve脚本开发这类话题与我讨论，欢迎你联系```martin03@qq.com```。