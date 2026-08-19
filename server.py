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
import hashlib

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

def ensure_firewall_rule(port=5000, rule_name=None):
    """尝试放行 Windows 防火墙入站端口, 使局域网内其他设备可访问。
    需要管理员权限; 失败时仅提示, 不影响启动。"""
    rule_name = rule_name or f"LAN_IDE {port}"
    try:
        proc = subprocess.run(
            ["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10
        )
        if rule_name in (proc.stdout or ""):
            print(f"[防火墙] 放行规则已存在: TCP {port}")
            return
        subprocess.run(
            ["netsh", "advfirewall", "firewall", "add", "rule",
             f"name={rule_name}", "dir=in", "action=allow",
             "protocol=TCP", f"localport={port}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15
        )
        print(f"[防火墙] 已添加放行规则: TCP {port}(局域网设备可访问 http://{get_ip()}:{port})")
    except Exception as e:
        print(f"[防火墙] 自动配置失败, 请以管理员身份运行一次: netsh advfirewall firewall add rule "
              f"name=\"{rule_name}\" dir=in action=allow protocol=TCP localport={port}  ({e})")

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

def scan_dir(path="", depth=0):
    # 深度上限: 防 symlink 环导致无限递归爆栈
    if depth > 16:
        return []
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
                "children": scan_dir(rel, depth + 1)
            })
        else:
            items.append({"name": name, "path": rel, "type": "file"})
    return items

# ---------- 编译运行 ----------
COMPILE_TIMEOUT = 20
RUN_TIMEOUT = 5
# c++17 优先: 与在线 OJ 一致, 编译最快且可生成体积最小的预编译头(PCH); 失败时再向更新标准降级。
CXX_STDS = ["c++17", "c++20", "c++23", "c++26"]
# 评测资源限制: 时间(秒)、内存(MB)、输出字节数
MEM_LIMIT_MB = 256
OUTPUT_LIMIT = 64 * 1024 * 1024

# 编译产物缓存目录(按源码内容哈希复用, 避免每次点击运行都重新编译)
COMPILE_CACHE_DIR = os.path.join(BASE_DIR, ".compile_cache")
os.makedirs(COMPILE_CACHE_DIR, exist_ok=True)
compile_lock = threading.Lock()

_compiler_cache = {}
_compiler_cache_lock = threading.Lock()

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

def cached_compiler(lang):
    """编译器路径结果缓存, 避免每次编译都重复 which 探测。"""
    with _compiler_cache_lock:
        if lang not in _compiler_cache:
            _compiler_cache[lang] = find_compiler(lang)
        return _compiler_cache[lang]

# ---------- 预编译头(PCH) ----------
# 将 <bits/stdc++.h> 预编译一次, 让 C++ 编译从约 5s(冷) 降到约 1.5s, 是「秒出答案」的关键。
PCH_DIR = os.path.join(COMPILE_CACHE_DIR, "pch")
os.makedirs(PCH_DIR, exist_ok=True)
PCH_HEADER_CONTENT = "#include <bits/stdc++.h>\n"
_pch_lock = threading.Lock()
_pch_generating = set()

def _pch_paths(compiler):
    key = hashlib.sha256(
        ((compiler or "") + "|" + PCH_HEADER_CONTENT).encode("utf-8", "ignore")
    ).hexdigest()
    hdr = os.path.join(PCH_DIR, key + ".h")
    return hdr, hdr + ".gch"

def _pch_build(compiler, hdr, gch):
    tmp_gch = gch + ".tmp"
    try:
        proc = subprocess.run(
            [compiler, "-std=c++17", "-O2", "-x", "c++-header", hdr, "-o", tmp_gch],
            capture_output=True, timeout=180
        )
        if proc.returncode == 0 and os.path.exists(tmp_gch):
            os.replace(tmp_gch, gch)  # 原子改名: 完整生成后才对编译可见
    except Exception:
        pass
    finally:
        try:
            if os.path.exists(tmp_gch):
                os.unlink(tmp_gch)
        except Exception:
            pass
        with _pch_lock:
            _pch_generating.discard((hdr, gch))

def ensure_pch(compiler):
    """PCH 不存在时后台生成; 返回当前是否可用。"""
    hdr, gch = _pch_paths(compiler)
    if os.path.exists(gch):
        return True
    with _pch_lock:
        if os.path.exists(gch):
            return True
        if (hdr, gch) in _pch_generating:
            return False
        _pch_generating.add((hdr, gch))
    try:
        with open(hdr, "w", encoding="utf-8") as f:
            f.write(PCH_HEADER_CONTENT)
    except Exception:
        with _pch_lock:
            _pch_generating.discard((hdr, gch))
        return False
    threading.Thread(target=_pch_build, args=(compiler, hdr, gch), daemon=True).start()
    return False

def warmup_pch():
    """服务启动后后台预热: 生成 bits/stdc++.h 预编译头, 加速首次点击运行。"""
    compiler = cached_compiler("cpp")
    if compiler:
        ensure_pch(compiler)

def _safe_remove(path):
    """删除文件, 忽略不存在/占用等异常(用于临时产物清理)。"""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass

COMPILE_CACHE_MAX_ENTRIES = 200  # 缓存的 exe 数量上限, 超出按最旧淘汰

def cleanup_compile_cache():
    """编译缓存容量控制: 超出上限时按修改时间淘汰最旧的条目。"""
    try:
        entries = [os.path.join(COMPILE_CACHE_DIR, n) for n in os.listdir(COMPILE_CACHE_DIR)
                   if not n.startswith("pch")]
        if len(entries) <= COMPILE_CACHE_MAX_ENTRIES:
            return
        entries.sort(key=lambda p: os.path.getmtime(p))
        for p in entries[:len(entries) - COMPILE_CACHE_MAX_ENTRIES]:
            _safe_remove(p)
    except OSError:
        pass

def compile_source(src_path, ext, work_dir):
    if ext == "c":
        compiler = cached_compiler("c")
        if not compiler:
            return None, "未找到 C 编译器，请安装 clang 或 gcc"
        stds = [None]
        pch_hdr = None
    elif ext in ("cpp", "cc", "cxx"):
        compiler = cached_compiler("cpp")
        if not compiler:
            return None, "未找到 C++ 编译器，请安装 clang++ 或 g++"
        stds = CXX_STDS
        pch_hdr = _pch_paths(compiler)[0] if ensure_pch(compiler) else None
    else:
        return None, f"不支持的语言: .{ext}"

    # 按「扩展名 + 编译器 + 源码内容」哈希, 命中缓存则跳过编译
    try:
        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
            src_text = f.read()
    except Exception:
        src_text = ""
    cache_key = hashlib.sha256(
        (ext + "|" + (compiler or "") + "|" + src_text).encode("utf-8", "ignore")
    ).hexdigest()
    cached_exe = os.path.join(COMPILE_CACHE_DIR, cache_key + (".exe" if platform.system() == "Windows" else ""))
    if os.path.exists(cached_exe):
        return [cached_exe], None

    with compile_lock:
        # 双重检查: 并发时可能已被其他线程编译完成
        if os.path.exists(cached_exe):
            return [cached_exe], None
        last_err = "编译失败"
        # 先编译到临时文件, 成功后 os.replace 原子进缓存:
        # 若直接 -o 缓存路径, 超时被 kill 时会留下半成品 exe, 之后同源码永远命中损坏缓存
        tmp_exe = cached_exe + ".tmp" + str(os.getpid()) + "-" + str(threading.get_ident())
        for i, s in enumerate(stds):
            cmd = [compiler]
            if s:
                cmd.append(f"-std={s}")
            # c++17 且 PCH 就绪时用预编译头加速; -pipe 减少磁盘 I/O, 关闭诊断颜色
            if s == "c++17" and pch_hdr:
                cmd += ["-include", pch_hdr]
            cmd += ["-O2", "-pipe", "-fdiagnostics-color=never", "-Wall", "-Wextra", "-o", tmp_exe, src_path]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=COMPILE_TIMEOUT)
            except subprocess.TimeoutExpired:
                _safe_remove(tmp_exe)
                return None, "编译超时"
            if proc.returncode == 0:
                try:
                    os.replace(tmp_exe, cached_exe)
                except OSError:
                    _safe_remove(tmp_exe)
                    return None, "缓存写入失败"
                cleanup_compile_cache()
                return [cached_exe], None
            last_err = proc.stderr or proc.stdout or "编译失败"
            _safe_remove(tmp_exe)
            # 仅当错误像「需要更新标准/标准不支持」时才尝试下一个标准, 语法错误不重复编译
            if s and i < len(stds) - 1:
                err_lower = last_err.lower()
                if not any(k in err_lower for k in [
                    "unrecognized", "invalid value", "unknown", "not found", "-std=",
                    "is not a member of", "was not declared", "has not been declared",
                    "no member named", "requires c++", "requires -std",
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
            encoding="utf-8", errors="replace", timeout=timeout, cwd=cwd
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

def run_process_with_stats(cmd, stdin_data="", timeout=RUN_TIMEOUT, cwd=None,
                           mem_limit_mb=MEM_LIMIT_MB, output_limit=OUTPUT_LIMIT):
    """运行程序并统计峰值内存(RSS)、墙钟时间与输出大小。
    超出时间→TLE、内存→MLE、输出→OLE, 否则返回 stdout/stderr/code。"""
    start = time.perf_counter()
    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", cwd=cwd
        )
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {"error": "RE", "stderr": str(e), "time_ms": elapsed_ms, "mem_kb": 0}

    mem_limit_bytes = mem_limit_mb * 1024 * 1024
    state = {
        "peak": 0,
        "over_mem": False,
        "over_out": False,
        "over_time": False,
        "stdout": "",
        "stderr": "",
    }

    def _kill():
        # 评测路径同样需要杀进程树, 防止被测程序 spawn 的子进程逃过超时 kill
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

    def reader(stream, key):
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                state[key] += chunk
                if len(state[key]) > output_limit:
                    state[key] = state[key][:output_limit]
                    state["over_out"] = True
                    _kill()
                    break
        except Exception:
            pass
        finally:
            try:
                stream.close()
            except Exception:
                pass

    def writer():
        try:
            if stdin_data:
                proc.stdin.write(stdin_data)
            proc.stdin.close()
        except Exception:
            pass

    mt = threading.Thread(target=monitor, daemon=True)
    t_out = threading.Thread(target=reader, args=(proc.stdout, "stdout"), daemon=True)
    t_err = threading.Thread(target=reader, args=(proc.stderr, "stderr"), daemon=True)
    t_in = threading.Thread(target=writer, daemon=True)
    mt.start()
    t_out.start()
    t_err.start()
    t_in.start()

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        state["over_time"] = True
        _kill()
        try:
            proc.wait(timeout=1)
        except Exception:
            pass

    for t in (t_in, t_out, t_err, mt):
        t.join(timeout=0.5)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    mem_kb = state["peak"] // 1024

    if state["over_time"]:
        return {"error": "TLE", "time_ms": elapsed_ms, "mem_kb": mem_kb}
    if state["over_mem"]:
        return {"error": "MLE", "time_ms": elapsed_ms, "mem_kb": mem_kb}
    if state["over_out"]:
        return {"error": "OLE", "time_ms": elapsed_ms, "mem_kb": mem_kb}

    return {
        "stdout": state["stdout"],
        "stderr": state["stderr"],
        "code": proc.returncode,
        "time_ms": elapsed_ms,
        "mem_kb": mem_kb,
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

    def definition(self, full_path, text, line, character):
        """转到声明/定义: 光标处标识符 → clangd textDocument/definition。
        clangd 对 declaration 请求的支持不如 definition 稳定, 因此统一走 definition
        (对函数/变量/类型基本等价于"跳转到声明/定义处", 与 VS Code F12 默认行为一致)。"""
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
presence_lock = threading.RLock()

# ---------- 用户身份 / 只读模式 / 使用统计 ----------
# clients: sid -> {"ip", "name", "device"}  当前 socket 连接的身份信息
# user_store: ip -> {name, readonly, code_chars, creates, deletes, uploads, saves, last_seen}
#   持久化到 BASE_DIR/users.json, 以 IP 为 key(同一台机子换浏览器/换名字统计仍累计)
clients = {}
clients_lock = threading.RLock()

# ---------- 全局在线用户(跨房间) ----------
# global_users: sid -> {"name", "ip", "device", "current_file", "last_active"}
global_users = {}
global_users_lock = threading.RLock()

USERS_DB = os.path.join(BASE_DIR, "users.json")
user_store = {}
user_store_lock = threading.Lock()
user_store_dirty = False

def _local_ip_set():
    """本机所有 IP(含回环): 从本机访问网页的用户视为管理员。"""
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

# 反查局域网 IP 的设备名(NetBIOS/DNS), 进程内缓存; 查不到回退为客户端上报的 UA 标签
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
    """展示用设备名: 服务器本机显示主机名, 其他优先反查结果, 否则用浏览器上报标签。"""
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
    """累计使用统计(内存累加, 由后台线程每 5s 落盘)。"""
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
    """写入用户数据字段; save_now=True 时立即落盘(只读开关等关键操作)。"""
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

def build_presence(rel):
    """构造 presence 事件负载: 每个在线者附带设备名/IP尾/只读/管理员标记, 供前端悬浮展示与管理。"""
    with presence_lock:
        sids = dict(presence.get(rel, {}))
        with clients_lock:
            info = {sid: dict(clients.get(sid, {})) for sid in sids}
    users = []
    for sid, name in sids.items():
        c = info.get(sid, {})
        ip = c.get("ip", "")
        users.append({
            "sid": sid,
            "name": name,
            "ip_tail": ip_tail(ip),
            "device": device_display(ip, c.get("device", "")),
            "readonly": is_readonly_ip(ip),
            "admin": is_admin_ip(ip),
        })
    return {"path": rel, "users": users, "sids": list(sids.keys())}

def _broadcast_global_presence():
    """向所有连接广播全局在线用户列表(跨房间), 前端据此渲染左下角在线用户。"""
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

def _presence_loop():
    while True:
        time.sleep(2)
        try:
            _broadcast_global_presence()
        except Exception:
            pass

threading.Thread(target=_presence_loop, daemon=True).start()

# ---------- OT 操作 (移植 ot.js TextOperation) ----------
class TextOperation:
    """组件列表表示的操作: 正数=保留(retain)、负数=删除(delete)、字符串=插入(insert)。
    一个操作可从 base_length 长的文档应用到 target_length 长的文档。"""
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
                out.append(text[i:i + op])
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
        """由单次替换 {start, end, text} 构造操作(需提供替换前文档长度)。"""
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
        """OT 核心: 对同一基文档的两个并发操作 a、b, 返回 (a', b')。
        满足 apply(apply(S, a), b') == apply(apply(S, b), a')。
        当两者在同一位置插入时, 优先保留 a 的插入(即 a 先于 b)。"""
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

# ---------- 协同文档权威状态: {path: {"content": str, "version": int, "history": [TextOperation,...], "history_start": int}} ----------
# history_start: history[0] 之前的版本数(裁剪发生时前移), 用于把全局版本号 base
# 换算成 history 内的下标: history[i] 产生版本 history_start + i + 1
docs = {}
docs_lock = threading.Lock()
DOC_HISTORY_LIMIT = 2000

def new_doc_state(content=""):
    return {"content": content, "version": 0, "history": [], "history_start": 0}

def append_history(d, op):
    """追加一个已应用到 d['content'] 的操作, 并维护 history 裁剪窗口。"""
    d["history"].append(op)
    if len(d["history"]) > DOC_HISTORY_LIMIT:
        cut = len(d["history"]) - DOC_HISTORY_LIMIT
        d["history"] = d["history"][cut:]
        d["history_start"] = d.get("history_start", 0) + cut

def get_doc_content(rel):
    """获取权威内容, 若未加载则从磁盘读入。"""
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
    """最后一个用户离开时: 在 docs_lock 内把权威内容落盘后移除缓存。
    必须在锁内完成「读缓存→写盘→pop」, 否则并发的 join 会在 pop 与写盘之间
    读到旧磁盘内容重新入缓存, 导致前一位用户的最后编辑被覆盖丢失。"""
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
            return  # 写盘失败保留缓存, 待下次尝试, 不丢内容
        docs.pop(rel, None)

# ---------- 交互式运行 ----------
RUN_MAX_SECONDS = 300
CONSOLE_RUN_TIMEOUT = 4  # 控制台「运行」的时间上限(秒), 超时判 TLE
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
    """杀掉整个进程树(含子进程), 防止被评测程序 spawn 的孙进程逃过 kill 继续占用资源。"""
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
    """流式运行程序: 每读到一块输出立即回调 on_output, 同时统计峰值内存/时间/输出大小。
    超出时间→TLE、内存→MLE、输出→OLE。stdin 喂入后默认立即关闭(EOF), 与 OJ 行为一致;
    keep_stdin=True 时保持 stdin 打开, 供控制台交互式运行后续追加输入。"""
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
            # keep_stdin 模式下不关闭 stdin, 否则控制台的 run_input 交互输入
            # 会写入已关闭的管道而静默失败(程序读到 EOF, 交互功能整体失效)
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
    """客户端身份信息: 是否管理员(服务器本机)/是否被设为只读。"""
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
    """管理员查看所有用户数据(只读标记/统计), 附带当前在线连接。仅服务器本机可访问。"""
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
    # 在线但还没有统计记录的 IP 也列出
    for ip, onl in online_by_ip.items():
        if ip and ip not in known:
            records.append({"ip": ip, "name": onl[0].get("name", ""), "online": onl})
    return jsonify(records)

@app.route("/api/admin/readonly", methods=["POST"])
def api_admin_readonly():
    """管理员把某个 IP 的用户设为/解除只读模式, 立即落盘并实时通知对方。"""
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
    # 实时通知目标的所有连接, 并刷新全局 presence 展示
    with clients_lock:
        for sid, c in clients.items():
            if c.get("ip") == ip:
                socketio.emit("readonly_changed", {"readonly": flag}, room=sid)
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
    # download=1 时以附件形式下发(浏览器弹出保存对话框), 实现云盘式下载; 否则内联用于预览
    as_attachment = request.args.get("download") == "1"
    return send_from_directory(os.path.dirname(full), os.path.basename(full),
                               mimetype=mime, as_attachment=as_attachment)

@app.route("/api/file", methods=["POST"])
def api_save():
    if is_readonly_ip(client_ip()):
        return jsonify({"error": "只读模式：管理员已禁止你修改内容"}), 403
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
    # 同步 OT 权威缓存: 若该文件已被协同会话加载, 将全文替换作为一个操作追加进历史,
    # 并广播给房间内客户端, 保证内存/磁盘/客户端三方一致(否则下一次 socket 保存会用旧内存覆盖磁盘)
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
                # 与 on_edit 一致: 广播必须在 docs_lock 内, 保证同一文件的
                # edit 事件严格按版本号顺序到达客户端, 避免锁外并发乱序触发误 resync
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

        req_ip = request.remote_addr or "127.0.0.1"
        # 用 IP 摘要做后缀: IPv6 地址含冒号, 直接拼进文件名在 Windows 上非法
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
            f.write(content if isinstance(content, str) else "")
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
    # 磁盘改名与 docs/presence 迁移必须在同一临界区, 否则窗口内其他客户端
    # 保存旧路径会把已改名的文件用旧内容重建出来(同一文件新旧两份并存)。
    # 锁顺序统一为 docs_lock -> presence_lock, 与 /api/delete 保持一致避免死锁。
    with docs_lock:
        os.rename(old_full, new_full)
        if old in docs:
            docs[new] = docs.pop(old)
        with presence_lock:
            if old in presence:
                presence[new] = presence.pop(old)
    # 先在旧 room 广播,让客户端更新 currentFile 并重新 join 新 room
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
    # 清理 OT 权威缓存(含目录下所有子文件), 否则残留缓存会在保存时重建已删除文件
    deleted_docs = []
    with docs_lock:
        if path in docs:
            deleted_docs.append(path)
            docs.pop(path, None)
        prefix = path.rstrip("/") + "/"
        for k in [k for k in docs if k.startswith(prefix)]:
            deleted_docs.append(k)
            docs.pop(k, None)
    # 同步清理 presence, 避免残留
    with presence_lock:
        presence.pop(path, None)
        for k in [k for k in presence if k.startswith(prefix)]:
            presence.pop(k, None)
    # 通知正在编辑被删文件的客户端立即停止编辑, 防止后续 edit/save 把文件"复活"
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
    # basename 后仍需校验(防 ".." / NTFS 备用数据流冒号等异常文件名)
    if not filename or filename in (".", "..") or ":" in filename or filename != filename.strip():
        return jsonify({"error": "非法文件名"}), 400
    save_path = os.path.join(WORKSPACE, filename)
    file.save(save_path)
    stat_add(client_ip(), uploads=1)
    socketio.emit('tree_changed', {})
    return jsonify({"ok": True, "name": filename})

MAX_ZIP_MEMBER_SIZE = 10 * 1024 * 1024  # 测试点单文件解压上限(防 zip 炸弹)

@app.route("/api/upload_tests", methods=["POST"])
def api_upload_tests():
    """上传 zip 测试包,解压到 {base}_T/ 文件夹,文件名统一为 {编号}.in/.out。"""
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
    # 记录导入前已存在的编号，避免同名测试点被静默覆盖/丢失
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
            # 先解析出 zip 内所有 (编号 -> {in, out}) 的映射，成对处理，
            # 避免只命中一半(比如只有 .in 没有 .out)时错位改号
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
                # 从文件名提取编号: 1.in -> 1, test1.in -> 1, sum.1.in -> 1
                m = re.match(r'^(?:.*?\.)*?(\d+)\.(in|out)$', low)
                if not m:
                    continue
                num, ext = m.group(1), m.group(2)
                pairs.setdefault(num, {})[ext] = name

            # 编号重映射：如果 zip 里的编号与工作区已有的测试点冲突，
            # 分配一个新的、当前不存在的编号，而不是覆盖原有测试点
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
                    # 单文件大小上限, 防 zip 炸弹(声明大小异常或解压超限直接拒绝)
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
        # 延迟清理(send_from_directory 需要文件存在); 用定时线程而非 atexit,
        # 避免频繁导出时临时 zip 累积到进程退出才释放
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
    # num 必须是纯数字, 防止 "../xxx" 之类路径注入逃逸测试目录删任意文件
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
    """从另一个源文件的测试点导入到当前文件, 编号冲突时自动重映射(不覆盖原有测试点)。"""
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

    # 解析源文件测试点: {num: {"in": path, "out": path}}, 只保留 in/out 成对的
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

    # 编号冲突时分配新的、不存在的编号, 而非覆盖原有测试点
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
    # num 必须是纯数字, 防止路径注入读取测试目录外文件
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
        # 运行期错误: TLE / MLE / OLE 由 error 字段直接给出
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
        # 首次遇到该 IP 时反查设备名(结果进程内缓存, 最多阻塞 1.5s)
        lookup_hostname(ip)
    join_room(rel)
    with presence_lock:
        presence.setdefault(rel, {})[request.sid] = username
        with clients_lock:
            clients[request.sid] = {"ip": ip, "name": username, "device": device}
    # 更新全局在线用户并广播(跨房间, 前端左下角列表)
    with global_users_lock:
        global_users[request.sid] = {
            "name": username,
            "ip": ip,
            "device": device,
            "current_file": rel,
            "last_active": int(time.time() * 1000),
        }
    _broadcast_global_presence()
    # 记录该 IP 最近使用的名字, 供管理员查看用户数据
    user_store_set(ip, name=username)
    # 推送当前权威内容与版本号, 确保新加入者/重连者立即拿到最新文档, 而不是过时的磁盘快照
    content, version = get_doc_content(rel)
    print(f"[join] sid={request.sid} path={rel} v={version} len={len(content)}")
    emit("doc_sync", {"path": rel, "content": content, "version": version}, room=request.sid)

@socketio.on("rename")
def on_rename(data):
    """用户点击左下角自己的名字改名: 更新所有所在房间并广播 presence。"""
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
        # 最后一个用户离开时, 把权威内容落盘后淘汰缓存, 保证磁盘始终是最新的
        _flush_and_evict_doc(rel)
    # 全局 presence 由周期广播 + 加入/离开/改名事件统一推送, 房间内广播已废弃

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
    # 用户是最后在线者的文件: 落盘并淘汰缓存,
    # 避免直接关浏览器(不发 leave)时未保存编辑随进程退出丢失、docs 只增不减
    for rel in emptied:
        _flush_and_evict_doc(rel)
    with global_users_lock:
        global_users.pop(request.sid, None)
    _broadcast_global_presence()
    kill_console(request.sid)
    cleanup_console(request.sid)

@socketio.on("edit")
def on_edit(data):
    rel = data.get("path")
    op_data = data.get("op")
    if not rel or op_data is None:
        print(f"[edit DEBUG] early return: rel={rel} op_data is None={op_data is None}")
        return {"version": None}
    # 只读模式: 拒绝协同编辑
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
                # 磁盘上不存在该文件(正常流程新建文件都会先落盘, 走到这里说明文件已被删除):
                # 拒绝编辑并回滚本次 setdefault 的空缓存, 防止后续保存把已删文件"复活"为空文件
                if docs.get(rel) is d:
                    docs.pop(rel, None)
                return {"version": None, "deleted": True}
        content = d["content"]
        version = d["version"]
        history = d["history"]
        history_start = d.get("history_start", 0)

        # 操作格式: 组件数组(新客户端) 或 {start,end,text}(旧客户端兼容)
        clamped = False
        if isinstance(op_data, list):
            try:
                op = TextOperation.from_json(op_data)
            except Exception as _e:
                print(f"[edit DEBUG] from_json failed: op_data={op_data} err={_e}")
                return {"version": None}
        elif isinstance(op_data, dict):
            try:
                start = int(op_data.get("start", 0))
                end = int(op_data.get("end", start))
                text = normalize_newlines(op_data.get("text", ""))
            except (TypeError, ValueError) as _e:
                print(f"[edit DEBUG] dict parse failed: err={_e}")
                return {"version": None}
            # 依据 base 版本确定替换前的文档长度(history 裁剪后需换算下标)
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
            print(f"[edit DEBUG] op_data is neither list nor dict: type={type(op_data).__name__}")
            return {"version": None}

        # 变换到当前权威版本(线性历史, base 需换算到裁剪窗口内下标)
        if 0 <= base < version:
            if base < history_start or version - base > len(history):
                print(f"[edit] resync: base={base} < history_start={history_start} or gap>history (v={version}, h={len(history)})")
                return {"version": None, "resync": True}
            try:
                for past in history[base - history_start:]:
                    op, _ = TextOperation.transform(op, past)
            except ValueError as _te:
                # transform 与 apply 一样可能因 op 与 base 版本长度不符抛 ValueError,
                # 必须捕获并返回 resync, 否则 handler 崩溃且客户端永远收不到 ack
                print(f"[edit] resync: transform failed base={base} version={version} err={_te}")
                return {"version": None, "resync": True}

        try:
            new_content = op.apply(content)
        except ValueError as _ve:
            print(f"[edit] resync: apply failed op.baseLength={getattr(op, 'base_length', '?')} content.len={len(content)} base={base} version={version} err={_ve}")
            return {"version": None, "resync": True}

        d["content"] = new_content
        d["version"] = version + 1
        append_history(d, op)
        final_version = d["version"]
        op_json = op.to_json()

        # 广播必须在 docs_lock 内、版本号写入后立即发生, 且早于本函数向发送者返回 ack。
        # 若放到锁外, threading async_mode 下并发的另一个 on_edit 线程可能先完成
        # 自己的加锁->广播->返回, 导致同一文件的多个 edit 广播/ack 在网络层乱序到达
        # 客户端, 使客户端的 otDrain() 长时间等不到 otRevision+1 而触发 resyncDoc(),
        # 把编辑器错误地切换为只读(即“先编辑者被顶成只读, 新加入者反而能写”的 bug)。
        # 在锁内广播可以保证同一文件的所有 edit 事件严格按版本号顺序发出。
        emit("edit", {"path": rel, "op": op_json, "version": final_version}, room=rel, include_self=False)

    # 统计代码量: 按插入的字符数累计到该用户 IP
    inserted = sum(len(x) for x in op.ops if isinstance(x, str))
    if inserted:
        stat_add(c_ip, code_chars=inserted)

    return {"version": final_version, "op": op_json, "clamped": clamped, "resync": False}

@socketio.on("cursor")
def on_cursor(data):
    rel = data.get("path")
    if not rel:
        return
    # 光标偏移量校验: 非法值直接丢弃, 防止接收端 getPositionAt 抛异常
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
    # 更新全局在线用户的活跃时间与当前文件(由周期性广播推送给前端)
    with global_users_lock:
        if request.sid in global_users:
            global_users[request.sid]["last_active"] = int(time.time() * 1000)
            global_users[request.sid]["current_file"] = rel
    emit("cursor", data, room=rel, include_self=False)

@socketio.on("save")
def on_save(data):
    """持久化: 优先写入 OT 权威内容; 权威已卸载时用客户端带来的内容兜底。
    不重置版本号/历史(协同状态保持连续)。"""
    rel = data.get("path")
    if not rel:
        return
    # 只读模式: 拒绝保存
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
            # 权威缓存不在(可能刚被 /api/delete 清理): 仅当磁盘文件仍存在时才兜底写盘,
            # 避免用客户端内容把已删除的文件重建出来
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

@socketio.on("lsp_definition")
def on_lsp_definition(data):
    """转到声明/定义(F12 / 右键菜单): 请求 clangd textDocument/definition,
    将结果 URI 转回 workspace 相对路径返回给前端, 前端负责打开目标文件并跳转定位。
    跨文件声明时, uri_to_rel 会把 clangd 返回的 file:// URI 转换成相对路径;
    若声明位于 workspace 之外(如系统头文件), 返回 outside=True 让前端提示用户。"""
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
    # LSP definition 返回值可能是: Location | Location[] | LocationLink[] | null
    locations = []
    if isinstance(resp, list):
        locations = resp
    elif isinstance(resp, dict):
        locations = [resp]
    if not locations:
        return {"found": False}
    loc = locations[0]
    # LocationLink 用 targetUri/targetSelectionRange, 普通 Location 用 uri/range
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
    """OJ 式一次性运行: 先输入(stdin)→编译→运行→流式输出, 超时/超内存/超输出给出 TLE/MLE/OLE。"""
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
    # 后台预热编译环境(探测编译器/标准 + 生成 bits/stdc++.h 预编译头), 加速首次点击运行
    threading.Thread(target=warmup_pch, daemon=True).start()
    # 后台放行防火墙端口, 保证局域网其他设备可访问(需管理员权限, 失败不影响启动)
    threading.Thread(target=ensure_firewall_rule, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)