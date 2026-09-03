from __future__ import annotations
import hashlib
import ipaddress
import json
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "input_images"
SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
RIGHTS_OK = {
    "내가 직접 촬영/제작",
    "상업 이용 라이선스 보유",
    "판매자/권리자 사용허락",
    "퍼블릭 도메인/상업 이용 가능 라이선스",
}
RIGHTS_OPTIONS = ["확인 필요", *sorted(RIGHTS_OK)]
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024


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


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_provenance(path: str | Path, *, source_type: str, source: str = "", rights_basis: str = "확인 필요") -> Path:
    p = Path(path)
    meta = {
        "asset": str(p),
        "source_type": source_type,
        "source": source,
        "rights_basis": rights_basis,
        "approved_for_ad_use": rights_basis in RIGHTS_OK,
        "sha256": sha256_file(p),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "policy_note": "워터마크 제거, 출처 은폐, 저작권 회피를 수행하지 않습니다. 실제 광고 사용 전 권리/라이선스를 확인하세요.",
    }
    sidecar = p.with_suffix(p.suffix + ".source.json")
    sidecar.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return sidecar


def import_image_file(src: str | Path, product: str = "product", rights_basis: str = "확인 필요") -> Path:
    p = Path(src)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(p)
    if p.suffix.lower() not in SUPPORTED:
        raise ValueError(f"지원 이미지 형식: {', '.join(sorted(SUPPORTED))}")
    dst = image_target(product, p.suffix.lower())
    shutil.copy2(p, dst)
    write_provenance(dst, source_type="local_file", source=str(p.resolve()), rights_basis=rights_basis)
    return dst


def save_pil_image(image: Any, product: str = "product", rights_basis: str = "확인 필요", source_type: str = "clipboard") -> Path:
    dst = image_target(product, ".png")
    image.convert("RGB").save(dst, "PNG")
    write_provenance(dst, source_type=source_type, source="Windows clipboard", rights_basis=rights_basis)
    return dst


def grab_clipboard_image(product: str = "product", rights_basis: str = "확인 필요") -> Path:
    try:
        from PIL import Image, ImageGrab
    except ImportError as exc:
        raise RuntimeError("클립보드 이미지 기능에는 Pillow가 필요합니다. pip install Pillow") from exc
    grabbed = ImageGrab.grabclipboard()
    if isinstance(grabbed, Image.Image):
        return save_pil_image(grabbed, product, rights_basis)
    if isinstance(grabbed, list) and grabbed:
        first = Path(grabbed[0])
        if first.suffix.lower() in SUPPORTED:
            return import_image_file(first, product, rights_basis)
    raise RuntimeError("클립보드에 이미지가 없습니다. 화면 캡처 후 Ctrl+V를 다시 시도하세요.")


def _validate_remote_url(url: str) -> None:
    u = urlparse(url.strip())
    if u.scheme not in {"http", "https"} or not u.hostname:
        raise ValueError("http:// 또는 https:// 이미지 URL만 지원합니다.")
    if u.username or u.password:
        raise ValueError("아이디/비밀번호가 포함된 URL은 지원하지 않습니다.")
    host = u.hostname.lower()
    if host in {"localhost", "localhost.localdomain"}:
        raise ValueError("로컬 주소 URL은 지원하지 않습니다.")
    try:
        for info in socket.getaddrinfo(host, u.port or (443 if u.scheme == "https" else 80)):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise ValueError("사설망/로컬 네트워크 이미지 URL은 지원하지 않습니다.")
    except socket.gaierror as exc:
        raise ValueError("이미지 URL의 호스트를 확인할 수 없습니다.") from exc


def download_image_url(url: str, product: str = "product", rights_basis: str = "확인 필요") -> Path:
    _validate_remote_url(url)
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("URL 이미지 가져오기에는 requests가 필요합니다.") from exc
    with requests.get(url, stream=True, timeout=(8, 20), allow_redirects=True, headers={"User-Agent": "ImageMovieAd/2.7"}) as r:
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        if not ctype.startswith("image/"):
            raise ValueError(f"직접 이미지 URL이 아닙니다. Content-Type={ctype or 'unknown'}")
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/bmp": ".bmp"}.get(ctype, ".img")
        if suffix == ".img":
            raise ValueError(f"지원하지 않는 이미지 형식입니다: {ctype}")
        dst = image_target(product, suffix)
        size = 0
        with dst.open("wb") as f:
            for chunk in r.iter_content(1024 * 256):
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_DOWNLOAD_BYTES:
                    f.close(); dst.unlink(missing_ok=True)
                    raise ValueError("이미지가 20MB를 초과합니다.")
                f.write(chunk)
    write_provenance(dst, source_type="image_url", source=url, rights_basis=rights_basis)
    return dst


def launch_gui() -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    try:
        from PIL import Image, ImageTk
    except ImportError as exc:
        raise RuntimeError("GUI 이미지 미리보기에는 Pillow가 필요합니다. pip install Pillow") from exc

    root = tk.Tk(); root.title("Image Movie Ad V2.7 - 상품 이미지 / 광고 입력"); root.geometry("1180x780"); root.minsize(980, 680)
    image_path=tk.StringVar(value=""); image_url=tk.StringVar(value=""); product_url=tk.StringVar(value=""); rights=tk.StringVar(value="확인 필요"); status=tk.StringVar(value="Ctrl+V, 파일 선택 또는 직접 이미지 URL을 사용할 수 있습니다.")
    product=tk.StringVar(); must=tk.StringVar(); features=tk.StringVar(); pain=tk.StringVar(); target=tk.StringVar(value="일반 소비자"); intensity=tk.StringVar(value="4"); preview_ref:dict[str,Any]={}

    main=ttk.Frame(root,padding=16);main.pack(fill="both",expand=True);left=ttk.Frame(main);left.pack(side="left",fill="y",padx=(0,16));right=ttk.Frame(main);right.pack(side="right",fill="both",expand=True)
    def row(label,var,width=48):
        ttk.Label(left,text=label).pack(anchor="w",pady=(7,2));e=ttk.Entry(left,textvariable=var,width=width);e.pack(fill="x");return e
    product_entry=row("상품명 *",product);row("상품 페이지 URL (선택)",product_url);row("반드시 강조할 특징",must);row("추가 특징",features);row("고객 Pain Point",pain);row("타깃 고객",target);row("광고 강도 1~5",intensity)
    ttk.Separator(left).pack(fill="x",pady=12);ttk.Label(left,text="광고 사용 권리 상태").pack(anchor="w");rights_box=ttk.Combobox(left,textvariable=rights,values=RIGHTS_OPTIONS,state="readonly");rights_box.pack(fill="x",pady=(2,6));row("직접 이미지 URL (선택)",image_url);ttk.Label(left,textvariable=image_path,wraplength=390).pack(anchor="w",pady=(4,6))
    preview=ttk.Label(right,anchor="center",text="이미지 미리보기\n\nCtrl+V / 파일 선택 / 직접 이미지 URL");preview.pack(fill="both",expand=True)

    def show(path:Path):
        img=Image.open(path);img.thumbnail((680,600));photo=ImageTk.PhotoImage(img);preview.configure(image=photo,text="");preview_ref["photo"]=photo;image_path.set(str(path));status.set(f"이미지 준비 완료: {path.name}")
    def paste(_event=None):
        try:show(grab_clipboard_image(product.get() or "product",rights.get()))
        except Exception as exc:messagebox.showwarning("클립보드 이미지",str(exc));status.set(str(exc))
        return "break"
    def load_file():
        p=filedialog.askopenfilename(title="상품 이미지 선택",filetypes=[("Image files","*.png *.jpg *.jpeg *.webp *.bmp"),("All files","*.*")])
        if p:
            try:show(import_image_file(p,product.get() or "product",rights.get()))
            except Exception as exc:messagebox.showerror("이미지 불러오기 실패",str(exc))
    def load_url():
        if not image_url.get().strip():messagebox.showwarning("URL","직접 이미지 URL을 입력하세요.");return
        try:show(download_image_url(image_url.get().strip(),product.get() or "product",rights.get()))
        except Exception as exc:messagebox.showerror("URL 이미지 불러오기 실패",str(exc))
    def check_rights():
        if image_path.get() and rights.get() not in RIGHTS_OK:
            raise ValueError("이미지를 광고에 사용하려면 권리 상태를 확인해 선택하세요. 출처를 숨기거나 저작권을 우회하는 방식은 지원하지 않습니다.")
    def args_common():
        if not product.get().strip():raise ValueError("상품명을 입력하세요.")
        check_rights()
        try:i=int(intensity.get() or "4")
        except ValueError:raise ValueError("광고 강도는 1~5 숫자로 입력하세요.")
        if i not in range(1,6):raise ValueError("광고 강도는 1~5입니다.")
        args=[product.get().strip(),"--must-emphasize",must.get(),"--features",features.get(),"--pain-point",pain.get(),"--target",target.get() or "일반 소비자","--intensity",str(i)]
        if image_path.get():args += ["--image",image_path.get()]
        return args
    def run(cmd,label):
        try:
            status.set(label+" 실행 중...");root.update_idletasks();r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace")
            if r.returncode:raise RuntimeError((r.stdout+"\n"+r.stderr)[-2500:])
            status.set(label+" 완료");messagebox.showinfo("완료",label+" 완료\n결과 폴더를 확인하세요.")
        except Exception as exc:status.set(label+" 실패");messagebox.showerror("실행 실패",str(exc))
    def generate_script():
        try:args=args_common()
        except Exception as exc:messagebox.showwarning("입력 확인",str(exc));return
        run([sys.executable,str(ROOT/"generator"/"script_generator_v2.py"),*args],"광고 대본 생성")
    def generate_package():
        try:args=args_common()
        except Exception as exc:messagebox.showwarning("입력 확인",str(exc));return
        if product_url.get().strip():args += ["--url",product_url.get().strip()]
        run([sys.executable,str(ROOT/"generator"/"creative_package_v26.py"),*args],"Creative Package 생성")

    btns=ttk.Frame(left);btns.pack(fill="x",pady=8);ttk.Button(btns,text="Ctrl+V 이미지 붙여넣기",command=paste).pack(fill="x",pady=2);ttk.Button(btns,text="이미지 파일 불러오기",command=load_file).pack(fill="x",pady=2);ttk.Button(btns,text="이미지 URL 불러오기",command=load_url).pack(fill="x",pady=2);ttk.Button(btns,text="광고 대본 생성",command=generate_script).pack(fill="x",pady=(10,2));ttk.Button(btns,text="UGC / Demo / Cinematic 패키지 생성",command=generate_package).pack(fill="x",pady=2)
    ttk.Label(left,textvariable=status,wraplength=390).pack(anchor="w",pady=8);ttk.Label(left,text="원본 이미지와 .source.json 출처/권리 기록은 input_images에 로컬 보관됩니다. 워터마크 제거·출처 은폐 기능은 제공하지 않습니다.",wraplength=390).pack(anchor="w")
    root.bind_all("<Control-v>",paste);product_entry.focus_set();root.mainloop();return 0

def main()->int:return launch_gui()
if __name__=="__main__":raise SystemExit(main())
