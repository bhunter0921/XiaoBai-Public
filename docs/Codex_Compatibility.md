# Codex 原生宠物适配（M9）

范围：只维护小白比熊；Clawd on Desk v1.7.0 运行主题仍以 themes/xiaobai-bichon/ 为权威，Codex 为派生输出，不改原 APNG、不修改宿主。

## 协议与映射

依据 OpenAI [Codex pet contract](https://github.com/openai/skills/blob/main/skills/.curated/hatch-pet/references/codex-pet-contract.md) 和 [animation rows](https://github.com/openai/skills/blob/main/skills/.curated/hatch-pet/references/animation-rows.md) 核对的基础协议：1536×1872、8×9、单格192×208、57有效格、15全透明空格；manifest 为 id/displayName/description/spritesheetPath。宿主控制帧时长，不能沿用 APNG 的速度。

| 行 | 状态 | 来源 | 0-based采样 |
|---|---|---|---|
|0|idle|A01|0,1,3,5,6,8|
|1|running-right|E07|0,4,8,12,16,20,24,28|
|2|running-left|E07|同右行，水平镜像|
|3|waving|D05|0,3,9,13|
|4|jumping|D06|0,2,9,17,20|
|5|failed|A10|0,2,3,4,5,6,8,11|
|6|waiting|A12|0,1,5,7,8,15|
|7|running|A07|0,1,2,4,6,8|
|8|review|F02|0,5,12,25,40,55|

固定缩放384→184，单格偏移(4,20)，不逐帧按bbox缩放，不伪造新关键帧；failed/waiting/running 去除独立小特效（保留最大连通主体），透明像素RGB归零。左右镜像逐像素相等。现有A02/A13/E07步态统一仍待处理；左右胸背带细节会镜像；工作与日常姿态比例、残余贴身动作线及采样运动效果待实际验收。Codex不直接提供现有Clawd全部41组状态及分级，A09修复独立于此次导出。

## 导出及校验

在仓库根目录，已有 Pillow 依赖：

```bash
python3 scripts/export_codex_pet.py --theme themes/xiaobai-bichon --output pets/xiaobai-bichon
python3 scripts/export_codex_pet.py --output pets/xiaobai-bichon --verify-only
```

输出目录不得预先存在，避免覆盖已验收资源。需要重导出时先备份/移走旧包。校验每个源资源SHA256、尺寸、关键帧索引；输出 lossless WebP，核对57格非空且不触边、15格透明、透明像素RGB及左右镜像；export-manifest.json 记录源资源、帧索引及atlas SHA256；preview-light.png / preview-dark.png 用于离线美术检查，不要求纳入运行包。该检查为项目自建，不等于运行官方 validator 或实际 Codex 客户端验收。

安装到 ${CODEX_HOME:-$HOME/.codex}/pets/xiaobai-bichon/（pet.json + spritesheet.webp）；客户端支持自定义宠物时刷新并选择。Linux/Wayland桌面浮窗支持需在目标版本确认，不将CLI宠物与桌面浮窗混同。

## 当前结果

已使用 RC1 动画资源导出首版 Codex 精灵图。

离线结构校验通过，客户端触发、播放、比例及深浅背景验收仍待完成。

派生资源应与导出脚本及资源清单共同维护。
