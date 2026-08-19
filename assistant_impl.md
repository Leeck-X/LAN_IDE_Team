## [2026-08-19T19:00:03.554000+08:00] ASSISTANT


这些样式 **不需要修改**，它们与新布局完全兼容。我们逐一看一下：

---

### 为什么这些样式不用动？

| 选择器 | 作用 | 与移动 D 框的关系 |
|--------|------|-------------------|
| `.binary-unsupported .hint-title` | 二进制文件预览提示样式 | 不涉及布局，只是文字颜色 |
| `#editor-host` | 编辑器主体容器（`flex:1` 占满剩余高度） | 现在内部**不再包含** D 框，只负责编辑区和 Monaco，`flex:1` 依然让它填满 `#editor-wrap` 剩余空间，D 框移到外部后，编辑器区域会稍微增高（因为 D 框不占内部空间了），这正是我们想要的 |
| `#editor-frame` | Textarea 模式的容器（flex 布局） | 不受影响 |
| `#gutter`、`#code` | 行号和代码区 | 不变 |
| `#code-overlay` | 错误波浪线叠加层 | 不变 |
| `#monaco-editor` | Monaco 编辑器容器 | 不变 |

---

### 移动后的整体结构

```
#editor-wrap (flex 列)
├── #editor-tabs-wrap
├── #empty-state
├── #editor-host (flex:1)          ← 只剩编辑器和 Monaco
│   ├── #editor-frame
│   └── #monaco-editor
├── #bottom-dock (面板)            ← 浮动/常驻模式
└── #d-frame (flex:0 0 auto)      ← D 框固定在底部 ✅
```

因为 `#editor-wrap` 本身是 `display:flex; flex-direction:column`，所以 `#d-frame` 作为最后一个子元素，会**自动贴在底部**，且高度固定（`flex:0 0 auto`），不会挤压编辑器空间。`#editor-host` 依然用 `flex:1` 填满剩余高度，所以编辑器区域会自适应。

---

### 唯一需要注意的细节

如果你希望 D 框在**浮动面板**（`#bottom-dock.floating`）打开时仍然保持**在最底部**（而不是被面板遮住），你可以给 `#d-frame` 加一个较高的 `z-index`（例如 `z-index: 60`），但之前我们已经建议过，浮动面板的 `z-index` 是 50，所以 D 框用 60 就能压住它。不过，如果你更喜欢 VS Code 的行为——浮动面板在 D 框**之上**（即面板可以覆盖状态栏），那就不需要额外加 `z-index`，保持原样即可。

---

### 结论

**所有你列出的样式都不需要改动**，直接移动 D 框的 HTML 位置即可。刷新页面后，顺序就会变成：
```
编辑器 → 面板 → 状态栏（D 框）
```

和 VS Code 完全一致。

## [2026-08-19T19:00:37.873000+08:00] ASSISTANT


好的，我直接给你**最简洁的操作步骤**，照着做就行，不用思考。

---

## [2026-08-19T19:02:56.190000+08:00] ASSISTANT


你的 HTML 中，**`#d-frame` 现在在 `#bottom-dock` 内部**（位于 `.dock-tabs` 和 `.dock-pane` 之间），这会导致 D 框显示在面板内容的上方，而不是下方。

你需要把它移动到 **`#bottom-dock` 的闭合标签 `</div>` 后面**，但仍在 `#editor-wrap` 内部。

---

## [2026-08-19T19:03:58.843000+08:00] ASSISTANT


**没错，这次位置完全正确！** ✅

现在 D 框已经在 `#bottom-dock` 的**后面**，布局顺序变成了：

```
编辑器（#editor-host）
    ↓
面板（#bottom-dock）← 控制台 / 评测 / 问题
    ↓
状态栏（#d-frame）← 最底部 ✅
```

**和 VS Code 的布局完全一致**：编辑器 → 面板 → 状态栏。

---

## [2026-08-19T19:05:14.357000+08:00] ASSISTANT


你说得对！我仔细看了你最新发的代码，发现问题了：

**D 框（`#d-frame`）被移到了 `#main` 外面**，所以它会横跨整个页面底部（包括侧边栏下方）。而你希望它**只在代码区（`#editor-wrap`）下方**，就像 VS Code 一样（状态栏只存在于编辑器区域底部，侧边栏下方是空的）。

---

## [2026-08-19T19:07:43.332000+08:00] ASSISTANT


**这次完全对了！** ✅

我检查了你最新发来的代码，D 框现在在正确的位置：

```html
<div id="editor-wrap">
    <div id="editor-tabs-wrap">...</div>
    <div id="empty-state">...</div>
    <div id="editor-host">...</div>
    <div id="bottom-dock">...</div>
    <!-- ✅ D 框在 #bottom-dock 后面，#editor-wrap 内部 -->
    <div id="d-frame">...</div>
</div>
```

---

## [2026-08-19T19:17:11.718000+08:00] ASSISTANT


我收到了这份需求文档，它整理了你这个协同 IDE 的完整功能清单和优先级。

根据文档标注，已完成项包括：
- **0. #include 补全选中 BUG**（已修复）
- **1. 独立媒体文件预览优化**（图片缩放/平移/视频静音，已实现）
- **2. 查找/替换文本功能**（已包含在 Monaco 内置，但未在需求中单独列，实际已可用）
- **6. D 状态栏错误/警告统计**（已在 D 框左侧展示，点击跳转问题面板）
- **7. 修复协同补全方向键错位 BUG**（已在 OT 编辑时通过 `setSelection` 修复）
- **9. 新增底部 D 状态栏**（IntelliSense 开关、远程光标开关、行列号、错误统计，均已实现）

待办项按优先级排列：
1. **3. 转到声明功能 (F12)** — 下一个最高优先级
2. **4. 自定义新建文件模板（多占位变量）**
3. **5. 右键菜单优化 + 代码格式化**
4. **8. 编辑器字体大小调整**
5. **10. 优化远程光标存活逻辑（10 秒超时）**
6. **11. 重构在线用户列表（全房间/灰显/悬浮提示）**
7. **12. Markdown 渲染预览**
8. **13. 文件分屏功能（最低优先级）**

---

你接下来想优先实现哪一项？  
- **转到声明 (F12)** 是目前最高优先级的未完成项，我可以开始实现（包括跨文件跳转、右键菜单集成）。
- 或者你有其他想先做的功能？

告诉我你的选择，我立即动手。

## [2026-08-19T19:18:34.751000+08:00] ASSISTANT


好的，按照你指定的顺序：

**5（右键菜单优化 + 格式化）→ 8（字体大小调整）→ 12（Markdown 预览）→ 10（远程光标存活逻辑）→ 11（在线用户列表重构）→ 3（转到声明）→ 4（自定义新建模板）→ 13（文件分屏）**

我把这个顺序整理成清晰的列表，方便你确认：

---

| 序号 | 需求 | 说明 |
|------|------|------|
| **1** | **5. 右键菜单优化 + 代码格式化** | 右键菜单整理归类 + 格式化功能（含快捷键，协同同步） |
| **2** | **8. 编辑器字体大小调整** | 放大/缩小/恢复默认，可在状态栏或菜单中操作 |
| **3** | **12. Markdown 渲染预览** | .md 文件支持 编辑/预览/分屏 三种模式，实时渲染 |
| **4** | **10. 优化远程光标存活逻辑** | 10秒无操作自动隐藏远程光标 |
| **5** | **11. 重构在线用户列表** | 全房间用户统计，灰显无操作用户，悬浮显示文件名 |
| **6** | **3. 转到声明功能 (F12)** | 右键菜单 + F12 跳转声明，支持跨文件 |
| **7** | **4. 自定义新建文件模板** | 多后缀模板配置，占位符变量替换 |
| **8** | **13. 文件分屏功能（最低优先级）** | 左右分屏打开两个独立文件编辑 |

---

**下一步做什么？**

既然你排了顺序，我就从**第 1 项：右键菜单优化 + 代码格式化**开始。

### 具体计划

1. **右键菜单优化**：
   - 梳理现有 Monaco 右键菜单项，移除无效项（如“命令面板”、“切换建议”等冗余项）。
   - 按 VS Code 分组：剪切/复制/粘贴 → 转到声明 → 格式化 → 选择相关。
   - 保留有用项：撤销/重做、剪切/复制/粘贴、选择全部。

2. **代码格式化功能**：
   - Monaco 内置 `editor.action.formatDocument` 支持（基于语言）。
   - 在右键菜单中添加“格式化文档”菜单项。
   - 快捷键：`Shift+Alt+F`（VS Code 标准）。
   - 协同场景：格式化产生的编辑变更经由现有 OT 管线同步给其他用户（已内置支持）。

3. **现有右键菜单保留项**：
   - “转到声明”（F12）—— 已实现，保留。
   - 其他：剪切/复制/粘贴、撤销/重做、选择全部等 Monaco 默认项。

确认后我就开始修改代码。

## [2026-08-19T19:19:22.429000+08:00] ASSISTANT


好的，开始实现 **右键菜单优化 + 代码格式化**。

---

## [2026-08-19T19:21:55.561000+08:00] ASSISTANT


好的，我们现在开始实现 **右键菜单优化 + 代码格式化**。

---

## [2026-08-19T19:25:18.770000+08:00] ASSISTANT


好的，开始实现 **编辑器字体大小调整**。

---

## [2026-08-19T19:30:19.611000+08:00] ASSISTANT


好的，现在开始实现 **Markdown 渲染预览**。

## [2026-08-19T19:32:01.728000+08:00] ASSISTANT


好的，现在开始实现 **Markdown 渲染预览**。

---

## [2026-08-19T19:34:53.225000+08:00] ASSISTANT


好的，开始实现 **10. 优化远程光标存活逻辑**。

---

## [2026-08-19T19:38:29.635000+08:00] ASSISTANT


好的，开始实现 **11. 重构在线用户列表**。

---

## [2026-08-19T19:39:21.857000+08:00] ASSISTANT


好的，我来检查一下当前代码中 **转到声明功能 (F12)** 的实现状态。

---

## [2026-08-19T19:40:17.451000+08:00] ASSISTANT


好的，开始实现 **4. 自定义新建文件模板**。

---

## [2026-08-19T19:41:19.539000+08:00] ASSISTANT


好的，开始实现 **13. 文件分屏功能（最低优先级）**。

---

## [2026-08-19T19:42:35.515000+08:00] ASSISTANT


好的，我来系统性地检查一下代码中可能存在的 bug。

---

## [2026-08-19T19:46:24.732000+08:00] ASSISTANT


明白了，你想要的是：

1. **右侧分屏显示远程光标** ✅ 已实现方案
2. **当前编辑者的位置**：两个分屏各自独立——用户在哪个分屏编辑，该分屏就是"活跃"的，另一个分屏只显示其他协作者的光标（观看模式），类似于 VS Code 的"焦点"概念。

---

## [2026-08-19T19:47:59.845000+08:00] ASSISTANT


好的，我来统一 Markdown 预览和文件分屏的布局，并添加拖拽分割线功能。

---

## [2026-08-19T19:49:25.571000+08:00] ASSISTANT


好的，我现在把 Markdown 预览和文件分屏的**完整整合代码**给你，直接替换 `#md-container` 及相关 JavaScript 即可。

---

## [2026-08-19T19:50:34.486000+08:00] ASSISTANT


好的，我发现了问题：**HTML 结构还没有更新**，当前仍然是旧的 `#md-container`（只有 `md-editor-wrap` 和 `md-preview`），缺少分屏布局的 `split-left`、`split-divider`、`split-right` 等元素。

## [2026-08-19T19:51:13.726000+08:00] ASSISTANT


我仔细检查了你的 `server.py`，并结合之前的对话，发现需要做以下两处关键调整，以支撑客户端分屏和在线用户列表功能：

---

## [2026-08-19T19:54:21.366000+08:00] ASSISTANT


好的，我为你整理了所有需要更新的代码。考虑到文件长度，我会：

1. **提供完整的 `server.py`**（已包含模板管理 API、全局在线用户列表等所有服务端改动）。
2. **提供 `index.html` 中需要替换或新增的核心部分**（分屏、Markdown、字体调整、右键菜单等），并说明替换位置。

如果你需要完整的 `index.html`（包含所有改动），我可以再提供，但会非常长。我会先按模块给出。

---

## [2026-08-19T19:57:38.471000+08:00] ASSISTANT


好的，我把更新过的代码按模块分段发送。请按顺序替换。

---

## [2026-08-19T20:04:17.229000+08:00] ASSISTANT


好的，我一次性把 **剩余的全部 server.py 代码** 发给你。将这段接在第一部分后面即可。

---

```python
# ---------- clangd LSP 语义补全 ----------
CLANGD_PATH = os.path.join(BASE_DIR, "tools", "clangd", "clangd_22.1.6", "bin", "clangd.exe")

def get_system_include_flags():
    gpp = shutil.which("g++")
    if not gpp:
        return []
    try:
        proc = subprocess.run(
            [gpp, "-E", "-x", "c++", "-", "-v"],
            input="", capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10
        )
        err = proc.stderr or ""
    except Exception:
        return []
    flags = []
    in_list = False
    for line in err.splitlines():
        s = line.strip()
        if s.startswith("#include <...> search starts here:"):
            in_list = True
            continue
        if in_list:
            if s.startswith("End of search list."):
                break
            if s and not s.startswith("#") and not s.startswith("("):
                norm = os.path.normpath(s)
                if norm:
                    flags.append("-isystem")
                    flags.append(norm)
    return flags

def path_to_uri(full_path: str) -> str:
    p = os.path.abspath(full_path).replace("\\", "/")
    if not p.startswith("/"):
        p = "/" + p
    return "file://" + p

def uri_to_rel(uri: str):
    if not uri.startswith("file://"):
        return None
    p = os.path.normpath(uri[len("file://"):].lstrip("/"))
    try:
        rel = os.path.relpath(p, WORKSPACE).replace("\\", "/")
    except ValueError:
        return None
    if rel == ".." or rel.startswith("../"):
        return None
    return rel

class ClangdClient:
    def __init__(self):
        self.proc = None
        self.write_lock = threading.Lock()
        self.pending_lock = threading.Lock()
        self.pending = {}
        self.seq = 0
        self.started = False
        self._start_lock = threading.Lock()
        self.opened = set()
        self.versions = {}
        self.texts = {}
        self.diag_callback = None

    def available(self):
        return os.path.exists(CLANGD_PATH)

    def start(self):
        if self.started:
            return True
        with self._start_lock:
            if self.started:
                return True
            if not self.available():
                return False
            try:
                args = [
                    CLANGD_PATH,
                    "--header-insertion=never",
                    "--pch-storage=memory",
                    "--limit-results=100",
                    "--log=error",
                ]
                gpp = shutil.which("g++")
                if gpp:
                    args.append("--query-driver=%s" % gpp.replace("\\", "/"))
                self.proc = subprocess.Popen(
                    args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=0,
                )
            except Exception as e:
                print(f"[clangd] 启动失败: {e}")
                self.proc = None
                return False
            threading.Thread(target=self._read_loop, daemon=True).start()
            resp = self.request("initialize", {
                "processId": os.getpid(),
                "rootUri": path_to_uri(WORKSPACE),
                "rootPath": WORKSPACE,
                "capabilities": {
                    "textDocument": {
                        "completion": {
                            "completionItem": {
                                "snippetSupport": True,
                                "documentationFormat": ["markdown", "plaintext"],
                            }
                        },
                        "definition": {
                            "linkSupport": False
                        }
                    }
                },
                "workspaceFolders": [{"uri": path_to_uri(WORKSPACE), "name": "workspace"}],
                "initializationOptions": {
                    "fallbackFlags": ["-std=c++17", "--target=x86_64-w64-mingw32", "-Wall", "-Wextra"] + get_system_include_flags(),
                },
            }, timeout=15)
            if resp is None:
                self.stop()
                return False
            self.notify("initialized", {})
            self.started = True
            print("[clangd] 已启动, 语义补全就绪")
            return True

    def stop(self):
        self.started = False
        proc, self.proc = self.proc, None
        if proc:
            try:
                proc.stdin.close()
            except Exception:
                pass
            try:
                proc.kill()
            except Exception:
                pass

    def _read_loop(self):
        while self.proc and self.proc.poll() is None:
            try:
                headers = {}
                while True:
                    line = self.proc.stdout.readline()
                    if not line:
                        return
                    line = line.decode("utf-8", "ignore").strip()
                    if line == "":
                        break
                    if ":" in line:
                        k, v = line.split(":", 1)
                        headers[k.strip().lower()] = v.strip()
                length = int(headers.get("content-length", "0"))
                if length <= 0:
                    continue
                body = self._read_exact(self.proc.stdout, length)
                if not body or len(body) < length:
                    return
                msg = json.loads(body.decode("utf-8", "ignore"))
            except Exception:
                return
            self._dispatch(msg)

    @staticmethod
    def _read_exact(stream, n):
        buf = b""
        while len(buf) < n:
            chunk = stream.read(n - len(buf))
            if not chunk:
                break
            buf += chunk
        return buf

    def _dispatch(self, msg):
        if "id" in msg and "method" not in msg:
            rid = msg["id"]
            with self.pending_lock:
                entry = self.pending.pop(rid, None)
            if entry:
                ev, box = entry
                box["result"] = msg.get("result")
                box["error"] = msg.get("error")
                ev.set()
        elif "method" in msg and "id" in msg:
            method = msg.get("method")
            result = [] if method == "workspace/configuration" else None
            self._send({"jsonrpc": "2.0", "id": msg["id"], "result": result})
        elif "method" in msg:
            if msg.get("method") == "textDocument/publishDiagnostics" and self.diag_callback:
                try:
                    self.diag_callback(msg.get("params") or {})
                except Exception:
                    pass

    def _send(self, msg):
        if not self.proc or self.proc.poll() is not None:
            return
        data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        header = ("Content-Length: %d\r\n\r\n" % len(data)).encode("ascii")
        with self.write_lock:
            try:
                self.proc.stdin.write(header + data)
                self.proc.stdin.flush()
            except Exception:
                pass

    def request(self, method, params, timeout=10):
        if not self.proc or self.proc.poll() is not None:
            return None
        with self.pending_lock:
            self.seq += 1
            rid = self.seq
            ev = threading.Event()
            box = {}
            self.pending[rid] = (ev, box)
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        if ev.wait(timeout):
            return box.get("result")
        with self.pending_lock:
            self.pending.pop(rid, None)
        return None

    def notify(self, method, params):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def did_open(self, full_path, text):
        uri = path_to_uri(full_path)
        self.opened.add(uri)
        self.versions[uri] = 1
        self.texts[uri] = text
        self.notify("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": "cpp",
                "version": 1,
                "text": text,
            }
        })

    def did_change(self, full_path, text):
        uri = path_to_uri(full_path)
        v = self.versions.get(uri, 0) + 1
        self.versions[uri] = v
        self.texts[uri] = text
        self.notify("textDocument/didChange", {
            "textDocument": {"uri": uri, "version": v},
            "contentChanges": [{"text": text}],
        })

    def completion(self, full_path, text, line, character):
        uri = path_to_uri(full_path)
        if uri not in self.opened:
            self.did_open(full_path, text)
        elif self.texts.get(uri) != text:
            self.did_change(full_path, text)
        return self.request("textDocument/completion", {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character},
            "context": {"triggerKind": 1},
        }, timeout=3)

    def definition(self, full_path, text, line, character):
        uri = path_to_uri(full_path)
        if uri not in self.opened:
            self.did_open(full_path, text)
        elif self.texts.get(uri) != text:
            self.did_change(full_path, text)
        return self.request("textDocument/definition", {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character},
        }, timeout=5)

    def sync(self, full_path, text):
        uri = path_to_uri(full_path)
        if uri not in self.opened:
            self.did_open(full_path, text)
        elif self.texts.get(uri) != text:
            self.did_change(full_path, text)

clangd = ClangdClient()

def _on_clangd_diagnostics(params):
    rel = uri_to_rel(params.get("uri", ""))
    if not rel:
        return
    socketio.emit("lsp_diagnostics", {
        "path": rel,
        "diagnostics": params.get("diagnostics", []),
    })

clangd.diag_callback = _on_clangd_diagnostics

# ---------- 在线用户 ----------
presence = {}
presence_lock = threading.RLock()

# ---------- 用户身份 / 只读模式 / 使用统计 ----------
clients = {}
clients_lock = threading.RLock()
USERS_DB = os.path.join(BASE_DIR, "users.json")
user_store = {}
user_store_lock = threading.Lock()
user_store_dirty = False

def _local_ip_set():
    ips = {"127.0.0.1", "::1"}
    try:
        ips.add(socket.gethostbyname(socket.gethostname()))
    except Exception:
        pass
    try:
        ips.add(get_ip())
    except Exception:
        pass
    if psutil:
        try:
            for addrs in psutil.net_if_addrs().values():
                for a in addrs:
                    if a.address:
                        ips.add(a.address.split('%')[0])
        except Exception:
            pass
    return ips

LOCAL_IPS = _local_ip_set()

def client_ip():
    try:
        return (request.remote_addr or "").strip()
    except RuntimeError:
        return ""

def is_admin_ip(ip):
    return ip in LOCAL_IPS

def is_admin_request():
    return is_admin_ip(client_ip())

def is_lan_ip(ip):
    if not ip:
        return False
    parts = ip.split('.')
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        a, b = int(parts[0]), int(parts[1])
        return a == 10 or (a == 192 and b == 168) or (a == 172 and 16 <= b <= 31) or a == 127
    return ip.startswith('fe80:') or ip.startswith('fd')

hostname_cache = {}
hostname_lock = threading.Lock()
_dns_pool = ThreadPoolExecutor(max_workers=2)

def lookup_hostname(ip):
    if not is_lan_ip(ip) or ip in ("127.0.0.1", "::1"):
        return ""
    with hostname_lock:
        if ip in hostname_cache:
            return hostname_cache[ip]
    name = ""
    try:
        fut = _dns_pool.submit(socket.gethostbyaddr, ip)
        name = ((fut.result(timeout=1.5) or ("",))[0] or "").split('.')[0]
    except Exception:
        name = ""
    with hostname_lock:
        hostname_cache[ip] = name
    return name

def device_display(ip, ua_label=""):
    if is_admin_ip(ip):
        try:
            return socket.gethostname() + "（服务器本机）"
        except Exception:
            return "服务器本机"
    with hostname_lock:
        h = hostname_cache.get(ip, "")
    return h or ua_label or "未知设备"

def ip_tail(ip):
    if not ip:
        return "?"
    if "." in ip:
        return "." + ip.rsplit(".", 1)[-1]
    return ":" + ip.rsplit(":", 1)[-1]

def _load_users():
    global user_store
    try:
        with open(USERS_DB, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        user_store = loaded if isinstance(loaded, dict) else {}
    except Exception:
        user_store = {}

def _save_users():
    try:
        with open(USERS_DB, "w", encoding="utf-8") as f:
            json.dump(user_store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[users] 保存用户数据失败: {e}")

def _user_rec(ip):
    rec = user_store.get(ip)
    if rec is None:
        rec = {"name": "", "readonly": False, "code_chars": 0, "creates": 0,
               "deletes": 0, "uploads": 0, "saves": 0, "last_seen": ""}
        user_store[ip] = rec
    return rec

def is_readonly_ip(ip):
    if not ip or is_admin_ip(ip):
        return False
    with user_store_lock:
        return bool(user_store.get(ip, {}).get("readonly"))

def stat_add(ip, **fields):
    global user_store_dirty
    if not ip:
        return
    with user_store_lock:
        rec = _user_rec(ip)
        for k, v in fields.items():
            rec[k] = rec.get(k, 0) + v
        rec["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")
        user_store_dirty = True

def user_store_set(ip, save_now=False, **fields):
    global user_store_dirty
    if not ip:
        return
    with user_store_lock:
        rec = _user_rec(ip)
        rec.update(fields)
        rec["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if save_now:
            _save_users()
            user_store_dirty = False
        else:
            user_store_dirty = True

def _users_flush_loop():
    global user_store_dirty
    while True:
        time.sleep(5)
        with user_store_lock:
            if user_store_dirty:
                _save_users()
                user_store_dirty = False

_load_users()
threading.Thread(target=_users_flush_loop, daemon=True).start()

# ---------- 全局在线用户（所有房间） ----------
global_users = {}
global_users_lock = threading.RLock()

def _broadcast_global_presence():
    now = int(time.time() * 1000)
    users = []
    with global_users_lock:
        for sid, info in global_users.items():
            users.append({
                "sid": sid,
                "name": info.get("name", "匿名"),
                "device": info.get("device", ""),
                "ip_tail": ip_tail(info.get("ip", "")),
                "admin": is_admin_ip(info.get("ip", "")),
                "readonly": is_readonly_ip(info.get("ip", "")),
                "current_file": info.get("current_file", ""),
                "last_active": info.get("last_active", now),
            })
    socketio.emit("presence", {"users": users})

# ---------- 文件模板管理 ----------
TEMPLATES_FILE = os.path.join(BASE_DIR, "templates.json")

def _load_templates():
    try:
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_templates(templates):
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)

# ---------- OT 操作 ----------
class TextOperation:
    __slots__ = ("ops", "base_length", "target_length")
    def __init__(self):
        self.ops = []
        self.base_length = 0
        self.target_length = 0

    @staticmethod
    def _is_retain(op):
        return isinstance(op, int) and not isinstance(op, bool) and op > 0
    @staticmethod
    def _is_delete(op):
        return isinstance(op, int) and not isinstance(op, bool) and op < 0
    @staticmethod
    def _is_insert(op):
        return isinstance(op, str)

    def retain(self, n):
        n = int(n)
        if n == 0:
            return self
        self.base_length += n
        self.target_length += n
        if self.ops and self._is_retain(self.ops[-1]):
            self.ops[-1] += n
        else:
            self.ops.append(n)
        return self

    def insert(self, s):
        if not isinstance(s, str):
            raise TypeError("insert expects a string")
        if s == "":
            return self
        self.target_length += len(s)
        ops = self.ops
        if ops and self._is_insert(ops[-1]):
            ops[-1] += s
        elif ops and self._is_delete(ops[-1]):
            if len(ops) >= 2 and self._is_insert(ops[-2]):
                ops[-2] += s
            else:
                last = ops[-1]
                ops[-1] = s
                ops.append(last)
        else:
            ops.append(s)
        return self

    def delete(self, n):
        if isinstance(n, str):
            n = len(n)
        n = int(n)
        if n == 0:
            return self
        if n > 0:
            n = -n
        self.base_length -= n
        if self.ops and self._is_delete(self.ops[-1]):
            self.ops[-1] += n
        else:
            self.ops.append(n)
        return self

    def is_noop(self):
        return not self.ops or (len(self.ops) == 1 and self._is_retain(self.ops[0]))

    def apply(self, text):
        if len(text) != self.base_length:
            raise ValueError(f"base length mismatch: {len(text)} != {self.base_length}")
        out = []
        i = 0
        for op in self.ops:
            if self._is_retain(op):
                out.append(text[i:i+op])
                i += op
            elif self._is_insert(op):
                out.append(op)
            else:
                i += -op
        if i != len(text):
            raise ValueError("operation did not consume whole string")
        return "".join(out)

    def to_json(self):
        return list(self.ops)

    @classmethod
    def from_json(cls, ops):
        op = cls()
        for o in ops:
            if isinstance(o, str):
                op.insert(o)
            elif isinstance(o, int) and not isinstance(o, bool):
                if o > 0:
                    op.retain(o)
                elif o < 0:
                    op.delete(o)
                else:
                    raise ValueError("zero-length component")
            else:
                raise ValueError(f"unknown operation component: {o!r}")
        return op

    @classmethod
    def from_splice(cls, start, end, text, doc_len):
        op = cls()
        if start > 0:
            op.retain(start)
        d = end - start
        if d > 0:
            op.delete(d)
        if len(text) > 0:
            op.insert(text)
        tail = doc_len - end
        if tail > 0:
            op.retain(tail)
        return op

    @staticmethod
    def transform(a, b):
        if a.base_length != b.base_length:
            raise ValueError("both operations must have the same base length")
        a_p = TextOperation()
        b_p = TextOperation()
        ops1 = a.ops
        ops2 = b.ops
        i1 = 0
        i2 = 0
        n1 = len(ops1)
        n2 = len(ops2)

        def next1():
            nonlocal i1
            if i1 >= n1:
                return None
            v = ops1[i1]
            i1 += 1
            return v

        def next2():
            nonlocal i2
            if i2 >= n2:
                return None
            v = ops2[i2]
            i2 += 1
            return v

        op1 = next1()
        op2 = next2()
        while True:
            if op1 is None and op2 is None:
                break
            if isinstance(op1, str):
                a_p.insert(op1)
                b_p.retain(len(op1))
                op1 = next1()
                continue
            if isinstance(op2, str):
                a_p.retain(len(op2))
                b_p.insert(op2)
                op2 = next2()
                continue
            if op1 is None:
                raise ValueError("first operation too short")
            if op2 is None:
                raise ValueError("first operation too long")
            if TextOperation._is_retain(op1) and TextOperation._is_retain(op2):
                if op1 > op2:
                    minl = op2
                    op1 = op1 - op2
                    op2 = next2()
                elif op1 == op2:
                    minl = op2
                    op1 = next1()
                    op2 = next2()
                else:
                    minl = op1
                    op2 = op2 - op1
                    op1 = next1()
                a_p.retain(minl)
                b_p.retain(minl)
            elif TextOperation._is_delete(op1) and TextOperation._is_delete(op2):
                if -op1 > -op2:
                    op1 = op1 - op2
                    op2 = next2()
                elif op1 == op2:
                    op1 = next1()
                    op2 = next2()
                else:
                    op2 = op2 - op1
                    op1 = next1()
            elif TextOperation._is_delete(op1) and TextOperation._is_retain(op2):
                if -op1 > op2:
                    minl = op2
                    op1 = op1 + op2
                    op2 = next2()
                elif -op1 == op2:
                    minl = op2
                    op1 = next1()
                    op2 = next2()
                else:
                    minl = -op1
                    op2 = op2 + op1
                    op1 = next1()
                a_p.delete(minl)
            elif TextOperation._is_retain(op1) and TextOperation._is_delete(op2):
                if op1 > -op2:
                    minl = -op2
                    op1 = op1 + op2
                    op2 = next2()
                elif op1 == -op2:
                    minl = op1
                    op1 = next1()
                    op2 = next2()
                else:
                    minl = op1
                    op2 = op2 + op1
                    op1 = next1()
                b_p.delete(minl)
            else:
                raise ValueError("incompatible operations")
        return (a_p, b_p)

# ---------- 协同文档权威状态 ----------
docs = {}
docs_lock = threading.Lock()
DOC_HISTORY_LIMIT = 2000

def new_doc_state(content=""):
    return {"content": content, "version": 0, "history": [], "history_start": 0}

def append_history(d, op):
    d["history"].append(op)
    if len(d["history"]) > DOC_HISTORY_LIMIT:
        cut = len(d["history"]) - DOC_HISTORY_LIMIT
        d["history"] = d["history"][cut:]
        d["history_start"] = d.get("history_start", 0) + cut

def get_doc_content(rel):
    with docs_lock:
        d = docs.get(rel)
        if d is not None and d.get("content") is not None:
            return d["content"], d["version"]
    try:
        full = safe_path(rel)
        with open(full, "r", encoding="utf-8", errors="ignore", newline="\n") as f:
            content = normalize_newlines(f.read())
    except Exception:
        content = ""
    with docs_lock:
        d = docs.setdefault(rel, new_doc_state(content))
        if d["content"] is None:
            d["content"] = content
        return d["content"], d["version"]

def _flush_and_evict_doc(rel):
    with docs_lock:
        d = docs.get(rel)
        if d is None or d.get("content") is None:
            return
        try:
            full = safe_path(rel)
            os.makedirs(os.path.dirname(full) or WORKSPACE, exist_ok=True)
            with open(full, "w", encoding="utf-8", newline="\n") as f:
                f.write(d["content"])
        except Exception:
            return
        docs.pop(rel, None)

# ---------- 交互式运行 ----------
RUN_MAX_SECONDS = 300
CONSOLE_RUN_TIMEOUT = 4
running_consoles = {}
running_consoles_lock = threading.Lock()

def cleanup_console(sid):
    with running_consoles_lock:
        entry = running_consoles.pop(sid, None)
    if entry:
        if entry.get("timer"):
            entry["timer"].cancel()
        if entry.get("workdir"):
            entry["workdir"].cleanup()

def _kill_tree(proc):
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                           capture_output=True, timeout=5)
        else:
            if psutil is not None:
                try:
                    p = psutil.Process(proc.pid)
                    for c in p.children(recursive=True):
                        try:
                            c.kill()
                        except Exception:
                            pass
                except Exception:
                    pass
            proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

def kill_console(sid):
    with running_consoles_lock:
        entry = running_consoles.get(sid)
    if entry and entry["proc"].poll() is None:
        _kill_tree(entry["proc"])

def run_process_streaming(cmd, stdin_data="", timeout=CONSOLE_RUN_TIMEOUT, cwd=None,
                          mem_limit_mb=MEM_LIMIT_MB, output_limit=OUTPUT_LIMIT,
                          on_output=None, on_proc=None, keep_stdin=False):
    start = time.perf_counter()
    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", cwd=cwd
        )
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {"error": "RE", "stderr": str(e), "time_ms": elapsed_ms, "mem_kb": 0}
    if on_proc:
        try:
            on_proc(proc)
        except Exception:
            pass

    mem_limit_bytes = mem_limit_mb * 1024 * 1024
    state = {"peak": 0, "over_mem": False, "over_out": False, "over_time": False, "out_size": 0}

    def _kill():
        _kill_tree(proc)

    def monitor():
        if psutil is None:
            return
        try:
            p = psutil.Process(proc.pid)
            while proc.poll() is None:
                try:
                    m = p.memory_info().rss
                    for c in p.children(recursive=True):
                        try:
                            m = max(m, c.memory_info().rss)
                        except Exception:
                            pass
                    if m > state["peak"]:
                        state["peak"] = m
                    if m > mem_limit_bytes:
                        state["over_mem"] = True
                        _kill()
                        break
                except Exception:
                    pass
                time.sleep(0.01)
        except Exception:
            pass

    def writer():
        try:
            if stdin_data:
                proc.stdin.write(stdin_data)
            if not keep_stdin:
                proc.stdin.close()
        except Exception:
            pass

    def reader():
        try:
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                if on_output:
                    try:
                        on_output(chunk)
                    except Exception:
                        pass
                state["out_size"] += len(chunk)
                if state["out_size"] > output_limit:
                    state["over_out"] = True
                    _kill()
                    break
        except Exception:
            pass

    mt = threading.Thread(target=monitor, daemon=True)
    rt = threading.Thread(target=reader, daemon=True)
    wt = threading.Thread(target=writer, daemon=True)
    mt.start()
    rt.start()
    wt.start()

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        state["over_time"] = True
        _kill()
        try:
            proc.wait(timeout=1)
        except Exception:
            pass

    for t in (wt, rt, mt):
        t.join(timeout=0.5)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    mem_kb = state["peak"] // 1024

    if state["over_time"]:
        return {"error": "TLE", "time_ms": elapsed_ms, "mem_kb": mem_kb}
    if state["over_mem"]:
        return {"error": "MLE", "time_ms": elapsed_ms, "mem_kb": mem_kb}
    if state["over_out"]:
        return {"error": "OLE", "time_ms": elapsed_ms, "mem_kb": mem_kb}
    return {"stdout": "", "stderr": "", "code": proc.returncode, "time_ms": elapsed_ms, "mem_kb": mem_kb}

# ---------- HTTP 路由 ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/me")
def api_me():
    ip = client_ip()
    with user_store_lock:
        rec = user_store.get(ip) or {}
    return jsonify({
        "ip": ip,
        "admin": is_admin_ip(ip),
        "readonly": is_readonly_ip(ip),
        "name": rec.get("name", ""),
    })

@app.route("/api/admin/users")
def api_admin_users():
    if not is_admin_request():
        return jsonify({"error": "仅服务器本机可查看用户数据"}), 403
    with user_store_lock:
        records = []
        known = set()
        for ip, r in user_store.items():
            rec = dict(r)
            rec["ip"] = ip
            records.append(rec)
            known.add(ip)
    online_by_ip = {}
    with clients_lock:
        for sid, c in clients.items():
            ip = c.get("ip", "")
            online_by_ip.setdefault(ip, []).append({
                "sid": sid,
                "name": c.get("name", ""),
                "device": device_display(ip, c.get("device", "")),
            })
    for rec in records:
        rec["online"] = online_by_ip.get(rec["ip"], [])
    for ip, onl in online_by_ip.items():
        if ip and ip not in known:
            records.append({"ip": ip, "name": onl[0].get("name", ""), "online": onl})
    return jsonify(records)

@app.route("/api/admin/readonly", methods=["POST"])
def api_admin_readonly():
    if not is_admin_request():
        return jsonify({"error": "仅服务器本机可管理用户"}), 403
    data = request.get_json(force=True)
    ip = str(data.get("ip") or "").strip()
    flag = bool(data.get("readonly"))
    if not ip:
        return jsonify({"error": "缺少 ip"}), 400
    if is_admin_ip(ip):
        return jsonify({"error": "不能对服务器本机设置只读"}), 400
    user_store_set(ip, save_now=True, readonly=flag)
    rooms = set()
    with presence_lock:
        with clients_lock:
            for sid, c in clients.items():
                if c.get("ip") == ip:
                    socketio.emit("readonly_changed", {"readonly": flag}, room=sid)
            for rel, users in presence.items():
                if any(clients.get(sid, {}).get("ip") == ip for sid in users):
                    rooms.add(rel)
    for rel in rooms:
        socketio.emit("presence", build_presence(rel), room=rel)
    _broadcast_global_presence()
    return jsonify({"ok": True})

@app.route("/api/tree")
def api_tree():
    return jsonify(scan_dir())

@app.route("/api/file", methods=["GET"])
def api_read():
    path = request.args.get("path", "")
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    if not os.path.isfile(full):
        return jsonify({"error": "文件不存在"}), 404

    if is_binary_file(full):
        mime = get_mime(full)
        from urllib.parse import quote
        try:
            size = os.path.getsize(full)
        except OSError:
            size = None
        return jsonify({
            "binary": True,
            "mime": mime,
            "size": size,
            "content": None,
            "url": f"/api/file/raw?path={quote(path)}"
        })

    with open(full, "r", encoding="utf-8", errors="ignore", newline="\n") as f:
        content = normalize_newlines(f.read())
    return jsonify({"binary": False, "content": content})

@app.route("/api/file/raw")
def api_file_raw():
    path = request.args.get("path", "")
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    if not os.path.isfile(full):
        return jsonify({"error": "文件不存在"}), 404
    mime = get_mime(full)
    as_attachment = request.args.get("download") == "1"
    return send_from_directory(os.path.dirname(full), os.path.basename(full),
                               mimetype=mime, as_attachment=as_attachment)

@app.route("/api/file", methods=["POST"])
def api_save():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    data = request.get_json(force=True)
    path = data.get("path", "")
    content = normalize_newlines(data.get("content", ""))
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    broadcast = None
    with docs_lock:
        d = docs.get(path)
        if d is not None and d.get("content") is not None and d["content"] != content:
            try:
                op = TextOperation.from_splice(0, len(d["content"]), content, len(d["content"]))
            except Exception:
                op = None
            if op is not None:
                d["content"] = content
                d["version"] += 1
                append_history(d, op)
                broadcast = {"path": path, "op": op.to_json(), "version": d["version"]}
                if broadcast:
                    socketio.emit("edit", broadcast, room=path)
    return jsonify({"ok": True})

@app.route("/api/backup", methods=["POST"])
def api_backup():
    if is_readonly_ip(client_ip()):
        return jsonify({"ok": False, "error": "只读模式：管理员已禁止你修改内容"}), 403
    try:
        data = request.get_json(force=True)
        path = data.get("path", "")
        content = normalize_newlines(data.get("content", ""))
        if not path:
            return jsonify({"ok": False, "error": "缺少路径"}), 400
        try:
            full = safe_path(path)
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
        if not os.path.isfile(full):
            return jsonify({"ok": False, "error": "文件不存在"}), 404
        req_ip = request.remote_addr or "127.0.0.1"
        ip_tag = req_ip.split(".")[-1] if re.fullmatch(r"[\d.]+", req_ip) else hashlib.sha256(req_ip.encode()).hexdigest()[:8]
        base_name = os.path.basename(full)
        backup_name = f"{base_name}_{ip_tag}.bak"
        backup_path = os.path.join(os.path.dirname(full), backup_name)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        with open(backup_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        try:
            socketio.emit('tree_changed', {})
        except Exception as e:
            print(f"备份广播失败: {e}")
        return jsonify({"ok": True, "backup_name": backup_name})
    except Exception as e:
        print(f"备份异常: {e}")
        return jsonify({"ok": False, "error": f"服务器内部错误: {str(e)}"}), 500

@app.route("/api/create", methods=["POST"])
def api_create():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    data = request.get_json(force=True)
    path = data.get("path", "")
    is_folder = data.get("folder", False)
    content = data.get("content", "")
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    if os.path.exists(full):
        return jsonify({"error": "已存在"}), 400
    if is_folder:
        os.makedirs(full, exist_ok=True)
    else:
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    stat_add(client_ip(), creates=1)
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True})

@app.route("/api/rename", methods=["POST"])
def api_rename():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    data = request.get_json(force=True)
    old = data.get("old", "")
    new = data.get("new", "")
    try:
        old_full = safe_path(old)
        new_full = safe_path(new)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    if not os.path.exists(old_full):
        return jsonify({"error": "源不存在"}), 404
    if os.path.exists(new_full):
        return jsonify({"error": "目标已存在"}), 400
    os.makedirs(os.path.dirname(new_full), exist_ok=True)
    with docs_lock:
        os.rename(old_full, new_full)
        if old in docs:
            docs[new] = docs.pop(old)
        with presence_lock:
            if old in presence:
                presence[new] = presence.pop(old)
    socketio.emit("file_renamed", {"old_path": old, "new_path": new}, room=old)
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True})

@app.route("/api/delete", methods=["POST"])
def api_delete():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    data = request.get_json(force=True)
    path = data.get("path", "")
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    if full == WORKSPACE:
        return jsonify({"error": "不能删除工作区根目录"}), 400
    if not os.path.exists(full):
        return jsonify({"error": "不存在"}), 404
    if os.path.isdir(full):
        shutil.rmtree(full)
    else:
        os.remove(full)
    deleted_docs = []
    with docs_lock:
        if path in docs:
            deleted_docs.append(path)
            docs.pop(path, None)
        prefix = path.rstrip("/") + "/"
        for k in [k for k in docs if k.startswith(prefix)]:
            deleted_docs.append(k)
            docs.pop(k, None)
    with presence_lock:
        presence.pop(path, None)
        for k in [k for k in presence if k.startswith(prefix)]:
            presence.pop(k, None)
    for p in deleted_docs:
        socketio.emit('file_deleted', {"path": p}, room=p)
    stat_add(client_ip(), deletes=1)
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True})

@app.route("/api/upload", methods=["POST"])
def api_upload():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    if "file" not in request.files:
        return jsonify({"error": "没有文件"}), 400
    file = request.files["file"]
    filename = os.path.basename(file.filename)
    if not filename or filename in (".", "..") or ":" in filename or filename != filename.strip():
        return jsonify({"error": "非法文件名"}), 400
    save_path = os.path.join(WORKSPACE, filename)
    file.save(save_path)
    stat_add(client_ip(), uploads=1)
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True, "name": filename})

MAX_ZIP_MEMBER_SIZE = 10 * 1024 * 1024

@app.route("/api/upload_tests", methods=["POST"])
def api_upload_tests():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    if "file" not in request.files:
        return jsonify({"error": "没有文件"}), 400
    file = request.files["file"]
    filename = os.path.basename(file.filename)
    if not filename.lower().endswith(".zip"):
        return jsonify({"error": "只支持 .zip 文件"}), 400
    source_path = request.form.get("source", "")
    try:
        src_full = safe_path(source_path) if source_path else None
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    if not src_full or not os.path.exists(src_full):
        return jsonify({"error": "源文件不存在"}), 400
    test_dir = get_test_dir(src_full)
    os.makedirs(test_dir, exist_ok=True)
    existing_nums = set()
    for f in os.listdir(test_dir):
        m = re.match(r'^(\d+)\.(in|out)$', f)
        if m:
            existing_nums.add(m.group(1))
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    count = 0
    try:
        with zipfile.ZipFile(tmp_path, 'r') as zf:
            pairs = {}
            for name in zf.namelist():
                if name.endswith('/') or name.startswith('.'):
                    continue
                base = os.path.basename(name)
                if not base or base.startswith('.'):
                    continue
                low = base.lower()
                if not (low.endswith('.in') or low.endswith('.out')):
                    continue
                m = re.match(r'^(?:.*?\.)*?(\d+)\.(in|out)$', low)
                if not m:
                    continue
                num, ext = m.group(1), m.group(2)
                pairs.setdefault(num, {})[ext] = name
            used_nums = set(existing_nums)
            remap = {}
            for num in sorted(pairs.keys(), key=lambda x: int(x)):
                if num not in used_nums:
                    remap[num] = num
                    used_nums.add(num)
                else:
                    n = 1
                    while str(n) in used_nums:
                        n += 1
                    remap[num] = str(n)
                    used_nums.add(str(n))
            for num, files in pairs.items():
                new_num = remap[num]
                for ext, name in files.items():
                    info = zf.getinfo(name)
                    if info.file_size > 10 * 1024 * 1024:
                        return jsonify({"error": f"测试点文件过大: {os.path.basename(name)}"}), 400
                    dest = os.path.join(test_dir, f"{new_num}.{ext}")
                    with zf.open(name) as src, open(dest, 'wb') as dst:
                        dst.write(src.read(MAX_ZIP_MEMBER_SIZE + 1))
                        if dst.tell() > MAX_ZIP_MEMBER_SIZE:
                            return jsonify({"error": f"测试点文件过大: {os.path.basename(name)}"}), 400
                    count += 1
    except zipfile.BadZipFile:
        return jsonify({"error": "无效的 zip 文件"}), 400
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True, "count": count})

@app.route("/api/export_tests")
def api_export_tests():
    source_path = request.args.get("source", "")
    try:
        src_full = safe_path(source_path) if source_path else None
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    if not src_full or not os.path.exists(src_full):
        return jsonify({"error": "源文件不存在"}), 400
    test_dir = get_test_dir(src_full)
    if not os.path.isdir(test_dir):
        return jsonify({"error": "没有测试点"}), 400
    base_name = os.path.splitext(os.path.basename(source_path))[0]
    tmp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp_zip.close()
    try:
        with zipfile.ZipFile(tmp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for fname in sorted(os.listdir(test_dir)):
                if fname.endswith('.in') or fname.endswith('.out'):
                    zf.write(os.path.join(test_dir, fname), fname)
        return send_from_directory(
            os.path.dirname(tmp_zip.name),
            os.path.basename(tmp_zip.name),
            as_attachment=True,
            download_name=f"{base_name}_tests.zip"
        )
    finally:
        def _delayed_unlink(p=tmp_zip.name):
            time.sleep(60)
            try:
                if os.path.exists(p):
                    os.unlink(p)
            except OSError:
                pass
        threading.Thread(target=_delayed_unlink, daemon=True).start()

# ---------- CPH 测试点管理 ----------
@app.route("/api/tests")
def api_tests():
    path = request.args.get("path", "")
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify([])
    tests = find_tests(full)
    result = []
    for name, in_path, out_path in tests:
        inp = ""
        exp = ""
        try:
            with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
                inp = f.read()
        except:
            pass
        if out_path:
            try:
                with open(out_path, "r", encoding="utf-8", errors="ignore") as f:
                    exp = f.read()
            except:
                pass
        result.append({"name": name, "input": inp, "expected": exp})
    return jsonify(result)

@app.route("/api/test/save", methods=["POST"])
def api_test_save():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    data = request.get_json(force=True)
    path = data.get("path", "")
    content = normalize_newlines(data.get("content", ""))
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    os.makedirs(os.path.dirname(full) or WORKSPACE, exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return jsonify({"ok": True})

@app.route("/api/test/delete", methods=["POST"])
def api_test_delete():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    data = request.get_json(force=True)
    source_path = data.get("path", "")
    test_num = data.get("num")
    if not re.fullmatch(r"\d+", str(test_num if test_num is not None else "")):
        return jsonify({"error": "非法测试点编号"}), 400
    try:
        full = safe_path(source_path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    test_dir = get_test_dir(full)
    for ext in [".in", ".out"]:
        f = os.path.join(test_dir, f"{test_num}{ext}")
        if os.path.exists(f):
            os.remove(f)
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True})

@app.route("/api/test/add", methods=["POST"])
def api_test_add():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    data = request.get_json(force=True)
    source_path = data.get("path", "")
    try:
        full = safe_path(source_path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    test_dir = get_test_dir(full)
    os.makedirs(test_dir, exist_ok=True)
    tests = find_tests(full)
    existing_nums = set()
    for name, in_path, out_path in tests:
        m = re.match(r"^test (\d+)$", name)
        if m:
            existing_nums.add(int(m.group(1)))
    n = 1
    while n in existing_nums:
        n += 1
    in_path = os.path.join(test_dir, f"{n}.in")
    out_path = os.path.join(test_dir, f"{n}.out")
    with open(in_path, "w", encoding="utf-8") as f:
        f.write("")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("")
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True, "num": n})

@app.route("/api/test/import", methods=["POST"])
def api_test_import():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
    data = request.get_json(force=True)
    source = data.get("source", "")
    target = data.get("target", "")
    nums = data.get("nums")
    try:
        src_full = safe_path(source) if source else None
        dst_full = safe_path(target) if target else None
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    if not src_full or not os.path.isfile(src_full):
        return jsonify({"error": "源文件不存在"}), 400
    if not dst_full or not os.path.isfile(dst_full):
        return jsonify({"error": "目标文件不存在"}), 400
    src_test_dir = get_test_dir(src_full)
    dst_test_dir = get_test_dir(dst_full)
    if not os.path.isdir(src_test_dir):
        return jsonify({"error": "源文件没有测试点"}), 400
    os.makedirs(dst_test_dir, exist_ok=True)

    src_tests = {}
    for f in sorted(os.listdir(src_test_dir)):
        m = re.match(r"^(\d+)\.(in|out)$", f)
        if m:
            num, ext = m.group(1), m.group(2)
            src_tests.setdefault(num, {})[ext] = os.path.join(src_test_dir, f)
    valid = {n: p for n, p in src_tests.items() if p.get("in") and p.get("out")}
    selected = set()
    if nums:
        for n in nums:
            n = str(n)
            if n in valid:
                selected.add(n)
    else:
        selected = set(valid.keys())
    if not selected:
        return jsonify({"error": "没有可导入的测试点"}), 400

    existing_nums = set()
    for f in os.listdir(dst_test_dir):
        m = re.match(r"^(\d+)\.(in|out)$", f)
        if m:
            existing_nums.add(m.group(1))
    used = set(existing_nums)
    mapping = {}
    for num in sorted(selected, key=lambda x: int(x)):
        if num not in used:
            mapping[num] = num
            used.add(num)
        else:
            n = 1
            while str(n) in used:
                n += 1
            mapping[num] = str(n)
            used.add(str(n))

    count = 0
    for num, new_num in mapping.items():
        for ext in ("in", "out"):
            with open(valid[num][ext], "rb") as s, open(os.path.join(dst_test_dir, f"{new_num}.{ext}"), "wb") as d:
                d.write(s.read())
            count += 1

    socketio.emit('tree_changed', {})
    return jsonify({"ok": True, "count": count, "mapping": mapping})

@app.route("/api/test/run", methods=["POST"])
def api_test_run():
    data = request.get_json(force=True)
    path = data.get("path", "")
    test_num = data.get("num")
    if not re.fullmatch(r"\d+", str(test_num if test_num is not None else "")):
        return jsonify({"error": "非法测试点编号"}), 400
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    test_dir = get_test_dir(full)
    in_full = os.path.join(test_dir, f"{test_num}.in")
    out_full = os.path.join(test_dir, f"{test_num}.out")
    if not os.path.exists(in_full):
        return jsonify({"error": f"测试点 {test_num} 不存在"}), 200
    with open(in_full, "r", encoding="utf-8", errors="ignore") as f:
        input_data = f.read()
    expected = ""
    if os.path.exists(out_full):
        with open(out_full, "r", encoding="utf-8", errors="ignore") as f:
            expected = f.read()
    with tempfile.TemporaryDirectory() as work_dir:
        with open(full, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        dangerous = find_dangerous_call(source)
        if dangerous:
            return jsonify({"verdict": "RE", "stderr": f"检测到危险函数「{dangerous}」，已阻止评测"})
        stripped = strip_freopen_for_judge(source)
        temp_src = os.path.join(work_dir, os.path.basename(full))
        with open(temp_src, "w", encoding="utf-8") as f:
            f.write(stripped)
        if ext == "py":
            run_cmd = [sys.executable, temp_src]
            compile_err = None
        else:
            run_cmd, compile_err = compile_source(temp_src, ext, work_dir)
        if compile_err:
            return jsonify({"verdict": "CE", "compile_error": compile_err})
        result = run_process_with_stats(run_cmd, input_data, cwd=work_dir)
        verdict = verdict_from_result(result, expected)
        return jsonify({
            "verdict": verdict,
            "input": input_data,
            "expected": expected,
            "actual": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "time_ms": result.get("time_ms", 0),
            "mem_kb": result.get("mem_kb", 0)
        })

@app.route("/api/environment")
def api_environment():
    return jsonify({
        "clang++": shutil.which("clang++") is not None,
        "g++": shutil.which("g++") is not None,
        "clangd": os.path.exists(CLANGD_PATH) or shutil.which("clangd") is not None,
        "python": True
    })

@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(force=True)
    path = data.get("path", "")
    stdin_data = data.get("stdin", "")
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    if not os.path.isfile(full):
        return jsonify({"error": "文件不存在"}), 404
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    source_dir = os.path.dirname(full)
    with open(full, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()
    dangerous = find_dangerous_call(source)
    if dangerous:
        return jsonify({"error": f"检测到危险函数调用「{dangerous}」，已阻止运行"}), 200
    if ext == "py":
        return jsonify(run_process([sys.executable, full], stdin_data, cwd=source_dir))
    with tempfile.TemporaryDirectory() as work_dir:
        run_cmd, err = compile_source(full, ext, work_dir)
        if err:
            return jsonify({"error": err}), 200
        return jsonify(run_process(run_cmd, stdin_data, cwd=source_dir))

def verdict_from_result(result, expected):
    err = result.get("error")
    if err:
        return err if err in ("TLE", "MLE", "OLE") else "RE"
    if result["code"] != 0:
        return "RE"
    if result["stdout"].strip() == expected.strip():
        return "AC"
    return "WA"

@app.route("/api/judge", methods=["POST"])
def api_judge():
    data = request.get_json(force=True)
    path = data.get("path", "")
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    tests = find_tests(full)
    if not tests:
        return jsonify({"error": "未找到测试数据，请上传 .in/.out 文件"}), 200
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    rank = {"AC": 0, "WA": 1, "RE": 2, "TLE": 3, "MLE": 3, "OLE": 3}
    with tempfile.TemporaryDirectory() as work_dir:
        with open(full, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        dangerous = find_dangerous_call(source)
        if dangerous:
            return jsonify({"error": f"检测到危险函数「{dangerous}」，已阻止评测"}), 200
        stripped = strip_freopen_for_judge(source)
        temp_src = os.path.join(work_dir, os.path.basename(full))
        with open(temp_src, "w", encoding="utf-8") as f:
            f.write(stripped)
        if ext == "py":
            run_cmd = [sys.executable, temp_src]
            compile_err = None
        else:
            run_cmd, compile_err = compile_source(temp_src, ext, work_dir)
        if compile_err:
            socketio.emit("judge_progress", {"path": path, "case": "__compile__", "result": {"verdict": "CE", "compile_error": compile_err}})
            return jsonify({"verdict": "CE", "compile_error": compile_err})
        case_data = []
        for name, in_path, out_path in tests:
            with open(in_path, "r", encoding="utf-8", errors="ignore", newline="\n") as f:
                input_data = f.read()
            with open(out_path, "r", encoding="utf-8", errors="ignore", newline="\n") as f:
                expected = f.read()
            case_data.append((name, input_data, expected))
        results = [None] * len(case_data)
        def run_one(idx, name, input_data, expected):
            result = run_process_with_stats(run_cmd, input_data, cwd=work_dir)
            verdict = verdict_from_result(result, expected)
            r = {
                "case": name,
                "verdict": verdict,
                "input": input_data,
                "expected": expected,
                "actual": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "time_ms": result.get("time_ms", 0),
                "mem_kb": result.get("mem_kb", 0)
            }
            socketio.emit("judge_progress", {"path": path, "case": name, "result": r})
            return idx, r
        workers = min(4, len(case_data))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(run_one, i, n, inp, exp) for i, (n, inp, exp) in enumerate(case_data)]
            for f in as_completed(futures):
                idx, r = f.result()
                results[idx] = r
        final = "AC"
        for r in results:
            if rank[r["verdict"]] > rank[final]:
                final = r["verdict"]
    return jsonify({"verdict": final, "cases": results})

# ---------- 模板管理 API ----------
@app.route("/api/templates", methods=["GET"])
def api_templates_get():
    return jsonify(_load_templates())

@app.route("/api/templates/<ext>", methods=["GET"])
def api_template_get(ext):
    templates = _load_templates()
    return jsonify(templates.get(ext, ""))

@app.route("/api/templates/<ext>", methods=["PUT"])
def api_template_put(ext):
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式"}), 403
    data = request.get_json(force=True)
    content = data.get("content", "")
    templates = _load_templates()
    templates[ext] = content
    _save_templates(templates)
    return jsonify({"ok": True})

@app.route("/api/templates/<ext>", methods=["DELETE"])
def api_template_delete(ext):
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式"}), 403
    templates = _load_templates()
    if ext in templates:
        del templates[ext]
        _save_templates(templates)
    return jsonify({"ok": True})

# ---------- Socket.IO 事件 ----------
@socketio.on("join")
def on_join(data):
    rel = data.get("path")
    if not rel:
        return
    username = str(data.get("username") or "匿名").strip()[:32] or "匿名"
    device = str(data.get("device") or "").strip()[:64]
    ip = client_ip()
    if not is_admin_ip(ip):
        lookup_hostname(ip)
    join_room(rel)
    with presence_lock:
        presence.setdefault(rel, {})[request.sid] = username
        with clients_lock:
            clients[request.sid] = {"ip": ip, "name": username, "device": device}
    with global_users_lock:
        global_users[request.sid] = {
            "name": username,
            "ip": ip,
            "device": device,
            "current_file": rel,
            "last_active": int(time.time() * 1000)
        }
    _broadcast_global_presence()
    emit("presence", build_presence(rel), room=rel)
    content, version = get_doc_content(rel)
    emit("doc_sync", {"path": rel, "content": content, "version": version}, room=request.sid)

@socketio.on("rename")
def on_rename(data):
    name = str(data.get("name") or "").strip()[:32]
    if not name:
        return
    ip = ""
    rooms = []
    with presence_lock:
        for rel, users in presence.items():
            if request.sid in users:
                users[request.sid] = name
                rooms.append(rel)
        with clients_lock:
            if request.sid in clients:
                clients[request.sid]["name"] = name
                ip = clients[request.sid].get("ip", "")
    with global_users_lock:
        if request.sid in global_users:
            global_users[request.sid]["name"] = name
    _broadcast_global_presence()
    for rel in rooms:
        emit("presence", build_presence(rel), room=rel)
    if ip:
        user_store_set(ip, name=name)

@socketio.on("leave")
def on_leave(data):
    rel = data.get("path")
    if not rel:
        return
    leave_room(rel)
    empty = False
    with presence_lock:
        if rel in presence and request.sid in presence[rel]:
            del presence[rel][request.sid]
            empty = not presence[rel]
    if empty:
        _flush_and_evict_doc(rel)
        with presence_lock:
            still_online = any(request.sid in users for users in presence.values())
        if not still_online:
            with global_users_lock:
                global_users.pop(request.sid, None)
            _broadcast_global_presence()
    emit("presence", build_presence(rel), room=rel)

@socketio.on("disconnect")
def on_disconnect():
    emptied = []
    rooms = []
    with presence_lock:
        for rel, users in list(presence.items()):
            if request.sid in users:
                del users[request.sid]
                rooms.append(rel)
                if not users:
                    emptied.append(rel)
    with clients_lock:
        clients.pop(request.sid, None)
    with global_users_lock:
        global_users.pop(request.sid, None)
    _broadcast_global_presence()
    for rel in emptied:
        _flush_and_evict_doc(rel)
    for rel in rooms:
        emit("presence", build_presence(rel), room=rel)
    kill_console(request.sid)
    cleanup_console(request.sid)

@socketio.on("edit")
def on_edit(data):
    rel = data.get("path")
    op_data = data.get("op")
    if not rel or op_data is None:
        return {"version": None}
    with clients_lock:
        c_ip = clients.get(request.sid, {}).get("ip", "")
    if is_readonly_ip(c_ip):
        return {"version": None, "readonly": True}
    try:
        base = int(data.get("base")) if data.get("base") is not None else -1
    except (TypeError, ValueError):
        base = -1

    with docs_lock:
        d = docs.setdefault(rel, new_doc_state(None))
        if d["content"] is None:
            try:
                full = safe_path(rel)
                with open(full, "r", encoding="utf-8", errors="ignore", newline="\n") as f:
                    d["content"] = normalize_newlines(f.read())
            except Exception:
                if docs.get(rel) is d:
                    docs.pop(rel, None)
                return {"version": None, "deleted": True}
        content = d["content"]
        version = d["version"]
        history = d["history"]
        history_start = d.get("history_start", 0)

        clamped = False
        if isinstance(op_data, list):
            try:
                op = TextOperation.from_json(op_data)
            except Exception:
                return {"version": None}
        elif isinstance(op_data, dict):
            try:
                start = int(op_data.get("start", 0))
                end = int(op_data.get("end", start))
                text = normalize_newlines(op_data.get("text", ""))
            except (TypeError, ValueError):
                return {"version": None}
            idx = base - history_start if base is not None else -1
            if 0 <= base < version and 0 <= idx < len(history):
                doc_len = history[idx].base_length
            else:
                doc_len = len(content)
            if start < 0 or end < start or end > doc_len:
                clamped = True
                start = max(0, min(start, doc_len))
                end = max(start, min(end, doc_len))
            op = TextOperation.from_splice(start, end, text, doc_len)
        else:
            return {"version": None}

        if 0 <= base < version:
            if base < history_start or version - base > len(history):
                return {"version": None, "resync": True}
            try:
                for past in history[base - history_start:]:
                    op, _ = TextOperation.transform(op, past)
            except ValueError:
                return {"version": None, "resync": True}

        try:
            new_content = op.apply(content)
        except ValueError:
            return {"version": None, "resync": True}

        d["content"] = new_content
        d["version"] = version + 1
        append_history(d, op)
        final_version = d["version"]
        op_json = op.to_json()

        emit("edit", {"path": rel, "op": op_json, "version": final_version}, room=rel, include_self=False)

    inserted = sum(len(x) for x in op.ops if isinstance(x, str))
    if inserted:
        stat_add(c_ip, code_chars=inserted)

    with global_users_lock:
        if request.sid in global_users:
            global_users[request.sid]["last_active"] = int(time.time() * 1000)
    _broadcast_global_presence()

    return {"version": final_version, "op": op_json, "clamped": clamped, "resync": False}

@socketio.on("cursor")
def on_cursor(data):
    rel = data.get("path")
    if not rel:
        return
    try:
        offset = int(data.get("offset", 0))
    except (TypeError, ValueError):
        return
    if offset < 0:
        return
    data = dict(data)
    data["offset"] = offset
    data["sid"] = request.sid
    with presence_lock:
        data["username"] = presence.get(rel, {}).get(request.sid, "匿名")
    emit("cursor", data, room=rel, include_self=False)
    with global_users_lock:
        if request.sid in global_users:
            global_users[request.sid]["last_active"] = int(time.time() * 1000)
            global_users[request.sid]["current_file"] = rel
    _broadcast_global_presence()

@socketio.on("save")
def on_save(data):
    rel = data.get("path")
    if not rel:
        return
    with clients_lock:
        c_ip = clients.get(request.sid, {}).get("ip", "")
    if is_readonly_ip(c_ip):
        emit("save_error", {"path": rel, "error": "只读模式：管理员已禁止你修改内容"}, room=request.sid)
        return
    try:
        full = safe_path(rel)
    except ValueError:
        return
    client_content = normalize_newlines(data.get("content", "") or "")
    with docs_lock:
        d = docs.get(rel)
        if d is not None and d.get("content") is not None:
            content = d["content"]
        else:
            if not os.path.exists(full):
                emit("file_deleted", {"path": rel}, room=request.sid)
                return
            content = client_content
    try:
        os.makedirs(os.path.dirname(full) or WORKSPACE, exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    except Exception as e:
        print(f"[save] 写盘失败 path={rel}: {e}")
        emit("save_error", {"path": rel, "error": str(e)}, room=request.sid)
        return
    stat_add(c_ip, saves=1)
    emit("saved", {"path": rel}, room=rel)

@socketio.on("judge_result")
def on_judge_result(data):
    rel = data.get("path")
    if not rel:
        return
    emit("judge_result", data, room=rel, include_self=False)

@socketio.on("lsp_open")
def on_lsp_open(data):
    rel = data.get("path")
    if not rel:
        return
    text = normalize_newlines(data.get("text", ""))
    try:
        full = safe_path(rel)
    except ValueError:
        return
    if not clangd.started:
        clangd.start()
    if clangd.started:
        clangd.did_open(full, text)

@socketio.on("lsp_change")
def on_lsp_change(data):
    rel = data.get("path")
    if not rel:
        return
    text = normalize_newlines(data.get("text", ""))
    try:
        full = safe_path(rel)
    except ValueError:
        return
    if not clangd.started:
        clangd.start()
    if clangd.started:
        clangd.sync(full, text)

@socketio.on("lsp_completion")
def on_lsp_completion(data):
    rel = data.get("path")
    if not rel:
        return {"items": []}
    text = normalize_newlines(data.get("text", ""))
    line = int(data.get("line", 0) or 0)
    character = int(data.get("character", 0) or 0)
    try:
        full = safe_path(rel)
    except ValueError:
        return {"items": []}
    if not clangd.started:
        clangd.start()
    if not clangd.started:
        return {"items": []}
    resp = clangd.completion(full, text, line, character)
    items = []
    if isinstance(resp, dict) and isinstance(resp.get("items"), list):
        items = resp["items"]
    elif isinstance(resp, list):
        items = resp
    return {"items": items}

@socketio.on("lsp_definition")
def on_lsp_definition(data):
    rel = data.get("path")
    if not rel:
        return {"error": "缺少 path"}
    text = normalize_newlines(data.get("text", ""))
    line = int(data.get("line", 0) or 0)
    character = int(data.get("character", 0) or 0)
    try:
        full = safe_path(rel)
    except ValueError:
        return {"error": "非法路径"}
    if not clangd.started:
        clangd.start()
    if not clangd.started:
        return {"error": "clangd 未就绪, 请稍后重试"}
    resp = clangd.definition(full, text, line, character)
    locations = []
    if isinstance(resp, list):
        locations = resp
    elif isinstance(resp, dict):
        locations = [resp]
    if not locations:
        return {"found": False}
    loc = locations[0]
    uri = loc.get("uri") or loc.get("targetUri")
    rng = loc.get("range") or loc.get("targetSelectionRange") or loc.get("targetRange")
    if not uri or not rng:
        return {"found": False}
    target_rel = uri_to_rel(uri)
    if target_rel is None:
        return {"found": False, "outside": True}
    start = rng.get("start", {})
    return {
        "found": True,
        "path": target_rel,
        "line": int(start.get("line", 0) or 0),
        "character": int(start.get("character", 0) or 0),
    }

@socketio.on("run_start")
def on_run_start(data):
    sid = request.sid
    rel = data.get("path", "")
    content = data.get("content")
    stdin_data = normalize_newlines(data.get("stdin", "") or "")
    kill_console(sid)
    cleanup_console(sid)
    try:
        full = safe_path(rel)
    except ValueError:
        emit("run_output", {"path": rel, "text": "[错误] 非法路径\n"})
        emit("run_exit", {"path": rel, "code": -1})
        return
    if content is not None:
        content = normalize_newlines(content)
        os.makedirs(os.path.dirname(full) or WORKSPACE, exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    else:
        try:
            with open(full, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            content = ""
    dangerous = find_dangerous_call(content or "")
    if dangerous:
        emit("run_output", {"path": rel, "text": f"[安全拦截] 检测到危险函数调用「{dangerous}」，已阻止运行\n"})
        emit("run_exit", {"path": rel, "code": -1, "reason": "blocked"})
        return
    ext = os.path.splitext(rel)[1].lstrip(".").lower()
    source_dir = os.path.dirname(full)
    work_dir_obj = tempfile.TemporaryDirectory()
    work_dir = work_dir_obj.name
    if ext in ("c", "cpp", "cc", "cxx"):
        emit("compile_start", {"path": rel})
        run_cmd, err = compile_source(full, ext, work_dir)
        if err:
            emit("run_output", {"path": rel, "text": err + "\n"})
            emit("run_exit", {"path": rel, "code": -1, "reason": "compile_error"})
            work_dir_obj.cleanup()
            return
    elif ext == "py":
        run_cmd = [sys.executable, "-u", full]
    else:
        emit("run_output", {"path": rel, "text": f"[错误] 不支持的语言: .{ext}\n"})
        emit("run_exit", {"path": rel, "code": -1})
        work_dir_obj.cleanup()
        return

    verdict_text = {"TLE": "时间超限", "MLE": "内存超限", "OLE": "输出超限", "RE": "运行时错误"}

    def runner():
        def on_proc(proc):
            with running_consoles_lock:
                running_consoles[sid] = {"proc": proc, "workdir": work_dir_obj, "timer": None, "path": rel}
            socketio.emit("run_started", {"path": rel}, room=sid)

        def on_output(chunk):
            socketio.emit("run_output", {"path": rel, "text": chunk}, room=sid)

        result = run_process_streaming(
            run_cmd, stdin_data, timeout=CONSOLE_RUN_TIMEOUT, cwd=source_dir,
            mem_limit_mb=MEM_LIMIT_MB, output_limit=OUTPUT_LIMIT,
            on_output=on_output, on_proc=on_proc, keep_stdin=True
        )
        verdict = result.get("error")
        if verdict:
            reason = verdict_text.get(verdict, verdict)
            socketio.emit("run_output", {"path": rel, "text": f"\n[{verdict}] {reason}（{result.get('time_ms', 0)}ms / {result.get('mem_kb', 0)}KB）\n"}, room=sid)
        code = result.get("code") if result.get("code") is not None else -1
        socketio.emit("run_exit", {"path": rel, "code": code, "verdict": verdict,
                                   "time_ms": result.get("time_ms", 0), "mem_kb": result.get("mem_kb", 0)}, room=sid)
        cleanup_console(sid)

    threading.Thread(target=runner, daemon=True).start()

@socketio.on("run_input")
def on_run_input(data):
    sid = request.sid
    with running_consoles_lock:
        entry = running_consoles.get(sid)
    if entry and entry["proc"].poll() is None:
        try:
            text = data.get("text", "")
            if not data.get("no_newline", False):
                text += "\n"
            entry["proc"].stdin.write(text)
            entry["proc"].stdin.flush()
        except:
            pass

@socketio.on("run_stop")
def on_run_stop(data):
    kill_console(request.sid)

if __name__ == "__main__":
    ip = get_ip()
    print(f"\n  LAN C++26 IDE")
    print(f"  本机: http://localhost:5000")
    print(f"  局域网: http://{ip}:5000\n")
    threading.Thread(target=warmup_pch, daemon=True).start()
    threading.Thread(target=ensure_firewall_rule, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
```

---

## [2026-08-19T20:09:16.065000+08:00] ASSISTANT


好的，现在发送**第二部分：JavaScript 全部改动**。

在 `</script>` 之前，找到合适位置（例如在 `initDFrame` 函数之后），插入以下所有代码。

---

## [2026-08-19T20:14:15.249000+08:00] ASSISTANT


明白了！你要的是完整的 `index.html` 文件。之前我说分两次发的是 `server.py` 和 JS 核心代码，但你没收到完整的 HTML 结构。

现在我把**完整的 `index.html`** 分两段发给你。这是第一段（开头到 `#bottom-dock` 之前）：

---

## [2026-08-19T20:17:25.179000+08:00] ASSISTANT


完全可以！把 JS 独立封装是更好的做法，可以保持 HTML 干净、方便维护、也利于浏览器缓存。

---

## [2026-08-19T20:19:57.502000+08:00] ASSISTANT


好的，由于 `ide.js` 代码量超过 3000 行，我分成 **3 段** 发送。拼接后即为完整文件。

---

## [2026-08-19T20:26:32.983000+08:00] ASSISTANT


好的，发送 `ide.js` **第 2 段**（包含：OT 变换、Socket 事件、分屏、Markdown、模板、字体、UI 核心）。

```javascript
// ============================================================
// ide.js 第 2 段
// ============================================================

// ===================== OT 核心 (TextOperation) =====================
const ot = {
    _isRetain: function(op) { return typeof op === 'number' && op > 0; },
    _isInsert: function(op) { return typeof op === 'string'; },
    _isDelete: function(op) { return typeof op === 'number' && op < 0; },

    TextOp: function() {
        this.ops = [];
        this.baseLength = 0;
        this.targetLength = 0;
    },

    transformCursor: function(p, op) {
        let oldIndex = 0, newIndex = 0;
        for (const c of op.ops) {
            if (ot._isRetain(c)) {
                if (oldIndex + c <= p) { oldIndex += c; newIndex += c; }
                else { return newIndex + (p - oldIndex); }
            } else if (ot._isInsert(c)) {
                newIndex += c.length;
            } else {
                const n = -c;
                if (oldIndex + n <= p) { oldIndex += n; }
                else { return newIndex; }
            }
        }
        return newIndex;
    },

    applyOpToEditor: function(op) {
        if (state.currentEditorType === 'textarea') {
            const oldVal = dom.codeEl.value;
            const newVal = op.apply(oldVal);
            const s = ot.transformCursor(dom.codeEl.selectionStart, op);
            const e = ot.transformCursor(dom.codeEl.selectionEnd, op);
            dom.codeEl.value = newVal;
            dom.codeEl.setSelectionRange(s, e);
            state.lastContent = newVal;
            editor.updateGutter();
        } else if (state.monacoEditor) {
            const model = state.monacoEditor.getModel();
            const edits = [];
            let pos = 0;
            for (const c of op.ops) {
                if (ot._isRetain(c)) { pos += c; }
                else if (ot._isInsert(c)) {
                    const p = model.getPositionAt(pos);
                    edits.push({ range: new monaco.Range(p.lineNumber, p.column, p.lineNumber, p.column), text: c });
                } else {
                    const n = -c;
                    const s = model.getPositionAt(pos);
                    const e = model.getPositionAt(pos + n);
                    edits.push({ range: new monaco.Range(s.lineNumber, s.column, e.lineNumber, e.column), text: '' });
                    pos += n;
                }
            }
            const suggestWasVisible = editor._isSuggestWidgetVisible();
            let localAnchorBefore = null, localActiveBefore = null;
            if (suggestWasVisible) {
                const sel = state.monacoEditor.getSelection();
                if (sel) {
                    localAnchorBefore = model.getOffsetAt({ lineNumber: sel.selectionStartLineNumber, column: sel.selectionStartColumn });
                    localActiveBefore = model.getOffsetAt({ lineNumber: sel.positionLineNumber, column: sel.positionColumn });
                }
            }
            model.applyEdits(edits);
            state.lastContent = state.monacoEditor.getValue();
            if (suggestWasVisible && localAnchorBefore !== null) {
                const newAnchorOffset = ot.transformCursor(localAnchorBefore, op);
                const newActiveOffset = ot.transformCursor(localActiveBefore, op);
                const anchorPos = model.getPositionAt(newAnchorOffset);
                const activePos = model.getPositionAt(newActiveOffset);
                state.monacoEditor.setSelection(new monaco.Selection(
                    anchorPos.lineNumber, anchorPos.column,
                    activePos.lineNumber, activePos.column
                ));
            }
        }
    },

    applyServer: function(op) {
        state.otRevision += 1;
        if (state.otOutstanding === null) {
            state.applyingRemote = true;
            ot.applyOpToEditor(op);
            state.applyingRemote = false;
        } else if (state.otBuffer !== null) {
            const p1 = ot._transform(state.otOutstanding, op);
            const p2 = ot._transform(state.otBuffer, p1[1]);
            state.applyingRemote = true;
            ot.applyOpToEditor(p2[1]);
            state.applyingRemote = false;
            state.otOutstanding = p1[0];
            state.otBuffer = p2[0];
        } else {
            const p1 = ot._transform(state.otOutstanding, op);
            state.applyingRemote = true;
            ot.applyOpToEditor(p1[1]);
            state.applyingRemote = false;
            state.otOutstanding = p1[0];
        }
    },

    applyAck: function() {
        state.otRevision += 1;
        if (state.otOutstanding !== null) {
            if (state.otBuffer !== null) {
                const b = state.otBuffer;
                state.otBuffer = null;
                state.otOutstanding = b;
                ot._send(b);
            } else {
                state.otOutstanding = null;
            }
        }
    },

    applyLocal: function(op) {
        if (state.otRevision < 0) return;
        if (state.otOutstanding === null) {
            state.otOutstanding = op;
            ot._send(op);
        } else if (state.otBuffer !== null) {
            state.otBuffer = state.otBuffer.compose(op);
        } else {
            state.otBuffer = op;
        }
    },

    _transform: function(a, b) {
        if (a.baseLength !== b.baseLength) throw new Error('OT transform base length');
        const op1p = new ot.TextOp();
        const op2p = new ot.TextOp();
        const ops1 = a.ops, ops2 = b.ops;
        let i1 = 0, i2 = 0;
        let o1 = ops1[i1++], o2 = ops2[i2++];
        while (true) {
            if (typeof o1 === 'undefined' && typeof o2 === 'undefined') break;
            if (ot._isInsert(o1)) {
                op1p.insert(o1);
                op2p.retain(o1.length);
                o1 = ops1[i1++];
                continue;
            }
            if (ot._isInsert(o2)) {
                op1p.retain(o2.length);
                op2p.insert(o2);
                o2 = ops2[i2++];
                continue;
            }
            if (typeof o1 === 'undefined') throw new Error('OT transform op1 short');
            if (typeof o2 === 'undefined') throw new Error('OT transform op2 long');
            let minl;
            if (ot._isRetain(o1) && ot._isRetain(o2)) {
                if (o1 > o2) { minl = o2; o1 = o1 - o2; o2 = ops2[i2++]; }
                else if (o1 === o2) { minl = o2; o1 = ops1[i1++]; o2 = ops2[i2++]; }
                else { minl = o1; o2 = o2 - o1; o1 = ops1[i1++]; }
                op1p.retain(minl);
                op2p.retain(minl);
            } else if (ot._isDelete(o1) && ot._isDelete(o2)) {
                if (-o1 > -o2) { o1 = o1 - o2; o2 = ops2[i2++]; }
                else if (o1 === o2) { o1 = ops1[i1++]; o2 = ops2[i2++]; }
                else { o2 = o2 - o1; o1 = ops1[i1++]; }
            } else if (ot._isDelete(o1) && ot._isRetain(o2)) {
                if (-o1 > o2) { minl = o2; o1 = o1 + o2; o2 = ops2[i2++]; }
                else if (-o1 === o2) { minl = o2; o1 = ops1[i1++]; o2 = ops2[i2++]; }
                else { minl = -o1; o2 = o2 + o1; o1 = ops1[i1++]; }
                op1p.delete(minl);
            } else if (ot._isRetain(o1) && ot._isDelete(o2)) {
                if (o1 > -o2) { minl = -o2; o1 = o1 + o2; o2 = ops2[i2++]; }
                else if (o1 === -o2) { minl = o1; o1 = ops1[i1++]; o2 = ops2[i2++]; }
                else { minl = o1; o2 = o2 + o1; o1 = ops1[i1++]; }
                op2p.delete(minl);
            } else {
                throw new Error('OT transform incompatible');
            }
        }
        return [op1p, op2p];
    },

    _send: function(op) {
        state.socket.emit('edit', { path: state.currentFile, op: op.toJSON(), base: state.otRevision },
            function(ack) { ot._handleAck(ack); });
    },

    _handleAck: function(ack) {
        if (!ack) return;
        if (ack.readonly) { state.myReadonly = true; utils.showToast('你已被管理员设为只读模式', 'warning'); return; }
        if (ack.resync || ack.version == null) { state.resyncDoc(); return; }
        ot._enqueue(ack.version, 'ack');
    },

    _enqueue: function(version, kind, op) {
        if (typeof version !== 'number' || version <= state.otRevision) return;
        state.otInbox.set(version, { kind: kind, op: op });
        ot._drain();
    },

    _drain: function() {
        while (state.otInbox.has(state.otRevision + 1)) {
            const m = state.otInbox.get(state.otRevision + 1);
            state.otInbox.delete(state.otRevision + 1);
            if (m.kind === 'ack') ot.applyAck();
            else ot.applyServer(m.op);
        }
        if (state.otInbox.size > 0 && !state.otInbox.has(state.otRevision + 1)) {
            if (!state.otGapTimer) {
                state.otGapTimer = setTimeout(function() {
                    state.otGapTimer = null;
                    if (state.otInbox.size > 0 && !state.otInbox.has(state.otRevision + 1)) {
                        state.resyncDoc();
                    }
                }, 8000);
            }
        } else if (state.otGapTimer) {
            clearTimeout(state.otGapTimer);
            state.otGapTimer = null;
        }
    },

    reset: function() {
        state.otRevision = -1;
        state.otOutstanding = null;
        state.otBuffer = null;
        state.otSynced = false;
        state.otInbox.clear();
        if (state.otGapTimer) { clearTimeout(state.otGapTimer);
            state.otGapTimer = null; }
        editor._updateReadOnly();
    },

    fromSplice: function(s, docLen) {
        const op = new ot.TextOp();
        if (s.start > 0) op.retain(s.start);
        const d = s.end - s.start;
        if (d > 0) op.delete(d);
        if (s.text.length > 0) op.insert(s.text);
        const tail = docLen - s.end;
        if (tail > 0) op.retain(tail);
        return op;
    },

    fromJSON: function(ops) {
        const o = new ot.TextOp();
        for (const op of ops) {
            if (ot._isRetain(op)) o.retain(op);
            else if (ot._isInsert(op)) o.insert(op);
            else if (ot._isDelete(op)) o.delete(op);
            else throw new Error('bad op');
        }
        return o;
    }
};

// 扩展 TextOp 原型
ot.TextOp.prototype = {
    retain: function(n) {
        n = n | 0;
        if (n === 0) return this;
        this.baseLength += n;
        this.targetLength += n;
        const last = this.ops[this.ops.length - 1];
        if (ot._isRetain(last)) this.ops[this.ops.length - 1] = last + n;
        else this.ops.push(n);
        return this;
    },
    insert: function(str) {
        if (str === '') return this;
        this.targetLength += str.length;
        const ops = this.ops;
        const last = ops[ops.length - 1];
        if (ot._isInsert(last)) { ops[ops.length - 1] = last + str; }
        else if (ot._isDelete(last)) {
            if (ot._isInsert(ops[ops.length - 2])) ops[ops.length - 2] += str;
            else { ops[ops.length] = last;
                ops[ops.length - 2] = str; }
        } else ops.push(str);
        return this;
    },
    delete: function(n) {
        if (typeof n === 'string') n = n.length;
        n = n | 0;
        if (n === 0) return this;
        if (n > 0) n = -n;
        this.baseLength -= n;
        const last = this.ops[this.ops.length - 1];
        if (ot._isDelete(last)) this.ops[this.ops.length - 1] += n;
        else this.ops.push(n);
        return this;
    },
    apply: function(str) {
        if (str.length !== this.baseLength) throw new Error('OT base length mismatch');
        let out = '';
        let i = 0;
        for (const op of this.ops) {
            if (ot._isRetain(op)) { out += str.slice(i, i + op);
                i += op; } else if (ot._isInsert(op)) { out += op; } else { i += -op; }
        }
        if (i !== str.length) throw new Error('OT did not consume whole string');
        return out;
    },
    toJSON: function() {
        return this.ops.slice();
    },
    compose: function(op2) {
        const op1 = this;
        if (op1.targetLength !== op2.baseLength) throw new Error('OT compose length');
        const operation = new ot.TextOp();
        const ops1 = op1.ops,
            ops2 = op2.ops;
        let i1 = 0,
            i2 = 0;
        let o1 = ops1[i1++],
            o2 = ops2[i2++];
        while (true) {
            if (typeof o1 === 'undefined' && typeof o2 === 'undefined') break;
            if (ot._isDelete(o1)) { operation.delete(o1);
                o1 = ops1[i1++];
                continue; }
            if (ot._isInsert(o2)) { operation.insert(o2);
                o2 = ops2[i2++];
                continue; }
            if (typeof o1 === 'undefined') throw new Error('OT compose op1 short');
            if (typeof o2 === 'undefined') throw new Error('OT compose op1 long');
            if (ot._isRetain(o1) && ot._isRetain(o2)) {
                if (o1 > o2) { operation.retain(o2);
                    o1 = o1 - o2;
                    o2 = ops2[i2++]; } else if (o1 === o2) { operation.retain(o1);
                    o1 = ops1[i1++];
                    o2 = ops2[i2++]; } else { operation.retain(o1);
                    o2 = o2 - o1;
                    o1 = ops1[i1++]; }
            } else if (ot._isInsert(o1) && ot._isDelete(o2)) {
                if (o1.length > -o2) { o1 = o1.slice(-o2);
                    o2 = ops2[i2++]; } else if (o1.length === -o2) { o1 = ops1[i1++];
                    o2 = ops2[i2++]; } else { o2 = o2 + o1.length;
                    o1 = ops1[i1++]; }
            } else if (ot._isInsert(o1) && ot._isRetain(o2)) {
                if (o1.length > o2) { operation.insert(o1.slice(0, o2));
                    o1 = o1.slice(o2);
                    o2 = ops2[i2++]; } else if (o1.length === o2) { operation.insert(o1);
                    o1 = ops1[i1++];
                    o2 = ops2[i2++]; } else { operation.insert(o1);
                    o2 = o2 - o1.length;
                    o1 = ops1[i1++]; }
            } else if (ot._isRetain(o1) && ot._isDelete(o2)) {
                if (o1 > -o2) { operation.delete(o2);
                    o1 = o1 + o2;
                    o2 = ops2[i2++]; } else if (o1 === -o2) { operation.delete(o2);
                    o1 = ops1[i1++];
                    o2 = ops2[i2++]; } else { operation.delete(o1);
                    o2 = o2 + o1;
                    o1 = ops1[i1++]; }
            } else {
                throw new Error('OT compose invalid');
            }
        }
        return operation;
    }
};

// ===================== Socket 事件 =====================
function setupSocketEvents() {
    state.socket.on('connect', function() {
        dom.statusText.textContent = '在线（' + state.username + (state.myReadonly ? ' · 只读' : '') + '）';
        if (state.currentFile) state.resyncDoc();
    });

    state.socket.on('readonly_changed', function(data) {
        state.myReadonly = !!data.readonly;
        editor._updateReadOnly();
        dom.statusText.textContent = '在线（' + state.username + (state.myReadonly ? ' · 只读' : '') + '）';
        utils.showToast(data.readonly ? '你已被管理员设为只读模式' : '管理员已解除你的只读模式',
            data.readonly ? 'warning' : 'success');
    });

    state.socket.on('disconnect', function() {
        dom.statusText.textContent = '断开连接';
        ot.reset();
        editor._updateReadOnly();
    });

    state.socket.on('connect_error', function() { dom.statusText.textContent = '连接失败'; });

    state.socket.on('lsp_diagnostics', function(data) {
        if (data.path !== state.currentFile) return;
        const diags = data.diagnostics || [];
        const sevRank = { 1: 0, 2: 1, 3: 2, 4: 3 };
        state.problemList = diags.map(function(d) {
            const s = d.range && d.range.start ? d.range.start : { line: 0, character: 0 };
            const e = d.range && d.range.end ? d.range.end : s;
            return {
                severity: d.severity || 1,
                message: d.message || '',
                line: (s.line || 0) + 1,
                column: (s.character || 0) + 1,
                endLine: (e.line || 0) + 1,
                endColumn: (e.character || 0) + 1,
                source: d.source || 'clangd',
                code: d.code || ''
            };
        }).sort(function(a, b) {
            return (sevRank[a.severity] || 9) - (sevRank[b.severity] || 9) || a.line - b.line;
        });
        ui.renderProblems();
        if (!state.monacoEditor) return;
        const model = state.monacoEditor.getModel();
        if (!model) return;
        const sevMap = { 1: monaco.MarkerSeverity.Error, 2: monaco.MarkerSeverity.Warning,
            3: monaco.MarkerSeverity.Info, 4: monaco.MarkerSeverity.Hint };
        const markers = diags.map(function(d) {
            const s = d.range && d.range.start ? d.range.start : { line: 0, character: 0 };
            const e = d.range && d.range.end ? d.range.end : { line: 0, character: 0 };
            return {
                severity: sevMap[d.severity] || monaco.MarkerSeverity.Error,
                message: d.message || '',
                startLineNumber: (s.line || 0) + 1,
                startColumn: (s.character || 0) + 1,
                endLineNumber: (e.line || 0) + 1,
                endColumn: (e.character || 0) + 1,
                source: d.source || 'clangd'
            };
        });
        monaco.editor.setModelMarkers(model, 'clangd', markers);
    });

    state.socket.on('presence', function(data) {
        const entries = data.users || [];
        const now = Date.now();
        dom.presenceList.innerHTML = '';
        const presentSids = new Set(entries.map(function(u) { return u.sid; }));
        for (const sid in state.remoteCursors) {
            if (!presentSids.has(sid)) clearRemoteCursor(sid);
        }
        const me = entries.find(function(u) { return u.sid === state.socket.id; });
        if (me) state.myReadonly = !!me.readonly;
        entries.forEach(function(u) {
            const chip = document.createElement('span');
            const isMe = u.sid === state.socket.id;
            const isActive = (now - (u.last_active || 0)) <= 10000;
            chip.className = 'user-chip' +
                (isMe ? ' me' : '') +
                (u.readonly ? ' ro' : '') +
                (!isMe && state.isAdmin ? ' clickable' : '') +
                (!isActive ? ' inactive' : '');
            if (isMe) {
                chip.title = '点击修改名字' + (state.myReadonly ? '（当前为只读模式）' : '');
            } else {
                const fileName = u.current_file ? u.current_file.split('/').pop() : '未打开文件';
                chip.title = (u.device || '未知设备') + ' · 正在编辑: ' + fileName;
            }
            chip.innerHTML = '<span class="swatch" style="background:' + colorFor(u.name) + '"></span>' +
                utils.escapeHtml(u.name) + (u.admin ? ' 👑' : '') + (u.readonly ? ' 🔒' : '');
            if (!isActive) {
                chip.style.opacity = '0.4';
                chip.style.color = 'var(--text-lo)';
            }
            if (isMe) {
                chip.addEventListener('click', promptRename);
            } else if (state.isAdmin) {
                chip.addEventListener('click', function(e) { e.stopPropagation();
                    showUserCard(u, chip); });
            }
            dom.presenceList.appendChild(chip);
        });
    });

    state.socket.on('cursor', function(data) {
        if (!data || typeof data.offset !== 'number') return;
        if (data.path === state.currentFile) {
            const uname = data.username || '匿名';
            state.remoteCursors[data.sid || 'unknown'] = {
                username: uname,
                color: colorFor(uname),
                offset: data.offset,
                ts: Date.now()
            };
            renderRemoteCursors();
        } else if (state.splitMode && data.path === state.rightFile) {
            const uname = data.username || '匿名';
            state.rightRemoteCursors[data.sid || 'unknown'] = {
                username: uname,
                color: colorFor(uname),
                offset: data.offset,
                ts: Date.now()
            };
            renderRightRemoteCursors();
        }
    });

    state.socket.on('doc_sync', function(data) {
        if (!data) return;
        if (data.path === state.currentFile) {
            state.fileContentCache[data.path] = data.content;
            ot.reset();
            state.otRevision = (typeof data.version === 'number') ? data.version : 0;
            state.otSynced = true;
            editor._updateReadOnly();
            state.applyingRemote = true;
            editor.setContent(data.content);
            state.applyingRemote = false;
        } else if (state.splitMode && state.rightFile && data.path === state.rightFile) {
            state.rightFileContent = data.content;
            if (state.rightMonaco && state.rightMonacoLoaded) {
                const current = state.rightMonaco.getValue();
                if (current !== data.content) {
                    state.rightMonaco.setValue(data.content);
                }
            }
        }
    });

    state.socket.on('edit', function(data) {
        if (data.path !== state.currentFile) return;
        if (typeof data.version === 'number' && data.op) {
            let op;
            try { op = ot.fromJSON(data.op); } catch (e) { state.resyncDoc(); return; }
            ot._enqueue(data.version, 'remote', op);
        }
    });

    state.socket.on('saved', function(data) {
        state.dirtySet.delete(data.path);
        if (data.path === state.currentFile) state.dirty = false;
        ui.updateTabDirty(data.path);
    });

    state.socket.on('save_error', function(data) {
        utils.showToast('保存失败: ' + (data.error || '未知错误'), 'error', 5000);
    });

    state.socket.on('compile_start', function(data) {
        if (data.path !== state.currentFile) return;
        dom.consoleStatus.textContent = '编译中...';
        dom.consoleStatus.className = 'cs-compiling';
    });

    state.socket.on('run_output', function(data) {
        if (data.path !== state.currentFile) return;
        appendConsole(data.text);
    });

    state.socket.on('run_started', function(data) {
        if (data.path !== state.currentFile) return;
        dom.consoleStatus.textContent = '运行中...';
        dom.consoleStatus.className = 'cs-running';
        dom.consoleInput.disabled = true;
        dom.btnSendInput.disabled = true;
        if (state.freEnabled) {
            appendConsole('程序已运行，输出重定向到文件，结束后将读取输出文件内容。\n');
        }
    });

    state.socket.on('run_exit', function(data) {
        if (data.path !== state.currentFile) return;
        clearTimeout(state.consoleWaitTimer);
        let exitText;
        if (data.reason === 'compile_error') exitText = '编译失败';
        else if (data.verdict) {
            const vText = { TLE: '时间超限', MLE: '内存超限', OLE: '输出超限', RE: '运行时错误' } [data.verdict] || data.verdict;
            exitText = data.verdict + ' · ' + vText + '（' + (data.time_ms || 0) + 'ms / ' + (data.mem_kb || 0) + 'KB）';
        } else {
            exitText = '已退出（代码 ' + data.code + '）';
        }
        dom.consoleStatus.textContent = exitText;
        dom.consoleStatus.className = 'cs-exited';
        dom.consoleInput.disabled = false;
        dom.consoleStop.disabled = true;
        dom.btnRunInConsole.disabled = false;
        dom.btnSendInput.disabled = true;
        if (state.freEnabled) {
            try {
                const fileName = state.currentFile.split('/').pop();
                const baseName = fileName.replace(/\.[^.]+$/, '');
                const outPath = state.currentFile.substring(0, state.currentFile.lastIndexOf('/') + 1) + baseName + '.out';
                fetch('/api/file?path=' + encodeURIComponent(outPath)).then(function(res) { return res.json(); })
                    .then(function(outData) {
                        if (outData && !outData.error) {
                            appendConsole('--- 输出文件内容 ---\n');
                            appendConsole(outData.content || '(空)');
                            appendConsole('\n--- 结束 ---\n');
                        } else {
                            appendConsole('[错误] 无法读取输出文件：' + (outData.error || '文件不存在') + '\n');
                        }
                    }).catch(function(e) {
                        appendConsole('[错误] 读取输出文件失败：' + e.message + '\n');
                    });
            } catch (e) {
                appendConsole('[错误] 读取输出文件失败：' + e.message + '\n');
            }
        }
    });

    state.socket.on('judge_result', function(data) {
        if (data.path !== state.currentFile) return;
        ui.renderJudgeResult(data.result);
    });

    state.socket.on('judge_progress', function(data) {
        if (data.path !== state.currentFile) return;
        if (data.case === '__compile__') {
            if (data.result && data.result.verdict === 'CE') {
                dom.judgeVerdict.textContent = 'CE';
                dom.judgeVerdict.className = 'v-ce';
                dom.judgeSummary.textContent = '编译错误';
                utils.showToast('编译错误', 'error');
            }
            return;
        }
        const m = data.case.match(/(\d+)/);
        const num = m ? parseInt(m[1]) : 0;
        const tc = state.cphTestCases.find(function(t) { return t.num === num; });
        if (tc) {
            tc.verdict = data.result.verdict;
            tc.actual = data.result.actual;
            tc.stderr = data.result.stderr;
            tc.time_ms = data.result.time_ms;
            tc.mem_kb = data.result.mem_kb;
            ui.renderCPH();
        }
    });

    state.socket.on('file_renamed', function(data) {
        if (data.old_path === state.currentFile) {
            state.socket.emit('leave', { path: data.old_path });
            state.currentFile = data.new_path;
            dom.filepathEl.textContent = state.currentFile;
            state.socket.emit('join', { path: state.currentFile, username: state.username, device: deviceLabel() });
            utils.showToast('文件已重命名为 ' + data.new_path, 'info');
        }
        const ti = state.openTabs.indexOf(data.old_path);
        if (ti !== -1) state.openTabs[ti] = data.new_path;
        if (state.fileContentCache[data.old_path] !== undefined) {
            state.fileContentCache[data.new_path] = state.fileContentCache[data.old_path];
            delete state.fileContentCache[data.old_path];
        }
        if (state.dirtySet.has(data.old_path)) { state.dirtySet.delete(data.old_path);
            state.dirtySet.add(data.new_path); }
        ui.renderEditorTabs();
        loadTree();
    });

    state.socket.on('tree_changed', function() { loadTree(); });

    state.socket.on('file_deleted', function(data) {
        ui.handleFileDeleted(data.path);
    });
}

function deviceLabel() {
    const ua = navigator.userAgent;
    const os = /Windows/.test(ua) ? 'Windows' : /Mac OS/.test(ua) ? 'macOS' : /Android/.test(ua) ? 'Android' :
        (/iPhone|iPad/.test(ua) ? 'iOS' : (/Linux/.test(ua) ? 'Linux' : '未知系统'));
    const br = /Edg\//.test(ua) ? 'Edge' : /Chrome\//.test(ua) ? 'Chrome' : /Firefox\//.test(ua) ? 'Firefox' :
        (/Safari\//.test(ua) ? 'Safari' : '浏览器');
    return os + ' · ' + br;
}

// ===================== 远程光标渲染 =====================
function renderRemoteCursors() {
    const now = Date.now();
    for (const sid in state.remoteCursors) {
        if (now - state.remoteCursors[sid].ts > 30000) delete state.remoteCursors[sid];
    }
    if (!state.remoteCursorsVisible) {
        if (state.currentEditorType !== 'textarea' && state.monacoEditor) {
            for (const sid in state.remoteWidgets) {
                try { state.monacoEditor.removeContentWidget(state.remoteWidgets[sid]); } catch (e) {}
                delete state.remoteWidgets[sid];
            }
        }
        return;
    }
    if (state.currentEditorType !== 'textarea' && state.monacoEditor) {
        for (const sid in state.remoteWidgets) {
            if (!state.remoteCursors[sid] || (now - state.remoteCursors[sid].ts > 10000)) {
                try { state.monacoEditor.removeContentWidget(state.remoteWidgets[sid]); } catch (e) {}
                delete state.remoteWidgets[sid];
            }
        }
        const model = state.monacoEditor.getModel();
        if (!model) return;
        const len = model.getValueLength();
        for (const sid in state.remoteCursors) {
            const u = state.remoteCursors[sid];
            if (now - u.ts > 10000) continue;
            const off = Math.max(0, Math.min(u.offset, len));
            const pos = model.getPositionAt(off);
            if (state.remoteWidgets[sid]) {
                try { state.monacoEditor.removeContentWidget(state.remoteWidgets[sid]); } catch (e) {}
                delete state.remoteWidgets[sid];
            }
            const domEl = document.createElement('div');
            domEl.className = 'remote-cursor';
            domEl.style.borderLeftColor = u.color;
            domEl.innerHTML = '<span class="remote-cursor-name" style="background:' + u.color + '">' +
                utils.escapeHtml(u.username) + '</span>';
            const widget = {
                getId: function() { return 'rc-' + sid; },
                getDomNode: function() { return domEl; },
                getPosition: function() {
                    return {
                        position: { lineNumber: pos.lineNumber, column: pos.column },
                        preference: [monaco.editor.ContentWidgetPositionPreference.EXACT]
                    };
                }
            };
            state.monacoEditor.addContentWidget(widget);
            state.remoteWidgets[sid] = widget;
        }
    } else {
        const text = dom.codeEl.value;
        for (const sid in state.remoteCursors) {
            const u = state.remoteCursors[sid];
            if (now - u.ts > 10000) { delete u.line; continue; }
            u.line = text.slice(0, Math.max(0, Math.min(u.offset, text.length))).split('\n').length;
        }
        editor.updateGutter();
    }
}

function clearRemoteCursor(sid) {
    if (state.remoteWidgets[sid] && state.monacoEditor) {
        try { state.monacoEditor.removeContentWidget(state.remoteWidgets[sid]); } catch (e) {}
    }
    delete state.remoteWidgets[sid];
    delete state.remoteCursors[sid];
}

// ===================== 字体控制 =====================
const font = {
    apply: function(size) {
        size = Math.min(32, Math.max(8, size));
        state.editorFontSize = size;
        localStorage.setItem('editor-font-size', size);
        if (state.monacoEditor) {
            state.monacoEditor.updateOptions({ fontSize: size });
        }
        if (state.currentEditorType === 'textarea') {
            dom.codeEl.style.fontSize = size + 'px';
            dom.gutterEl.style.fontSize = size + 'px';
        }
    },
    increase: function() { font.apply(state.editorFontSize + 1); },
    decrease: function() { font.apply(state.editorFontSize - 1); },
    reset: function() { font.apply(14); }
};

// ===================== 分屏 =====================
const split = {
    init: function() {
        dom.splitDivider.addEventListener('mousedown', function(e) {
            state.isSplitDragging = true;
            dom.splitDivider.classList.add('active');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });
        document.addEventListener('mousemove', function(e) {
            if (!state.isSplitDragging) return;
            const rect = dom.mdContainer.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const total = rect.width;
            state.splitRatio = Math.max(0.15, Math.min(0.85, x / total));
            split.applyRatio();
        });
        document.addEventListener('mouseup', function() {
            if (state.isSplitDragging) {
                state.isSplitDragging = false;
                dom.splitDivider.classList.remove('active');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                localStorage.setItem('split-ratio', state.splitRatio);
                if (state.monacoEditor) setTimeout(function() { state.monacoEditor.layout(); }, 50);
                if (state.rightMonaco) setTimeout(function() { state.rightMonaco.layout(); }, 50);
            }
        });
        window.addEventListener('resize', function() {
            if (state.splitMode) split.applyRatio();
        });
        dom.splitClose.addEventListener('click', split.close);
        dom.splitRightClose.addEventListener('click', split.close);
    },

    applyRatio: function() {
        const total = dom.mdContainer.clientWidth;
        if (total < 160) {
            dom.splitLeft.style.flex = '1';
            dom.splitRight.style.flex = '1';
            dom.splitLeft.style.flexBasis = 'auto';
            dom.splitRight.style.flexBasis = 'auto';
            return;
        }
        const leftWidth = Math.max(80, total * state.splitRatio);
        const rightWidth = Math.max(80, total * (1 - state.splitRatio));
        dom.splitLeft.style.flex = '0 0 ' + leftWidth + 'px';
        dom.splitRight.style.flex = '0 0 ' + rightWidth + 'px';
    },

    open: function(filePath) {
        state.splitMode = true;
        state.isPreviewMode = false;
        dom.splitRight.style.display = 'flex';
        dom.splitRightEditorWrap.style.display = 'flex';
        dom.splitRightPreview.style.display = 'none';
        dom.splitDivider.style.display = 'block';
        dom.splitClose.style.display = 'inline-block';
        split.applyRatio();
        split.openFile(filePath);
        if (state.monacoEditor) setTimeout(function() { state.monacoEditor.layout(); }, 50);
    },

    close: function() {
        state.splitMode = false;
        state.isPreviewMode = false;
        dom.splitRight.style.display = 'none';
        dom.splitDivider.style.display = 'none';
        dom.splitClose.style.display = 'none';
        dom.splitLeft.style.flex = '1';
        dom.splitLeft.style.flexBasis = 'auto';
        dom.splitRight.style.flex = '1';
        dom.splitRight.style.flexBasis = 'auto';
        if (state.rightMonaco) {
            state.rightMonaco.dispose();
            state.rightMonaco = null;
            state.rightMonacoLoaded = false;
        }
        state.rightFile = null;
        state.rightFileContent = null;
        state.rightRemoteCursors = {};
        state.rightRemoteWidgets = {};
        state.rightDirty = false;
        if (state.monacoEditor) setTimeout(function() { state.monacoEditor.layout(); }, 50);
    },

    openFile: function(filePath) {
        if (!filePath) return;
        state.rightFile = filePath;
        fetch('/api/file?path=' + encodeURIComponent(filePath)).then(function(res) { return res.json(); })
            .then(function(data) {
                if (data.error) {
                    utils.showToast('打开失败: ' + data.error, 'error');
                    return;
                }
                state.rightFileContent = data.content || '';
                dom.splitRightLabel.textContent = filePath.split('/').pop();
                dom.splitRightLabel.title = filePath;
                if (!state.rightMonacoLoaded) {
                    split._initRightMonaco();
                }
                if (state.rightMonaco) {
                    state.rightMonaco.setValue(state.rightFileContent);
                    state.rightMonaco.setModelLanguage(state.rightMonaco.getModel(),
                        utils.langForExt(utils.extOf(filePath)));
                    setTimeout(function() { state.rightMonaco.layout(); }, 50);
                }
            }).catch(function(e) { utils.showToast('加载失败', 'error'); });
    },

    _initRightMonaco: function() {
        if (state.rightMonacoLoaded) return;
        const requireFn = window.monacoRequire || window.require;
        if (!requireFn) { setTimeout(function() { split._initRightMonaco(); }, 200); return; }
        requireFn(['vs/editor/editor.main'], function() {
            state.rightMonaco = monaco.editor.create(dom.splitRightMonaco, {
                value: state.rightFileContent || '',
                language: 'plaintext',
                theme: 'cpp26-dark',
                automaticLayout: true,
                fontFamily: "'Cascadia Code','Cascadia Mono','Fira Code','Consolas',monospace",
                fontSize: state.editorFontSize || 14,
                lineHeight: 22,
                minimap: { enabled: true, maxColumn: 80 },
                padding: { top: 12 },
                smoothScrolling: true,
                cursorSmoothCaretAnimation: true,
                fontLigatures: true,
                suggestOnTriggerCharacters: true,
                quickSuggestions: { other: true, comments: false, strings: false },
                tabSize: 4,
                insertSpaces: true,
                scrollBeyondLastLine: false
            });
            state.rightMonacoLoaded = true;
            state.rightMonaco.onDidChangeModelContent(function() {
                if (!state.rightFile) return;
                state.rightFileContent = state.rightMonaco.getValue();
                state.rightDirty = true;
                clearTimeout(state.rightSaveTimer);
                state.rightSaveTimer = setTimeout(function() {
                    if (state.rightFile) {
                        state.socket.emit('save', { path: state.rightFile, content: state.rightFileContent });
                        state.rightDirty = false;
                    }
                }, 1500);
            });
            state.rightMonaco.onDidChangeCursorPosition(function() {
                const pos = state.rightMonaco.getPosition();
                if (pos && state.rightFile) {
                    const offset = state.rightMonaco.getModel().getOffsetAt(pos);
                    state.socket.emit('cursor', { path: state.rightFile, offset: offset });
                }
            });
            state.rightMonaco.addAction({
                id: 'right-format-document',
                label: '格式化文档',
                keybindings: [monaco.KeyMod.Shift | monaco.KeyMod.Alt | monaco.KeyCode.KeyF],
                contextMenuGroupId: '2_editor',
                contextMenuOrder: 1,
                run: function(ed) { ed.getAction('editor.action.formatDocument').run(); }
            });
            split.applyRatio();
        });
    },

    toggle: function(filePath) {
        if (!state.splitMode) {
            split.open(filePath);
        } else if (filePath === state.rightFile) {
            if (state.rightMonaco) state.rightMonaco.focus();
        } else {
            split.openFile(filePath);
        }
    }
};

// ===================== 右侧远程光标渲染 =====================
function renderRightRemoteCursors() {
    if (!state.rightMonaco || !state.rightMonacoLoaded) return;
    if (!state.remoteCursorsVisible) {
        for (const sid in state.rightRemoteWidgets) {
            try { state.rightMonaco.removeContentWidget(state.rightRemoteWidgets[sid]); } catch (e) {}
            delete state.rightRemoteWidgets[sid];
        }
        return;
    }
    const now = Date.now();
    const model = state.rightMonaco.getModel();
    if (!model) return;
    const len = model.getValueLength();
    for (const sid in state.rightRemoteWidgets) {
        if (!state.rightRemoteCursors[sid] || (now - state.rightRemoteCursors[sid].ts > 10000)) {
            try { state.rightMonaco.removeContentWidget(state.rightRemoteWidgets[sid]); } catch (e) {}
            delete state.rightRemoteWidgets[sid];
        }
    }
    for (const sid in state.rightRemoteCursors) {
        const u = state.rightRemoteCursors[sid];
        if (now - u.ts > 10000) continue;
        const off = Math.max(0, Math.min(u.offset, len));
        const pos = model.getPositionAt(off);
        if (state.rightRemoteWidgets[sid]) {
            try { state.rightMonaco.removeContentWidget(state.rightRemoteWidgets[sid]); } catch (e) {}
            delete state.rightRemoteWidgets[sid];
        }
        const domEl = document.createElement('div');
        domEl.className = 'remote-cursor';
        domEl.style.borderLeftColor = u.color;
        domEl.innerHTML = '<span class="remote-cursor-name" style="background:' + u.color + '">' +
            utils.escapeHtml(u.username) + '</span>';
        const widget = {
            getId: function() { return 'rrc-' + sid; },
            getDomNode: function() { return domEl; },
            getPosition: function() {
                return {
                    position: { lineNumber: pos.lineNumber, column: pos.column },
                    preference: [monaco.editor.ContentWidgetPositionPreference.EXACT]
                };
            }
        };
        state.rightMonaco.addContentWidget(widget);
        state.rightRemoteWidgets[sid] = widget;
    }
}

// ===================== Markdown =====================
const markdown = {
    init: function() {
        document.querySelectorAll('.md-mode-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.md-mode-btn').forEach(function(b) { b.classList.remove('active'); });
                this.classList.add('active');
                state.mdMode = this.dataset.mode;
                markdown.applyMode();
            });
        });
    },

    applyMode: function() {
        if (!state.mdDomMoved) {
            const monacoEl = document.getElementById('monaco-editor');
            const frameEl = document.getElementById('editor-frame');
            if (!dom.mdEditorWrap.contains(monacoEl) && monacoEl) {
                dom.mdEditorWrap.appendChild(monacoEl);
            }
            if (!dom.mdEditorWrap.contains(frameEl) && frameEl) {
                dom.mdEditorWrap.appendChild(frameEl);
            }
            state.mdDomMoved = true;
        }
        if (state.mdMode === 'edit') {
            if (state.splitMode) split.close();
            dom.splitLeft.style.flex = '1';
            dom.splitLeft.style.flexBasis = 'auto';
        } else if (state.mdMode === 'preview' || state.mdMode === 'split') {
            if (!state.splitMode || !state.isPreviewMode) {
                state.isPreviewMode = true;
                state.splitMode = true;
                dom.splitRight.style.display = 'flex';
                dom.splitRightEditorWrap.style.display = 'none';
                dom.splitRightPreview.style.display = 'block';
                dom.splitDivider.style.display = 'block';
                dom.splitClose.style.display = 'inline-block';
                dom.splitRightLabel.textContent = '预览';
                split.applyRatio();
                markdown.render();
                if (state.monacoEditor) setTimeout(function() { state.monacoEditor.layout(); }, 50);
            }
            split.applyRatio();
        }
    },

    render: function() {
        if (!state.monacoEditor || !state.isMarkdownFile) return;
        const content = state.monacoEditor.getValue();
        if (content === state.mdLastContent) return;
        state.mdLastContent = content;
        try {
            const html = marked.parse(content);
            dom.splitRightPreview.innerHTML = html;
            if (typeof hljs !== 'undefined') {
                dom.splitRightPreview.querySelectorAll('pre code').forEach(function(block) {
                    hljs.highlightElement(block);
                });
            }
        } catch (e) {
            dom.splitRightPreview.innerHTML = '<div style="color:var(--err);">渲染错误: ' + e.message + '</div>';
        }
    },

    setupForCurrentFile: function() {
        const isMd = utils.isMarkdownFile(state.currentFile);
        if (isMd) {
            state.isMarkdownFile = true;
            dom.mdToolbar.style.display = 'flex';
        } else {
            state.isMarkdownFile = false;
            dom.mdToolbar.style.display = 'none';
            if (state.splitMode && state.isPreviewMode) split.close();
            if (state.monacoEditor) setTimeout(function() { state.monacoEditor.layout(); }, 50);
        }
    }
};

// ===================== 模板 =====================
const templates = {
    loadAll: function() {
        return fetch('/api/templates').then(function(res) { return res.json(); })
            .then(function(data) { state.templates = data || {}; return state.templates; })
            .catch(function() { state.templates = {}; return state.templates; });
    },

    loadOne: function(ext) {
        return fetch('/api/templates/' + encodeURIComponent(ext)).then(function(res) { return res.json(); })
            .then(function(content) {
                dom.tmplContent.value = typeof content === 'string' ? content : '';
            }).catch(function() { dom.tmplContent.value = ''; });
    },

    save: function(ext, content) {
        return fetch('/api/templates/' + encodeURIComponent(ext), {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        }).then(function(res) { return res.json(); }).then(function(data) {
            if (data.ok) { state.templates[ext] = content;
                utils.showToast('模板已保存', 'success'); return true; }
            return false;
        }).catch(function() { utils.showToast('保存失败', 'error'); return false; });
    },

    delete: function(ext) {
        return fetch('/api/templates/' + encodeURIComponent(ext), { method: 'DELETE' })
            .then(function(res) { return res.json(); }).then(function(data) {
                if (data.ok) {
                    delete state.templates[ext];
                    dom.tmplContent.value = '';
                    utils.showToast('模板已删除', 'info');
                    return true;
                }
                return false;
            }).catch(function() { utils.showToast('删除失败', 'error'); return false; });
    },

    replaceVariables: function(content, fileName) {
        const now = new Date();
        const author = state.username || '匿名';
        const nameNoExt = fileName.replace(/\.[^.]+$/, '');
        const vars = {
            '{FileName}': fileName,
            '{FileNameNoExt}': nameNoExt,
            '{Date}': now.toISOString().slice(0, 10),
            '{Time}': now.toTimeString().slice(0, 8),
            '{Year}': String(now.getFullYear()),
            '{Month}': String(now.getMonth() + 1).padStart(2, '0'),
            '{Day}': String(now.getDate()).padStart(2, '0'),
            '{Author}': author
        };
        let result = content;
        for (const key in vars) {
            result = result.replaceAll(key, vars[key]);
        }
        return result;
    },

    initModal: function() {
        dom.btnTemplates.addEventListener('click', function() {
            dom.templateModal.style.display = 'flex';
            dom.tmplExt.value = '';
            dom.tmplContent.value = '';
            dom.tmplExt.focus();
        });
        dom.tmplClose.addEventListener('click', function() { dom.templateModal.style.display = 'none'; });
        dom.templateModal.addEventListener('click', function(e) {
            if (e.target === dom.templateModal) dom.templateModal.style.display = 'none';
        });
        dom.tmplLoad.addEventListener('click', function() {
            const ext = dom.tmplExt.value.trim().toLowerCase();
            if (!ext) { utils.showToast('请输入扩展名', 'warning'); return; }
            state.currentTemplateExt = ext;
            templates.loadOne(ext);
        });
        dom.tmplExt.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') dom.tmplLoad.click();
        });
        dom.tmplSave.addEventListener('click', function() {
            const ext = dom.tmplExt.value.trim().toLowerCase();
            if (!ext) { utils.showToast('请输入扩展名', 'warning'); return; }
            templates.save(ext, dom.tmplContent.value);
        });
        dom.tmplDelete.addEventListener('click', function() {
            const ext = dom.tmplExt.value.trim().toLowerCase();
            if (!ext) { utils.showToast('请输入扩展名', 'warning'); return; }
            utils.showConfirm('确定要删除 .' + ext + ' 的模板配置吗？', function() {
                templates.delete(ext);
            });
        });
    }
};
```

---

## [2026-08-19T20:28:12.105000+08:00] ASSISTANT


好的，发送 `ide.js` **第 3 段（最后一段）**，包含：UI 核心、文件树、初始化、以及最终的导出。

```javascript
// ============================================================
// ide.js 第 3 段（最终段）
// ============================================================

// ===================== UI 核心 =====================
const ui = {
    // 缓存 DOM
    cacheDom: function() {
        dom.statusText = document.getElementById('status-text');
        dom.filepathEl = document.getElementById('filepath');
        dom.treeEl = document.getElementById('tree');
        dom.sidebarEl = document.getElementById('sidebar');
        dom.mainEl = document.getElementById('main');
        dom.sidebarResizer = document.getElementById('sidebar-resizer');
        dom.btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
        dom.sidebarDrawer = document.getElementById('sidebar-drawer');
        dom.presenceList = document.getElementById('presence-list');
        dom.emptyState = document.getElementById('empty-state');
        dom.editorHost = document.getElementById('editor-host');
        dom.editorFrame = document.getElementById('editor-frame');
        dom.monacoContainer = document.getElementById('monaco-editor');
        dom.codeEl = document.getElementById('code');
        dom.gutterEl = document.getElementById('gutter');
        dom.codeOverlay = document.getElementById('code-overlay');
        dom.bottomDock = document.getElementById('bottom-dock');
        dom.dockResizer = document.getElementById('dock-resizer');
        dom.dockClose = document.getElementById('dock-close');
        dom.dockPin = document.getElementById('dock-pin');
        dom.dockGrip = document.getElementById('dock-grip');
        dom.consoleStatus = document.getElementById('console-status');
        dom.consoleOutput = document.getElementById('console-output');
        dom.consoleInput = document.getElementById('console-input');
        dom.consoleStop = document.getElementById('console-stop');
        dom.btnRunInConsole = document.getElementById('btn-run-in-console');
        dom.btnSendInput = document.getElementById('btn-send-input');
        dom.btnClearInput = document.getElementById('btn-clear-input');
        dom.btnPanel = document.getElementById('btn-panel');
        dom.btnFre = document.getElementById('btn-fre');
        dom.btnExport = document.getElementById('btn-export');
        dom.btnBackup = document.getElementById('btn-backup');
        dom.btnUpload = document.getElementById('btn-upload');
        dom.btnTT = document.getElementById('btn-tt');
        dom.btnAddProblem = document.getElementById('btn-add-problem');
        dom.uploadInput = document.getElementById('upload-input');
        dom.uploadZipInput = document.getElementById('upload-zip-input');
        dom.editorModeSelect = document.getElementById('editor-mode-select');
        dom.toastContainer = document.getElementById('toast-container');
        dom.cphBadge = document.getElementById('cph-badge');
        dom.cphRunAll = document.getElementById('cph-run-all');
        dom.cphAdd = document.getElementById('cph-add');
        dom.cphSaveAll = document.getElementById('cph-save-all');
        dom.cphZip = document.getElementById('cph-zip');
        dom.judgeVerdict = document.getElementById('cph-verdict');
        dom.judgeSummary = document.getElementById('cph-summary');
        dom.judgeBody = document.getElementById('cph-list');
        dom.dFontDecrease = document.getElementById('d-font-decrease');
        dom.dFontReset = document.getElementById('d-font-reset');
        dom.dFontIncrease = document.getElementById('d-font-increase');
        dom.btnTemplates = document.getElementById('btn-templates');
        dom.templateModal = document.getElementById('template-modal');
        dom.tmplExt = document.getElementById('tmpl-ext');
        dom.tmplContent = document.getElementById('tmpl-content');
        dom.tmplLoad = document.getElementById('tmpl-load');
        dom.tmplSave = document.getElementById('tmpl-save');
        dom.tmplDelete = document.getElementById('tmpl-delete');
        dom.tmplClose = document.getElementById('tmpl-close');
        dom.splitLeft = document.getElementById('split-left');
        dom.splitRight = document.getElementById('split-right');
        dom.splitDivider = document.getElementById('split-divider');
        dom.splitClose = document.getElementById('split-close');
        dom.splitRightClose = document.getElementById('split-right-close');
        dom.splitLeftLabel = document.getElementById('split-left-label');
        dom.splitRightLabel = document.getElementById('split-right-label');
        dom.splitRightEditorWrap = document.getElementById('split-right-editor-wrap');
        dom.splitRightMonaco = document.getElementById('split-right-monaco');
        dom.splitRightPreview = document.getElementById('split-right-preview');
        dom.mdToolbar = document.getElementById('md-toolbar');
        dom.mdEditorWrap = document.getElementById('md-editor-wrap');
        dom.mdContainer = document.getElementById('md-container');
        dom.problemsSummary = document.getElementById('problems-summary');
        dom.problemsBadge = document.getElementById('problems-badge');
        dom.problemsList = document.getElementById('problems-list');
        dom.dErrCount = document.getElementById('d-err-count');
        dom.dWarnCount = document.getElementById('d-warn-count');
        dom.dProblemsBtn = document.getElementById('d-problems');
        dom.dCursorPos = document.getElementById('d-cursor-pos');
        dom.dSwitchIntellisense = document.getElementById('d-switch-intellisense');
        dom.dSwitchRemoteCursor = document.getElementById('d-switch-remote-cursor');
        dom.dFrame = document.getElementById('d-frame');
        dom.problemsClear = document.getElementById('problems-clear');
        dom.exportCode = document.getElementById('export-code');
        dom.exportTests = document.getElementById('export-tests');
        dom.importZip = document.getElementById('import-zip');
        dom.importFromFile = document.getElementById('import-from-file');
        dom.cphBadge = document.getElementById('cph-badge');
    },

    // ===== 状态栏（D 框）=====
    updateDFrameCursorPos: function() {
        if (!dom.dCursorPos) return;
        let line = 1, col = 1;
        if (state.currentEditorType === 'textarea') {
            const before = dom.codeEl.value.slice(0, dom.codeEl.selectionStart);
            const lines = before.split('\n');
            line = lines.length;
            col = lines[lines.length - 1].length + 1;
        } else if (state.monacoEditor) {
            const pos = state.monacoEditor.getPosition();
            if (pos) { line = pos.lineNumber; col = pos.column; }
        }
        dom.dCursorPos.textContent = '行 ' + line + ', 列 ' + col;
    },

    updateDFrameProblemCount: function() {
        if (!dom.dErrCount || !dom.dWarnCount) return;
        const errors = state.problemList.filter(function(p) { return p.severity === 1; }).length;
        const warnings = state.problemList.filter(function(p) { return p.severity === 2; }).length;
        dom.dErrCount.textContent = '✕ ' + errors;
        dom.dWarnCount.textContent = '⚠ ' + warnings;
    },

    initDFrame: function() {
        ui.applyIntellisenseState();
        ui.applyRemoteCursorState();
        ui.updateDFrameCursorPos();
        ui.updateDFrameProblemCount();

        [ [dom.dSwitchIntellisense, toggleIntellisense],
          [dom.dSwitchRemoteCursor, toggleRemoteCursorVisibility] ].forEach(function(pair) {
            var el = pair[0], fn = pair[1];
            el.addEventListener('click', fn);
            el.addEventListener('keydown', function(e) {
                if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); fn(); }
            });
        });

        dom.dProblemsBtn.addEventListener('click', function() { ui.openDock('problems'); });
        dom.dFontDecrease.addEventListener('click', font.decrease);
        dom.dFontIncrease.addEventListener('click', font.increase);
        dom.dFontReset.addEventListener('click', font.reset);
    },

    applyIntellisenseState: function() {
        var on = state.intellisenseEnabled;
        var el = dom.dSwitchIntellisense;
        el.classList.toggle('on', on);
        el.setAttribute('aria-checked', on ? 'true' : 'false');
        if (state.monacoEditor) {
            state.monacoEditor.updateOptions({
                quickSuggestions: on ? { other: true, comments: false, strings: false } : false,
                suggestOnTriggerCharacters: on,
                parameterHints: { enabled: on }
            });
        }
    },

    applyRemoteCursorState: function() {
        var on = state.remoteCursorsVisible;
        var el = dom.dSwitchRemoteCursor;
        el.classList.toggle('on', on);
        el.setAttribute('aria-checked', on ? 'true' : 'false');
        renderRemoteCursors();
    },

    // ===== 标签页 =====
    updateTabDirty: function(path) {
        document.querySelectorAll('#editor-tabs .etab').forEach(function(tab) {
            if (tab.dataset.path === path) {
                var dot = tab.querySelector('.etab-dot');
                if (dot) dot.classList.toggle('show', state.dirtySet.has(path));
            }
        });
    },

    renderEditorTabs: function() {
        var bar = document.getElementById('editor-tabs');
        var wrap = document.getElementById('editor-tabs-wrap');
        bar.innerHTML = '';
        state.openTabs.forEach(function(p) {
            var tab = document.createElement('div');
            tab.className = 'etab' + (p === state.currentFile ? ' active' : '');
            tab.draggable = true;
            tab.dataset.path = p;
            tab.title = p;
            var name = document.createElement('span');
            name.className = 'etab-name';
            name.textContent = p.split('/').pop();
            var dot = document.createElement('span');
            dot.className = 'etab-dot' + (state.dirtySet.has(p) ? ' show' : '');
            var close = document.createElement('span');
            close.className = 'etab-close';
            close.textContent = '×';
            close.title = '关闭';
            tab.appendChild(name);
            tab.appendChild(dot);
            tab.appendChild(close);
            tab.addEventListener('click', function() { if (p !== state.currentFile) ui.switchEditorTab(p); });
            close.addEventListener('click', function(e) { e.stopPropagation(); ui.closeEditorTab(p); });
            tab.addEventListener('dragstart', function(e) {
                e.dataTransfer.setData('text/plain', p);
                e.dataTransfer.effectAllowed = 'move';
                state.dragPath = p;
                tab.classList.add('dragging');
            });
            tab.addEventListener('dragend', function() {
                state.dragPath = null;
                tab.classList.remove('dragging');
                document.querySelectorAll('#editor-tabs .etab').forEach(function(t) { t.classList.remove('drag-over-left'); });
            });
            tab.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.dataTransfer.dropEffect = 'move';
                document.querySelectorAll('#editor-tabs .etab').forEach(function(t) { t.classList.remove('drag-over-left'); });
                tab.classList.add('drag-over-left');
            });
            tab.addEventListener('dragleave', function() { tab.classList.remove('drag-over-left'); });
            tab.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                document.querySelectorAll('#editor-tabs .etab').forEach(function(t) { t.classList.remove('drag-over-left'); });
                var from = e.dataTransfer.getData('text/plain') || state.dragPath;
                if (from && from !== p) {
                    var fromIdx = state.openTabs.indexOf(from);
                    if (fromIdx !== -1) {
                        state.openTabs.splice(fromIdx, 1);
                        var toIdx = state.openTabs.indexOf(p);
                        state.openTabs.splice(toIdx, 0, from);
                    }
                }
                ui.renderEditorTabs();
            });
            bar.appendChild(tab);
        });
        var spacer = document.createElement('div');
        spacer.className = 'etab-spacer';
        spacer.addEventListener('dragover', function(e) { e.preventDefault();
            e.dataTransfer.dropEffect = 'move'; });
        spacer.addEventListener('drop', function(e) {
            e.preventDefault();
            var from = e.dataTransfer.getData('text/plain') || state.dragPath;
            if (from) {
                var fromIdx = state.openTabs.indexOf(from);
                if (fromIdx !== -1) { state.openTabs.splice(fromIdx, 1);
                    state.openTabs.push(from); }
            }
            ui.renderEditorTabs();
        });
        bar.appendChild(spacer);
        wrap.style.display = state.openTabs.length ? 'flex' : 'none';
    },

    switchEditorTab: function(path) {
        if (path === state.currentFile) return;
        clearTimeout(state.saveTimer);
        if (state.currentFile) {
            state.fileContentCache[state.currentFile] = editor.getContent();
            if (state.dirtySet.has(state.currentFile)) editor.persistFile(state.currentFile);
            state.socket.emit('leave', { path: state.currentFile });
            state.socket.emit('run_stop', {});
        }
        ui.activateFile(path);
    },

    closeEditorTab: function(path) {
        var idx = state.openTabs.indexOf(path);
        if (idx === -1) return;
        if (state.dirtySet.has(path)) {
            utils.showConfirm('文件「' + path.split('/').pop() + '」有未保存的修改，保存并关闭吗？', function() {
                editor.persistFile(path);
                ui.doCloseTab(path);
            });
        } else {
            ui.doCloseTab(path);
        }
    },

    doCloseTab: function(path) {
        var idx = state.openTabs.indexOf(path);
        if (idx === -1) return;
        state.openTabs.splice(idx, 1);
        state.dirtySet.delete(path);
        delete state.fileContentCache[path];
        if (path === state.currentFile) {
            state.socket.emit('leave', { path: path });
            state.socket.emit('run_stop', {});
            var next = state.openTabs[Math.min(idx, state.openTabs.length - 1)];
            if (next) {
                ui.activateFile(next);
            } else {
                state.currentFile = null;
                dom.editorHost.style.display = 'none';
                dom.emptyState.style.display = 'flex';
                dom.filepathEl.textContent = '';
                dom.btnPanel.disabled = true;
                dom.btnFre.disabled = true;
                dom.btnExport.disabled = true;
                dom.btnBackup.disabled = true;
                dom.btnRunInConsole.disabled = true;
                state.problemList = [];
                ui.renderProblems();
                ui.renderEditorTabs();
            }
        } else {
            ui.renderEditorTabs();
        }
    },

    handleFileDeleted: function(path) {
        utils.showToast('文件「' + path.split('/').pop() + '」已被删除', 'info', 4000);
        var idx = state.openTabs.indexOf(path);
        if (idx !== -1) state.openTabs.splice(idx, 1);
        state.dirtySet.delete(path);
        delete state.fileContentCache[path];
        if (path === state.currentFile) {
            var next = state.openTabs[Math.min(idx, state.openTabs.length - 1)];
            if (next) {
                ui.activateFile(next);
            } else {
                state.currentFile = null;
                dom.editorHost.style.display = 'none';
                dom.emptyState.style.display = 'flex';
                dom.filepathEl.textContent = '';
                dom.btnPanel.disabled = true;
                dom.btnFre.disabled = true;
                dom.btnExport.disabled = true;
                dom.btnBackup.disabled = true;
                dom.btnRunInConsole.disabled = true;
                state.problemList = [];
                ui.renderProblems();
            }
        }
        ui.renderEditorTabs();
        loadTree();
    },

    activateFile: function(path) {
        state.currentFile = path;
        ot.reset();
        for (var sid in state.remoteWidgets) {
            if (state.monacoEditor) {
                try { state.monacoEditor.removeContentWidget(state.remoteWidgets[sid]); } catch (e) {}
            }
        }
        state.remoteWidgets = {};
        state.remoteCursors = {};
        dom.filepathEl.textContent = path;
        dom.emptyState.style.display = 'none';
        dom.editorHost.style.display = 'flex';
        document.querySelectorAll('.tree-item').forEach(function(el) {
            el.classList.toggle('active', el.dataset.path === path);
        });
        state.applyingRemote = true;
        editor.setContent(state.fileContentCache[path] || '');
        state.applyingRemote = false;
        if (['c', 'cpp', 'cc', 'cxx', 'h', 'hpp', 'hh'].indexOf(utils.extOf(path)) >= 0) {
            state.socket.emit('lsp_open', { path: path, text: utils.normalizeContent(editor.getContent()) });
        }
        if (state.monacoEditor) {
            monaco.editor.setModelLanguage(state.monacoEditor.getModel(), utils.langForExt(utils.extOf(path)));
        }
        if (state.currentEditorType === 'textarea') editor.updateGutter();
        state.dirty = state.dirtySet.has(path);
        dom.btnBackup.disabled = false;
        dom.btnPanel.disabled = false;
        dom.btnFre.disabled = ['c', 'cpp', 'cc', 'cxx'].indexOf(utils.extOf(path)) < 0;
        dom.btnExport.disabled = false;
        var baseName = path.split('/').pop().replace(/\.[^.]+$/, '');
        state.freEnabled = editor.getContent().indexOf('freopen("' + baseName + '.in') >= 0;
        dom.btnFre.textContent = state.freEnabled ? 'fre ON' : 'fre OFF';
        dom.btnFre.classList.toggle('active', state.freEnabled);
        dom.consoleOutput.textContent = '';
        dom.consoleStatus.textContent = '空闲';
        dom.consoleInput.value = '';
        dom.consoleInput.disabled = true;
        dom.consoleStop.disabled = true;
        dom.btnRunInConsole.disabled = false;
        dom.btnSendInput.disabled = true;
        state.socket.emit('join', { path: path, username: state.username, device: deviceLabel() });
        state.problemList = [];
        ui.renderProblems();
        ui.loadCPH(path);
        ui.renderEditorTabs();
        markdown.setupForCurrentFile();
    },

    // ===== CPH =====
    loadCPH: function(path) {
        if (!path || !utils.isJudgeableExt(utils.extOf(path))) {
            state.cphTestCases = [];
            dom.cphRunAll.disabled = true;
            dom.cphAdd.disabled = true;
            dom.cphSaveAll.disabled = true;
            dom.cphZip.disabled = true;
            ui.renderCPH();
            return;
        }
        dom.cphAdd.disabled = false;
        dom.cphSaveAll.disabled = false;
        dom.cphRunAll.disabled = false;
        dom.cphZip.disabled = false;
        var seq = ++state.cphLoadSeq;
        fetch('/api/tests?path=' + encodeURIComponent(path)).then(function(res) { return res.json(); })
            .then(function(tests) {
                if (seq !== state.cphLoadSeq || path !== state.currentFile) return;
                state.cphTestCases = tests;
                state.cphTestCases.forEach(function(tc) {
                    var m = tc.name.match(/(\d+)/);
                    tc.num = m ? parseInt(m[1]) : 0;
                });
                state.cphTestCases.sort(function(a, b) { return a.num - b.num; });
                ui.renderCPH();
            }).catch(function() {
                if (seq !== state.cphLoadSeq || path !== state.currentFile) return;
                state.cphTestCases = [];
                ui.renderCPH();
            });
    },

    renderCPH: function() {
        dom.judgeBody.innerHTML = '';
        var results = state.cphTestCases.filter(function(tc) { return tc.verdict; });
        var acCount = results.filter(function(tc) { return tc.verdict === 'AC'; }).length;
        var totalCount = results.length;
        if (totalCount > 0) {
            var allAc = acCount === totalCount && totalCount === state.cphTestCases.length;
            dom.judgeVerdict.textContent = allAc ? 'AC' :
                results.some(function(tc) { return tc.verdict === 'WA'; }) ? 'WA' :
                results.some(function(tc) { return tc.verdict === 'TLE'; }) ? 'TLE' :
                results.some(function(tc) { return tc.verdict === 'RE'; }) ? 'RE' : '—';
            dom.judgeVerdict.className = 'v-' + dom.judgeVerdict.textContent.toLowerCase();
            dom.judgeSummary.textContent = acCount + '/' + totalCount + ' passed';
            ui.setCphBadge(true, acCount + '/' + totalCount, allAc ? 'ac' : (acCount < totalCount ? 'wa' : ''));
        } else {
            dom.judgeVerdict.textContent = '—';
            dom.judgeVerdict.className = 'v-pending';
            dom.judgeSummary.textContent = state.cphTestCases.length + ' 个测试点';
            ui.setCphBadge(state.cphTestCases.length > 0, state.cphTestCases.length + ' 个', '');
        }
        if (state.cphTestCases.length === 0) {
            dom.judgeBody.innerHTML =
                '<div id="cph-empty">暂无测试点<br><span style="font-size:11px">点击「+ 添加测试点」或上传 zip 测试包</span></div>';
            return;
        }
        for (var i = 0; i < state.cphTestCases.length; i++) {
            var tc = state.cphTestCases[i];
            var row = document.createElement('div');
            row.className = 'tc-row';
            row.dataset.num = tc.num;
            var vClass = tc.verdict ? 'v-' + tc.verdict.toLowerCase() : '';
            var actualClass = tc.verdict === 'WA' ? 'wa' : tc.verdict === 'AC' ? 'ac' : '';
            var html = '<div class="tc-num">#' + tc.num + '</div>';
            html += '<div class="tc-io"><label>Input</label><textarea class="tc-input" rows="2">' +
                utils.escapeHtml(tc.input || '') + '</textarea></div>';
            html += '<div class="tc-io"><label>Expected</label><textarea class="tc-expected" rows="2">' +
                utils.escapeHtml(tc.expected || '') + '</textarea></div>';
            html += '<div class="tc-verdict ' + vClass + '">' + utils.escapeHtml(tc.verdict || '—') + '</div>';
            html += '<div class="tc-time">' + (tc.time_ms ? tc.time_ms + 'ms' : '—') +
                '<span class="tc-mem">' + (tc.mem_kb ? (tc.mem_kb >= 1024 ? (tc.mem_kb / 1024).toFixed(1) + 'MB' : tc
                    .mem_kb + 'KB') : '') + '</span></div>';
            html += '<div class="tc-actions">';
            html += '<button class="run" title="运行此测试点">▶</button>';
            html += '<button class="open-in" title="在工作区打开 .in 文件">in</button>';
            html += '<button class="open-out" title="在工作区打开 .out 文件">out</button>';
            html += '<button class="del" title="删除此测试点">🗑</button>';
            html += '</div>';
            if (tc.actual !== undefined) {
                html += '<div class="tc-io" style="grid-column:2/-1"><label>Actual Output</label>' +
                    '<textarea class="actual ' + actualClass + '" rows="2" readonly>' +
                    utils.escapeHtml(tc.actual || '') + '</textarea></div>';
            }
            if (tc.stderr) {
                html += '<div class="tc-stderr">' + utils.escapeHtml(tc.stderr) + '</div>';
            }
            row.innerHTML = html;
            row.querySelector('.run').addEventListener('click', function() {
                ui.runSingleCPH(parseInt(this.closest('.tc-row').dataset.num));
            });
            row.querySelector('.del').addEventListener('click', function() {
                ui.deleteCPH(parseInt(this.closest('.tc-row').dataset.num));
            });
            row.querySelector('.open-in').addEventListener('click', function() {
                var num = parseInt(this.closest('.tc-row').dataset.num);
                ui.openTestFile(num, 'in');
            });
            row.querySelector('.open-out').addEventListener('click', function() {
                var num = parseInt(this.closest('.tc-row').dataset.num);
                ui.openTestFile(num, 'out');
            });
            row.querySelector('.tc-input').addEventListener('blur', function() {
                var num = parseInt(this.closest('.tc-row').dataset.num);
                ui.saveCPHField(num, 'in', this.value);
            });
            row.querySelector('.tc-expected').addEventListener('blur', function() {
                var num = parseInt(this.closest('.tc-row').dataset.num);
                ui.saveCPHField(num, 'out', this.value);
            });
            dom.judgeBody.appendChild(row);
        }
    },

    setCphBadge: function(visible, text, cls) {
        dom.cphBadge.style.display = visible ? 'inline-block' : 'none';
        dom.cphBadge.textContent = text;
        dom.cphBadge.className = 'badge' + (cls ? ' ' + cls : '');
    },

    runSingleCPH: function(num) {
        if (!state.currentFile || state.cphRunning) return;
        var tc = state.cphTestCases.find(function(t) { return t.num === num; });
        if (!tc) return;
        state.cphRunning = true;
        ui.syncCPHFromDOM();
        ui.saveCPHField(num, 'in', tc.input || '');
        ui.saveCPHField(num, 'out', tc.expected || '');
        tc.verdict = '...';
        tc.actual = undefined;
        tc.stderr = undefined;
        tc.time_ms = 0;
        ui.renderCPH();
        fetch('/api/test/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: state.currentFile, num: num })
        }).then(function(res) { return res.json(); }).then(function(result) {
            tc.verdict = result.verdict;
            tc.actual = result.actual;
            tc.stderr = result.stderr;
            tc.time_ms = result.time_ms;
            tc.mem_kb = result.mem_kb;
            ui.renderCPH();
        }).catch(function() {
            tc.verdict = 'RE';
            tc.stderr = '请求失败';
            ui.renderCPH();
        }).finally(function() { state.cphRunning = false; });
    },

    syncCPHFromDOM: function() {
        document.querySelectorAll('.tc-row').forEach(function(row) {
            var num = parseInt(row.dataset.num);
            var tc = state.cphTestCases.find(function(t) { return t.num === num; });
            if (tc) {
                var inp = row.querySelector('.tc-input');
                var exp = row.querySelector('.tc-expected');
                if (inp) tc.input = inp.value;
                if (exp) tc.expected = exp.value;
            }
        });
    },

    deleteCPH: function(num) {
        if (!state.currentFile) return;
        fetch('/api/test/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: state.currentFile, num: num })
        }).then(function(res) { return res.json(); }).then(function(data) {
            if (data.ok) {
                utils.showToast('已删除测试点 #' + num, 'info');
                ui.loadCPH(state.currentFile);
            }
        }).catch(function() { utils.showToast('请求失败', 'error'); });
    },

    openTestFile: function(num, ext) {
        if (!state.currentFile) return;
        var base = state.currentFile.replace(/\.[^.]+$/, '');
        ui.openFile(base + '_T/' + num + '.' + ext);
    },

    saveCPHField: function(num, ext, content) {
        if (!state.currentFile) return;
        var base = state.currentFile.replace(/\.[^.]+$/, '');
        var path = base + '_T/' + num + '.' + ext;
        fetch('/api/test/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path, content: content })
        }).catch(function() {});
    },

    renderJudgeResult: function(result) {
        ui.syncCPHFromDOM();
        if (result.error) {
            dom.judgeVerdict.textContent = '—';
            dom.judgeVerdict.className = 'v-pending';
            dom.judgeSummary.textContent = result.error;
            return;
        }
        if (result.verdict === 'CE') {
            dom.judgeVerdict.textContent = 'CE';
            dom.judgeVerdict.className = 'v-ce';
            dom.judgeSummary.textContent = 'Compile Error';
            dom.judgeBody.innerHTML = '<pre style="color:var(--err);white-space:pre-wrap;padding:10px;">' +
                utils.escapeHtml(result.compile_error || '') + '</pre>';
            return;
        }
        if (result.cases) {
            for (var i = 0; i < result.cases.length; i++) {
                var c = result.cases[i];
                var m = c.case.match(/(\d+)/);
                var num = m ? parseInt(m[1]) : 0;
                var tc = state.cphTestCases.find(function(t) { return t.num === num; });
                if (tc) {
                    tc.verdict = c.verdict;
                    tc.actual = c.actual;
                    tc.stderr = c.stderr;
                    tc.time_ms = c.time_ms;
                    tc.mem_kb = c.mem_kb;
                }
            }
        }
        ui.renderCPH();
    },

    // ===== 问题面板 =====
    renderProblems: function() {
        ui.updateDFrameProblemCount();
        if (state.problemList.length === 0) {
            dom.problemsSummary.textContent = '';
            dom.problemsBadge.style.display = 'none';
            dom.problemsList.innerHTML = '<div id="problems-empty">没有检测到代码问题</div>';
            editor.updateCodeOverlay();
            return;
        }
        var errors = state.problemList.filter(function(p) { return p.severity === 1; }).length;
        var warnings = state.problemList.filter(function(p) { return p.severity === 2; }).length;
        var others = state.problemList.length - errors - warnings;
        var parts = [];
        if (errors) parts.push(errors + ' 个错误');
        if (warnings) parts.push(warnings + ' 个警告');
        if (others) parts.push(others + ' 个其他');
        dom.problemsSummary.textContent = parts.join(' · ');
        if (errors > 0) {
            dom.problemsBadge.style.display = 'inline-block';
            dom.problemsBadge.textContent = errors;
            dom.problemsBadge.className = 'badge error';
        } else if (warnings > 0) {
            dom.problemsBadge.style.display = 'inline-block';
            dom.problemsBadge.textContent = warnings;
            dom.problemsBadge.className = 'badge warning';
        } else {
            dom.problemsBadge.style.display = 'inline-block';
            dom.problemsBadge.textContent = others;
            dom.problemsBadge.className = 'badge';
        }
        var sevLabel = { 1: 'E', 2: 'W', 3: 'I', 4: 'H' };
        var sevClass = { 1: 'error', 2: 'warning', 3: 'info', 4: 'hint' };
        var fileName = state.currentFile ? state.currentFile.split('/').pop() : '';
        dom.problemsList.innerHTML = '';
        state.problemList.forEach(function(p) {
            var rangeText = (p.endLine && p.endColumn && (p.endLine !== p.line || p.endColumn !== p.column)) ?
                p.line + ':' + p.column + ' - ' + p.endLine + ':' + p.endColumn :
                p.line + ':' + p.column;
            var meta = [];
            if (p.source) meta.push(p.source);
            if (p.code !== undefined && p.code !== null && p.code !== '') meta.push(String(p.code));
            var metaText = meta.length ? '  [' + meta.join(': ') + ']' : '';
            var row = document.createElement('div');
            row.className = 'prob-row';
            row.title = p.message + (meta.length ? ' [' + meta.join(': ') + ']' : '');
            row.innerHTML = '<span class="prob-sev ' + (sevClass[p.severity] || 'hint') + '">' +
                (sevLabel[p.severity] || 'H') + '</span>' +
                '<div class="prob-body">' +
                '<div class="prob-msg">' + utils.escapeHtml(p.message) + '</div>' +
                '<div class="prob-loc">' + utils.escapeHtml(fileName) + ':' + rangeText +
                utils.escapeHtml(metaText) + '</div></div>';
            row.addEventListener('click', function() { ui.gotoProblem(p); });
            dom.problemsList.appendChild(row);
        });
        editor.updateCodeOverlay();
    },

    gotoProblem: function(p) {
        if (!p) return;
        if (state.monacoEditor) {
            state.monacoEditor.revealLineInCenter(p.line);
            state.monacoEditor.setPosition({ lineNumber: p.line, column: Math.max(1, p.column) });
            state.monacoEditor.focus();
        } else if (state.currentEditorType === 'textarea') {
            var lines = dom.codeEl.value.split('\n');
            var offset = 0;
            for (var i = 0; i < p.line - 1 && i < lines.length; i++) offset += lines[i].length + 1;
            offset += Math.max(0, p.column - 1);
            dom.codeEl.focus();
            dom.codeEl.setSelectionRange(offset, offset);
            var lineHeight = parseFloat(getComputedStyle(dom.codeEl).lineHeight) || 21;
            dom.codeEl.scrollTop = Math.max(0, (p.line - 1) * lineHeight);
        }
    },

    // ===== Dock 面板 =====
    openDock: function(tab) {
        dom.bottomDock.classList.add('open');
        dom.bottomDock.classList.remove('minimized');
        ui.switchDockTab(tab);
    },

    switchDockTab: function(tab) {
        state.activeTab = tab;
        document.querySelectorAll('.dock-tab').forEach(function(t) {
            t.classList.toggle('active', t.dataset.tab === tab);
        });
        document.querySelectorAll('.dock-pane').forEach(function(p) {
            p.classList.toggle('active', p.id === 'pane-' + tab);
        });
    },

    applyDockMode: function() {
        var isPermanent = state.dockMode === 'permanent';
        dom.bottomDock.classList.toggle('floating', !isPermanent);
        dom.bottomDock.classList.toggle('permanent', isPermanent);
        dom.dockPin.textContent = isPermanent ? '📌' : '📍';
        dom.dockPin.classList.toggle('active', isPermanent);
        dom.dockPin.title = isPermanent ? '常驻模式 - 点击切换为浮动' : '浮动模式 - 点击切换为常驻';
        dom.dockClose.title = isPermanent ? '最小化(常驻模式不会完全关闭)' : '关闭面板';
        if (isPermanent) {
            dom.bottomDock.classList.add('open');
        }
    },

    setDockMode: function(mode) {
        state.dockMode = mode;
        localStorage.setItem('dock-mode', mode);
        dom.bottomDock.classList.remove('minimized');
        dom.bottomDock.style.left = '';
        dom.bottomDock.style.top = '';
        dom.bottomDock.style.right = '';
        dom.bottomDock.style.bottom = '';
        dom.bottomDock.style.width = '';
        ui.applyDockMode();
    },

    isPanelOpen: function() {
        return dom.bottomDock.classList.contains('open') && !dom.bottomDock.classList.contains('minimized');
    },

    closeDock: function() {
        if (state.dockMode === 'permanent') {
            dom.bottomDock.classList.add('minimized');
        } else {
            state.socket.emit('run_stop', {});
            dom.bottomDock.classList.remove('open');
        }
    },

    // ===== 打开文件 =====
    openFile: function(path, rowEl) {
        document.querySelectorAll('.tree-item').forEach(function(el) { el.classList.remove('active'); });
        if (rowEl) rowEl.classList.add('active');
        if (state.currentFile && state.currentFile !== path) {
            clearTimeout(state.saveTimer);
            state.fileContentCache[state.currentFile] = editor.getContent();
            if (state.dirtySet.has(state.currentFile)) editor.persistFile(state.currentFile);
            state.socket.emit('leave', { path: state.currentFile });
            state.socket.emit('run_stop', {});
        }
        if (state.openTabs.indexOf(path) === -1) state.openTabs.push(path);
        if (state.fileContentCache[path] === undefined) {
            fetch('/api/file?path=' + encodeURIComponent(path)).then(function(res) { return res.json(); })
                .then(function(data) {
                    if (data.error) {
                        state.openTabs.splice(state.openTabs.indexOf(path), 1);
                        ui.renderEditorTabs();
                        utils.showToast('打开失败: ' + data.error, 'error');
                        return;
                    }
                    if (data.binary) {
                        state.openTabs.splice(state.openTabs.indexOf(path), 1);
                        ui.renderEditorTabs();
                        editor.setContent('');
                        dom.editorHost.style.display = 'none';
                        dom.emptyState.style.display = 'flex';
                        ui.renderBinaryPreview(path, data);
                        dom.btnPanel.disabled = true;
                        dom.btnFre.disabled = true;
                        dom.btnExport.disabled = true;
                        dom.btnBackup.disabled = true;
                        dom.btnRunInConsole.disabled = true;
                        return;
                    }
                    state.fileContentCache[path] = data.content || '';
                    ui.activateFile(path);
                });
            return;
        }
        ui.activateFile(path);
    },

    renderBinaryPreview: function(path, data) {
        var mime = data.mime || 'application/octet-stream';
        var name = path.split('/').pop();
        var ext = name.includes('.') ? name.split('.').pop().toUpperCase() : '';
        dom.filepathEl.textContent = path;
        var rawUrl = utils.rawFileUrl(path, false);
        var kind = mime.startsWith('image/') ? 'image' :
            mime.startsWith('video/') ? 'video' :
            mime.startsWith('audio/') ? 'audio' :
            (mime === 'application/pdf') ? 'pdf' : 'other';
        var bodyHtml = '';
        if (kind === 'image') {
            bodyHtml = '<div class="img-canvas" id="img-canvas">' +
                '<img src="' + rawUrl + '" alt="' + utils.escapeHtml(name) +
                '" id="img-canvas-el" draggable="false" />' +
                '</div>' +
                '<div class="img-canvas-toolbar" id="img-canvas-toolbar">' +
                '<button id="img-zoom-out" title="缩小">−</button>' +
                '<span class="zoom-pct" id="img-zoom-pct">100%</span>' +
                '<button id="img-zoom-in" title="放大">＋</button>' +
                '<span class="sep"></span>' +
                '<button id="img-zoom-reset" title="重置视图 (适应窗口)">⟲</button>' +
                '</div>';
        } else if (kind === 'video') {
            bodyHtml = '<video src="' + rawUrl + '" controls preload="metadata" muted></video>';
        } else if (kind === 'audio') {
            bodyHtml = '<audio src="' + rawUrl + '" controls preload="metadata"></audio>';
        } else if (kind === 'pdf') {
            bodyHtml = '<iframe src="' + rawUrl + '" title="pdf-preview"></iframe>';
        } else {
            bodyHtml = '<div class="binary-unsupported">' +
                '<span class="big-icon">📦</span>' +
                '<div class="hint-title">「' + utils.escapeHtml(ext || 'BIN') + '」类型文件暂不支持在线预览</div>' +
                '<div>可下载到本地后使用对应软件打开</div>' +
                '</div>';
        }
        var metaBits = [mime];
        if (data.size !== null && data.size !== undefined) metaBits.push(utils.formatSize(data.size));
        dom.emptyState.innerHTML = '<div class="binary-preview">' +
            '<div class="binary-toolbar">' +
            '<span class="binary-name" title="' + utils.escapeHtml(path) + '">' + utils.escapeHtml(name) + '</span>' +
            '<span class="binary-meta">' + metaBits.join(' · ') + '</span>' +
            '<span class="spacer"></span>' +
            '<button class="btn" id="btn-binary-open">新窗口打开</button>' +
            '<button class="btn primary" id="btn-binary-download">下载</button>' +
            '</div>' +
            '<div class="binary-body" style="' + (kind === 'image' ? 'position:relative;padding:0;' : '') + '">' +
            bodyHtml + '</div></div>';
        var img = dom.emptyState.querySelector('#img-canvas-el');
        if (img) {
            img.addEventListener('error', function() {
                var canvas = dom.emptyState.querySelector('#img-canvas');
                var toolbar = dom.emptyState.querySelector('#img-canvas-toolbar');
                if (toolbar) toolbar.remove();
                if (canvas) canvas.outerHTML =
                    '<div class="binary-unsupported"><span class="big-icon">⚠</span><div class="hint-title">预览加载失败, 文件可能已损坏</div><div>可尝试下载后查看</div></div>';
            });
            ui.initImageCanvas(img);
        }
        document.getElementById('btn-binary-download').addEventListener('click', function() {
            var a = document.createElement('a');
            a.href = utils.rawFileUrl(path, true);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            utils.showToast('开始下载: ' + path.split('/').pop(), 'info', 2000);
        });
        document.getElementById('btn-binary-open').addEventListener('click', function() {
            window.open(utils.rawFileUrl(path, false), '_blank');
        });
    },

    initImageCanvas: function(img) {
        var canvas = document.getElementById('img-canvas');
        var toolbar = document.getElementById('img-canvas-toolbar');
        if (!canvas || !toolbar) return;
        var zoomPctEl = document.getElementById('img-zoom-pct');
        var btnIn = document.getElementById('img-zoom-in');
        var btnOut = document.getElementById('img-zoom-out');
        var btnReset = document.getElementById('img-zoom-reset');
        var fitScale = 1, scale = 1, tx = 0, ty = 0;
        var naturalW = 0, naturalH = 0, ready = false, userAdjusted = false;

        function clampScale(s) { return Math.min(16, Math.max(0.05, s)); }

        function computeFit() {
            var cw = canvas.clientWidth,
                ch = canvas.clientHeight;
            if (!naturalW || !naturalH || !cw || !ch) { fitScale = 1; return; }
            fitScale = Math.min(cw / naturalW, ch / naturalH, 1) || 1;
            if (fitScale <= 0) fitScale = 1;
        }

        function applyTransform() {
            img.style.transform = 'translate(' + tx + 'px, ' + ty + 'px) scale(' + scale + ')';
            if (zoomPctEl) zoomPctEl.textContent = Math.round(scale * 100) + '%';
            if (btnIn) btnIn.disabled = scale >= 16 - 1e-6;
            if (btnOut) btnOut.disabled = scale <= 0.05 + 1e-6;
        }

        function resetView() {
            computeFit();
            scale = clampScale(fitScale);
            var cw = canvas.clientWidth,
                ch = canvas.clientHeight;
            tx = (cw - naturalW * scale) / 2;
            ty = (ch - naturalH * scale) / 2;
            userAdjusted = false;
            applyTransform();
        }

        function zoomAt(anchorX, anchorY, nextScale) {
            nextScale = clampScale(nextScale);
            if (nextScale === scale) return;
            var ratio = nextScale / scale;
            tx = anchorX - (anchorX - tx) * ratio;
            ty = anchorY - (anchorY - ty) * ratio;
            scale = nextScale;
            applyTransform();
        }

        function zoomAtCenter(nextScale) {
            var cw = canvas.clientWidth,
                ch = canvas.clientHeight;
            zoomAt(cw / 2, ch / 2, nextScale);
        }

        function onImgReady() {
            naturalW = img.naturalWidth || img.width || 1;
            naturalH = img.naturalHeight || img.height || 1;
            ready = true;
            resetView();
        }

        if (img.complete && img.naturalWidth) { onImgReady(); } else {
            img.addEventListener('load', onImgReady, { once: true });
        }

        var ro = new ResizeObserver(function() { if (ready && !userAdjusted) resetView(); });
        ro.observe(canvas);
        canvas._imgCanvasCleanup = function() { ro.disconnect(); };

        btnIn.addEventListener('click', function() { if (ready) { userAdjusted = true;
                zoomAtCenter(scale * 1.25); } });
        btnOut.addEventListener('click', function() { if (ready) { userAdjusted = true;
                zoomAtCenter(scale / 1.25); } });
        btnReset.addEventListener('click', function() { if (ready) resetView(); });

        canvas.addEventListener('wheel', function(e) {
            if (!ready) return;
            e.preventDefault();
            userAdjusted = true;
            var rect = canvas.getBoundingClientRect();
            var anchorX = e.clientX - rect.left;
            var anchorY = e.clientY - rect.top;
            var factor = Math.pow(1.25, -e.deltaY / 100);
            zoomAt(anchorX, anchorY, scale * factor);
        }, { passive: false });

        var panning = false,
            panStartX = 0,
            panStartY = 0,
            panOrigTx = 0,
            panOrigTy = 0,
            activePointerId = null;
        canvas.addEventListener('pointerdown', function(e) {
            if (!ready || e.button !== 0) return;
            panning = true;
            userAdjusted = true;
            activePointerId = e.pointerId;
            panStartX = e.clientX;
            panStartY = e.clientY;
            panOrigTx = tx;
            panOrigTy = ty;
            canvas.classList.add('panning');
            canvas.setPointerCapture(e.pointerId);
            e.preventDefault();
        });
        canvas.addEventListener('pointermove', function(e) {
            if (!panning || e.pointerId !== activePointerId) return;
            tx = panOrigTx + (e.clientX - panStartX);
            ty = panOrigTy + (e.clientY - panStartY);
            applyTransform();
        });

        function endPan(e) {
            if (!panning || (e && e.pointerId !== activePointerId)) return;
            panning = false;
            canvas.classList.remove('panning');
            if (activePointerId !== null) { try { canvas.releasePointerCapture(activePointerId); } catch (_e) {} }
            activePointerId = null;
        }
        canvas.addEventListener('pointerup', endPan);
        canvas.addEventListener('pointercancel', endPan);
    },

    // ===== 侧边栏 =====
    applySidebarVisible: function() {
        var visible = localStorage.getItem('sidebar-visible') !== 'false';
        dom.mainEl.classList.toggle('sidebar-hidden', !visible);
        dom.btnToggleSidebar.title = visible ? '隐藏文件树' : '显示文件树';
    },

    toggleSidebar: function() {
        var visible = localStorage.getItem('sidebar-visible') !== 'false';
        visible = !visible;
        localStorage.setItem('sidebar-visible', visible ? 'true' : 'false');
        ui.applySidebarVisible();
        if (visible && state.monacoEditor) {
            setTimeout(function() { if (state.monacoEditor) state.monacoEditor.layout(); }, 50);
        }
    },

    initSidebarResizer: function() {
        var saved = parseInt(localStorage.getItem('sidebar-width'), 10);
        if (saved && saved >= 160 && saved <= 800) {
            dom.sidebarEl.style.width = saved + 'px';
        }
        var resizing = false;
        dom.sidebarResizer.addEventListener('mousedown', function(e) {
            e.preventDefault();
            resizing = true;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });
        document.addEventListener('mousemove', function(e) {
            if (!resizing) return;
            var w = Math.max(160, Math.min(800, e.clientX));
            dom.sidebarEl.style.width = w + 'px';
        });
        document.addEventListener('mouseup', function() {
            if (!resizing) return;
            resizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            localStorage.setItem('sidebar-width', parseInt(dom.sidebarEl.style.width, 10));
            if (state.monacoEditor) { state.monacoEditor.layout(); }
        });
        dom.btnToggleSidebar.addEventListener('click', ui.toggleSidebar);
        dom.sidebarDrawer.addEventListener('click', function() {
            localStorage.setItem('sidebar-visible', 'true');
            ui.applySidebarVisible();
            if (state.monacoEditor) {
                setTimeout(function() { if (state.monacoEditor) state.monacoEditor.layout(); }, 50);
            }
        });
        ui.applySidebarVisible();
    }
};

// ===================== 文件树 =====================
function loadTree() {
    fetch('/api/tree', { cache: 'no-cache' }).then(function(res) { return res.json(); })
        .then(function(data) {
            dom.treeEl.innerHTML = '';
            var rootRow = document.createElement('div');
            rootRow.className = 'tree-item tree-root';
            rootRow.dataset.path = '';
            rootRow.dataset.type = 'folder';
            var rootLabel = document.createElement('span');
            rootLabel.className = 'tree-label';
            var rootExpanded = state.expandedFolders.has('__root__');
            rootLabel.innerHTML = '<span class="icon">' + (rootExpanded ? '▾' : '▸') + '</span><b>WORKSPACE</b>';
            rootRow.appendChild(rootLabel);
            var rootActions = document.createElement('span');
            rootActions.className = 'tree-actions';
            var rootNewFileBtn = document.createElement('button');
            rootNewFileBtn.className = 'tree-action-btn';
            rootNewFileBtn.textContent = '📄';
            rootNewFileBtn.title = '新建文件';
            rootNewFileBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                state.selectedFolder = '';
                if (state.selectedFolderElement) { state.selectedFolderElement.classList.remove('active'); }
                state.selectedFolderElement = rootRow;
                rootRow.classList.add('active');
                createItem(false);
            });
            var rootNewFolderBtn = document.createElement('button');
            rootNewFolderBtn.className = 'tree-action-btn';
            rootNewFolderBtn.textContent = '📁';
            rootNewFolderBtn.title = '新建文件夹';
            rootNewFolderBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                state.selectedFolder = '';
                if (state.selectedFolderElement) { state.selectedFolderElement.classList.remove('active'); }
                state.selectedFolderElement = rootRow;
                rootRow.classList.add('active');
                createItem(true);
            });
            rootActions.appendChild(rootNewFileBtn);
            rootActions.appendChild(rootNewFolderBtn);
            rootRow.appendChild(rootActions);
            var rootChildWrap = document.createElement('div');
            rootChildWrap.className = 'tree-children';
            rootChildWrap.style.display = rootExpanded ? 'block' : 'none';
            rootLabel.addEventListener('click', function(e) {
                e.stopPropagation();
                var expanded = state.expandedFolders.has('__root__');
                if (expanded) {
                    state.expandedFolders.delete('__root__');
                    rootChildWrap.style.display = 'none';
                    rootLabel.querySelector('.icon').textContent = '▸';
                } else {
                    state.expandedFolders.add('__root__');
                    rootChildWrap.style.display = 'block';
                    rootLabel.querySelector('.icon').textContent = '▾';
                }
                if (state.selectedFolderElement) state.selectedFolderElement.classList.remove('active');
                rootRow.classList.add('active');
                state.selectedFolderElement = rootRow;
                state.selectedFolder = '';
            });
            dom.treeEl.appendChild(rootRow);
            dom.treeEl.appendChild(rootChildWrap);
            renderTree(data, rootChildWrap);
            if (state.selectedFolder === '' && state.selectedFolderElement === null) {
                rootRow.classList.add('active');
                state.selectedFolderElement = rootRow;
            }
        }).catch(function() {
            dom.treeEl.innerHTML = '<div style="color:var(--text-lo)">加载失败</div>';
        });
}

function renderTree(items, container) {
    items.forEach(function(item) {
        var row = document.createElement('div');
        row.className = 'tree-item';
        row.dataset.path = item.path;
        row.dataset.type = item.type;
        var label = document.createElement('span');
        label.className = 'tree-label';
        var isExpanded = state.expandedFolders.has(item.path);
        if (item.type === 'folder') {
            label.innerHTML = '<span class="icon">' + (isExpanded ? '▾' : '▸') + '</span>' + utils.escapeHtml(item.name);
        } else {
            label.innerHTML = '<span class="icon">·</span>' + utils.escapeHtml(item.name);
        }
        row.appendChild(label);
        var actions = document.createElement('span');
        actions.className = 'tree-actions';
        if (item.type === 'folder') {
            var newFileBtn = document.createElement('button');
            newFileBtn.className = 'tree-action-btn';
            newFileBtn.textContent = '📄';
            newFileBtn.title = '新建文件';
            newFileBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                if (state.selectedFolderElement) { state.selectedFolderElement.classList.remove('active'); }
                state.selectedFolderElement = row;
                row.classList.add('active');
                state.selectedFolder = item.path;
                createItem(false);
            });
            var newFolderBtn = document.createElement('button');
            newFolderBtn.className = 'tree-action-btn';
            newFolderBtn.textContent = '📁';
            newFolderBtn.title = '新建文件夹';
            newFolderBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                if (state.selectedFolderElement) { state.selectedFolderElement.classList.remove('active'); }
                state.selectedFolderElement = row;
                row.classList.add('active');
                state.selectedFolder = item.path;
                createItem(true);
            });
            actions.appendChild(newFileBtn);
            actions.appendChild(newFolderBtn);
        }
        var renameBtn = document.createElement('button');
        renameBtn.className = 'tree-action-btn';
        renameBtn.textContent = '✎';
        renameBtn.addEventListener('click', function(e) { e.stopPropagation();
            renameItem(item); });
        var deleteBtn = document.createElement('button');
        deleteBtn.className = 'tree-action-btn';
        deleteBtn.textContent = '🗑';
        deleteBtn.addEventListener('click', function(e) { e.stopPropagation();
            deleteItem(item); });
        actions.appendChild(renameBtn);
        actions.appendChild(deleteBtn);
        if (item.type === 'file') {
            var dlBtn = document.createElement('button');
            dlBtn.className = 'tree-action-btn';
            dlBtn.textContent = '⬇';
            dlBtn.title = '下载';
            dlBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                var a = document.createElement('a');
                a.href = utils.rawFileUrl(item.path, true);
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                utils.showToast('开始下载: ' + item.path.split('/').pop(), 'info', 2000);
            });
            actions.insertBefore(dlBtn, renameBtn);

            var splitBtn = document.createElement('button');
            splitBtn.className = 'tree-action-btn';
            splitBtn.textContent = '⇢';
            splitBtn.title = '在右侧分屏打开';
            splitBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                split.toggle(item.path);
            });
            actions.insertBefore(splitBtn, renameBtn);
        }
        row.appendChild(actions);
        if (item.type === 'folder') {
            var childWrap = document.createElement('div');
            childWrap.className = 'tree-children';
            childWrap.style.display = isExpanded ? 'block' : 'none';
            renderTree(item.children, childWrap);
            label.addEventListener('click', function(e) {
                e.stopPropagation();
                var expanded = state.expandedFolders.has(item.path);
                if (expanded) {
                    state.expandedFolders.delete(item.path);
                    childWrap.style.display = 'none';
                    label.querySelector('.icon').textContent = '▸';
                } else {
                    state.expandedFolders.add(item.path);
                    childWrap.style.display = 'block';
                    label.querySelector('.icon').textContent = '▾';
                }
                if (state.selectedFolderElement) state.selectedFolderElement.classList.remove('active');
                row.classList.add('active');
                state.selectedFolderElement = row;
                state.selectedFolder = item.path;
            });
            container.appendChild(row);
            container.appendChild(childWrap);
        } else {
            label.addEventListener('click', function() { ui.openFile(item.path, row); });
            container.appendChild(row);
        }
    });
}

// ===================== 文件操作 =====================
function createItem(folder) {
    utils.showPrompt(folder ? '输入文件夹名:' : '输入文件名:', '').then(function(name) {
        if (!name) return;
        var path = state.selectedFolder ? state.selectedFolder + '/' + name : name;
        var content = '';
        if (!folder && name.indexOf('.') >= 0) {
            var ext = name.split('.').pop().toLowerCase();
            if (state.templates[ext]) {
                content = templates.replaceVariables(state.templates[ext], name);
            }
        }
        fetch('/api/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path, folder: folder, content: content })
        }).then(function(res) { return res.json(); }).then(function(data) {
            if (data.ok) {
                utils.showToast(folder ? '文件夹已创建' : '文件已创建', 'success');
                loadTree();
                if (!folder) {
                    var row = document.querySelector('.tree-item[data-path="' + path + '"]');
                    if (row) ui.openFile(path, row);
                }
            } else {
                utils.showToast(data.error || '创建失败', 'error');
            }
        });
    });
}

function renameItem(item) {
    utils.showPrompt('重命名为:', item.name).then(function(newName) {
        if (!newName || newName === item.name) return;
        var parts = item.path.split('/');
        parts[parts.length - 1] = newName;
        var newPath = parts.join('/');
        fetch('/api/rename', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old: item.path, new: newPath })
        }).then(function(res) { return res.json(); }).then(function(data) {
            if (data.ok) { utils.showToast('重命名成功', 'success');
                loadTree(); } else { utils.showToast(data.error || '重命名失败', 'error'); }
        });
    });
}

function deleteItem(item) {
    utils.showConfirm('确定要删除 "' + item.name + '" 吗？', function() {
        fetch('/api/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: item.path })
        }).then(function(res) { return res.json(); }).then(function(data) {
            if (data.ok) {
                state.expandedFolders.delete(item.path);
                for (var p of state.expandedFolders) {
                    if (p.startsWith(item.path + '/')) state.expandedFolders.delete(p);
                }
                if (state.selectedFolder === item.path || (state.selectedFolder && state.selectedFolder.startsWith(item
                        .path + '/'))) {
                    state.selectedFolder = '';
                    if (state.selectedFolderElement) { state.selectedFolderElement.classList.remove('active');
                        state.selectedFolderElement = null; }
                }
                if (state.currentFile === item.path || (state.currentFile && state.currentFile.startsWith(item.path +
                        '/'))) {
                    state.currentFile = null;
                    dom.filepathEl.textContent = '未打开文件';
                    dom.emptyState.style.display = 'flex';
                    dom.editorHost.style.display = 'none';
                    dom.btnPanel.disabled = true;
                    dom.btnFre.disabled = true;
                    dom.btnExport.disabled = true;
                    dom.btnBackup.disabled = true;
                    ui.closeDock();
                    state.socket.emit('leave', { path: item.path });
                }
                utils.showToast('删除成功', 'success');
                loadTree();
            } else {
                utils.showToast(data.error || '删除失败', 'error');
            }
        });
    });
}

// ===================== 控制台 =====================
function appendConsole(text) {
    var atBottom = dom.consoleOutput.scrollTop + dom.consoleOutput.clientHeight >= dom.consoleOutput.scrollHeight - 4;
    dom.consoleOutput.appendChild(document.createTextNode(text));
    if (atBottom) dom.consoleOutput.scrollTop = dom.consoleOutput.scrollHeight;
}

// ===================== TT 模式 =====================
function toggleTT() {
    if (state.ttActive) {
        state.ttActive = false;
        state.ttUser = '';
        dom.btnTT.textContent = 'TT';
        dom.btnTT.classList.remove('active');
        dom.btnAddProblem.style.display = 'none';
        utils.showToast('已退出 TT 模式', 'info');
        return;
    }
    utils.showPrompt('请输入你的名字（将作为做题文件夹名）:').then(function(user) {
        if (!user || !user.trim()) return;
        state.ttUser = user.trim();
        fetch('/api/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: state.ttUser, folder: true })
        }).then(function() {
            state.ttActive = true;
            dom.btnTT.textContent = 'TT: ' + state.ttUser;
            dom.btnTT.classList.add('active');
            dom.btnAddProblem.style.display = '';
            state.selectedFolder = state.ttUser;
            utils.showToast('TT 模式已启用，做题目录: ' + state.ttUser + '/', 'success');
            state.expandedFolders.add('__root__');
            state.expandedFolders.add(state.ttUser);
            loadTree();
            var folderRow = document.querySelector('.tree-item[data-path="' + state.ttUser + '"][data-type="folder"]');
            if (folderRow) {
                if (state.selectedFolderElement) state.selectedFolderElement.classList.remove('active');
                folderRow.classList.add('active');
                state.selectedFolderElement = folderRow;
            }
        });
    });
}

function addProblem() {
    if (!state.ttActive || !state.ttUser) return;
    utils.showPrompt('请输入题名（将创建同名文件夹和 cpp 文件）:').then(function(name) {
        if (!name || !name.trim()) return;
        var problem = name.trim();
        var folderPath = state.ttUser + '/' + problem;
        var filePath = folderPath + '/' + problem + '.cpp';
        var template = '#include<bits/stdc++.h>\nusing namespace std;\nint main(){\n    return 0;\n}\n';
        fetch('/api/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: folderPath, folder: true })
        }).then(function() {
            return fetch('/api/file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: filePath, content: template })
            });
        }).then(function() {
            loadTree();
            state.expandedFolders.add('__root__');
            expandPath(state.ttUser);
            expandPath(folderPath);
            var row = document.querySelector('.tree-item[data-path="' + filePath + '"]');
            if (row) ui.openFile(filePath, row);
            utils.showToast('已创建题目: ' + problem, 'success');
        });
    });
}

function expandPath(path) {
    state.expandedFolders.add(path);
    var row = document.querySelector('.tree-item[data-path="' + path + '"][data-type="folder"]');
    if (row) {
        var childWrap = row.nextElementSibling;
        if (childWrap) childWrap.style.display = 'block';
        var icon = row.querySelector('.icon');
        if (icon) icon.textContent = '▾';
    }
}

// ===================== 导出下拉菜单 =====================
function closeAllDropdowns() {
    document.querySelectorAll('.dropdown.open').forEach(function(d) { d.classList.remove('open'); });
}

// ===================== 初始化 =====================
function init() {
    // 缓存 DOM
    ui.cacheDom();

    // 创建 Socket 连接
    state.socket = io({ transports: ["websocket", "polling"] });
    setupSocketEvents();

    // 获取用户信息
    fetch('/api/me').then(function(r) { return r.json(); }).then(function(d) {
        state.isAdmin = !!d.admin;
        if (d.readonly) {
            state.myReadonly = true;
            dom.statusText.textContent = '在线（' + state.username + ' · 只读）';
        }
    }).catch(function() {});

    // 名字提示
    if (!localStorage.getItem('cpp26-username')) {
        utils.showPrompt('你的名字（协作者可见）:', '匿名').then(function(n) {
            if (n && n.trim()) {
                state.username = n.trim();
                localStorage.setItem('cpp26-username', state.username);
                dom.statusText.textContent = '在线（' + state.username + (state.myReadonly ? ' · 只读' : '') + '）';
            }
        });
    }

    // 编辑器模式
    dom.editorModeSelect.value = state.currentEditorType;
    dom.editorModeSelect.addEventListener('change', function(e) {
        var mode = e.target.value;
        if (mode === state.currentEditorType) return;
        if (state.currentFile) state.fileContentCache[state.currentFile] = editor.getContent();
        state.currentEditorType = mode;
        localStorage.setItem('editor-mode', mode);
        if (mode === 'textarea') {
            if (state.monacoEditor) { state.monacoEditor.dispose();
                state.monacoEditor = null;
                state.monacoLoaded = false; }
            dom.monacoContainer.style.display = 'none';
            dom.editorFrame.style.display = 'flex';
            if (state.currentFile) {
                dom.codeEl.value = state.fileContentCache[state.currentFile] || '';
                state.lastContent = dom.codeEl.value;
                dom.codeEl.style.fontSize = state.editorFontSize + 'px';
                dom.gutterEl.style.fontSize = state.editorFontSize + 'px';
                editor.updateGutter();
                editor.updateCodeOverlay();
            }
        } else {
            dom.editorFrame.style.display = 'none';
            dom.monacoContainer.style.display = 'block';
            loadMonaco(mode);
        }
        if (state.currentFile) {
            dom.emptyState.style.display = 'none';
            dom.editorHost.style.display = 'flex';
        }
        if (state.isMarkdownFile) {
            markdown.applyMode();
        }
    });

    // 加载 Monaco
    if (state.currentEditorType === 'textarea') {
        dom.monacoContainer.style.display = 'none';
        dom.editorFrame.style.display = 'flex';
    } else {
        dom.editorFrame.style.display = 'none';
        dom.monacoContainer.style.display = 'block';
        loadMonaco(state.currentEditorType);
    }

    // 初始化 UI
    ui.initDFrame();
    ui.initSidebarResizer();
    split.init();
    markdown.init();
    templates.initModal();

    // 加载树
    loadTree();
    templates.loadAll();

    // 绑定事件
    dom.btnUpload.addEventListener('click', function() { dom.uploadInput.click(); });
    dom.uploadInput.addEventListener('change', function() {
        var files = dom.uploadInput.files;
        var promises = [];
        for (var i = 0; i < files.length; i++) {
            var fd = new FormData();
            fd.append('file', files[i]);
            promises.push(fetch('/api/upload', { method: 'POST', body: fd }));
        }
        Promise.all(promises).then(function() {
            dom.uploadInput.value = '';
            utils.showToast('上传完成', 'success');
            loadTree();
        });
    });

    dom.uploadZipInput.addEventListener('change', function() {
        var file = dom.uploadZipInput.files[0];
        if (!file) return;
        if (!state.currentFile) {
            utils.showToast('请先打开要导入测试点的源文件', 'warning');
            dom.uploadZipInput.value = '';
            return;
        }
        var fd = new FormData();
        fd.append('file', file);
        fd.append('source', state.currentFile);
        fetch('/api/upload_tests', { method: 'POST', body: fd }).then(function(res) { return res.json(); })
            .then(function(data) {
                if (data.ok) {
                    utils.showToast('导入完成: 新增/覆盖 ' + data.count + ' 个文件', 'success');
                    loadTree();
                    if (state.currentFile && utils.isJudgeableExt(utils.extOf(state.currentFile))) {
                        ui.loadCPH(state.currentFile);
                    }
                } else {
                    utils.showToast('导入失败: ' + (data.error || '未知错误'), 'error');
                }
                dom.uploadZipInput.value = '';
            }).catch(function() {
                utils.showToast('上传请求失败', 'error');
                dom.uploadZipInput.value = '';
            });
    });

    dom.btnTT.addEventListener('click', toggleTT);
    dom.btnAddProblem.addEventListener('click', addProblem);

    dom.btnFre.addEventListener('click', function() {
        if (!state.currentFile) return;
        var oldContent = editor.getContent();
        var fileName = state.currentFile.split('/').pop();
        var baseName = fileName.replace(/\.[^.]+$/, '');
        var newContent = oldContent;
        if (state.freEnabled) {
            var lines = oldContent.split('\n');
            var filtered = lines.filter(function(line) {
                var s = line.trim();
                if (s.startsWith('freopen("' + baseName + '.in"')) return false;
                if (s.startsWith('freopen("' + baseName + '.out"')) return false;
                if (s === 'fclose(stdin);' || s === 'fclose(stdout);') return false;
                return true;
            });
            newContent = filtered.join('\n').replace(/\n{3,}/g, '\n\n');
            state.freEnabled = false;
            dom.btnFre.textContent = 'fre OFF';
            dom.btnFre.classList.remove('active');
            utils.showToast('已禁用 freopen', 'info');
        } else {
            var mainMatch = oldContent.match(/\bmain\s*\([^)]*\)\s*\{/);
            if (!mainMatch) {
                utils.showToast('未找到 main 函数,无法插入 freopen', 'error');
                return;
            }
            var bracePos = mainMatch.index + mainMatch[0].length;
            var freBlock = '\n    freopen("' + baseName + '.in", "r", stdin);\n' +
                '    freopen("' + baseName + '.out", "w", stdout);\n';
            var result = oldContent.slice(0, bracePos) + freBlock + oldContent.slice(bracePos);
            var matches = [...result.matchAll(/\n([ \t]*)return\s+0\s*;/g)];
            if (matches.length > 0) {
                var m = matches[matches.length - 1];
                var indent = m[1];
                var fcloseBlock = '\n' + indent + 'fclose(stdin);\n' + indent + 'fclose(stdout);';
                result = result.slice(0, m.index) + fcloseBlock + result.slice(m.index);
            } else {
                var lastBrace = result.lastIndexOf('}');
                if (lastBrace !== -1) {
                    result = result.slice(0, lastBrace) + '    fclose(stdin);\n    fclose(stdout);\n' + result.slice(
                    lastBrace);
                }
            }
            newContent = result;
            state.freEnabled = true;
            dom.btnFre.textContent = 'fre ON';
            dom.btnFre.classList.add('active');
            utils.showToast('已启用 freopen,输入输出文件为 ' + baseName + '.in/.out', 'success');
        }
        editor.setContent(newContent);
        if (state.currentFile) {
            var op = utils.computeDiff(oldContent, newContent);
            if (op.start !== op.end || op.text.length > 0) {
                ot.applyLocal(ot.fromSplice(op, oldContent.length));
            }
            editor.markDirty(state.currentFile);
            dom.btnBackup.disabled = false;
            clearTimeout(state.saveTimer);
            var freSavePath = state.currentFile;
            state.saveTimer = setTimeout(function() { editor.persistFile(freSavePath); }, 1500);
        }
    });

    dom.btnPanel.addEventListener('click', function() {
        if (ui.isPanelOpen()) {
            state.socket.emit('run_stop', {});
            dom.bottomDock.classList.remove('open');
            dom.bottomDock.classList.remove('minimized');
        } else {
            ui.openDock(state.activeTab);
        }
        dom.consoleInput.disabled = false;
        dom.btnRunInConsole.disabled = !state.currentFile || !utils.isJudgeableExt(utils.extOf(state.currentFile));
        if (dom.consoleStatus.textContent === '空闲') {
            dom.consoleStatus.textContent = '就绪';
        }
    });

    dom.btnRunInConsole.addEventListener('click', function() {
        if (!state.currentFile) return;
        ui.openDock('console');
        dom.consoleOutput.textContent = '';
        var inputText = dom.consoleInput.value;
        dom.consoleStatus.textContent = '编译中...';
        dom.consoleStatus.className = 'cs-compiling';
        dom.consoleInput.disabled = true;
        dom.btnRunInConsole.disabled = true;
        dom.consoleStop.disabled = false;
        dom.btnSendInput.disabled = true;
        state.socket.emit('run_start', {
            path: state.currentFile,
            content: editor.getContent(),
            stdin: inputText
        });
    });

    dom.btnSendInput.addEventListener('click', function() {
        var text = dom.consoleInput.value;
        if (!text) return;
        state.socket.emit('run_input', { text: text, no_newline: true });
        appendConsole(text + '\n');
        dom.consoleInput.value = '';
        clearTimeout(state.consoleWaitTimer);
        if (dom.consoleStatus.className === 'cs-waiting') {
            dom.consoleStatus.textContent = '运行中...';
            dom.consoleStatus.className = 'cs-running';
        }
        state.consoleWaitTimer = setTimeout(function() {
            if (dom.consoleStatus.className === 'cs-running') {
                dom.consoleStatus.textContent = '等待输入...';
                dom.consoleStatus.className = 'cs-waiting';
            }
        }, 800);
    });

    dom.btnClearInput.addEventListener('click', function() { dom.consoleInput.value = ''; });
    dom.consoleStop.addEventListener('click', function() {
        clearTimeout(state.consoleWaitTimer);
        state.socket.emit('run_stop', {});
    });

    dom.btnBackup.addEventListener('click', function() {
        if (!state.currentFile) return;
        var content = utils.normalizeContent(editor.getContent());
        fetch('/api/backup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: state.currentFile, content: content })
        }).then(function(res) { return res.json(); }).then(function(data) {
            if (data.ok) {
                utils.showToast('备份成功：' + data.backup_name, 'success', 2000);
                loadTree();
            } else {
                utils.showToast('备份失败：' + (data.error || '未知错误'), 'error', 5000);
            }
        }).catch(function(e) { console.error('备份请求异常:', e);
            utils.showToast('备份请求失败', 'error'); });
    });

    // 导出
    dom.exportCode.addEventListener('click', function() {
        closeAllDropdowns();
        if (!state.currentFile) return;
        var content = editor.getContent();
        var fileName = state.currentFile.split('/').pop();
        var baseName = fileName.replace(/\.[^.]+$/, '');
        if (!state.freEnabled) {
            var hasFre = content.indexOf('freopen("' + baseName + '.in"') >= 0;
            if (!hasFre) {
                var mainMatch = content.match(/\bmain\s*\([^)]*\)\s*\{/);
                if (mainMatch) {
                    var bracePos = mainMatch.index + mainMatch[0].length;
                    var freBlock = '\n    freopen("' + baseName + '.in", "r", stdin);\n' +
                        '    freopen("' + baseName + '.out", "w", stdout);\n';
                    content = content.slice(0, bracePos) + freBlock + content.slice(bracePos);
                    var matches = [...content.matchAll(/\n([ \t]*)return\s+0\s*;/g)];
                    if (matches.length > 0) {
                        var m = matches[matches.length - 1];
                        var indent = m[1];
                        var fcloseBlock = '\n' + indent + 'fclose(stdin);\n' + indent + 'fclose(stdout);';
                        content = content.slice(0, m.index) + fcloseBlock + content.slice(m.index);
                    }
                }
            }
        }
        var blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(a.href);
        utils.showToast('导出成功', 'success');
    });

    dom.exportTests.addEventListener('click', function() {
        closeAllDropdowns();
        if (!state.currentFile) return;
        var a = document.createElement('a');
        a.href = '/api/export_tests?source=' + encodeURIComponent(state.currentFile);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });

    dom.importZip.addEventListener('click', function() {
        closeAllDropdowns();
        dom.uploadZipInput.click();
    });

    dom.importFromFile.addEventListener('click', function() {
        closeAllDropdowns();
        if (!state.currentFile) return;
        utils.showPrompt('输入源文件名（相对 workspace，如 sum.cpp）:', state.currentFile).then(function(srcName) {
            if (!srcName) return;
            fetch('/api/tests?path=' + encodeURIComponent(srcName)).then(function(res) { return res.json(); })
                .then(function(srcTests) {
                    if (!srcTests || !srcTests.length) {
                        utils.showToast('该文件没有测试点', 'warning');
                        return;
                    }
                    var overlay = document.createElement('div');
                    overlay.className = 'modal-overlay';
                    overlay.innerHTML = '<div class="modal import-modal">' +
                        '<h3>从 ' + utils.escapeHtml(srcName) + ' 导入测试点</h3>' +
                        '<div class="import-list">' +
                        srcTests.map(function(t) {
                            var num = ((t.name || '').match(/(\d+)/) || ['0'])[0];
                            return '<label class="import-item">' +
                                '<input type="checkbox" class="import-check" data-num="' + num + '" checked>' +
                                '<span class="import-num">#' + num + '</span>' +
                                '<span class="import-preview">in: ' + utils.escapeHtml((t.input || '').slice(
                                    0, 24)) + ' · out: ' + utils.escapeHtml((t.expected || '').slice(
                                    0, 24)) + '</span>' +
                                '</label>';
                        }).join('') +
                        '</div>' +
                        '<div class="modal-buttons">' +
                        '<button class="btn" id="import-cancel">取消</button>' +
                        '<button class="btn primary" id="import-ok">导入选中</button>' +
                        '</div></div>';
                    document.body.appendChild(overlay);
                    overlay.querySelector('#import-cancel').addEventListener('click', function() { overlay
                            .remove(); });
                    overlay.querySelector('#import-ok').addEventListener('click', function() {
                        var nums = [];
                        overlay.querySelectorAll('.import-check:checked').forEach(function(c) {
                            nums.push(c.dataset.num);
                        });
                        overlay.remove();
                        if (!nums.length) { utils.showToast('未选择任何测试点', 'warning'); return; }
                        fetch('/api/test/import', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                source: srcName,
                                target: state.currentFile,
                                nums: nums
                            })
                        }).then(function(res) { return res.json(); }).then(function(data) {
                            if (data.ok) {
                                utils.showToast('导入完成: ' + data.count +
                                    ' 个文件（冲突编号已自动重映射）', 'success');
                                ui.loadCPH(state.currentFile);
                            } else {
                                utils.showToast('导入失败: ' + (data.error || '未知错误'), 'error');
                            }
                        });
                    });
                });
        });
    });

    // Dock 模式
    ui.applyDockMode();
    dom.dockPin.addEventListener('click', function() {
        ui.setDockMode(state.dockMode === 'floating' ? 'permanent' : 'floating');
    });
    dom.dockClose.addEventListener('click', ui.closeDock);

    // Dock 标签切换
    document.querySelectorAll('.dock-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            if (dom.bottomDock.classList.contains('minimized')) {
                dom.bottomDock.classList.remove('minimized');
            }
            ui.switchDockTab(tab.dataset.tab);
        });
    });

    // Dock 拖拽（浮动模式）
    var dockTabsBar = document.querySelector('.dock-tabs');
    dockTabsBar.addEventListener('mousedown', function(e) {
        if (state.dockMode !== 'floating') return;
        if (e.target.closest('button')) return;
        var rect = dom.bottomDock.getBoundingClientRect();
        var parent = dom.bottomDock.offsetParent || document.body;
        var parentRect = parent.getBoundingClientRect();
        var offsetX = e.clientX - rect.left;
        var offsetY = e.clientY - rect.top;
        dom.bottomDock.style.right = 'auto';
        dom.bottomDock.style.bottom = 'auto';
        dom.bottomDock.style.left = (rect.left - parentRect.left) + 'px';
        dom.bottomDock.style.top = (rect.top - parentRect.top) + 'px';
        dom.bottomDock.style.width = rect.width + 'px';
        var maxX = parent.clientWidth - 80;
        var maxY = parent.clientHeight - 40;

        function move(ev) {
            var nx = ev.clientX - offsetX - parentRect.left;
            var ny = ev.clientY - offsetY - parentRect.top;
            nx = Math.max(0, Math.min(maxX, nx));
            ny = Math.max(0, Math.min(maxY, ny));
            dom.bottomDock.style.left = nx + 'px';
            dom.bottomDock.style.top = ny + 'px';
        }

        function up() {
            document.removeEventListener('mousemove', move);
            document.removeEventListener('mouseup', up);
        }
        document.addEventListener('mousemove', move);
        document.addEventListener('mouseup', up);
        e.preventDefault();
    });

    // Dock 拖拽调整高度
    var dockResizing = false,
        dockStartY = 0,
        dockStartH = 0;
    dom.dockResizer.addEventListener('mousedown', function(e) {
        dockResizing = true;
        dockStartY = e.clientY;
        dockStartH = dom.bottomDock.offsetHeight;
        document.body.style.cursor = 'ns-resize';
        e.preventDefault();
    });
    document.addEventListener('mousemove', function(e) {
        if (!dockResizing) return;
        var dy = e.clientY - dockStartY;
        var newH = Math.max(100, Math.min(window.innerHeight - 120, dockStartH - dy));
        dom.bottomDock.style.height = newH + 'px';
    });
    document.addEventListener('mouseup', function() {
        if (dockResizing) { dockResizing = false;
            document.body.style.cursor = ''; }
    });

    // 问题面板清除
    dom.problemsClear.addEventListener('click', function() {
        state.problemList = [];
        ui.renderProblems();
        if (state.monacoEditor && state.monacoEditor.getModel()) {
            monaco.editor.setModelMarkers(state.monacoEditor.getModel(), 'clangd', []);
        }
    });

    // CPH 事件
    dom.cphRunAll.addEventListener('click', function() {
        ui.openDock('cph');
        if (!state.currentFile || state.cphTestCases.length === 0 || state.cphRunning) return;
        state.cphRunning = true;
        ui.syncCPHFromDOM();
        dom.judgeVerdict.textContent = '…';
        dom.judgeVerdict.className = 'v-pending';
        dom.judgeSummary.textContent = '评测中...';
        state.cphTestCases.forEach(function(tc) { tc.verdict = null;
            tc.actual = undefined;
            tc.stderr = undefined;
            tc.time_ms = 0; });
        ui.renderCPH();
        ui.saveAllCPH();
        fetch('/api/judge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: state.currentFile })
        }).then(function(res) { return res.json(); }).then(function(result) {
            if (result.error) {
                dom.judgeVerdict.textContent = '—';
                dom.judgeVerdict.className = 'v-pending';
                dom.judgeSummary.textContent = result.error;
                state.cphRunning = false;
                return;
            }
            if (result.verdict === 'CE') {
                dom.judgeVerdict.textContent = 'CE';
                dom.judgeVerdict.className = 'v-ce';
                dom.judgeSummary.textContent = 'Compile Error';
                dom.judgeBody.innerHTML = '<pre style="color:var(--err);white-space:pre-wrap;padding:10px;">' +
                    utils.escapeHtml(result.compile_error || '') + '</pre>';
                state.cphRunning = false;
                return;
            }
            if (result.cases) {
                for (var i = 0; i < result.cases.length; i++) {
                    var c = result.cases[i];
                    var m = c.case.match(/(\d+)/);
                    var num = m ? parseInt(m[1]) : 0;
                    var tc = state.cphTestCases.find(function(t) { return t.num === num; });
                    if (tc) {
                        tc.verdict = c.verdict;
                        tc.actual = c.actual;
                        tc.stderr = c.stderr;
                        tc.time_ms = c.time_ms;
                        tc.mem_kb = c.mem_kb;
                    }
                }
            }
            ui.renderCPH();
            state.socket.emit('judge_result', { path: state.currentFile, result: result });
            state.cphRunning = false;
        }).catch(function(e) {
            utils.showToast('评测请求失败', 'error');
            state.cphRunning = false;
        });
    });

    dom.cphAdd.addEventListener('click', function() {
        if (!state.currentFile) return;
        fetch('/api/test/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: state.currentFile })
        }).then(function(res) { return res.json(); }).then(function(data) {
            if (data.ok) {
                utils.showToast('已添加测试点 #' + data.num, 'success');
                ui.loadCPH(state.currentFile);
            } else {
                utils.showToast(data.error || '添加失败', 'error');
            }
        });
    });

    dom.cphSaveAll.addEventListener('click', function() {
        ui.syncCPHFromDOM();
        ui.saveAllCPH();
        utils.showToast('测试点已保存', 'success');
    });

    dom.cphZip.addEventListener('click', function(e) {
        e.stopPropagation();
        if (dom.uploadZipInput) dom.uploadZipInput.click();
    });

    // 字体快捷键（Monaco 在加载后会注册）
    // 初始化完成
    font.apply(state.editorFontSize);
    split.applyRatio();
    ui.applyDockMode();

    console.log('[IDE] 初始化完成');
}

function saveAllCPH() {
    if (!state.currentFile) return;
    var base = state.currentFile.replace(/\.[^.]+$/, '');
    var promises = [];
    for (var i = 0; i < state.cphTestCases.length; i++) {
        var tc = state.cphTestCases[i];
        promises.push(fetch('/api/test/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: base + '_T/' + tc.num + '.in', content: tc.input || '' })
        }));
        promises.push(fetch('/api/test/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: base + '_T/' + tc.num + '.out', content: tc.expected || '' })
        }));
    }
    return Promise.all(promises);
}

function loadMonaco(mode) {
    if (state.monacoLoaded && state.monacoEditor) return;
    var vsPath;
    if (mode === 'local-monaco') {
        vsPath = '/static/monaco/vs';
        if (!document.getElementById('monaco-loader-script')) {
            var script = document.createElement('script');
            script.id = 'monaco-loader-script';
            script.src = '/static/monaco/vs/loader.js';
            script.onload = function() { initMonaco(vsPath); };
            document.head.appendChild(script);
        } else {
            initMonaco(vsPath);
        }
    } else if (mode === 'cdn-monaco') {
        vsPath = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs';
        if (!window.monacoRequire) {
            var script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs/loader.js';
            script.onload = function() { window.monacoRequire = window.require;
                initMonaco(vsPath); };
            document.head.appendChild(script);
        } else {
            initMonaco(vsPath);
        }
    }
}

function initMonaco(vsPath) {
    if (state.monacoEditor) return;
    var requireFn = window.monacoRequire || window.require;
    if (!requireFn) return;
    requireFn.config({ paths: { vs: vsPath } });
    requireFn(['vs/editor/editor.main'], function() {
        monaco.editor.defineTheme('cpp26-dark', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: '', foreground: 'cccccc', background: '0d1117' },
                { token: 'comment', foreground: '6a9955', fontStyle: 'italic' },
                { token: 'keyword', foreground: '569cd6' },
                { token: 'keyword.cpp', foreground: '569cd6' },
                { token: 'number', foreground: 'b5cea8' },
                { token: 'string', foreground: 'ce9178' },
                { token: 'type', foreground: '4ec9b0' },
                { token: 'class', foreground: '4ec9b0' },
                { token: 'interface', foreground: '4ec9b0' },
                { token: 'function', foreground: 'dcdcaa' },
                { token: 'variable', foreground: '9cdcfe' },
                { token: 'constant', foreground: '4fc1ff' },
                { token: 'delimiter', foreground: 'd4d4d4' },
                { token: 'operator', foreground: 'd4d4d4' },
                { token: 'predefined', foreground: 'dcdcaa' },
                { token: 'namespace', foreground: '9cdcfe' },
                { token: 'identifier', foreground: '9cdcfe' },
                { token: 'macro', foreground: 'dcdcaa' },
                { token: 'annotation', foreground: 'b5cea8' },
                { token: 'tag', foreground: '569cd6' },
                { token: 'attribute.name', foreground: '9cdcfe' },
                { token: 'attribute.value', foreground: 'ce9178' }
            ],
            colors: {
                'editor.background': '#0d1117',
                'editor.foreground': '#e6edf3',
                'editorLineNumber.foreground': '#6e7681',
                'editorLineNumber.activeForeground': '#e6edf3',
                'editorCursor.foreground': '#e0a84a',
                'editor.selectionBackground': '#264f78',
                'editor.inactiveSelectionBackground': '#3a3d41',
                'editor.selectionHighlightBackground': '#264f7855',
                'editor.lineHighlightBackground': '#161b22',
                'editor.lineHighlightBorder': '#21262d',
                'editorIndentGuide.background': '#21262d',
                'editorIndentGuide.activeBackground': '#6e7681',
                'editorWidget.background': '#161b22',
                'editorWidget.border': '#30363d',
                'editorSuggestWidget.background': '#1c2330',
                'editorSuggestWidget.border': '#30363d',
                'editorSuggestWidget.foreground': '#e6edf3',
                'editorSuggestWidget.selectedBackground': '#242c3a',
                'editorSuggestWidget.selectedForeground': '#ffffff',
                'editorSuggestWidget.highlightForeground': '#58a6ff',
                'editorHoverWidget.background': '#161b22',
                'editorHoverWidget.border': '#30363d',
                'editorBracketMatch.background': '#264f7840',
                'editorBracketMatch.border': '#58a6ff',
                'editorGutter.background': '#0d1117',
                'editorError.foreground': '#f85149',
                'editorWarning.foreground': '#d29922',
                'editorInfo.foreground': '#58a6ff',
                'minimap.background': '#0d1117',
                'scrollbarSlider.background': '#30363d80',
                'scrollbarSlider.hoverBackground': '#6e7681cc',
                'scrollbarSlider.activeBackground': '#9aa4b2cc',
                'editor.findMatchBackground': '#9e6a03aa',
                'editor.findMatchHighlightBackground': '#ea983355',
                'editor.findMatchBorder': '#e0a84a',
                'editor.findMatchHighlightBorder': '#00000000'
            }
        });

        state.monacoEditor = monaco.editor.create(dom.monacoContainer, {
            value: '',
            language: 'cpp',
            theme: 'cpp26-dark',
            automaticLayout: true,
            fontFamily: "'Cascadia Code','Cascadia Mono','Fira Code','JetBrains Mono','Sarasa Mono SC',Consolas,ui-monospace,SFMono-Regular,Menlo,monospace",
            fontSize: state.editorFontSize,
            lineHeight: 22,
            minimap: { enabled: true, maxColumn: 80 },
            padding: { top: 12 },
            smoothScrolling: true,
            cursorSmoothCaretAnimation: true,
            fontLigatures: true,
            suggestOnTriggerCharacters: true,
            quickSuggestions: { other: true, comments: false, strings: false },
            quickSuggestionsDelay: 0,
            tabSize: 4,
            insertSpaces: true,
            scrollBeyondLastLine: false,
            wordBasedSuggestions: 'currentDocument',
            tabCompletion: 'on',
            acceptSuggestionOnEnter: 'smart',
            suggestSelection: 'first',
            inlineSuggest: { enabled: false },
            find: {
                cursorMoveOnType: true,
                seedSearchStringFromSelection: 'always',
                autoFindInSelection: 'never',
                addExtraSpaceOnTop: true,
                loop: true
            }
        });

        // TypeScript / JavaScript IntelliSense
        if (monaco.languages.typescript) {
            var TS = monaco.languages.typescript;
            var compilerOpts = {
                target: TS.ScriptTarget.ESNext,
                allowNonTsExtensions: true,
                moduleResolution: TS.ModuleResolutionKind.NodeJs,
                module: TS.ModuleKind.ESNext,
                noEmit: true,
                esModuleInterop: true,
                allowJs: true,
                jsx: TS.JsxEmit.React,
                strict: false,
                noImplicitAny: false,
                lib: ['esnext', 'dom', 'dom.iterable', 'webworker']
            };
            TS.typescriptDefaults.setCompilerOptions(compilerOpts);
            TS.javascriptDefaults.setCompilerOptions(compilerOpts);
            TS.typescriptDefaults.setEagerModelSync(true);
            TS.javascriptDefaults.setEagerModelSync(true);
            TS.typescriptDefaults.setDiagnosticsOptions({ noSemanticValidation: false, noSyntaxValidation: false,
                diagnosticCodesToIgnore: [] });
            TS.javascriptDefaults.setDiagnosticsOptions({ noSemanticValidation: false, noSyntaxValidation: false,
                diagnosticCodesToIgnore: [] });
        }

        var K = monaco.languages.CompletionItemKind;
        var SNIPPET = monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet;

        function mkRange(model, position) {
            var word = model.getWordUntilPosition(position);
            return { startLineNumber: position.lineNumber, endLineNumber: position.lineNumber,
                startColumn: word.startColumn, endColumn: word.endColumn };
        }

        // 转到声明
        state.monacoEditor.addAction({
            id: 'goto-declaration',
            label: '转到声明',
            keybindings: [monaco.KeyCode.F12],
            contextMenuGroupId: 'navigation',
            contextMenuOrder: 1.5,
            run: function(ed) { gotoDeclaration(ed); }
        });

        async function gotoDeclaration(ed) {
            if (!state.currentFile) { return; }
            var ext = utils.extOf(state.currentFile);
            if (['cpp', 'cc', 'cxx', 'h', 'hpp', 'hh', 'c'].indexOf(ext) < 0) {
                utils.showToast('当前文件类型暂不支持转到声明', 'error');
                return;
            }
            var model = ed.getModel();
            var position = ed.getPosition();
            if (!model || !position) return;
            var word = model.getWordAtPosition(position);
            if (!word) {
                utils.showToast('请先将光标放在变量 / 函数 / 类型名上', 'error');
                return;
            }
            var payload = {
                path: state.currentFile,
                text: model.getValue(),
                line: position.lineNumber - 1,
                character: position.column - 1
            };
            var resp;
            try {
                resp = await new Promise(function(resolve, reject) {
                    var timer = setTimeout(function() { reject(new Error('timeout')); }, 6000);
                    state.socket.emit('lsp_definition', payload, function(r) { clearTimeout(timer);
                        resolve(r); });
                });
            } catch (e) {
                utils.showToast('转到声明请求超时, 请稍后重试', 'error');
                return;
            }
            if (!resp || resp.error) {
                utils.showToast(resp && resp.error ? resp.error : '转到声明失败', 'error');
                return;
            }
            if (resp.outside) {
                utils.showToast('声明位于工作区外(如系统头文件), 暂不支持跳转', 'error');
                return;
            }
            if (!resp.found) {
                utils.showToast('未找到 "' + word.word + '" 的声明', 'error');
                return;
            }
            var targetLine = resp.line + 1;
            var targetCol = resp.character + 1;
            if (resp.path === state.currentFile) {
                ed.revealPositionInCenter({ lineNumber: targetLine, column: targetCol });
                ed.setPosition({ lineNumber: targetLine, column: targetCol });
                ed.focus();
            } else {
                var targetRow = document.querySelector('.tree-item[data-path="' + resp.path + '"]');
                await ui.openFile(resp.path, targetRow);
                if (state.monacoEditor && state.currentFile === resp.path) {
                    state.monacoEditor.revealPositionInCenter({ lineNumber: targetLine, column: targetCol });
                    state.monacoEditor.setPosition({ lineNumber: targetLine, column: targetCol });
                    state.monacoEditor.focus();
                }
            }
        }

        // C++ 补全
        var CPP_HEADERS = ['algorithm', 'bits/stdc++.h', 'bitset', 'cctype', 'cmath', 'cstdio', 'cstdlib', 'cstring',
            'deque', 'functional', 'iomanip', 'iostream', 'limits', 'list', 'map', 'memory', 'numeric', 'queue',
            'set', 'span', 'sstream', 'stack', 'string', 'tuple', 'unordered_map', 'unordered_set', 'utility',
            'vector'
        ];
        var CPP_TYPES = ['int', 'long long', 'double', 'float', 'char', 'bool', 'string', 'vector', 'pair', 'map',
            'set', 'unordered_map', 'unordered_set', 'auto', 'size_t', 'long double'
        ];
        var CPP_KEYWORDS = ['const', 'constexpr', 'static', 'typedef', 'using', 'namespace', 'template', 'typename',
            'struct', 'class', 'enum', 'union', 'public', 'private', 'protected', 'virtual', 'override', 'inline',
            'return', 'break', 'continue', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'goto',
            'try', 'catch', 'throw', 'new', 'delete', 'sizeof', 'decltype', 'auto', 'void', 'bool', 'char', 'int',
            'long', 'short', 'unsigned', 'signed', 'float', 'double', 'true', 'false', 'nullptr', 'this', 'explicit',
            'friend', 'operator', 'extern', 'register', 'volatile', 'mutable', 'const_cast', 'static_cast',
            'dynamic_cast', 'reinterpret_cast'
        ];

        var CPP_VAR_TYPES =
            'int|long long|long|short|double|float|char|bool|string|vector|map|set|unordered_map|unordered_set|multiset|multimap|queue|stack|deque|pair|tuple|array|bitset|priority_queue|size_t|auto|ll|ull|ld|pii|unsigned|signed|void|list|forward_list';
        var CPP_RESERVED = new Set([].concat(CPP_KEYWORDS, CPP_HEADERS, 'main', 'std', 'cin', 'cout', 'endl', 'cerr',
            'clog', 'printf', 'scanf', 'puts', 'getchar', 'putchar', 'getline', 'sort', 'reverse', 'find', 'count',
            'fill', 'swap', 'min', 'max', 'abs', 'pow', 'sqrt', 'gcd', 'lcm', 'accumulate', 'lower_bound',
            'upper_bound', 'binary_search', 'unique', 'next_permutation', 'prev_permutation', 'memset', 'memcpy',
            'to_string', 'stoi', 'stoll', 'stol', 'stod', 'stof', 'begin', 'end', 'rbegin', 'rend', 'size', 'empty',
            'push_back', 'pop_back', 'push_front', 'pop_front', 'front', 'back', 'top', 'insert', 'erase', 'clear',
            'resize', 'reserve', 'first', 'second', 'make_pair', 'make_tuple', 'get', 'tie', 'emplace',
            'emplace_back', 'emplace_front', 'data', 'c_str', 'substr', 'find_first_of', 'find_last_of', 'npos',
            'ios', 'sync_with_stdio', 'cin_tie'
        ]));
        var DECL_TYPE_RE = new RegExp('\\b(?:' + CPP_VAR_TYPES +
            ')\\b\\s*(?:<[^<>]*(?:<[^<>]*>[^<>]*)*>)?\\s*(?:&{0,2}|\\*{0,2})\\s*([a-zA-Z_]\\w*)\\s*(?:[;=,\\[\\(])', 'g');
        var DECL_FUNC_RE = new RegExp('\\b(?:' + CPP_VAR_TYPES +
            ')\\b\\s*(?:<[^<>]*>)?\\s*(?:&{0,2}|\\*{0,2})\\s*([a-zA-Z_]\\w*)\\s*\\([^)]*\\)\\s*\\{', 'g');
        var DECL_RANGEFOR_RE =
            /for\s*\(\s*(?:const\s+)?(?:[a-zA-Z_]\w*\s+)?(?:auto|int|long long|long|short|char|double|float|bool|ll)\s*&?\s*([a-zA-Z_]\w*)\s*:/g;

        function extractDeclaredNames(text) {
            var names = new Map();
            DECL_TYPE_RE.lastIndex = 0;
            DECL_FUNC_RE.lastIndex = 0;
            DECL_RANGEFOR_RE.lastIndex = 0;
            var m;
            while ((m = DECL_TYPE_RE.exec(text)) !== null) {
                var name = m[1];
                if (name && !CPP_RESERVED.has(name)) {
                    if (!names.has(name)) names.set(name, 'var');
                }
            }
            while ((m = DECL_FUNC_RE.exec(text)) !== null) {
                var name = m[1];
                if (name && !CPP_RESERVED.has(name)) {
                    if (!names.has(name)) names.set(name, 'func');
                }
            }
            while ((m = DECL_RANGEFOR_RE.exec(text)) !== null) {
                if (m[1] && !CPP_RESERVED.has(m[1])) names.set(m[1], 'var');
            }
            return names;
        }

        var CPP_PREPROCESS = [
            { label: 'include', insertText: 'include <${1:iostream}>', detail: '库名已选中, 可直接输入替换' },
            { label: 'define', insertText: 'define ${1:NAME} ${2:value}' },
            { label: 'ifdef', insertText: 'ifdef ${1:NAME}' },
            { label: 'ifndef', insertText: 'ifndef ${1:NAME}' },
            { label: 'if', insertText: 'if ${1:condition}' },
            { label: 'elif', insertText: 'elif ${1:condition}' },
            { label: 'else', insertText: 'else' },
            { label: 'endif', insertText: 'endif' },
            { label: 'pragma', insertText: 'pragma once' },
            { label: 'error', insertText: 'error ${1:message}' },
            { label: 'undef', insertText: 'undef ${1:NAME}' }
        ];

        var CPP_SNIPPETS = [
            { label: 'inc', kind: K.Snippet, insertText: '#include <bits/stdc++.h>\nusing namespace std;\n',
                detail: '万能头+命名空间', sortText: '0', ctx: 'noinclude' },
            { label: 'inc_io', kind: K.Snippet, insertText: '#include <iostream>\nusing namespace std;\n',
                detail: 'iostream+命名空间', sortText: '0', ctx: 'noinclude' },
            { label: 'main', kind: K.Snippet,
                insertText: 'int main() {\n\tios::sync_with_stdio(false);\n\tcin.tie(nullptr);\n\t$0\n\treturn 0;\n}',
                detail: 'main + fast io', documentation: '快速 I/O 主函数模板', sortText: '0', ctx: 'noinclude',
                funcDef: true },
            { label: 'fastio', kind: K.Snippet, insertText: 'ios::sync_with_stdio(false);\ncin.tie(nullptr);',
                detail: '快速 I/O', ctx: 'noinclude' },
            { label: 'vector', kind: K.Class, insertText: 'vector<${1:int}> ${2:v};', detail: 'vector',
                documentation: '动态数组, O(1) 随机访问, O(1) amortized 尾部插入', sortText: '1', ctx: 'noinclude',
                commitCharacters: ['.', '>'] },
            { label: 'vector2d', kind: K.Snippet,
                insertText: 'vector<vector<${1:int}>> ${2:grid}(${3:n}, vector<${1:int}>(${4:m}));', detail: '二维 vector',
                ctx: 'noinclude' },
            { label: 'map', kind: K.Class, insertText: 'map<${1:int}, ${2:int}> ${3:m};', detail: 'map',
                documentation: '有序映射, 基于红黑树, O(log n)', sortText: '1', ctx: 'noinclude', commitCharacters: ['.',
                    '>'
                ] },
            { label: 'unordered_map', kind: K.Class, insertText: 'unordered_map<${1:int}, ${2:int}> ${3:m};',
                detail: 'unordered_map', documentation: '哈希映射, 平均 O(1)', sortText: '1', ctx: 'noinclude',
                commitCharacters: ['.', '>'] },
            { label: 'set', kind: K.Class, insertText: 'set<${1:int}> ${2:s};', detail: 'set',
                documentation: '有序集合, 自动去重, O(log n)', sortText: '1', ctx: 'noinclude', commitCharacters: ['.',
                    '>'
                ] },
            { label: 'unordered_set', kind: K.Class, insertText: 'unordered_set<${1:int}> ${2:s};',
                detail: 'unordered_set', documentation: '哈希集合, 平均 O(1)', sortText: '1', ctx: 'noinclude',
                commitCharacters: ['.', '>'] },
            { label: 'multiset', kind: K.Class, insertText: 'multiset<${1:int}> ${2:ms};', detail: 'multiset',
                documentation: '允许重复元素的有序集合', ctx: 'noinclude', commitCharacters: ['.', '>'] },
            { label: 'priority_queue', kind: K.Class, insertText: 'priority_queue<${1:int}> ${2:pq};', detail: '大根堆',
                documentation: '默认大根堆, O(log n) 插入/弹出', ctx: 'noinclude', commitCharacters: ['.', '>'] },
            { label: 'priority_queue_min', kind: K.Class,
                insertText: 'priority_queue<${1:int}, vector<${1:int}>, greater<${1:int}>> ${2:pq};', detail: '小根堆',
                documentation: '小根堆: greater<> 比较器', ctx: 'noinclude' },
            { label: 'queue', kind: K.Class, insertText: 'queue<${1:int}> ${2:q};', detail: 'queue',
                documentation: 'FIFO 队列', ctx: 'noinclude', commitCharacters: ['.', '>'] },
            { label: 'stack', kind: K.Class, insertText: 'stack<${1:int}> ${2:st};', detail: 'stack',
                documentation: 'LIFO 栈', ctx: 'noinclude', commitCharacters: ['.', '>'] },
            { label: 'deque', kind: K.Class, insertText: 'deque<${1:int}> ${2:dq};', detail: 'deque',
                documentation: '双端队列, 两端 O(1) 插入删除', ctx: 'noinclude', commitCharacters: ['.', '>'] },
            { label: 'pair', kind: K.Class, insertText: 'pair<${1:int}, ${2:int}> ${3:p};', detail: 'pair',
                documentation: '二元组: first, second', ctx: 'noinclude', commitCharacters: ['.', '>'] },
            { label: 'tuple', kind: K.Class, insertText: 'tuple<${1:int}, ${2:int}, ${3:int}> ${4:t};', detail: 'tuple',
                documentation: '多元组: get<i>(t)', ctx: 'noinclude', commitCharacters: ['.', '>'] },
            { label: 'string', kind: K.Class, insertText: 'string ${1:s};', detail: 'string',
                documentation: '字符串, 支持 +, substr, find 等', sortText: '1', ctx: 'noinclude', commitCharacters: [
                    '.'
                ] },
            { label: 'array', kind: K.Class, insertText: 'array<${1:int}, ${2:10}> ${3:arr};', detail: 'array',
                documentation: '固定大小数组, 栈上分配', ctx: 'noinclude', commitCharacters: ['.', '>'] },
            { label: 'bitset', kind: K.Class, insertText: 'bitset<${1:64}> ${2:bs};', detail: 'bitset',
                documentation: '定长位数组, 支持 & | ^ ~ 及移位', ctx: 'noinclude', commitCharacters: ['.'] },
            { label: 'cin', kind: K.Function, insertText: 'cin >> ${1:x};', documentation: '标准输入流, >> 提取运算符',
                ctx: 'noinclude' },
            { label: 'cout', kind: K.Function, insertText: 'cout << ${1:value} << "\\n";',
                documentation: '标准输出流, << 插入运算符', ctx: 'noinclude' },
            { label: 'endl', kind: K.Function, insertText: 'endl', documentation: '换行并刷新缓冲区', ctx: 'noinclude' },
            { label: 'cin_array', kind: K.Snippet, insertText: 'for (int i = 0; i < ${1:n}; i++) cin >> ${2:arr}[i];',
                detail: '读入数组', ctx: 'noinclude' },
            { label: 'cout_array', kind: K.Snippet,
                insertText: 'for (int i = 0; i < ${1:n}; i++) cout << ${2:arr}[i] << " \\n"[i == ${1:n} - 1];',
                detail: '输出数组(空格分隔)', ctx: 'noinclude' },
            { label: 'scanf', kind: K.Function, insertText: 'scanf("%${1:d}", &${2:x});', documentation: '格式化输入: %d %lld %lf %c %s',
                ctx: 'noinclude' },
            { label: 'printf', kind: K.Function, insertText: 'printf("%${1:d}\\n", ${2:x});',
                documentation: '格式化输出: %d %lld %.nf %c %s', ctx: 'noinclude' },
            { label: 'sort', kind: K.Function, insertText: 'sort(${1:v}.begin(), ${1:v}.end());',
                documentation: 'O(n log n) 排序, 原地修改', ctx: 'noinclude' },
            { label: 'sort_desc', kind: K.Function, insertText: 'sort(${1:v}.begin(), ${1:v}.end(), greater<>());',
                detail: '降序排序', ctx: 'noinclude' },
            { label: 'sort_range', kind: K.Function,
                insertText: 'sort(${1:v}.begin() + ${2:l}, ${1:v}.begin() + ${3:r});', detail: '区间排序',
                ctx: 'noinclude' },
            { label: 'reverse', kind: K.Function, insertText: 'reverse(${1:v}.begin(), ${1:v}.end());',
                documentation: '反转区间', ctx: 'noinclude' },
            { label: 'max_element', kind: K.Function, insertText: '*max_element(${1:v}.begin(), ${1:v}.end())',
                documentation: '返回最大值的迭代器, 解引用得值', ctx: 'noinclude' },
            { label: 'min_element', kind: K.Function, insertText: '*min_element(${1:v}.begin(), ${1:v}.end())',
                documentation: '返回最小值的迭代器, 解引用得值', ctx: 'noinclude' },
            { label: 'accumulate', kind: K.Function,
                insertText: 'accumulate(${1:v}.begin(), ${1:v}.end(), ${2:0}LL)',
                documentation: '求和, 第三个参数决定返回类型', ctx: 'noinclude' },
            { label: 'find', kind: K.Function, insertText: 'find(${1:v}.begin(), ${1:v}.end(), ${2:x})',
                documentation: '线性查找, 返回迭代器', ctx: 'noinclude' },
            { label: 'count', kind: K.Function, insertText: 'count(${1:v}.begin(), ${1:v}.end(), ${2:x})',
                documentation: '统计等于 x 的元素个数', ctx: 'noinclude' },
            { label: 'binary_search', kind: K.Function,
                insertText: 'binary_search(${1:v}.begin(), ${1:v}.end(), ${2:x})',
                documentation: '二分查找, 返回 bool (要求有序)', ctx: 'noinclude' },
            { label: 'lower_bound', kind: K.Function,
                insertText: 'lower_bound(${1:v}.begin(), ${1:v}.end(), ${2:x})',
                documentation: '第一个 >= x 的位置 (要求有序)', ctx: 'noinclude' },
            { label: 'upper_bound', kind: K.Function,
                insertText: 'upper_bound(${1:v}.begin(), ${1:v}.end(), ${2:x})',
                documentation: '第一个 > x 的位置 (要求有序)', ctx: 'noinclude' },
            { label: 'unique', kind: K.Function,
                insertText: '${1:v}.erase(unique(${1:v}.begin(), ${1:v}.end()), ${1:v}.end());', detail: '去重',
                documentation: '需先排序, 真正删除重复元素', ctx: 'noinclude' },
            { label: 'fill', kind: K.Function, insertText: 'fill(${1:v}.begin(), ${1:v}.end(), ${2:0});',
                documentation: '填充区间为指定值', ctx: 'noinclude' },
            { label: 'swap', kind: K.Function, insertText: 'swap(${1:a}, ${2:b});', documentation: '交换两值',
                ctx: 'noinclude' },
            { label: 'min', kind: K.Function, insertText: 'min(${1:a}, ${2:b})', documentation: '返回较小值',
                ctx: 'noinclude' },
            { label: 'max', kind: K.Function, insertText: 'max(${1:a}, ${2:b})', documentation: '返回较大值',
                ctx: 'noinclude' },
            { label: 'abs', kind: K.Function, insertText: 'abs(${1:x})', documentation: '绝对值 (整型用 abs, 浮点用 fabs)',
                ctx: 'noinclude' },
            { label: 'pow', kind: K.Function, insertText: 'pow(${1:base}, ${2:exp})', documentation: '幂运算, 返回 double',
                ctx: 'noinclude' },
            { label: 'sqrt', kind: K.Function, insertText: 'sqrt(${1:x})', documentation: '平方根, 返回 double',
                ctx: 'noinclude' },
            { label: '__gcd', kind: K.Function, insertText: '__gcd(${1:a}, ${2:b})',
                documentation: 'GCD (内置, C++17 起推荐用 std::gcd)', ctx: 'noinclude' },
            { label: 'next_permutation', kind: K.Function,
                insertText: 'next_permutation(${1:v}.begin(), ${1:v}.end())',
                documentation: '下一个排列, 用于全排列枚举', ctx: 'noinclude' },
            { label: 'memset', kind: K.Function, insertText: 'memset(${1:arr}, ${2:0}, sizeof(${1:arr}))',
                documentation: '按字节填充, 常用于清零 (-1) 或极大值 (0x3f)', ctx: 'noinclude' },
            { label: 'memcpy', kind: K.Function, insertText: 'memcpy(${1:dst}, ${2:src}, sizeof(${2:src}))',
                documentation: '按字节复制', ctx: 'noinclude' },
            { label: 'to_string', kind: K.Function, insertText: 'to_string(${1:x})', documentation: '数字转字符串',
                ctx: 'noinclude' },
            { label: 'stoi', kind: K.Function, insertText: 'stoi(${1:s})', documentation: '字符串转 int', ctx: 'noinclude' },
            { label: 'for', kind: K.Snippet,
                insertText: 'for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {\n\t$0\n}', sortText: '1',
                ctx: 'noinclude' },
            { label: 'for_range', kind: K.Snippet,
                insertText: 'for (int ${1:i} = ${2:0}; ${1:i} < ${3:n}; ${1:i}++) {\n\t$0\n}', ctx: 'noinclude' },
            { label: 'for_auto', kind: K.Snippet, insertText: 'for (auto &${1:x} : ${2:container}) {\n\t$0\n}',
                detail: '范围 for 循环', ctx: 'noinclude' },
            { label: 'while', kind: K.Snippet, insertText: 'while (${1:condition}) {\n\t$0\n}', sortText: '1',
                ctx: 'noinclude' },
            { label: 'rep', kind: K.Snippet, insertText: 'for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) $0',
                detail: '单行循环', ctx: 'noinclude' },
            { label: 'if', kind: K.Snippet, insertText: 'if (${1:condition}) {\n\t$0\n}', sortText: '1',
                ctx: 'noinclude' },
            { label: 'ifelse', kind: K.Snippet, insertText: 'if (${1:condition}) {\n\t$0\n} else {\n\t\n}',
                ctx: 'noinclude' },
            { label: 'else', kind: K.Snippet, insertText: 'else {\n\t$0\n}', ctx: 'noinclude' },
            { label: 'll', kind: K.Keyword, insertText: 'typedef long long ll;', documentation: 'long long 简写',
                ctx: 'noinclude' },
            { label: 'ull', kind: K.Keyword, insertText: 'typedef unsigned long long ull;', ctx: 'noinclude' },
            { label: 'ld', kind: K.Keyword, insertText: 'typedef long double ld;', ctx: 'noinclude' },
            { label: 'pii', kind: K.Keyword, insertText: 'typedef pair<int,int> pii;', ctx: 'noinclude' },
            { label: 'all', kind: K.Keyword, insertText: '#define all(x) x.begin(), x.end()', ctx: 'noinclude' },
            { label: 'bfs', kind: K.Snippet,
                insertText: 'void bfs(int ${1:start}) {\n\tqueue<int> q;\n\tq.push(${1:start});\n\tvector<bool> vis(n, false);\n\tvis[${1:start}] = true;\n\twhile (!q.empty()) {\n\t\tint u = q.front(); q.pop();\n\t\tfor (int v : adj[u]) {\n\t\t\tif (!vis[v]) {\n\t\t\t\tvis[v] = true;\n\t\t\t\tq.push(v);\n\t\t\t}\n\t\t}\n\t}\n}',
                detail: 'BFS 模板', ctx: 'noinclude', funcDef: true },
            { label: 'dfs', kind: K.Snippet,
                insertText: 'void dfs(int u, int fa) {\n\tfor (int v : adj[u]) {\n\t\tif (v != fa) {\n\t\t\tdfs(v, u);\n\t\t}\n\t}\n}',
                detail: 'DFS 模板', ctx: 'noinclude', funcDef: true },
            { label: 'binary_search_template', kind: K.Snippet,
                insertText: 'int lo = ${1:0}, hi = ${2:n};\nwhile (lo < hi) {\n\tint mid = (lo + hi) / 2;\n\tif (${3:check(mid)}) hi = mid;\n\telse lo = mid + 1;\n}\n// 答案: lo',
                detail: '二分模板', ctx: 'noinclude' },
            { label: 'dsu', kind: K.Snippet,
                insertText: 'int fa[MAXN];\nint find(int x) {\n\treturn fa[x] == x ? x : fa[x] = find(fa[x]);\n}\nvoid unite(int x, int y) {\n\tfa[find(x)] = find(y);\n}\n// 初始化: for (int i = 0; i <= n; i++) fa[i] = i;',
                detail: '并查集(路径压缩)', ctx: 'noinclude' },
            { label: 'gcd', kind: K.Snippet, insertText: 'int gcd(int a, int b) {\n\treturn b ? gcd(b, a % b) : a;\n}',
                detail: 'GCD (递归)', ctx: 'noinclude' },
            { label: 'gcd_iter', kind: K.Snippet,
                insertText: 'int gcd(int a, int b) {\n\twhile (b) {\n\t\ta %= b;\n\t\tswap(a, b);\n\t}\n\treturn a;\n}',
                detail: 'GCD (迭代)', ctx: 'noinclude' },
            { label: 'lcm', kind: K.Snippet, insertText: 'int lcm(int a, int b) {\n\treturn a / gcd(a, b) * b;\n}',
                detail: 'LCM', ctx: 'noinclude' },
            { label: 'qpow', kind: K.Snippet,
                insertText: 'long long qpow(long long a, long long b, long long mod) {\n\tlong long res = 1;\n\ta %= mod;\n\twhile (b > 0) {\n\t\tif (b & 1) res = res * a % mod;\n\t\ta = a * a % mod;\n\t\tb >>= 1;\n\t}\n\treturn res;\n}',
                detail: '快速幂 (带取模)', ctx: 'noinclude' },
            { label: 'lowbit', kind: K.Snippet, insertText: 'int lowbit(int x) {\n\treturn x & -x;\n}',
                detail: 'lowbit (返回最低位的1)', ctx: 'noinclude' },
            { label: 'exgcd', kind: K.Snippet,
                insertText: 'long long exgcd(long long a, long long b, long long &x, long long &y) {\n\tif (b == 0) { x = 1; y = 0; return a; }\n\tlong long x1, y1;\n\tlong long d = exgcd(b, a % b, x1, y1);\n\tx = y1;\n\ty = x1 - (a / b) * y1;\n\treturn d;\n}',
                detail: '扩展欧几里得', ctx: 'noinclude' },
            { label: 'is_prime', kind: K.Snippet,
                insertText: 'bool is_prime(int n) {\n\tif (n < 2) return false;\n\tfor (int i = 2; (long long)i * i <= n; i++) {\n\t\tif (n % i == 0) return false;\n\t}\n\treturn true;\n}',
                detail: '质数判定', ctx: 'noinclude' },
            { label: 'sieve', kind: K.Snippet,
                insertText: 'bool is_p[MAXN];\nvector<int> primes;\nvoid sieve(int n) {\n\tmemset(is_p, true, sizeof(is_p));\n\tis_p[0] = is_p[1] = false;\n\tfor (int i = 2; i <= n; i++) {\n\t\tif (is_p[i]) {\n\t\t\tprimes.push_back(i);\n\t\t\tfor (long long j = (long long)i * i; j <= n; j += i)\n\t\t\t\tis_p[j] = false;\n\t\t}\n\t}\n}',
                detail: '埃氏筛', ctx: 'noinclude' },
            { label: 'euler_sieve', kind: K.Snippet,
                insertText: 'bool is_p[MAXN];\nint primes[MAXN], cnt;\nvoid sieve(int n) {\n\tmemset(is_p, true, sizeof(is_p));\n\tis_p[0] = is_p[1] = false;\n\tfor (int i = 2; i <= n; i++) {\n\t\tif (is_p[i]) primes[cnt++] = i;\n\t\tfor (int j = 0; j < cnt && (long long)i * primes[j] <= n; j++) {\n\t\t\tis_p[i * primes[j]] = false;\n\t\t\tif (i % primes[j] == 0) break;\n\t\t}\n\t}\n}',
                detail: '欧拉线性筛', ctx: 'noinclude' },
            { label: 'comb', kind: K.Snippet,
                insertText: 'long long C[MAXN][MAXN];\nvoid init_comb(int n) {\n\tfor (int i = 0; i <= n; i++) {\n\t\tC[i][0] = 1;\n\t\tfor (int j = 1; j <= i; j++)\n\t\t\tC[i][j] = C[i-1][j-1] + C[i-1][j];\n\t}\n}',
                detail: '组合数 (杨辉三角)', ctx: 'noinclude' },
            { label: 'bit', kind: K.Snippet,
                insertText: 'int tree[MAXN];\nvoid update(int i, int v, int n) {\n\tfor (; i <= n; i += i & -i) tree[i] += v;\n}\nint query(int i) {\n\tint s = 0;\n\tfor (; i > 0; i -= i & -i) s += tree[i];\n\treturn s;\n}',
                detail: '树状数组 (单点更新+前缀和)', ctx: 'noinclude' },
            { label: 'segt', kind: K.Snippet,
                insertText: 'int tree[4 * MAXN], a[MAXN];\nvoid build(int p, int l, int r) {\n\tif (l == r) { tree[p] = a[l]; return; }\n\tint mid = (l + r) / 2;\n\tbuild(2*p, l, mid);\n\tbuild(2*p+1, mid+1, r);\n\ttree[p] = tree[2*p] + tree[2*p+1];\n}\nvoid update(int p, int l, int r, int x, int v) {\n\tif (l == r) { tree[p] = v; return; }\n\tint mid = (l + r) / 2;\n\tif (x <= mid) update(2*p, l, mid, x, v);\n\telse update(2*p+1, mid+1, r, x, v);\n\ttree[p] = tree[2*p] + tree[2*p+1];\n}\nint query(int p, int l, int r, int ql, int qr) {\n\tif (qr < l || r < ql) return 0;\n\tif (ql <= l && r <= qr) return tree[p];\n\tint mid = (l + r) / 2;\n\treturn query(2*p, l, mid, ql, qr) + query(2*p+1, mid+1, r, ql, qr);\n}',
                detail: '线段树 (区间求和)', ctx: 'noinclude' },
            { label: 'dijkstra', kind: K.Snippet,
                insertText: 'struct Edge { int to, w; };\nvector<Edge> adj[MAXN];\nlong long dist[MAXN];\nbool vis[MAXN];\nvoid dijkstra(int s, int n) {\n\tmemset(dist, 0x3f, sizeof(dist));\n\tmemset(vis, false, sizeof(vis));\n\tdist[s] = 0;\n\tpriority_queue<pair<long long,int>, vector<pair<long long,int>>, greater<>> pq;\n\tpq.push({0, s});\n\twhile (!pq.empty()) {\n\t\tauto [d, u] = pq.top(); pq.pop();\n\t\tif (vis[u]) continue;\n\t\tvis[u] = true;\n\t\tfor (auto &e : adj[u]) {\n\t\t\tif (dist[u] + e.w < dist[e.to]) {\n\t\t\t\tdist[e.to] = dist[u] + e.w;\n\t\t\t\tpq.push({dist[e.to], e.to});\n\t\t\t}\n\t\t}\n\t}\n}',
                detail: 'Dijkstra (堆优化)', ctx: 'noinclude' },
            { label: 'floyd', kind: K.Snippet,
                insertText: 'long long d[MAXN][MAXN];\nvoid floyd(int n) {\n\tfor (int k = 1; k <= n; k++)\n\t\tfor (int i = 1; i <= n; i++)\n\t\t\tfor (int j = 1; j <= n; j++)\n\t\t\t\tif (d[i][k] + d[k][j] < d[i][j])\n\t\t\t\t\td[i][j] = d[i][k] + d[k][j];\n}\n// 初始化: d[i][i]=0; d[i][j]=INF; 读入边 d[u][v]=w;',
                detail: 'Floyd 全源最短路', ctx: 'noinclude' },
            { label: 'topsort', kind: K.Snippet,
                insertText: 'vector<int> adj[MAXN];\nint in_deg[MAXN];\nbool topsort(int n) {\n\tqueue<int> q;\n\tfor (int i = 1; i <= n; i++) if (in_deg[i] == 0) q.push(i);\n\tint cnt = 0;\n\twhile (!q.empty()) {\n\t\tint u = q.front(); q.pop();\n\t\tcnt++;\n\t\tfor (int v : adj[u]) if (--in_deg[v] == 0) q.push(v);\n\t}\n\treturn cnt == n;\n}',
                detail: '拓扑排序 (Kahn)', ctx: 'noinclude' },
            { label: 'kruskal', kind: K.Snippet,
                insertText: 'struct Edge { int u, v, w; };\nbool cmp(const Edge &a, const Edge &b) { return a.w < b.w; }\nint fa[MAXN];\nint find(int x) { return fa[x] == x ? x : fa[x] = find(fa[x]); }\nlong long kruskal(int n, vector<Edge>& edges) {\n\tsort(edges.begin(), edges.end(), cmp);\n\tfor (int i = 0; i <= n; i++) fa[i] = i;\n\tlong long sum = 0; int cnt = 0;\n\tfor (auto &e : edges) {\n\t\tint fu = find(e.u), fv = find(e.v);\n\t\tif (fu != fv) { fa[fu] = fv; sum += e.w; cnt++; }\n\t\tif (cnt == n - 1) break;\n\t}\n\treturn sum;\n}',
                detail: 'Kruskal 最小生成树', ctx: 'noinclude' },
            { label: 'kmp', kind: K.Snippet,
                insertText: 'int nxt[MAXN];\nvoid get_next(const string &p) {\n\tint m = p.size();\n\tnxt[0] = -1;\n\tfor (int i = 0, j = -1; i < m;) {\n\t\tif (j == -1 || p[i] == p[j]) { i++; j++; nxt[i] = j; }\n\t\telse j = nxt[j];\n\t}\n}\nint kmp(const string &s, const string &p) {\n\tget_next(p);\n\tint n = s.size(), m = p.size();\n\tfor (int i = 0, j = 0; i < n;) {\n\t\tif (j == -1 || s[i] == p[j]) { i++; j++; }\n\t\telse j = nxt[j];\n\t\tif (j == m) return i - m;\n\t}\n\treturn -1;\n}',
                detail: 'KMP 字符串匹配', ctx: 'noinclude' },
            { label: 'trie', kind: K.Snippet,
                insertText: 'int ch[MAXN][26], cnt;\nbool is_end[MAXN];\nvoid insert(const string &s) {\n\tint u = 0;\n\tfor (char c : s) {\n\t\tint v = c - \'a\';\n\t\tif (!ch[u][v]) ch[u][v] = ++cnt;\n\t\tu = ch[u][v];\n\t}\n\tis_end[u] = true;\n}\nbool search(const string &s) {\n\tint u = 0;\n\tfor (char c : s) {\n\t\tint v = c - \'a\';\n\t\tif (!ch[u][v]) return false;\n\t\tu = ch[u][v];\n\t}\n\treturn is_end[u];\n}',
                detail: 'Trie 字典树', ctx: 'noinclude' },
            { label: 'manacher', kind: K.Snippet,
                insertText: 'int p[MAXN*2];\nstring manacher(const string &s) {\n\tstring t = "#";\n\tfor (char c : s) { t += c; t += \'#\'; }\n\tint n = t.size(), c = 0, r = 0;\n\tfor (int i = 0; i < n; i++) {\n\t\tp[i] = i < r ? min(p[2*c-i], r-i) : 1;\n\t\twhile (i-p[i] >= 0 && i+p[i] < n && t[i-p[i]] == t[i+p[i]]) p[i]++;\n\t\tif (i+p[i] > r) { c = i; r = i+p[i]; }\n\t}\n\treturn t;\n}',
                detail: 'Manacher 回文串', ctx: 'noinclude' },
            { label: 'knapsack01', kind: K.Snippet,
                insertText: 'int dp[MAXN];\nfor (int i = 0; i < n; i++) {\n\tfor (int j = W; j >= w[i]; j--) {\n\t\tdp[j] = max(dp[j], dp[j - w[i]] + v[i]);\n\t}\n}\n// 答案: dp[W]',
                detail: '01 背包', ctx: 'noinclude' },
            { label: 'knapsack_full', kind: K.Snippet,
                insertText: 'int dp[MAXN];\nfor (int i = 0; i < n; i++) {\n\tfor (int j = w[i]; j <= W; j++) {\n\t\tdp[j] = max(dp[j], dp[j - w[i]] + v[i]);\n\t}\n}\n// 答案: dp[W]',
                detail: '完全背包', ctx: 'noinclude' },
            { label: 'lis', kind: K.Snippet,
                insertText: 'vector<int> dp;\nfor (int i