# 批次排版配置

将用户原片保留在可读路径，在任务目录写 JSON。所有相对路径相对于 JSON 所在目录。示例见 [batch.example.json](../examples/batch.example.json)。`font` 必填真实字体文件路径；不要把本机字体路径写进公开仓库。按 [fonts.md](fonts.md) 选用英文字体，按语言检查字体覆盖。示例中的 `fonts/AlegreyaSans-Bold.ttf` 是待提供的文件位置，本包不附带字体文件。整个批次只支持一个顶层 `font`；不要添加脚本不支持的逐图字体、CSS 字族名或字重字段。使用可变字体时，先导出所需字重的静态实例，避免脚本以默认轴值渲染。

- `width`：输出宽度，默认 1080。按可选 crop 裁切后再等比缩放；未设置 crop 则保留原比例。
- `crop`：每张可选 `[left, top, right, bottom]`，0–1 的原图坐标，基于 EXIF 方向矫正后的图像。模型须检查主体安全，脚本不会识别主体。
- `grade`：整组调色设置，可在每个 item 中覆盖。mode 为 fixed（默认）或 none（已调色图复用）；strength 0–1、darkening 0–0.5、saturation 0.8–1.25、light 0–0.15、detail 0–0.3。默认值见 style.md，未知参数会报错。
- `font_ratio`：字号/宽度，默认 0.09。本 skill 仅允许 0.085–0.095；脚本通用缩字逻辑可能输出更小字号，必须按 style.md 检查实际 `font_size/width`，低于范围则改写重跑。
- `line_spacing`：行间起点间距/字号，默认 1.24。
- `items`：按用户顺序，每项含 `id`、`image`、`lines` 和可选 `box`。
- `box`：归一化 `[left, top, width, height]`，本 skill 显式设置 `[0.175, 0.20, 0.65, 0.60]`；脚本省略该字段时的旧默认值较宽，不用于本规则。框自身必须关于画面中心对称，否则脚本拒绝。其宽高仅限制文字尺寸；实际字形包围盒严格对齐画面中心，不强制拉伸铺满。
- `lines`：显式换行的字符串数组，空数组表示无字。脚本不生成文案、不翻译、不检查语义，也不能自动识别面部或判断字体缺字。

从 skill 根目录执行（将路径换成实际工作目录）：

```bash
python3 scripts/render_batch.py /path/to/batch.json --output /path/to/rendered
```

输出为编号 JPG、`contact-sheet.jpg`、相对路径 `layout.json` 和 `finals.zip`。无字调色版本位于 `graded/*.png`，不重复放入成片 ZIP。layout.json 记录实际参数、亮度中位数和预设版本；保留原批次 JSON 供重跑，不将 layout.json 当输入。输出目录必须不存在。先检查全部输入及版式再写文件，读取或溢出错误不静默跳过。

EXIF 方向会规范化，输出不会复制原始 EXIF。输入应为 sRGB JPG/PNG；如为 HEIC、RAW 或非 sRGB，先使用宿主的可靠图像工具转换并检查颜色。转换是格式预处理，不代表完成调色。

## 主体在文字前面（有字成片必需）

每个有文字的 item 必须指定 `foreground_mask` 路径（这是本 skill 的交付要求；通用脚本本身仍接受无蒙版输入），读取为灰度蒙版。尺寸必须等于最终输出画布；黑=背景，白=主体。模型先在最终裁切的无字图上分割或描边，再输入排版脚本。脚本先计算文字居中位置，再用 `文字透明度 × (1 - 主体蒙版)` 合成，主体始终来自原始无字图。记录遮挡前 text_bounds_before_occlusion 与 occluded_text_pixels，便于检查。

若需按经过视觉核对的轮廓生成蒙版，JSON 格式为 `{"size":[1080,1440],"polygons":[[[0.3,0.4],[0.5,0.3],[0.6,0.7]]]}`；示例仅解释结构，不是主体轮廓。坐标为最终画布的归一化位置。主体轮廓需包含足够控制点，不要用示例三角形处理照片。

```bash
python3 scripts/build_mask.py /path/to/contours.json --output /path/to/subject-mask.png
```

蒙版边缘外扩约 1 px，轻微柔化。放大检查文字交界处有无白边、漏字或不合理缺口。

文字尺寸验收公式：若遮挡前包围盒为 `[l,t,r,b]`，则宽占比为 `(r-l)/画布宽`，高占比为 `(b-t)/画布高`。分别须为 0.35–0.65、0.30–0.60；无字时包围盒为空且免检。不要用 `occluded_text_pixels` 反推尺寸。
