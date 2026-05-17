# 关于ProTurnover

ProTurnover是基于Davinci Resolve API开发的一套Python脚本。它可以快速完成视效镜头标注、在离线工作流程下抽取VFX ID与VFX Plate EDL等常见视效交接工作。

要开始使用，请首先在```PTAsset```目录下创建你自己的帧计数素材。创建方式可以参考[这个视频](https://www.bilibili.com/video/BV12z411b7uL/)。帧计数素材的文件名应该为```FrameCount_2KDCI_24P.mov```。目前尚未支持对其他规格的帧计数素材。

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

|           名称 | 用途                               |
|-------------:|:---------------------------------|
|       Source | 存放原始素材                           |
|        Asset | 存放美术资产                           |
|    Reference | 存放效果参考、离线参考                      |
|     Sequence | 存放剪辑时间线                          |
|     VFXTitle | 存放视效镜头号的子片段                      |
|      Returns | 存放自视音效团队发送回来的媒体文件                |
|      Offline | 存放离线剪辑使用的媒体，可以离线的```Source```文件夹 |
| .ProTurnover | ProTurnover的工作文件夹                |

这些定义存储于```Utils\PTLib.py```中```WorkTimeline```和```WorkMediaPool```两个类中。你**应该根据所在团队的工作流程修改这些定义**。

---

另外，在```Disabled```文件夹下存放了一些过时的脚本文件。请勿在不了解其具体功能的状况下将其用于生产环境。你也**不应该在完全不了解Turnover流程的前提下将ProTurnover用于生产环境**。

关于Turnover流程，你可参考[剪辑小常老师的视效剪辑不完全操作指南](https://space.bilibili.com/24461148/lists/1457126?type=series)。此脚本是基于这个指南开发的。出于Davinci Resolve的API限制，此脚本无法创建与操作指南中完全一致的```VFXTitle```和```VFXPlate```。但与之关联的EDL文件，ProTurnover均可直接输出。

---

要反馈Bug，请提交Issue。你可以自行Fork此项目，并基于此开发你所需要的特定功能。其中package```davinci_resolve```已经整理出了多数API中提供的方法。```PTLib.py```也对常用功能做了封装。

**碍于个人精力，ProTurnover不保证及时修复Issue中的Bug。在使用ProTurnover的代码时，你应当遵守项目中标注的GPL协议。**

如果你希望就视效交接流程、Davinci Resolve脚本开发这类话题与我讨论，欢迎你联系```martin03@qq.com```。