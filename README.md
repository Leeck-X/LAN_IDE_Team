# LAN C++26 IDE

![logo](static/logo.svg)

一个基于 **Flask + Socket.IO + Monaco + clangd** 的局域网 C++ 竞赛 IDE，支持多人实时协同编辑、评测与补全诊断。

## 功能特性

- **实时协同（OT）**：基于操作变换（Operational Transformation）的多人协同编辑，按文件分房间同步，支持增量操作变换、版本确认与冲突消解，避免并发编辑丢字；在线用户列表 + 远程光标（编辑器内实时显示他人光标位置与用户名配色）。新增断线重连自动重新对齐权威版本、未同步期间编辑器自动只读保护（防止编辑被 `doc_sync` 覆盖丢失）、history 裁剪窗口偏移修正（避免超过 2000 次编辑后 transform 错位）
- **编辑体验**：Monaco 编辑器（VSCode 同源），clangd 语义补全 + 实时语法诊断（红波浪线）；Textarea 模式同样支持红/黄波浪线标注。补全体验增强：已声明变量/函数名优先提示、`#include <...>` 自动闭合 `>`、函数定义式模板智能识别返回类型前缀（避免 `int int main`、`void void bfs` 重复）
- **算法模板库**：内置常用竞赛模板（BFS / DFS / Dijkstra / Floyd / 拓扑排序 / Kruskal、KMP / Trie / Manacher、01 背包 / 完全背包 / LIS / LCS、树状数组 / 线段树、GCD / 快速幂 / 扩展欧几里得 / 埃氏筛 / 欧拉线性筛 / 组合数、并查集等），均采用函数定义式基础写法，避免高级语法
- **问题窗口**：CLion 风格「问题」标签页（与评测/控制台同位置），错误/警告数量徽章、按严重度排序、显示精确行列、点击跳转到对应位置
- **编译运行**：C / C++ / Python，C++ 标准 `c++26 → c++23 → c++20 → c++17` 自动降级探测；C++ 预编译头（PCH）缓存加速首次编译；运行带内存 / 时间统计，控制台流式实时输出
- **安全拦截**：运行/评测前检测 `system`、`popen`、`fork`、`exec*`、`unlink`、`os.system`、`subprocess`、`shutil` 等危险调用，命中即阻止编译执行，防止破坏服务器
- **评测面板（CPH）**：多测试点、多线程并发评测、内存 / 时间统计、zip 导入导出、错误样例一键打开
- **文件管理**：VSCode 式文件树（文件夹 hover 新建 / 重命名 / 删除）、可隐藏侧边栏、标签页拖拽排序。文件重命名/删除会同步清理 OT 权威缓存，避免已删文件被残留内存状态“复活”
- **TT 模式**：按人名建文件夹、一键加题（自动创建题目文件夹 + 同名 `cpp`）
- **网络就绪**：自动添加 Windows 防火墙规则放行服务端口（默认 5000），局域网内其他机器可直接访问
- **主题**：GitHub Dark 界面配色 + VSCode 语法高亮；浏览器标签页使用黄铜金 (#d4a24a) 双向对角箭头 logo
- **Markdown 预览 / 文件分屏**：`.md` 文件支持 编辑 / 预览 / 分屏 三模式（marked + highlight.js 实时渲染）；任意文件可在文件树点 `⇢` 或右键在右侧分屏打开，拖拽中间分割线调整左右比例（记忆到 localStorage），右侧编辑器独立协同
- **状态栏增强**：D 框深色主题、白色文字；`A- / A / A+` 一键调整编辑器字号（持久化）；IntelliSense / 远程光标开关
- **文件模板**：顶部「模板」按钮按扩展名配置新建文件初始内容，支持 `{FileName}`、`{Date}`、`{Author}` 等占位符替换
- **全局在线用户**：左下角在线用户列表改为跨房间统计，10 秒无操作置灰，悬停显示当前编辑文件
- **格式化文档**：右键菜单 + `Shift+Alt+F` 一键格式化当前文档（格式化产生的编辑经 OT 同步给协作者）

## 快速开始

```bash
# Windows：一键搭建环境（安装依赖 + 下载前端资源与 clangd + 检测编译器）
setup_environment.bat

# 启动
python server.py
```

浏览器访问 `http://localhost:5000`，局域网内其他机器访问打印出的局域网地址。

也可以手动安装依赖：

```bash
pip install flask flask-socketio psutil
python server.py
```

> C++ 编译运行需要系统已安装 `g++`（MinGW-w64）或 `clang++`（LLVM）。缺失时前端会提示。

## 依赖

| 依赖 | 用途 | 说明 |
|---|---|---|
| Python 3.9+ | 运行时 | 运行必需 |
| flask / flask-socketio / psutil | 后端框架与资源统计 | 运行必需 |
| g++ 或 clang++ | 编译运行 | 需系统 PATH 中存在 |
| clangd 22.1.6 | LSP 补全与诊断 | 位于 `tools/clangd/`，体积大未入库 |
| Monaco Editor | 前端编辑器 | 位于 `static/monaco/`，体积大未入库 |

`tools/` 与 `static/monaco/` 因体积大未提交到仓库。克隆后运行 `setup_environment.bat` 一键下载 Monaco、Socket.IO 与 clangd（clangd 走 GitHub 官方源，约 50MB，下载失败时需代理或手动放入 `tools/clangd/clangd_22.1.6/`）。

## 目录结构

```
.
├── server.py              # 后端（Flask 路由 + Socket.IO 事件 + clangd LSP + 评测线程池）
├── templates/index.html   # 前端（单文件，含全部 UI 与逻辑）
├── static/                # 前端静态资源
│   ├── socket.io.min.js
│   └── monaco/            # Monaco Editor（未入库）
├── tools/clangd/          # clangd LSP（未入库）
├── workspace/             # 运行时工作区（自动创建，未入库）
└── setup_environment.bat  # 一键环境搭建（检测 Python/编译器，下载依赖、Monaco、Socket.IO 与 clangd）
```

## 测试点规范

测试点存放在源文件同级的 `{文件名}_T/` 目录下，命名 `{编号}.in` / `{编号}.out`：

```
workspace/
└── sum.cpp
└── sum_T/
    ├── 1.in
    ├── 1.out
    ├── 2.in
    └── 2.out
```

## 近期修复与优化

- **编译缓存原子化**：编译先写临时 exe 再 `os.replace` 进缓存，避免超时 kill 留下半成品导致同源码永久命中损坏缓存；缓存满 200 条自动淘汰最旧
- **进程树超时杀**：运行/评测超时改用 `taskkill /T /F`（Windows）/ psutil 递归杀子进程，防止被测程序 spawn 的孙进程逃过 kill 继续占资源
- **OT 文档内存释放**：房间最后一个用户离开时落盘后清除权威缓存，避免长期空闲文件堆积占内存
- **目录扫描深度限**：`scan_dir` 加 16 层上限，防 symlink 环导致递归爆栈
- **CPH 全部运行**：评测面板支持一键跑全部测试点
- **测试点 verdict 展示**：每个测试点显示通过/失败标记
- **协同编辑健壮性**：`on_edit` 的 history 裁剪后索引错位（超过 2000 次编辑后 transform 用错操作序列导致内容错乱）——引入 `history_start` 记录窗口偏移并换算下标
- **换行符统一**：`api_read`、`get_doc_content`、`on_edit` 加载磁盘文件统一调用 `normalize_newlines`，消除 HTTP 读取到 CRLF 与 OT 内存中 LF 的长度不一致（曾导致编辑被服务端拒绝→内容回滚→光标跳到左上角的故障）
- **断线重连自动重新对齐**：socket `connect` 时触发 `resyncDoc()`，避免重连后用失效版本号继续编辑必然触发 resync 覆盖
- **未同步只读保护**：新增 `otSynced` 状态，未对齐权威版本前编辑器只读，对齐后自动解除（防止编辑窗口期内容被 `doc_sync` 覆盖丢失）
- **文件操作同步 OT 缓存**：HTTP `/api/file` 保存后将全文替换作为操作追加进历史并广播；`/api/rename` 迁移缓存到新路径；`/api/delete` 连带清理子路径缓存——避免已删文件被残留内存状态“复活”
- **保存失败可感知**：写盘失败不再静默，回推 `save_error` 事件让前端弹出错误提示
- **光标偏移校验**：服务端 `on_cursor` 校验非法/负数 offset，防止接收端 `getPositionAt` 抛异常
- **补全性能**：声明名提取的 3 个正则预编译为常量，每次补全只重置 `lastIndex` 复用，不再每键重建
- **算法模板扩充**：新增数学/数据结构/图论/字符串/DP 多组基础函数式模板
- **新 logo**：浏览器标签页使用黄铜金 (#d4a24a) 双向对角箭头 logo，矢量 (logo.svg) 与位图 (logo.png) 双格式

## Logo

浏览器标签页图标采用极简线条风格的方形边框 + 双向对角箭头（↖ 和 ↘），黄铜金 (#d4a24a) on 白底，1:1 方形，位于 [`static/logo.svg`](static/logo.svg) 与 [`static/logo.png`](static/logo.png)。
