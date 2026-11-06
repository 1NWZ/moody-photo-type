# 批次排版配置

将用户原片保留在可读路径，在任务目录写 JSON。所有相对路径相对于 JSON 所在目录。示例见 [batch.example.json](../examples/batch.example.json)。`font` 必填真实字体文件路径；不要把本机字体路径写进公开仓库。按 [fonts.md](fonts.md) 选用英文字体，按语言检查字体覆盖。示例中的 `fonts/AlegreyaSans-Bold.ttf` 是待提供的文件位置，本包不附带字体文件。整个批次只支持一个顶层 `font`；不要添加脚本不支持的逐图字体、CSS 字族名或字重字段。使用可变字体时，先导出所需字重的静态实例，避免脚本以默认轴值渲染。

- `width`：输出宽度，默认 1080。按可选 crop 裁切后再等比缩放；未设置 crop 则保留原比例。
- `crop`：每张可选 `[left, top, right, bottom]`，0–1 的原图坐标，基于 EXIF 方向矫正后的图像。模型须检查主体安全，脚本不会识别主体。
- `grade`：整组调色设置，可在每个 item 中覆盖。mode 为 fixed（默认）或 none（已调色图复用）；strength 0–1、darkening 0–0.5、saturation 0.8–1.25、light 0–0.15、detail 0–0.3。默认值见 style.md，未知参数会报错。
## 随机参考版式（默认）

- 顶层 `layout_seed`：可选整数随机种子；省略时自动生成并记录。相同候选和顺序可复现抽样；局部返修请固定 item 中唯一候选。
- item 的 `layouts`：键为 `split`、`micro` 或 `vertical`，值为该候选的文字块数组。只提供经读图确认可行的候选，脚本随机选一类并尽量避免相邻重复。
- 文字块字段：`role`、`lines`（明确分行的非空字符串数组），以及可选 `font_ratio`、`line_spacing`。框和对齐由模板固定，不接收逐块自定义 `box`。具体比例见 [layouts.md](layouts.md)。
- `vertical` 必须有 `main`；`split` 必须有 `title`、`body`，可选 `top_left`、`top_right`、`bottom_left`、`bottom_right`；`micro` 必须有 `main`，可选 `left`、`right`。角色不可重复。
- 有 `layouts` 时 `foreground_mask` 必填、尺寸等于最终画布；顶层字号及 item 的旧 `lines`/`box` 不控制这些文字块。脚本不能判断蒙版语义或缺字，仍需审片。
- 每个输出 item 记录 `layout_id` 与 `blocks`；字号和遮挡前边界以各块记录为准。此路径不自动缩小字号，超框报错且不写成片目录。

## 旧配置与无字输出

没有 `layouts` 时仍可使用原 `lines`/`box`、顶层 `font_ratio`/`line_spacing` 单文字组配置，用于旧批次复现。它不会随机选择版式，仍采用旧中心对齐及自动缩字逻辑，不代表新版验收通过。新有字任务使用 `layouts`。无字任务省略 `layouts` 并设置 `lines=[]`。

从 skill 根目录执行（将路径换成实际工作目录）：

```bash
python3 scripts/render_batch.py /path/to/batch.json --output /path/to/rendered
```

输出为编号 JPG、`contact-sheet.jpg`、相对路径 `layout.json` 和 `finals.zip`。无字调色版本位于 `graded/*.png`，不重复放入成片 ZIP。layout.json 记录实际参数、亮度中位数和预设版本；保留原批次 JSON 供重跑，不将 layout.json 当输入。输出目录必须不存在。先检查全部输入及版式再写文件，读取或溢出错误不静默跳过。

EXIF 方向会规范化，输出不会复制原始 EXIF。输入应为 sRGB JPG/PNG；如为 HEIC、RAW 或非 sRGB，先使用宿主的可靠图像工具转换并检查颜色。转换是格式预处理，不代表完成调色。

## 主体在文字前面（有字成片必需）

每个有文字的 item 必须指定 `foreground_mask` 路径（这是本 skill 的交付要求；通用脚本本身仍接受无蒙版输入），读取为灰度蒙版。尺寸必须等于最终输出画布；黑=背景，白=主体。模型先在最终裁切的无字图上分割或描边，再输入排版脚本。脚本先计算各模板文字位置，再用 `文字透明度 × (1 - 主体蒙版)` 合成，主体始终来自原始无字图。记录遮挡前 text_bounds_before_occlusion 与 occluded_text_pixels，便于检查。

若需按经过视觉核对的轮廓生成蒙版，JSON 格式为 `{"size":[1080,1440],"polygons":[[[0.3,0.4],[0.5,0.3],[0.6,0.7]]]}`；示例仅解释结构，不是主体轮廓。坐标为最终画布的归一化位置。主体轮廓需包含足够控制点，不要用示例三角形处理照片。

```bash
python3 scripts/build_mask.py /path/to/contours.json --output /path/to/subject-mask.png
```

蒙版边缘外扩约 1 px，轻微柔化。放大检查文字交界处有无白边、漏字或不合理缺口。

各文字块尺寸验收公式：若遮挡前包围盒为 `[l,t,r,b]`，则宽占比为 `(r-l)/画布宽`，高占比为 `(b-t)/画布高`。仅 `vertical/main` 须分别为 0.35–0.65、0.30–0.60，其他模板检查各块是否位于对应框内；无字时包围盒为空且免检。不要用 `occluded_text_pixels` 反推尺寸。
