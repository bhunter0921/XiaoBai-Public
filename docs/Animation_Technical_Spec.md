# 动画技术规范 v0.1

## 原生协议

固定上游 v1.7.0，theme.json schemaVersion: 1，主题 ID 为目录名。官方 [开发指南](https://github.com/rullerzhou-afk/clawd-on-desk/blob/v1.7.0/docs/guides/guide-theme-creation.md) 明确支持 SVG/GIF/APNG/WebP/PNG/JPG/JPEG。优先 APNG（完整 alpha）；GIF 作为讨论预览，WebP 为优化备选。SVG 仅在后续眼球跟随等确有需要时引入，不能假设外部 SVG 脚本可运行。

MVP eyeTracking.enabled=false，states=[]；miniMode.supported=false；sleepSequence.mode=direct；idle/thinking/working/sleeping 为实际文件，attention/error 也采用独立动画。完整睡眠流程启用 full 时必须补齐 yawning/dozing/collapsing/waking。原始 pet.json 不再作为原生配置入口。

## 生产要求

- 源画布目标 512×512；运行尺寸在显示验证后定，逻辑 viewBox 与像素尺度分离。所有资产一致画布、地面基准与角色比例。
- 普通 8–12 帧，复杂 12–24 帧，工作约12 FPS、普通约8 FPS，按动作调整；一次性动作不得无限循环。实际帧延时、循环参数必须检查。
- 真 alpha，不含棋盘格；深浅背景验证边缘；帧对齐以固定桌面/脚底基准为准，避免逐帧强制缩放造成抖动。
- 角色小耳、尖脸、头身比例保持一致；工作桌道具不得漂移；动态特效不应扩大点击区域。
- 行走面向右，宿主负责左向镜像；含文字的镜像资源单独处理。
- 通过官方 node scripts/validate-theme.js <theme-dir>；并在真实桌面进行安装、切换、休眠、显示、资源消耗验收。

## 当前样品及阻塞

Working v0.2 生成文件实际为 GIF（尽管临时文件名为 .png），430×406，9 帧，每帧 100ms，循环，透明区域存在；仍有边缘及帧一致性风险，未达到正式资产验收。
资源完整性应通过实际文件解码、哈希及动画参数检查确认。

## M3 转码验证记录

scripts/convert_animation.py 用于动画无损格式转换，检查逐帧 RGBA 像素、播放时长、帧数和循环属性。不负责消除源图杂边、调整比例或实现补帧。

命令：

```sh
python scripts/convert_animation.py input.gif output.apng
python scripts/convert_animation.py input.gif output.apng --loop 1
```

动画处理工具用于资源制作及离线验证，安装主题不要求执行这些工具。

## M3 素材质量检查

新增 `scripts/check_animation.py`：检查画布、有效帧、透明像素、时长、内容触边、预期循环参数；记录每帧可见区域及边缘位置变化，不以几何检查替代美术验收。

Working v0.2 APNG 实测 430×406、9 帧、900ms、loop=0，每帧透明占比 38.54%–40.12%；可见区域左/上/右/下边界变化范围分别为 3/21/2/0px。基础检查通过；上边缘变化可能源于头部动作或汗滴，仍需目视验证，不应按包围盒逐帧缩放。静态不透明图及错误尺寸/帧数/循环参数均被拒绝。

本轮 A01/A14 生成尝试未获得符合宠物形象的素材，拒绝入库；仍为待制作。完整工作动画未提交，主题加载尚未验证。

## M3 分层合成原型（A11）

采用 Python/Pillow 离线合成，而非修改 Clawd 引擎。尾巴为独立透明 PNG；身体为无尾巴的关键姿势 PNG 序列。timeline.json 记录 canvas、fps、poseFrames、tail.file/pivot/amplitudeDegrees/frequencyHz、poses[].file/anchor。尾巴围绕根部以固定尺寸旋转，先绘尾巴、后叠身体。每个身体姿势的尾根位置独立标注，随跳跃移动。当前原型为二维刚性旋转，不等于三维摆尾或骨骼动画。

摇尾基准：±40°、1.5Hz、约30FPS，固定尾巴尺寸，围绕尾根独立运动。A11 v0.2 分层合成采用60帧、2000ms、单次播放。尾根接缝、姿势连贯性及状态衔接仍需美术验收。

scripts/compose_animation.py 使用方式：python scripts/compose_animation.py <timeline.json> <attention.apng>。暂仅支持等时长身体姿势、独立单尾巴轨道及单次 APNG 输出；后续再按需求扩展。

## MVP v0.1.0 预览技术结果

统一运行画布 384×384。使用固定缩放及共同底部基准，不逐帧重新缩放。清理微小透明杂点。实际资源尺寸、帧数、时长、循环及 SHA256 见 themes/xiaobai-bichon/asset-manifest.json。完整官方 CLI 和真实桌面仍待验收。

## Alpha 回归检查（A09 缺陷）

sweeping-v0.1 存在眼鼻透明度缺陷。A09 v0.2 局部恢复深色面部区域，帧数、时长及修复区域外像素保持不变。必须在深浅背景下逐帧检查实体内部透明缺口。该修复并非原纹理无损恢复，仍待实机验收。Codex 导出同样须检查 alpha 与深浅背景。
