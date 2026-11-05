# 英文字体选用规则

本指南把用户指定英文候选转为本 skill 的选字规则；候选不是随机轮换列表。保留白字、中轴短行、照片为主的默认视觉。用户明确指定的字体或风格优先。

## 默认与按场景选择

| 条件 | 选用方向 | 使用限制 |
| --- | --- | --- |
| 日常生活、饮品、雨天、旅行等默认暗调组图 | Alegreya Sans Bold | 首选真实粗体，先试排完整文案 |
| 背景纹理较多，Bold 试排后视觉分量不足 | Alegreya Sans Black | 检查字腔与行间留白；不要仅因照片更暗就加重 |
| 用户要求小型大写、标题式秩序 | Alegreya Sans SC 的实际可用粗体或 Black | 核对文件真实字族；SC 字形会改变大小写观感，不能只看清单标签 |
| 用户明确要求文学、复古、柔和编辑感 | Alegreya Regular、Medium、Bold 或 Alegreya SC；也可试排 BioRhyme SemiExpanded Regular、Medium、SemiBold | 属于衬线风格例外；半扩展字形较宽，先改写和换行，禁止横向压扁 |
| 用户明确要求轻盈、极简 | Alata Regular、Alatsi Regular、Alef Regular、Alegreya Sans Regular；更细的风格可试 Alegreya Sans Thin、Alegreya Sans SC 细体/Thin、BioRhyme SemiExpanded Light/ExtraLight | Regular 不等于 Bold。细体只用于背景干净且缩略图仍清楚的照片，不作为默认暗调替代 |
| 用户明确要求复古铭牌、手写或装饰感 | Copperplate CC Bold、智勇手书体英文版；Affigere、Albura、Analogue OS、mip-font 需先查看真实字样再决定 | 不仅凭字体名猜造型。属于风格例外，不用于默认整组；一组仍只选一个字体文件 |

这是基于照片排版需求制定的选择建议，不代表原字体清单给每款字体规定了使用场景。没有明确风格要求时，不自动换成手写、细体或装饰字。

## 文件核对与降级

1. 先找实际字体文件，再看内部字族和样式信息；清单显示名、文件名和内部名称可能不一致。尤其不要把 `AlegreyaSans-Bold.ttf` 当成 `Alegreya Sans SC`。默认示例使用 `AlegreyaSans-Bold.ttf`，加重候选为 `AlegreyaSans-Black.ttf`。
2. 用最终文案试排，覆盖大小写、数字、撇号、引号、连字符及其他实际出现的符号。逐一检查方框、空白、错误替代字形和字腔闭合；脚本不会自动判断缺字。
3. Bold 不可用时可试同候选中的 Black，视觉通过后再采用并记录替换。两者均不可用时，索取可用候选字体文件，或请用户指定替代；不得静默回退到 Inter、Arial、系统默认字体等表外字体。
4. 不用描边伪造粗体，不拉伸字形。可变字体先生成目标字重的静态实例；当前脚本不设置字体轴，也不支持一行内按字符切换字体。
5. 中英混排需一个字体文件完整覆盖该批文案；否则调整执行方案并说明，不能让英文专用字体产生缺字。中文文案沿用 style.md 的中文规则，英文候选范围不限制用户主动指定的中文字体。

## 整组一致与审片

- 一个批次选一个实际字体文件和字重。不能按每张照片随机换字体，也不能逐行混搭。用户要求不同风格时拆成独立批次，保留原图编号。
- 起始 `font_ratio=0.09`、`line_spacing=1.24`；依据实际字形调整，整组共用。相同字号不保证不同字体的视觉大小相同；换字体后重查全部版式。
- 文字过宽时先缩短文案或调整分行，再有限调整共同字号。保持原有中心对齐、蒙版遮挡和安全区域规则。
- 同时查看单张大图和缩略图：白字清楚、行间不粘连、人物遮挡后短句仍能理解、字号不因单张长词拖累整组。
- 在批次旁保存简短选字记录：实际字族、样式、字体文件名、选用原因及替换情况。不要写入机器个人绝对路径。`layout.json` 现有脚本不会自动记录字体身份，不能声称它已完成这项记录。

## 获取字体

本包提供规则，不附字体文件。使用者从合法字体来源获取对应文件，并核对该文件随附许可；上传字体二进制时一并保留所需许可文件。公开来源可参考 [Alegreya Sans](https://fonts.google.com/specimen/Alegreya+Sans)、[Alegreya Sans SC](https://fonts.google.com/specimen/Alegreya+Sans+SC) 和 [Alegreya](https://fonts.google.com/specimen/Alegreya)。不能把表中的许可标签当成所有同名字体文件均可再分发的证明。
