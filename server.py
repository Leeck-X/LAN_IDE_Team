import os
import sys
import time
import glob
import shutil
import socket
import tempfile
import subprocess
import platform
import threading
import mimetypes
import re
import json
import zipfile

from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room

try:
    import psutil
except ImportError:
    psutil = None

def app_root() -> str:
    """可执行文件所在目录(可写)。PyInstaller 冻结时为 exe 所在目录, 否则为脚本目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def resource_path(rel: str) -> str:
    """只读资源目录。PyInstaller 冻结时优先使用 exe 同级目录(结构完整、用户可见)，
    缺失时回退到 _MEIPASS 解压目录。"""
    if getattr(sys, "frozen", False):
        base = os.path.join(os.path.dirname(sys.executable), rel)
        if os.path.exists(base):
            return base
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel)

BASE_DIR = app_root()
WORKSPACE = os.path.join(BASE_DIR, "workspace")
os.makedirs(WORKSPACE, exist_ok=True)

app = Flask(__name__,
            template_folder=resource_path("templates"),
            static_folder=resource_path("static"),
            static_url_path="/static")
app.config["SECRET_KEY"] = "cpp26-ide-secret"
app.config["TEMPLATES_AUTO_RELOAD"] = True

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------- 工具函数 ----------
def safe_path(rel_path: str) -> str:
    if rel_path is None:
        rel_path = ""
    full = os.path.normpath(os.path.join(WORKSPACE, rel_path.lstrip("/\\")))
    if not (full == WORKSPACE or full.startswith(WORKSPACE + os.sep)):
        raise ValueError("非法路径")
    return full

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def is_binary_file(full_path):
    try:
        with open(full_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
    except:
        pass
    return False

def get_mime(full_path):
    mime, _ = mimetypes.guess_type(full_path)
    return mime or 'application/octet-stream'

def normalize_newlines(text):
    return text.replace('\r\n', '\n').replace('\r', '\n')

def scan_dir(path=""):
    root = safe_path(path)
    items = []
    for name in sorted(os.listdir(root)):
        if name.startswith("."):
            continue
        full = os.path.join(root, name)
        rel = os.path.relpath(full, WORKSPACE).replace('\\', '/')
        if os.path.isdir(full):
            items.append({
                "name": name,
                "path": rel,
                "type": "folder",
                "children": scan_dir(rel)
            })
        else:
            items.append({"name": name, "path": rel, "type": "file"})
    return items

# ---------- 编译运行 ----------
COMPILE_TIMEOUT = 20
RUN_TIMEOUT = 5
CXX_STDS = ["c++26", "c++23", "c++20", "c++17"]

def find_compiler(lang):
    candidates = {
        "c": ["clang", "gcc", "cc"],
        "cpp": ["clang++", "g++", "c++"]
    }
    for exe in candidates.get(lang, []):
        path = shutil.which(exe)
        if path:
            return path
    return None

def compile_source(src_path, ext, work_dir):
    exe_name = "main.exe" if platform.system() == "Windows" else "main"
    exe_path = os.path.join(work_dir, exe_name)
    if ext == "c":
        compiler = find_compiler("c")
        if not compiler:
            return None, "未找到 C 编译器，请安装 clang 或 gcc"
        stds = [None]
    elif ext in ("cpp", "cc", "cxx"):
        compiler = find_compiler("cpp")
        if not compiler:
            return None, "未找到 C++ 编译器，请安装 clang++ 或 g++"
        stds = CXX_STDS
    else:
        return None, f"不支持的语言: .{ext}"
    last_err = "编译失败"
    for i, std in enumerate(stds):
        cmd = [compiler]
        if std:
            cmd.append(f"-std={std}")
        cmd += ["-O2", "-Wall", "-Wextra", "-o", exe_path, src_path]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=COMPILE_TIMEOUT)
        except subprocess.TimeoutExpired:
            return None, "编译超时"
        if proc.returncode == 0:
            return [exe_path], None
        last_err = proc.stderr or proc.stdout or "编译失败"
        # 仅当错误与 std 标志相关时才降级重试
        if std and i < len(stds) - 1:
            err_lower = last_err.lower()
            if not any(k in err_lower for k in [
                "unrecognized", "invalid value", "unknown", "not found",
                "-std=", "c++26", "c++23", "c++20"
            ]):
                break
    return None, last_err

def strip_freopen_for_judge(source):
    """评测模式下移除 I/O 重定向,避免 freopen 与 stdin 喂入冲突。
    使用正则逐条移除 freopen/fclose 语句,不影响同一行上的其他代码。"""
    source = re.sub(r'freopen\s*\([^)]*(?:stdin|stdout)[^)]*\)\s*;?', '', source)
    source = re.sub(r'fclose\s*\(\s*(?:stdin|stdout)\s*\)\s*;?', '', source)
    source = re.sub(r'sys\.stdin\s*=\s*open\s*\([^)]*\)', '', source)
    source = re.sub(r'sys\.stdout\s*=\s*open\s*\([^)]*\)', '', source)
    return source

def find_dangerous_call(source):
    """检测源码中是否包含可能破坏服务器的危险调用, 命中则返回函数名, 否则返回 None。"""
    patterns = [
        (r'\bsystem\s*\(', 'system'),
        (r'\b_?popen\s*\(', 'popen'),
        (r'\b_?fork\s*\(', 'fork'),
        (r'\bexecl\s*\(', 'execl'),
        (r'\bexeclp\s*\(', 'execlp'),
        (r'\bexecle\s*\(', 'execle'),
        (r'\bexecv\s*\(', 'execv'),
        (r'\bexecvp\s*\(', 'execvp'),
        (r'\bexecvpe\s*\(', 'execvpe'),
        (r'\bexecve\s*\(', 'execve'),
        (r'\b_?wsystem\s*\(', '_wsystem'),
        (r'\bunlink\s*\(', 'unlink'),
        (r'\bos\.system\s*\(', 'os.system'),
        (r'\bos\.popen\s*\(', 'os.popen'),
        (r'\bos\.exec\w*\s*\(', 'os.exec'),
        (r'\bos\.fork\s*\(', 'os.fork'),
        (r'\bos\.spawn\w*\s*\(', 'os.spawn'),
        (r'\bsubprocess\s*\.', 'subprocess'),
        (r'\bos\.remove\s*\(', 'os.remove'),
        (r'\bos\.unlink\s*\(', 'os.unlink'),
        (r'\bos\.rmdir\s*\(', 'os.rmdir'),
        (r'\bshutil\s*\.', 'shutil'),
    ]
    for pattern, name in patterns:
        if re.search(pattern, source):
            return name
    return None

def run_process(cmd, stdin_data="", timeout=RUN_TIMEOUT, cwd=None):
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, input=stdin_data, capture_output=True, text=True,
            timeout=timeout, cwd=cwd
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "code": proc.returncode,
            "time_ms": elapsed_ms
        }
    except subprocess.TimeoutExpired:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {"error": "TLE", "time_ms": elapsed_ms}

def run_process_with_stats(cmd, stdin_data="", timeout=RUN_TIMEOUT, cwd=None):
    """运行程序并统计峰值内存(RSS)与墙钟时间。使用 psutil 监控子进程内存。"""
    start = time.perf_counter()
    peak_mem_bytes = 0
    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, cwd=cwd
        )
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {"error": "RE", "stderr": str(e), "time_ms": elapsed_ms, "mem_kb": 0}

    # 内存监控线程: 轮询进程及其子进程的 RSS 峰值
    mem_box = {"peak": 0}
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
                    if m > mem_box["peak"]:
                        mem_box["peak"] = m
                except Exception:
                    pass
                time.sleep(0.02)
        except Exception:
            pass
    mt = threading.Thread(target=monitor, daemon=True)
    mt.start()

    try:
        stdout, stderr = proc.communicate(input=stdin_data, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.communicate(timeout=1)
        except Exception:
            pass
        mt.join(timeout=0.2)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {"error": "TLE", "time_ms": elapsed_ms, "mem_kb": mem_box["peak"] // 1024}
    except Exception as e:
        proc.kill()
        mt.join(timeout=0.2)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {"error": "RE", "stderr": str(e), "time_ms": elapsed_ms, "mem_kb": mem_box["peak"] // 1024}

    mt.join(timeout=0.2)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return {
        "stdout": stdout,
        "stderr": stderr,
        "code": proc.returncode,
        "time_ms": elapsed_ms,
        "mem_kb": mem_box["peak"] // 1024
    }

def get_test_dir(src_full_path):
    """返回源文件对应的测试点文件夹路径: {base}_T/"""
    d = os.path.dirname(src_full_path)
    base = os.path.splitext(os.path.basename(src_full_path))[0]
    return os.path.join(d, f"{base}_T")

def find_tests(src_full_path):
    test_dir = get_test_dir(src_full_path)
    if not os.path.isdir(test_dir):
        return []
    tests = []
    for in_path in sorted(glob.glob(os.path.join(test_dir, "*.in"))):
        m = re.match(r"^(\d+)\.in$", os.path.basename(in_path))
        if m:
            n = m.group(1)
            out_path = os.path.join(test_dir, f"{n}.out")
            if os.path.exists(out_path):
                tests.append((f"test {n}", in_path, out_path))
    return tests

# ---------- clangd LSP 语义补全 ----------
CLANGD_PATH = os.path.join(BASE_DIR, "tools", "clangd", "clangd_22.1.6", "bin", "clangd.exe")

def get_system_include_flags():
    """查询 g++ 的系统头文件搜索路径, 转为 -isystem 参数, 使 clangd 能解析标准库。"""
    gpp = shutil.which("g++")
    if not gpp:
        return []
    try:
        proc = subprocess.run(
            [gpp, "-E", "-x", "c++", "-", "-v"],
            input="", capture_output=True, text=True, timeout=10
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
    """将 file:/// 形式的 URI 转回 workspace 相对路径, 非 workspace 内返回 None。"""
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
    """最小化 LSP 客户端: 管理 clangd 子进程, 按 Content-Length 分帧收发 JSON-RPC。"""

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
                        }
                    }
                },
                "workspaceFolders": [{"uri": path_to_uri(WORKSPACE), "name": "workspace"}],
                "initializationOptions": {
                    "fallbackFlags": ["-std=c++17", "--target=x86_64-w64-mingw32"] + get_system_include_flags(),
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
            # clangd 主动请求(如 workspace/configuration), 空响应
            method = msg.get("method")
            result = [] if method == "workspace/configuration" else None
            self._send({"jsonrpc": "2.0", "id": msg["id"], "result": result})
        elif "method" in msg:
            # 通知类消息(无 id), 转发 diagnostics 到前端
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

    def sync(self, full_path, text):
        """仅同步文档内容(用于实时诊断), 不请求补全。"""
        uri = path_to_uri(full_path)
        if uri not in self.opened:
            self.did_open(full_path, text)
        elif self.texts.get(uri) != text:
            self.did_change(full_path, text)

clangd = ClangdClient()

def _on_clangd_diagnostics(params):
    """将 clangd 的 publishDiagnostics 转发给对应文件的客户端。"""
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
presence_lock = threading.Lock()

# ---------- 交互式运行 ----------
RUN_MAX_SECONDS = 300
running_consoles = {}
running_consoles_lock = threading.Lock()

def console_reader(sid, proc, path):
    try:
        for line in iter(proc.stdout.readline, ""):
            socketio.emit("run_output", {"path": path, "text": line}, room=sid)
    except:
        pass
    finally:
        rc = proc.wait()
        socketio.emit("run_exit", {"path": path, "code": rc}, room=sid)
        cleanup_console(sid)

def cleanup_console(sid):
    with running_consoles_lock:
        entry = running_consoles.pop(sid, None)
    if entry:
        if entry.get("timer"):
            entry["timer"].cancel()
        if entry.get("workdir"):
            entry["workdir"].cleanup()

def kill_console(sid):
    with running_consoles_lock:
        entry = running_consoles.get(sid)
    if entry and entry["proc"].poll() is None:
        try:
            entry["proc"].kill()
        except:
            pass

# ---------- HTTP 路由 ----------
@app.route("/")
def index():
    return render_template("index.html")

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
        return jsonify({
            "binary": True,
            "mime": mime,
            "content": None,
            "url": f"/api/file/raw?path={path}"
        })

    with open(full, "r", encoding="utf-8", errors="ignore", newline="\n") as f:
        content = f.read()
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
    return send_from_directory(os.path.dirname(full), os.path.basename(full), mimetype=mime)

@app.route("/api/file", methods=["POST"])
def api_save():
    data = request.get_json(force=True)
    path = data.get("path", "")
    content = data.get("content", "")
    content = normalize_newlines(content)
    try:
        full = safe_path(path)
    except ValueError:
        return jsonify({"error": "非法路径"}), 400
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return jsonify({"ok": True})

@app.route("/api/backup", methods=["POST"])
def api_backup():
    try:
        data = request.get_json(force=True)
        path = data.get("path", "")
        content = data.get("content", "")
        content = normalize_newlines(content)

        if not path:
            return jsonify({"ok": False, "error": "缺少路径"}), 400

        try:
            full = safe_path(path)
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400

        if not os.path.isfile(full):
            return jsonify({"ok": False, "error": "文件不存在"}), 404

        client_ip = request.remote_addr or "127.0.0.1"
        last_ip = client_ip.split(".")[-1] if "." in client_ip else client_ip

        base_name = os.path.basename(full)
        backup_name = f"{base_name}_{last_ip}.bak"
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
    data = request.get_json(force=True)
    path = data.get("path", "")
    is_folder = data.get("folder", False)
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
        open(full, "w", encoding="utf-8", newline="\n").close()
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True})

@app.route("/api/rename", methods=["POST"])
def api_rename():
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
    os.rename(old_full, new_full)
    with presence_lock:
        if old in presence:
            presence[new] = presence.pop(old)
    # 先在旧 room 广播,让客户端更新 currentFile 并重新 join 新 room
    socketio.emit("file_renamed", {"old_path": old, "new_path": new}, room=old)
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True})

@app.route("/api/delete", methods=["POST"])
def api_delete():
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
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True})

@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "没有文件"}), 400
    file = request.files["file"]
    filename = os.path.basename(file.filename)
    save_path = os.path.join(WORKSPACE, filename)
    file.save(save_path)
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True, "name": filename})

@app.route("/api/upload_tests", methods=["POST"])
def api_upload_tests():
    """上传 zip 测试包,解压到 {base}_T/ 文件夹,文件名统一为 {编号}.in/.out。"""
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
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    count = 0
    try:
        with zipfile.ZipFile(tmp_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('/') or name.startswith('.'):
                    continue
                base = os.path.basename(name)
                if not base or base.startswith('.'):
                    continue
                low = base.lower()
                if not (low.endswith('.in') or low.endswith('.out')):
                    continue
                # 从文件名提取编号: 1.in -> 1, test1.in -> 1, sum.1.in -> 1
                m = re.match(r'^(?:.*?\.)*?(\d+)\.(in|out)$', low)
                if not m:
                    continue
                num = m.group(1)
                ext = m.group(2)
                new_name = f"{num}.{ext}"
                dest = os.path.join(test_dir, new_name)
                with zf.open(name) as src, open(dest, 'wb') as dst:
                    dst.write(src.read())
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
    """导出测试点为 zip,文件名 {编号}.in/.out。"""
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
        # 延迟清理(send_from_directory 需要文件存在)
        import atexit
        atexit.register(lambda: os.path.exists(tmp_zip.name) and os.unlink(tmp_zip.name))

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
    data = request.get_json(force=True)
    source_path = data.get("path", "")
    test_num = data.get("num")
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

@app.route("/api/test/run", methods=["POST"])
def api_test_run():
    data = request.get_json(force=True)
    path = data.get("path", "")
    test_num = data.get("num")
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
    if result.get("error"):
        return "TLE"
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
    rank = {"AC": 0, "WA": 1, "RE": 2, "TLE": 3}
    with tempfile.TemporaryDirectory() as work_dir:
        # 读取源码并移除 freopen,避免与 stdin 喂入冲突
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
        # 预读所有测试数据
        case_data = []
        for name, in_path, out_path in tests:
            with open(in_path, "r", encoding="utf-8", errors="ignore", newline="\n") as f:
                input_data = f.read()
            with open(out_path, "r", encoding="utf-8", errors="ignore", newline="\n") as f:
                expected = f.read()
            case_data.append((name, input_data, expected))
        # 多线程并行评测, 每完成一个立即推送
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
        # 汇总最终结果
        final = "AC"
        for r in results:
            if rank[r["verdict"]] > rank[final]:
                final = r["verdict"]
    return jsonify({"verdict": final, "cases": results})

# ---------- Socket.IO 事件 ----------
@socketio.on("join")
def on_join(data):
    rel = data.get("path")
    if not rel:
        return
    username = data.get("username", "匿名")
    join_room(rel)
    with presence_lock:
        presence.setdefault(rel, {})[request.sid] = username
        users = list(presence[rel].values())
    emit("presence", {"path": rel, "users": users}, room=rel)

@socketio.on("leave")
def on_leave(data):
    rel = data.get("path")
    if not rel:
        return
    leave_room(rel)
    with presence_lock:
        if rel in presence and request.sid in presence[rel]:
            del presence[rel][request.sid]
            users = list(presence[rel].values())
        else:
            users = []
    emit("presence", {"path": rel, "users": users}, room=rel)

@socketio.on("disconnect")
def on_disconnect():
    with presence_lock:
        for rel, users in list(presence.items()):
            if request.sid in users:
                del users[request.sid]
                emit("presence", {"path": rel, "users": list(users.values())}, room=rel)
    kill_console(request.sid)
    cleanup_console(request.sid)

@socketio.on("edit")
def on_edit(data):
    rel = data.get("path")
    if not rel:
        return
    if "content" in data:
        data["content"] = normalize_newlines(data["content"])
    emit("edit", data, room=rel, include_self=False)

@socketio.on("cursor")
def on_cursor(data):
    rel = data.get("path")
    if not rel:
        return
    emit("cursor", data, room=rel, include_self=False)

@socketio.on("save")
def on_save(data):
    rel = data.get("path")
    if not rel:
        return
    content = data.get("content", "")
    content = normalize_newlines(content)
    try:
        full = safe_path(rel)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        emit("saved", {"path": rel}, room=rel)
    except ValueError:
        pass

@socketio.on("judge_result")
def on_judge_result(data):
    rel = data.get("path")
    if not rel:
        return
    emit("judge_result", data, room=rel, include_self=False)

@socketio.on("lsp_open")
def on_lsp_open(data):
    """文件打开时预热 clangd, 提前构建 preamble, 加速后续补全。"""
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
    """编辑时同步文档内容, 触发 clangd 重新解析并发回诊断。"""
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
    """clangd 语义补全: 同步当前文本后请求 textDocument/completion, 结果通过 ack 返回。"""
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

@socketio.on("run_start")
def on_run_start(data):
    sid = request.sid
    rel = data.get("path", "")
    content = data.get("content")
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
        os.makedirs(os.path.dirname(full), exist_ok=True)
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
        emit("run_exit", {"path": rel, "code": -1})
        return
    ext = os.path.splitext(rel)[1].lstrip(".").lower()
    source_dir = os.path.dirname(full)
    work_dir_obj = tempfile.TemporaryDirectory()
    work_dir = work_dir_obj.name
    if ext in ("c", "cpp", "cc", "cxx"):
        run_cmd, err = compile_source(full, ext, work_dir)
        if err:
            emit("run_output", {"path": rel, "text": err + "\n"})
            emit("run_exit", {"path": rel, "code": -1})
            work_dir_obj.cleanup()
            return
    elif ext == "py":
        run_cmd = [sys.executable, "-u", full]
    else:
        emit("run_output", {"path": rel, "text": f"[错误] 不支持的语言: .{ext}\n"})
        emit("run_exit", {"path": rel, "code": -1})
        work_dir_obj.cleanup()
        return
    try:
        # cwd 设为源文件目录,使 freopen 相对路径能找到 .in/.out
        proc = subprocess.Popen(
            run_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=source_dir
        )
    except Exception as e:
        emit("run_output", {"path": rel, "text": f"[错误] 启动失败: {e}\n"})
        emit("run_exit", {"path": rel, "code": -1})
        work_dir_obj.cleanup()
        return
    timer = threading.Timer(RUN_MAX_SECONDS, kill_console, args=(sid,))
    timer.daemon = True
    timer.start()
    with running_consoles_lock:
        running_consoles[sid] = {"proc": proc, "workdir": work_dir_obj, "timer": timer, "path": rel}
    # 通知客户端进程已启动，可发送初始输入
    emit("run_started", {"path": rel}, room=sid)
    threading.Thread(target=console_reader, args=(sid, proc, rel), daemon=True).start()

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
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)