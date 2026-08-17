# LAN C++26 IDE

一个基于 **Flask + Socket.IO + Monaco + clangd** 的局域网 C++ 竞赛 IDE，支持多人实时协同编辑、评测与补全诊断。

## 功能特性

- **实时协同（OT）**：基于操作变换（Operational Transformation）的多人协同编辑，按文件分房间同步，支持增量操作变换、版本确认与冲突消解，避免并发编辑丢字；在线用户列表 + 远程光标（编辑器内实时显示他人光标位置与用户名配色）
- **编辑体验**：Monaco 编辑器（VSCode 同源），clangd 语义补全 + 实时语法诊断（红波浪线）；Textarea 模式同样支持红/黄波浪线标注
- **问题窗口**：CLion 风格「问题」标签页（与评测/控制台同位置），错误/警告数量徽章、按严重度排序、显示精确行列、点击跳转到对应位置
- **编译运行**：C / C++ / Python，C++ 标准 `c++26 → c++23 → c++20 → c++17` 自动降级探测；C++ 预编译头（PCH）缓存加速首次编译；运行带内存 / 时间统计，控制台流式实时输出
- **安全拦截**：运行/评测前检测 `system`、`popen`、`fork`、`exec*`、`unlink`、`os.system`、`subprocess`、`shutil` 等危险调用，命中即阻止编译执行，防止破坏服务器
- **评测面板（CPH）**：多测试点、多线程并发评测、内存 / 时间统计、zip 导入导出、错误样例一键打开
- **文件管理**：VSCode 式文件树（文件夹 hover 新建 / 重命名 / 删除）、可隐藏侧边栏、标签页拖拽排序
- **TT 模式**：按人名建文件夹、一键加题（自动创建题目文件夹 + 同名 `cpp`）
- **网络就绪**：自动添加 Windows 防火墙规则放行服务端口（默认 5000），局域网内其他机器可直接访问
- **主题**：GitHub Dark 界面配色 + VSCode 语法高亮

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

## 致谢

本次代码提交与推送工作流由 **trae-remote-official:github** 插件协助完成（仓库分支管理、提交与推送到 `https://github.com/Leeck-X/LAN_IDE_Team`）。
