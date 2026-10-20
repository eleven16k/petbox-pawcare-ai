# 视觉规范——宠物信箱（ToThereOn 同源语言）

模板 `templates/preview.template.html` 已内联全部样式，**通常不需要改**。本文是调性约束与 token 速查。

- **设计指南（拍板稿）**：`prototypes/它盒全站风格方案-宠物信箱语言.html`；明信片形态参照 `prototypes/宠物训练模块-宠物信箱风原型.html` 的 `.postcard`。
- **语义真相**仍是小程序端渲染器（petbox-uniapp `pages/agent/components/agent-card-spec/`）；preview.html 是同语言镜像预览：语义零漂移（块与 props 同源 catalog），样式允许轻微漂移。

## 明信片形态（签名元素）

1. **信纸卡**：米白 `#fffdf8`，外层 14px 圆角 + 7px 衬边，内层 9px 圆角 + **航空斜纹边框**（45° 重复渐变：sky-300/slate-300 与纸色相间）。
2. **信头**：左侧衬线体「**To. {宠物名}的铲屎官**」（`"Playfair Display","Songti SC","STSong",serif`，无网络依赖：无 Playfair 时落到宋体），下缀大写字距行 `FROM TUANHUAN · PETBOX SKILL`（8.5px、.18em、slate-400）。
3. **邮票位**：右侧 52×58 虚线框（slate-300 虚线、sky-50 底、6px 圆角），内置 🐾 + `PETBOX`（6.5px、.08em）+ 数据徽标（demo=「示例数据」琥珀底 / live=「实时数据」，由 render_html.py `--live` 控制，agent 不要手改）。
4. **页脚**：虚线分隔 + 大写字距行（同信头语言）。

## Token 速查（与拍板稿 CSS 变量同源）

| 用途 | 值 |
|---|---|
| 页面底 / 信纸 | `#fafbfc` / `#fffdf8` |
| 主色 sky | 500 `#0ea5e9`、600 `#0284c7`、700 `#0369a1`、50 `#f0f9ff`、100 `#e0f2fe`、300 `#7dd3fc` |
| 达标 emerald | 500 `#10b981`、50 `#ecfdf5`、700 `#047857` |
| 警示 amber | 600 `#d97706`、50 `#fffbeb`、100 `#fef3c7`（规范无红，danger 用暖红底仅就医级） |
| 文字 / 线 | ink `#1a1a1a`、slate-900 `#0f172a`、gray-200 `#e5e7eb`、slate-400 `#94a3b8` |
| 渐变 | `--grad-primary: linear-gradient(135deg,#0284c7,#38bdf8)`（进度条填充） |
| 圆角 | 卡 14px / 内页 9px / 元素 8px / 胶囊 999px |
| 字距 | 大写标注行 `.18em`、邮票 `.08em`、标题 `-0.02em` |

## 禁止

加新块类型、改 $ref 语义、引入外部字体/图表库/CDN（Playfair Display 仅作本地渐进增强，无网络时落宋体）；preview 必须是离线单文件；agent 不要手改数据徽标文案。
