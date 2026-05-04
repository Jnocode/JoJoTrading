"""
JoJo Trading — Portable Environment Launcher
==============================================
自動部署可攜式 Python 環境，讓使用者無需安裝 Python 即可啟動 Desktop App。

用法:
    python portable_launcher.py          # 首次: 自動部署環境 + 啟動 App
    python portable_launcher.py --setup  # 只執行環境部署，不啟動 App
    python portable_launcher.py --check  # 只執行環境健康檢查

基於 portable-app-pattern Skill 的 5 大核心支柱設計。
"""
import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
import ssl
import time
from pathlib import Path

# ============================================================
# 支柱 1: 目錄結構沙盒化
# ============================================================
LAUNCHER_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = LAUNCHER_DIR.parent  # jojo_trading/

RUNTIME_DIR = LAUNCHER_DIR / "runtime_python"
LIBS_DIR = LAUNCHER_DIR / "trading_libs"
LOCAL_PYTHON = RUNTIME_DIR / "python.exe"

SRC_DIR = PROJECT_ROOT / "src"

# Python 3.11.9 Embeddable (Windows x64)
PYTHON_VERSION = "3.11.9"
PYTHON_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_VERSION}/"
    f"python-{PYTHON_VERSION}-embed-amd64.zip"
)
PYTHON_PTH_NAME = "python311._pth"

# Desktop App 所需的依賴 (排除 streamlit — 只有 Web App 使用)
# 完整掃描自 src/ 目錄的所有 import 語句 (2026-05-02)
DESKTOP_DEPENDENCIES = [
    # --- GUI ---
    "PySide6>=6.5.0",
    # --- 資料分析 ---
    "pandas>=1.5.0",
    "numpy>=1.21.0",
    "plotly>=5.15.0",
    "matplotlib",
    "mplfinance",
    # --- 資料來源 ---
    "yfinance>=0.2.18",
    "FinMind",
    "requests>=2.28.0",
    "urllib3",
    "beautifulsoup4",
    # --- AI 引擎 ---
    # Gemini: 改用 REST API 直接呼叫，不再需要 google-generativeai SDK
    # Ollama: 使用 requests 呼叫本機 REST API，不需額外套件
    "groq",  # Groq 仍需 SDK
    # --- 工具 / 基礎設施 ---
    "openpyxl>=3.1.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "sqlalchemy>=2.0.0",
    "psutil>=5.9.0",
    # --- 安全 / 認證 ---
    "bcrypt",
    "PyJWT",
    # --- 券商 API ---
    "shioaji>=1.2.0",
]


def log(msg: str):
    """統一日誌格式"""
    print(f"  {msg}")


def log_section(title: str):
    """區段標題"""
    print(f"\n{'='*56}")
    print(f"  {title}")
    print(f"{'='*56}")


# ============================================================
# 支柱 3: 靜態 Python 解封裝
# ============================================================
def fix_python_pth():
    """修改 ._pth 檔以解鎖 pip 與 site-packages"""
    pth_file = RUNTIME_DIR / PYTHON_PTH_NAME
    if not pth_file.exists():
        # 嘗試尋找任何 ._pth 檔
        pth_files = list(RUNTIME_DIR.glob("*._pth"))
        if not pth_files:
            log("⚠️  找不到 ._pth 檔案，跳過修改")
            return
        pth_file = pth_files[0]

    with open(pth_file, "r") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    # 必須包含的項目
    required = [
        "python311.zip",
        ".",
        "Lib/site-packages",
        f"..\\{LIBS_DIR.name}",
        "import site",
    ]

    changed = False
    for item in required:
        if item not in lines:
            # 檢查是否被註解
            commented = f"#{item}"
            if commented in lines:
                lines[lines.index(commented)] = item
            else:
                lines.append(item)
            changed = True

    if changed:
        with open(pth_file, "w") as f:
            f.write("\n".join(lines) + "\n")
        log(f"✅ 已修改 {pth_file.name} (解鎖 pip + site-packages)")
    else:
        log(f"✅ {pth_file.name} 已是正確狀態")


# ============================================================
# 下載與解壓工具
# ============================================================
def download_file(url: str, dest: Path, description: str = ""):
    """下載檔案 (含進度顯示)"""
    desc = description or url.split("/")[-1]
    log(f"📥 正在下載 {desc}...")

    # SSL context (部分企業環境需要)
    # NOTE: 生產環境建議使用 certifi 修復憑證鏈
    ctx = ssl.create_default_context()
    try:
        urllib.request.urlopen(url, context=ctx)
    except ssl.SSLError:
        log("⚠️  SSL 驗證失敗，降級為不驗證模式")
        ctx = ssl._create_unverified_context()

    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx)
    )
    opener.addheaders = [("User-agent", "Mozilla/5.0")]
    urllib.request.install_opener(opener)

    urllib.request.urlretrieve(url, dest)
    log(f"✅ 下載完成: {dest.name}")


def extract_zip(zip_path: Path, target_dir: Path):
    """解壓 ZIP 檔"""
    log(f"📦 正在解壓 {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP 檔案損壞: {bad}")
        zf.extractall(target_dir)
    zip_path.unlink()
    log("✅ 解壓完成")


# ============================================================
# 環境部署流程
# ============================================================
def setup_python():
    """下載並設定 Embeddable Python"""
    if LOCAL_PYTHON.exists():
        log("✅ Embeddable Python 已存在，跳過下載")
        return

    RUNTIME_DIR.mkdir(exist_ok=True)
    zip_path = RUNTIME_DIR / "python_embed.zip"
    download_file(PYTHON_URL, zip_path, f"Python {PYTHON_VERSION} Embeddable")
    extract_zip(zip_path, RUNTIME_DIR)
    fix_python_pth()


def setup_pip():
    """確保 pip 可用"""
    pip_check = subprocess.run(
        [str(LOCAL_PYTHON), "-m", "pip", "--version"],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if pip_check.returncode == 0:
        log("✅ pip 已可用")
        return

    log("📥 正在安裝 pip...")
    get_pip = RUNTIME_DIR / "get-pip.py"
    download_file("https://bootstrap.pypa.io/get-pip.py", get_pip, "get-pip.py")

    subprocess.run(
        [str(LOCAL_PYTHON), str(get_pip)],
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=True,
    )
    if get_pip.exists():
        get_pip.unlink()
    log("✅ pip 安裝完成")


def install_dependencies():
    """安裝 Desktop App 依賴到 trading_libs/"""
    LIBS_DIR.mkdir(exist_ok=True)

    # ──────────────────────────────────────────────
    # 智能缺失偵測: 逐一檢查關鍵套件是否可 import
    # ──────────────────────────────────────────────
    # 映射: pip 套件名 → Python import 名 (只列不同的)
    IMPORT_MAP = {
        "PySide6": "PySide6",
        "pandas": "pandas",
        "numpy": "numpy",
        "plotly": "plotly",
        "matplotlib": "matplotlib",
        "mplfinance": "mplfinance",
        "yfinance": "yfinance",
        "FinMind": "FinMind",
        "requests": "requests",
        "beautifulsoup4": "bs4",
        "openpyxl": "openpyxl",
        "python-dotenv": "dotenv",
        "pydantic": "pydantic",
        "sqlalchemy": "sqlalchemy",
        "psutil": "psutil",
        "bcrypt": "bcrypt",
        "PyJWT": "jwt",
        "groq": "groq",
        "shioaji": "shioaji",
        "loguru": "loguru",
    }

    # 建構子進程環境，確保能找到 trading_libs 中的套件
    check_env = os.environ.copy()
    check_env["PYTHONPATH"] = str(LIBS_DIR)

    missing_packages = []
    for pip_name, import_name in IMPORT_MAP.items():
        result = subprocess.run(
            [str(LOCAL_PYTHON), "-c", f"import {import_name}"],
            capture_output=True,
            env=check_env,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            missing_packages.append(pip_name)

    if not missing_packages:
        log("✅ 所有必要套件已就緒")
        return

    log(f"⚠️  偵測到 {len(missing_packages)} 個缺失套件:")
    for pkg in missing_packages:
        log(f"   • {pkg}")
    log("")

    pip_cmd = [
        str(LOCAL_PYTHON), "-m", "pip", "install",
        "--target", str(LIBS_DIR),
        "--upgrade",
        "--no-warn-script-location",
    ]

    # 區分安裝批次: 大型套件單獨裝，避免一個失敗拖垮全部
    heavy_packages = {"PySide6", "shioaji"}
    light_missing = [p for p in missing_packages if p not in heavy_packages]
    heavy_missing = [p for p in missing_packages if p in heavy_packages]

    if light_missing:
        log(f"  [1/2] 安裝一般套件 ({len(light_missing)} 個)...")
        try:
            subprocess.run(
                pip_cmd + light_missing,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True,
            )
            log(f"  ✅ 一般套件安裝完成")
        except subprocess.CalledProcessError as e:
            log(f"  ⚠️ 部分套件安裝失敗，嘗試逐一安裝...")
            for pkg in light_missing:
                try:
                    subprocess.run(
                        pip_cmd + [pkg],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        check=True,
                    )
                    log(f"    ✅ {pkg}")
                except subprocess.CalledProcessError:
                    log(f"    ❌ {pkg} 安裝失敗 (非致命，繼續)")

    if heavy_missing:
        log(f"  [2/2] 安裝大型套件 ({', '.join(heavy_missing)})...")
        for pkg in heavy_missing:
            try:
                subprocess.run(
                    pip_cmd + [pkg],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True,
                )
                log(f"    ✅ {pkg}")
            except subprocess.CalledProcessError:
                log(f"    ❌ {pkg} 安裝失敗 (非致命，繼續)")

    log("\n✅ 依賴修復完成！")


# ============================================================
# 支柱 2: 運行時環境劫持
# ============================================================
def hijack_environment():
    """劫持 PATH、PYTHONPATH，讓沙盒資源優先"""
    os.environ["PATH"] = (
        f"{RUNTIME_DIR}{os.pathsep}"
        f"{RUNTIME_DIR / 'Scripts'}{os.pathsep}"
        f"{os.environ.get('PATH', '')}"
    )
    os.environ["PYTHONPATH"] = str(LIBS_DIR)

    # Windows DLL 搜尋路徑 (Python 3.8+)
    if hasattr(os, "add_dll_directory"):
        for search_dir in [RUNTIME_DIR, LIBS_DIR]:
            if search_dir.exists():
                try:
                    os.add_dll_directory(str(search_dir))
                except OSError:
                    pass
                # 遞迴搜尋 bin/ 和 lib/ 子目錄 (shioaji DLLs)
                for subdir in search_dir.rglob("bin"):
                    try:
                        os.add_dll_directory(str(subdir))
                    except OSError:
                        pass


# ============================================================
# 環境健康檢查
# ============================================================
def check_dotnet():
    """檢查 .NET Framework (shioaji 依賴)"""
    try:
        result = subprocess.run(
            ["dotnet", "--info"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode == 0:
            log("✅ .NET Runtime 已安裝")
            return True
    except FileNotFoundError:
        pass

    # Fallback: 檢查 Windows Registry
    dotnet_dir = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Microsoft.NET"
    if dotnet_dir.exists():
        log("✅ .NET Framework 已安裝 (Windows 內建)")
        return True

    log("⚠️  未偵測到 .NET Runtime")
    log("   shioaji 需要 .NET 才能正常運作")
    log("   下載: https://dotnet.microsoft.com/download")
    return False


def health_check():
    """執行完整環境健康檢查"""
    log_section("環境健康檢查")
    all_ok = True

    # 1. Python
    if LOCAL_PYTHON.exists():
        log(f"✅ Python: {LOCAL_PYTHON}")
    else:
        log(f"❌ Python 不存在: {LOCAL_PYTHON}")
        all_ok = False

    # 2. trading_libs
    if (LIBS_DIR / "PySide6").exists():
        log("✅ PySide6: 已安裝")
    else:
        log("❌ PySide6: 未安裝")
        all_ok = False

    if (LIBS_DIR / "shioaji").exists():
        log("✅ shioaji: 已安裝")
    else:
        log("❌ shioaji: 未安裝")
        all_ok = False

    # 3. .NET
    check_dotnet()

    # 4. 專案原始碼
    entry_point = PROJECT_ROOT / "desktop_app" / "real_desktop_app.py"
    if entry_point.exists():
        log(f"✅ Desktop App 入口: {entry_point.name}")
    else:
        log(f"❌ 找不到: {entry_point}")
        all_ok = False

    # 5. 路徑中的特殊字元
    if any(ord(c) > 127 for c in str(LAUNCHER_DIR)):
        log("⚠️  路徑含非 ASCII 字元，可能影響部分套件")
        log(f"   當前路徑: {LAUNCHER_DIR}")

    if all_ok:
        log("\n🎉 環境健康檢查全部通過！")
    else:
        log("\n⚠️  部分檢查未通過，請先執行: portable_launcher.py --setup")

    return all_ok


# ============================================================
# 啟動 Desktop App
# ============================================================
def launch_app():
    """啟動 JoJo Trader Desktop App"""
    log_section("啟動 JoJo Trader Desktop")

    hijack_environment()

    entry_point = LAUNCHER_DIR / "real_desktop_app.py"
    if not entry_point.exists():
        log(f"❌ 找不到桌面應用入口: {entry_point}")
        return False

    log(f"🚀 正在啟動 {entry_point.name}...")

    # 建構 subprocess 環境
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{LIBS_DIR}{os.pathsep}{SRC_DIR}"

    process = subprocess.Popen(
        [str(LOCAL_PYTHON), str(entry_point)],
        cwd=str(LAUNCHER_DIR),
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    log(f"✅ Desktop App 已啟動 (PID: {process.pid})")
    return True


# ============================================================
# 主流程
# ============================================================
def main():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║          JoJo Trader — Portable Launcher            ║")
    print("║          台股智慧投資分析系統 (可攜式啟動器)           ║")
    print("╚══════════════════════════════════════════════════════╝")

    # 解析命令列參數
    args = sys.argv[1:]

    if "--check" in args:
        health_check()
        return

    if "--deps-check" in args:
        log("🔍 正在掃描缺失套件...")
        install_dependencies()
        return

    if "--setup" in args or not LOCAL_PYTHON.exists():
        log_section("Phase 1: 部署 Embeddable Python")
        setup_python()

        log_section("Phase 2: 安裝 pip")
        setup_pip()

        log_section("Phase 3: 安裝依賴套件")
        install_dependencies()

        log_section("Phase 4: 環境健康檢查")
        check_dotnet()

        if "--setup" in args:
            log("\n✅ 環境部署完成！可使用 run_portable.bat 啟動。")
            return

    # 啟動 App
    launch_app()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[中斷] 使用者取消操作。")
    except Exception as e:
        print(f"\n❌ 啟動失敗: {e}")
        import traceback
        traceback.print_exc()
        print("\n請嘗試: portable_launcher.py --setup 重新部署環境")
        input("按 Enter 鍵關閉...")
