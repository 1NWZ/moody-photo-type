# 暗调日常 · 多图文字排版

一个可分享的 Codex skill：将多张生活照片统一为有细节的高级暗调、轻饱和色彩和自然光感，再根据每张画面写自然短句，以白色粗体居中分行排版。一张照片对应一张图，附整组预览与下载包。

## 使用

将本目录 `moody-photo-type` 放入自己的 Codex 个人 skills 目录（通常为 `~/.codex/skills/`，自定义安装则使用 `$CODEX_HOME/skills/`）。重新打开聊天，确认 skill 可选后，上传原始照片并输入：

> 使用 $moody-photo-type，处理这组照片：统一高级暗调，微微增强饱和度和自然光感，按每张照片内容写简短英文，白色粗体居中分行，每张独立输出。

也可以指定“中文文案”“保持原比例”“不要文字”“更亮一点”或“只改第 3 张的文案”。

默认采用“模型理解＋固定代码处理”：视觉模型识图、写短句、选择布局；Python 代码调色、增强光感、裁切和加字。完整默认流程只需支持视觉理解的宿主，无需图像生成 API。生成式修复为可选扩展。本仓库不含 API 密钥、不绑定第三方端点。模型给出批次 JSON 后，相同输入、参数、字体和环境可重复生成。

## 固定处理脚本

需要 Python 3.10+ 与用户有权使用的字体文件。英文默认使用 Alegreya Sans Bold；字体选择、风格例外与缺字检查见 [references/fonts.md](references/fonts.md)。本包不附带字体二进制文件，示例路径需替换为实际可读文件。建议使用独立虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/render_batch.py /path/to/batch.json --output /path/to/new-rendered-directory
```

Windows 使用虚拟环境对应的 `Scripts` 激活命令。复制 `examples/batch.example.json` 到任务目录，将图片和字体路径改成真实路径；配置说明见 [references/manifest.md](references/manifest.md)。默认直接输入原片，代码完成调色并加字；按可选 crop 裁切，未指定则保留比例。只改文案时复用输出中的 graded 无字图，设置 grade.mode=none。

## 风格与文件

- [SKILL.md](SKILL.md)：模型执行流程与完成标准。
- [references/fonts.md](references/fonts.md)：英文候选、场景选字、字重与缺字检查。
- [references/style.md](references/style.md)：从参考图提炼的色调、版式和写作规则。
- `scripts/build_mask.py`：将核对过的主体轮廓转成蒙版，配合 foreground_mask 让文字位于主体后面。
- `scripts/grade_photo.py`：固定曲线、自适应压暗、轻增强饱和度与已有光感。
- `scripts/render_batch.py`：裁切、调色、无字版保存、统一字号、文字框约束、预览和 ZIP。
- `agents/openai.yaml`：Codex 展示名称与默认调用提示。

仅使用白色粗体、居中纵向分行这一种排版，优先 6 行，不随机切换版式。默认 3:4、1080×1440；保护人物身份、主体和材质。文字整体严格水平、垂直居中；所有主视觉主体（人物、宠物、杯子、商品等）必须在文字前面，每张有字图提供精细主体蒙版；分割失败不能交付文字盖住主体的版本。字号固定为画面宽的 8.5%–9.5%（默认 9%），遮挡前文字组占宽 35%–65%、占高 30%–60%；按实际包围盒验收。亮图与暗图分别调整曝光，使整组风格协调。文案以真实可见内容为依据，不照搬参考图中的英文病句。

## 上传 GitHub

本文件夹即为可上传的仓库根目录。可在自己的 GitHub 新建仓库后，将该文件夹内容上传。参考照片及用户原片不随包分发；字体由使用者提供。发布时仅上传 skill 源文件及必要资源。

`.gitignore` 已排除默认输入、调色输出、虚拟环境和环境变量文件。若在其他文件夹中处理个人照片，上传前只选择 skill 的源文件。需要开源许可证时，由仓库所有者选择并添加；当前包未代替作者作许可决定。

## 验证范围

已检查 skill 结构，并验证固定调色的可重复性、关闭调色时像素不变、暗图保护、批量排版和无字输出。技术测试不代表每张真实照片的审美效果，实际处理后仍须逐张审片。

本次规则更新已校验 skill 结构、内部链接与示例配置；未新增自动分割模型。现有渲染脚本是通用工具，主体蒙版必填和尺寸下限由 skill 执行流程核对，脚本运行成功不代表审片通过。
