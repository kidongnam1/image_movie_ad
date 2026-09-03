from __future__ import annotations
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "input_images"
SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def safe_name(text: str) -> str:
    import re
    v = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", (text or "product").strip()).strip("_")
    return v or "product"


def image_target(product: str, suffix: str = ".png") -> Path:
    day = datetime.now().strftime("%Y%m%d")
    stamp = datetime.now().strftime("%H%M%S_%f")
    folder = IMAGE_DIR / day
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{safe_name(product)}_{stamp}{suffix.lower()}"


def import_image_file(src: str | Path, product: str = "product") -> Path:
    p = Path(src)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(p)
    if p.suffix.lower() not in SUPPORTED:
        raise ValueError(f"지원 이미지 형식: {', '.join(sorted(SUPPORTED))}")
    dst = image_target(product, p.suffix.lower())
    shutil.copy2(p, dst)
    return dst


def save_pil_image(image: Any, product: str = "product") -> Path:
    dst = image_target(product, ".png")
    image.convert("RGB").save(dst, "PNG")
    return dst


def grab_clipboard_image(product: str = "product") -> Path:
    try:
        from PIL import Image, ImageGrab
    except ImportError as exc:
        raise RuntimeError("클립보드 이미지 기능에는 Pillow가 필요합니다. pip install Pillow") from exc
    grabbed = ImageGrab.grabclipboard()
    if isinstance(grabbed, Image.Image):
        return save_pil_image(grabbed, product)
    if isinstance(grabbed, list) and grabbed:
        first = Path(grabbed[0])
        if first.suffix.lower() in SUPPORTED:
            return import_image_file(first, product)
    raise RuntimeError("클립보드에 이미지가 없습니다. 화면 캡처 후 Ctrl+V를 다시 시도하세요.")


def launch_gui() -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    try:
        from PIL import Image, ImageTk
    except ImportError as exc:
        raise RuntimeError("GUI 이미지 미리보기에는 Pillow가 필요합니다. pip install Pillow") from exc

    root = tk.Tk()
    root.title("Image Movie Ad V2.7 - 상품 이미지 / 광고 입력")
    root.geometry("1080x720")
    root.minsize(920, 620)
    image_path = tk.StringVar(value="")
    status = tk.StringVar(value="상품 이미지를 Ctrl+V로 붙이거나 파일로 불러오세요.")
    product = tk.StringVar(); must = tk.StringVar(); features = tk.StringVar(); pain = tk.StringVar(); target = tk.StringVar(value="일반 소비자"); intensity = tk.StringVar(value="4")
    preview_ref: dict[str, Any] = {}

    main = ttk.Frame(root, padding=16); main.pack(fill="both", expand=True)
    left = ttk.Frame(main); left.pack(side="left", fill="y", padx=(0,16))
    right = ttk.Frame(main); right.pack(side="right", fill="both", expand=True)

    def row(label: str, var: tk.StringVar, width: int = 46):
        ttk.Label(left, text=label).pack(anchor="w", pady=(8,2))
        e=ttk.Entry(left,textvariable=var,width=width);e.pack(fill="x");return e

    product_entry=row("상품명 *", product)
    row("반드시 강조할 특징", must)
    row("추가 특징", features)
    row("고객 Pain Point", pain)
    row("타깃 고객", target)
    row("광고 강도 1~5", intensity)

    ttk.Separator(left).pack(fill="x", pady=14)
    ttk.Label(left,text="상품 이미지").pack(anchor="w")
    path_label=ttk.Label(left,textvariable=image_path,wraplength=360);path_label.pack(anchor="w",pady=(4,8))

    preview = ttk.Label(right, anchor="center", text="이미지 미리보기\n\nCtrl+V 또는 [이미지 파일 불러오기]")
    preview.pack(fill="both", expand=True)

    def show(path: Path):
        img=Image.open(path); img.thumbnail((620,540)); photo=ImageTk.PhotoImage(img);preview.configure(image=photo,text="");preview_ref["photo"]=photo;image_path.set(str(path));status.set(f"이미지 준비 완료: {path.name}")

    def paste(_event=None):
        try: show(grab_clipboard_image(product.get() or "product"))
        except Exception as exc: messagebox.showwarning("클립보드 이미지",str(exc));status.set(str(exc))
        return "break"

    def load_file():
        p=filedialog.askopenfilename(title="상품 이미지 선택",filetypes=[("Image files","*.png *.jpg *.jpeg *.webp *.bmp"),("All files","*.*")])
        if not p:return
        try: show(import_image_file(p,product.get() or "product"))
        except Exception as exc: messagebox.showerror("이미지 불러오기 실패",str(exc))

    def args_common():
        if not product.get().strip(): raise ValueError("상품명을 입력하세요.")
        try:i=int(intensity.get() or "4")
        except ValueError:raise ValueError("광고 강도는 1~5 숫자로 입력하세요.")
        if i not in range(1,6):raise ValueError("광고 강도는 1~5입니다.")
        args=[product.get().strip(),"--must-emphasize",must.get(),"--features",features.get(),"--pain-point",pain.get(),"--target",target.get() or "일반 소비자","--intensity",str(i)]
        if image_path.get(): args += ["--image", image_path.get()]
        return args

    def run(cmd: list[str], label: str):
        try:
            status.set(label+" 실행 중...");root.update_idletasks();r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace")
            if r.returncode: raise RuntimeError((r.stdout+"\n"+r.stderr)[-2500:])
            status.set(label+" 완료");messagebox.showinfo("완료",label+" 완료\n결과 폴더를 확인하세요.")
        except Exception as exc:status.set(label+" 실패");messagebox.showerror("실행 실패",str(exc))

    def generate_script():
        try: args=args_common()
        except Exception as exc:messagebox.showwarning("입력 확인",str(exc));return
        run([sys.executable,str(ROOT/"generator"/"script_generator_v2.py"),*args],"광고 대본 생성")

    def generate_package():
        try: args=args_common()
        except Exception as exc:messagebox.showwarning("입력 확인",str(exc));return
        run([sys.executable,str(ROOT/"generator"/"creative_package_v26.py"),*args],"Creative Package 생성")

    btns=ttk.Frame(left);btns.pack(fill="x",pady=10)
    ttk.Button(btns,text="Ctrl+V 이미지 붙여넣기",command=paste).pack(fill="x",pady=3)
    ttk.Button(btns,text="이미지 파일 불러오기",command=load_file).pack(fill="x",pady=3)
    ttk.Button(btns,text="광고 대본 생성",command=generate_script).pack(fill="x",pady=(14,3))
    ttk.Button(btns,text="UGC / Demo / Cinematic 패키지 생성",command=generate_package).pack(fill="x",pady=3)
    ttk.Label(left,textvariable=status,wraplength=360).pack(anchor="w",pady=12)
    ttk.Label(left,text="이미지는 input_images 폴더에 로컬 보관되며 GitHub에는 업로드되지 않습니다.",wraplength=360).pack(anchor="w")

    root.bind_all("<Control-v>",paste)
    product_entry.focus_set();root.mainloop();return 0


def main() -> int:
    return launch_gui()

if __name__=="__main__":raise SystemExit(main())
