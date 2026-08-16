# LAN C++26 IDE

一个基于 **Flask + Socket.IO + Monaco + clangd** 的局域网 C++ 竞赛 IDE，支持多人实时协同编辑、评测与补全诊断。

## 功能特性

- **实时协同**：多人同时编辑同一文件，按文件分房间同步（增量操作广播、在线用户列表）
- **编辑体验**：Monaco 编辑器（VSCode 同源），clangd 语义补全 + 实时语法诊断（红波浪线）
- **编译运行**：C / C++ / Python，C++ 标准 `c++26 → c++23 → c++20 → c++17` 自动降级探测
- **评测面板（CPH）**：多测试点、多线程并发评测、内存 / 时间统计、zip 导入导出、错误样例一键打开
- **文件管理**：VSCode 式文件树（文件夹 hover 新建 / 重命名 / 删除）、可隐藏侧边栏、标签页拖拽排序
- **TT 模式**：按人名建文件夹、一键加题（自动创建题目文件夹 + 同名 `cpp`）
- **主题**：GitHub Dark 界面配色 + VSCode 语法高亮

## 快速开始

```bash
# 1. 安装依赖
pip install flask flask-socketio psutil

# 2. 启动
python server.py
```

浏览器访问 `http://localhost:5000`，局域网内其他机器访问打印出的局域网地址。

> C++ 编译运行需要系统已安装 `g++`（MinGW-w64）或 `clang++`（LLVM）。缺失时前端会提示。

## 依赖

| 依赖 | 用途 | 说明 |
|---|---|---|
| Python 3.9+ | 运行时 | 打包后不再需要 |
| flask / flask-socketio / psutil | 后端框架与资源统计 | 打包后内嵌 |
| g++ 或 clang++ | 编译运行 | 需系统 PATH 中存在 |
| clangd 22.1.6 | LSP 补全与诊断 | 位于 `tools/clangd/`，体积大未入库 |
| Monaco Editor | 前端编辑器 | 位于 `static/monaco/`，体积大未入库 |

`tools/` 与 `static/monaco/` 因体积大未提交到仓库。克隆后运行 `setup_environment.bat` 一键下载 Monaco、Socket.IO 与 clangd（clangd 走 GitHub 官方源，约 50MB，下载失败时需代理或手动放入 `tools/clangd/clangd_22.1.6/`）。

## 打包为 exe

```bash
python -m PyInstaller --noconfirm LAN_IDE.spec
```

产物在 `dist/LAN_IDE/`，其中 `_internal/` 为 Python 运行时与前端，`tools/clangd/` 需手动复制到该目录旁（`dist/LAN_IDE/tools/clangd/`）。

## 生成自解压安装程序

需已安装 [7-Zip](https://www.7-zip.org/)：

```bash
make_sfx.bat
```

生成 `LAN_IDE_Setup.exe`（约 56MB），双击解压后自动运行 `LAN_IDE.exe`。路径检测支持：

- `C:\Program Files\7-Zip\`
- `C:\Program Files (x86)\7-Zip\`
- `D:\Apps\Compress\7z\7-Zip\`

## 目录结构

```
.
├── server.py             # 后端（Flask 路由 + Socket.IO 事件 + clangd LSP + 评测线程池）
├── templates/index.html  # 前端（单文件，含全部 UI 与逻辑）
├── static/               # 前端静态资源
│   ├── socket.io.min.js
│   └── monaco/           # Monaco Editor（未入库）
├── tools/clangd/         # clangd LSP（未入库）
├── workspace/            # 运行时工作区（自动创建，未入库）
├── LAN_IDE.spec          # PyInstaller 打包配置
├── make_sfx.bat          # 7-Zip 自解压安装包生成脚本
├── sfx_config.txt        # 自解压配置
└── setup_environment.bat # 一键环境搭建（检测 Python/编译器，下载依赖、Monaco、Socket.IO 与 clangd）
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
