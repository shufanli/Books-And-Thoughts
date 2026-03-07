"""
后台文件监听器：检测到根目录有新书文件，自动转换为 Markdown 并移入 _inbox/
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

REPO_ROOT = Path(__file__).parent.parent
INBOX = REPO_ROOT / "_inbox"
CONVERT = Path(__file__).parent / "convert.py"
SUPPORTED = {".pdf", ".epub", ".mobi", ".azw3", ".azw"}


def log(msg: str):
    print(msg, flush=True)


class BookHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        # 只处理直接放在根目录的文件，忽略子文件夹
        if path.parent != REPO_ROOT:
            return
        if path.suffix.lower() not in SUPPORTED:
            return
        # 等文件完整落盘
        time.sleep(1.5)
        self._process(path)

    def _process(self, src: Path):
        INBOX.mkdir(exist_ok=True)
        log(f"\n[书] 发现新书: {src.name}")

        result = subprocess.run(
            [sys.executable, str(CONVERT), str(src), "-o", str(INBOX)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            dest = INBOX / src.name
            shutil.move(str(src), dest)
            log(f"[✓] 转换完成，已移入 _inbox/{src.name}")
            log(f"    现在可以打开 Claude，告诉我「读 _inbox 里的书」")
        else:
            log(f"[✗] 转换失败: {result.stderr[:300]}")


def main():
    log(f"[监听中] 将 PDF/EPUB/MOBI/AZW3 拖入仓库根目录即可自动转换")
    log(f"        目录: {REPO_ROOT}\n")

    handler = BookHandler()
    observer = Observer()
    observer.schedule(handler, str(REPO_ROOT), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
