from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database/content_script.sqlite"
LOG_DIR = ROOT / "logs"
MIN_CREATIVE_SCORE = 80.0

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("beauty", ("세럼", "로션", "크림", "토너", "앰플", "화장품", "마스크팩", "선크림", "클렌저", "립", "파운데이션", "스킨케어")),
    ("golf", ("골프", "거리측정기", "퍼터", "드라이버", "아이언", "웨지", "골프공", "골프백")),
    ("automotive", ("자동차", "차량용", "세차", "거치대", "발수", "블랙박스", "타이어", "카매트")),
    ("pet", ("강아지", "고양이", "반려", "펫", "급식기", "배변", "캣")),
    ("travel", ("캐리어", "여행", "트래블", "여권", "수하물", "기내용", "파우치")),
    ("kitchen", ("주방", "프라이팬", "냄비", "칼", "도마", "텀블러", "에어프라이어", "믹서기")),
    ("fashion", ("의류", "셔츠", "바지", "자켓", "재킷", "신발", "운동화", "가방", "모자", "패션")),
    ("food", ("식품", "간식", "커피", "차 ", "음료", "소스", "라면", "건강식", "과자")),
    ("home_appliance", ("청소기", "가습기", "제습기", "선풍기", "에어컨", "공기청정기", "건조기", "가전")),
    ("electronics", ("이어폰", "헤드폰", "충전기", "보조배터리", "키보드", "마우스", "스피커", "모니터", "전자")),
    ("sports", ("러닝", "운동", "헬스", "요가", "자전거", "스포츠", "등산")),
    ("office", ("사무", "의자", "책상", "문구", "노트", "펜", "프린터")),
    ("household", ("세제", "수납", "정리", "생활용품", "휴지", "타월", "욕실", "청소")),
]

CATEGORY_PROFILES: dict[str, dict[str, str]] = {
    "beauty": {
        "label": "뷰티/스킨케어",
        "pain": "내 피부와 맞지 않는 사용감 때문에 제품을 바꿔도 만족하기 어려운 상황",
        "feature": "제형과 사용감, 성분·사용법의 적합성",
        "demo": "제품을 소량 사용해 제형과 실제 사용감을 가까이 보여준다",
        "proof": "동일한 조건에서 사용감과 루틴 적합성을 과장 없이 비교한다",
        "environment": "clean vanity or bathroom setting",
        "motive": "내 피부와 루틴에 잘 맞는 제품을 고르는 것",
    },
    "golf": {
        "label": "골프",
        "pain": "거리와 상황 판단이 흔들려 클럽 선택이 애매해지는 순간",
        "feature": "측정 정확도·속도와 라운드 중 사용 편의성",
        "demo": "티잉구역이나 페어웨이에서 제품을 실제로 작동시키고 결과를 즉시 보여준다",
        "proof": "같은 지점을 반복 측정하거나 실제 라운드 상황에서 사용 과정을 보여준다",
        "environment": "golf course or driving range",
        "motive": "판단 시간을 줄이고 더 자신 있게 플레이하는 것",
    },
    "automotive": {
        "label": "자동차용품",
        "pain": "운전이나 차량 관리 중 반복되는 작지만 짜증나는 불편",
        "feature": "설치·사용 편의성과 실제 차량 환경에서의 체감 기능",
        "demo": "차량 내부 또는 외부에서 설치 전후의 사용 과정을 직접 보여준다",
        "proof": "같은 차량 환경에서 기능 작동 여부와 사용 편의성을 비교한다",
        "environment": "real car interior, garage, or parking area",
        "motive": "운전과 차량 관리를 더 간단하고 편하게 만드는 것",
    },
    "pet": {
        "label": "반려동물",
        "pain": "외출하거나 바쁠 때 반려동물 돌봄을 놓칠까 신경 쓰이는 상황",
        "feature": "반려동물과 보호자가 실제로 편해지는 핵심 기능",
        "demo": "반려동물이 있는 실제 생활 공간에서 기능을 작동시키는 모습을 보여준다",
        "proof": "설정부터 실제 사용까지의 흐름을 끊김 없이 보여준다",
        "environment": "warm pet-friendly home",
        "motive": "돌봄 부담을 줄이고 안심하는 것",
    },
    "travel": {
        "label": "여행",
        "pain": "이동 중 짐 때문에 생기는 번거로움과 예상치 못한 불편",
        "feature": "수납·내구성·휴대성과 이동 중 사용 편의성",
        "demo": "실제 짐을 넣고 이동하거나 펼치고 접는 과정을 빠르게 보여준다",
        "proof": "공항·숙소·차량 등 실제 이동 동선에서 사용성을 확인한다",
        "environment": "airport, hotel room, or travel transit setting",
        "motive": "짐 스트레스를 줄이고 이동을 편하게 만드는 것",
    },
    "kitchen": {
        "label": "주방용품",
        "pain": "조리할 때 매번 반복되는 번거로운 작업과 정리 스트레스",
        "feature": "조리 시간·세척·보관을 줄여주는 실제 사용성",
        "demo": "실제 재료와 함께 제품을 사용해 핵심 동작을 한 번에 보여준다",
        "proof": "사용 전후의 작업 단계와 정리 시간을 같은 조건에서 비교한다",
        "environment": "realistic modern kitchen",
        "motive": "요리와 정리를 더 빠르고 간단하게 만드는 것",
    },
    "fashion": {
        "label": "패션",
        "pain": "사진과 실제 착용감·핏이 달라 구매 후 손이 잘 안 가는 문제",
        "feature": "핏·소재·착용감과 활용도",
        "demo": "실제 착용 후 앞·옆·움직임을 짧게 보여준다",
        "proof": "여러 코디나 움직임에서 핏과 활용도를 확인한다",
        "environment": "clean wardrobe, studio, or real street setting",
        "motive": "자주 손이 가고 활용하기 쉬운 선택을 하는 것",
    },
    "food": {
        "label": "식품/음료",
        "pain": "맛이나 편의성을 기대했지만 재구매할 이유가 약한 제품을 고르는 문제",
        "feature": "맛·구성·조리 또는 섭취 편의성",
        "demo": "개봉부터 준비·섭취까지 실제 과정을 빠르게 보여준다",
        "proof": "구성·용량·조리 과정을 사실적으로 보여주고 과장된 건강 효능은 피한다",
        "environment": "home dining table or kitchen",
        "motive": "맛과 편의성을 동시에 만족시키는 것",
    },
    "home_appliance": {
        "label": "생활가전",
        "pain": "기존 제품을 써도 시간과 손이 계속 많이 가는 불편",
        "feature": "성능과 사용 시간, 관리 편의성을 체감할 수 있는 기능",
        "demo": "실제 집 안에서 제품을 작동시키고 핵심 기능을 바로 보여준다",
        "proof": "같은 조건에서 작동 과정과 결과를 연속 촬영으로 보여준다",
        "environment": "real lived-in home interior",
        "motive": "집안일 시간을 줄이고 반복 작업을 덜어내는 것",
    },
    "electronics": {
        "label": "전자기기",
        "pain": "매일 쓰는 기기에서 연결·충전·조작 때문에 흐름이 끊기는 불편",
        "feature": "속도·호환성·배터리·조작 편의성 같은 핵심 스펙",
        "demo": "실제 기기와 연결해 핵심 기능이 작동하는 장면을 보여준다",
        "proof": "연결 과정과 실제 작동 상태를 한 화면에서 확인시킨다",
        "environment": "clean desk or everyday tech setup",
        "motive": "매일 쓰는 환경을 더 빠르고 단순하게 만드는 것",
    },
    "sports": {
        "label": "스포츠/운동",
        "pain": "운동 흐름을 끊거나 반복 사용이 불편해 결국 안 쓰게 되는 문제",
        "feature": "착용감·휴대성·운동 중 실제 사용 편의성",
        "demo": "실제 운동 동작 속에서 제품이 어떻게 쓰이는지 보여준다",
        "proof": "정지 화면보다 실제 움직임 속 안정성과 사용성을 확인한다",
        "environment": "gym, running track, or outdoor sports setting",
        "motive": "운동 흐름을 유지하고 꾸준히 쓰기 쉬운 장비를 고르는 것",
    },
    "office": {
        "label": "사무/오피스",
        "pain": "작업 중 작은 불편이 반복되어 집중이 끊기는 문제",
        "feature": "업무 속도·정리·편안함을 개선하는 실사용 기능",
        "demo": "실제 책상에서 업무 흐름 안에 제품을 사용해 보여준다",
        "proof": "사용 전후 작업 단계를 비교해 불필요한 동작이 줄어드는지 보여준다",
        "environment": "realistic office or desk setup",
        "motive": "집중을 덜 끊고 업무를 더 단순하게 만드는 것",
    },
    "household": {
        "label": "생활용품",
        "pain": "매일 반복되는 집안일에서 사소한 불편이 계속 쌓이는 문제",
        "feature": "사용·정리·세척을 줄여주는 실용성",
        "demo": "실제 생활 공간에서 문제 상황과 제품 사용을 연속으로 보여준다",
        "proof": "같은 조건에서 사용 전후 작업 과정을 비교한다",
        "environment": "realistic home utility setting",
        "motive": "반복되는 생활 불편을 줄이는 것",
    },
    "general": {
        "label": "일반 상품",
        "pain": "비슷한 제품이 많아 무엇을 기준으로 골라야 할지 애매한 상황",
        "feature": "실제 사용에서 차이를 만드는 핵심 기능과 편의성",
        "demo": "제품의 대표 기능을 실제 사용 환경에서 바로 보여준다",
        "proof": "광고 문구 대신 실제 작동·사용 과정을 한 화면에서 확인시킨다",
        "environment": "realistic everyday product-use setting",
        "motive": "돈을 두 번 쓰지 않고 나에게 맞는 제품을 고르는 것",
    },
}

ANGLE_PROFILES: dict[str, dict[str, str]] = {
    "problem_attack": {"label": "문제공격형", "copywriter": "A · 문제/손실회피"},
    "loss_aversion": {"label": "손실회피형", "copywriter": "B · 손실회피"},
    "curiosity": {"label": "호기심형", "copywriter": "C · 호기심"},
    "comparison": {"label": "비교형", "copywriter": "D · 비교/전문가"},
    "contrarian": {"label": "반전형", "copywriter": "E · 반전/UGC"},
    "discovery": {"label": "발견형", "copywriter": "F · 발견/직설"},
    "proof": {"label": "증거형", "copywriter": "G · 증거/실사용"},
}

ANGLE_ORDER = tuple(ANGLE_PROFILES)
BANNED_CLAIMS = (
    "치료", "완치", "100%", "즉시 효과", "무조건", "절대", "주름 제거", "여드름 치료", "완전히 사라",
)


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("script_generator_v2")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


LOGGER = configure_logging()


def log_status(message: str) -> None:
    print(message)
    LOGGER.info(message)


def split_values(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        raw = [str(v) for v in value]
    else:
        raw = re.split(r"[,;|\n]+", str(value))
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        cleaned = re.sub(r"\s+", " ", item).strip(" -\t")
        if cleaned and cleaned not in seen:
            out.append(cleaned)
            seen.add(cleaned)
    return out


def infer_category(product: str, description: str = "", override: str = "") -> str:
    override = (override or "").strip().lower()
    if override:
        aliases = {
            "뷰티": "beauty", "화장품": "beauty", "골프": "golf", "자동차": "automotive", "차량": "automotive",
            "펫": "pet", "반려동물": "pet", "여행": "travel", "주방": "kitchen", "패션": "fashion",
            "식품": "food", "가전": "home_appliance", "전자": "electronics", "스포츠": "sports",
            "사무": "office", "생활": "household", "일반": "general",
        }
        normalized = aliases.get(override, override)
        if normalized in CATEGORY_PROFILES:
            return normalized
    haystack = f"{product} {description}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword.lower() in haystack for keyword in keywords):
            return category
    return "general"


def product_profile(
    product: str,
    category: str = "",
    features: str | list[str] | None = None,
    must_emphasize: str | list[str] | None = None,
    pain_point: str = "",
    target: str = "일반 소비자",
    description: str = "",
) -> dict[str, Any]:
    resolved = infer_category(product, description, category)
    base = CATEGORY_PROFILES[resolved]
    required = split_values(must_emphasize)
    optional = split_values(features)
    selling_points: list[str] = []
    for item in required + optional + [base["feature"]]:
        if item and item not in selling_points:
            selling_points.append(item)
    return {
        "product": product.strip(),
        "category": resolved,
        "category_label": base["label"],
        "description": (description or "").strip(),
        "target": (target or "일반 소비자").strip(),
        "pain_point": (pain_point or base["pain"]).strip(),
        "must_emphasize": required,
        "features": optional,
        "selling_points": selling_points,
        "primary_selling_point": selling_points[0],
        "default_feature": base["feature"],
        "demo_action": base["demo"],
        "proof_action": base["proof"],
        "environment": base["environment"],
        "buyer_motive": base["motive"],
        "claim_verification_required": bool(required or optional),
    }


@dataclass
class Hook:
    rank: int
    text: str
    category: str
    angle: str
    score: float
    hook_strength: float
    scroll_stop: float
    curiosity_gap: float
    purchase_desire: float
    clarity: float
    credibility: float
    risk: float
    curiosity: float
    relevance: float
    differentiation: float
    db_source_id: int | None = None
    db_hook_id: int | None = None


def risk_score(text: str) -> float:
    lowered = (text or "").lower()
    hits = [term for term in BANNED_CLAIMS if term.lower() in lowered]
    if not hits:
        return 0.0
    return min(100.0, 35.0 + len(hits) * 20.0)


def score_hook(text: str, angle: str, product_ctx: dict[str, Any], intensity: int, quality_bonus: float = 0.0) -> tuple[float, dict[str, float]]:
    n = len(text)
    has_product = product_ctx["product"] in text
    has_point = any(point in text for point in product_ctx["selling_points"][:3])
    hook_strength = min(98.0, 76.0 + intensity * 4.0 + (5.0 if angle in {"problem_attack", "loss_aversion", "contrarian"} else 2.0))
    scroll_stop = min(98.0, 72.0 + intensity * 4.5 + (6.0 if angle in {"problem_attack", "loss_aversion", "curiosity"} else 2.0))
    curiosity_gap = 94.0 if angle in {"curiosity", "contrarian", "discovery"} else 86.0 if angle in {"comparison", "problem_attack"} else 82.0
    purchase_desire = 94.0 if has_point else 84.0
    clarity = 95.0 if n <= 48 else 90.0 if n <= 64 else 82.0
    credibility = 94.0 if has_point else 88.0
    if not has_product:
        credibility -= 4.0
    risk = risk_score(text)
    total = (
        hook_strength * .30
        + scroll_stop * .20
        + curiosity_gap * .15
        + purchase_desire * .15
        + clarity * .10
        + credibility * .10
        + min(3.0, quality_bonus)
        - risk * .30
    )
    parts = {
        "hook_strength": round(hook_strength, 1),
        "scroll_stop": round(scroll_stop, 1),
        "curiosity_gap": round(curiosity_gap, 1),
        "purchase_desire": round(purchase_desire, 1),
        "clarity": round(clarity, 1),
        "credibility": round(credibility, 1),
        "risk": round(risk, 1),
    }
    return round(max(0.0, min(100.0, total)), 1), parts


def open_db() -> sqlite3.Connection | None:
    if not DB.exists():
        return None
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    out: dict[str, int] = {}
    for table in ("sources", "viral_hooks", "short_form_scripts", "ctas", "before_after_patterns", "product_demo_patterns", "testimonial_patterns"):
        try:
            out[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        except Exception:
            out[table] = 0
    return out


def allowed_clause(alias: str = "s") -> str:
    return f"{alias}.usage_class IN ('COMMERCIAL_OK','TRANSFORM_ONLY')"


def infer_db_angle(text: str) -> str:
    t = (text or "").lower()
    mapping = [
        ("comparison", ("compare", "comparison", "versus", "비교", "vs")),
        ("problem_attack", ("problem", "pain", "mistake", "warning", "문제", "고민", "실수")),
        ("loss_aversion", ("loss", "cost", "fear", "consequence", "손실", "비용")),
        ("contrarian", ("contrarian", "myth", "reversal", "반전", "오해")),
        ("proof", ("proof", "testimonial", "review", "demo", "증거", "후기", "시연")),
        ("curiosity", ("curiosity", "secret", "mystery", "question", "궁금", "비밀")),
    ]
    for angle, words in mapping:
        if any(word in t for word in words):
            return angle
    return "discovery"


def db_hook_signals(conn: sqlite3.Connection, limit: int = 80) -> list[dict[str, Any]]:
    try:
        rows = conn.execute(
            f"""
            SELECT h.hook_id,h.source_id,h.hook_category,h.hook_formula,h.formula_family,h.quality_score,
                   h.claim_risk,s.usage_class
            FROM viral_hooks h JOIN sources s ON s.source_id=h.source_id
            WHERE {allowed_clause('s')} AND COALESCE(h.claim_risk,'LOW') NOT IN ('HIGH','PROHIBITED')
            ORDER BY h.quality_score DESC,h.hook_id ASC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    except Exception:
        return []
    signals: list[dict[str, Any]] = []
    for row in rows:
        raw = " ".join(str(row[key] or "") for key in ("hook_category", "hook_formula", "formula_family"))
        signals.append({
            "hook_id": row["hook_id"],
            "source_id": row["source_id"],
            "angle": infer_db_angle(raw),
            "quality": float(row["quality_score"] or 0),
            "usage_class": row["usage_class"],
        })
    return signals


def db_best(conn: sqlite3.Connection, table: str, fields: list[str], risk_field: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    risk_cond = f" AND COALESCE(t.{risk_field},'LOW') NOT IN ('HIGH','PROHIBITED')" if risk_field else ""
    cols = ",".join("t." + field for field in fields)
    try:
        rows = conn.execute(
            f"""
            SELECT t.rowid as row_id,t.source_id,t.quality_score,{cols},s.usage_class
            FROM {table} t JOIN sources s ON s.source_id=t.source_id
            WHERE {allowed_clause('s')} {risk_cond}
            ORDER BY t.quality_score DESC,t.rowid ASC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    except Exception:
        return []
    return [dict(row) for row in rows]


def db_context() -> dict[str, Any]:
    conn = open_db()
    if not conn:
        return {"connected": False, "reason": "DB file not found", "counts": {}, "hook_signals": []}
    counts = table_counts(conn)
    connected = counts.get("viral_hooks", 0) > 0
    ctx: dict[str, Any] = {"connected": connected, "counts": counts}
    if connected:
        ctx["hook_signals"] = db_hook_signals(conn)
        ctx["scripts"] = db_best(conn, "short_form_scripts", ["framework_name"], limit=3)
        ctx["ctas"] = db_best(conn, "ctas", ["cta_type", "goal"], limit=5)
        ctx["product_demo"] = db_best(conn, "product_demo_patterns", ["demo_type", "camera_pattern"], limit=3)
    conn.close()
    return ctx


def intensity_tone(intensity: int) -> str:
    return {
        1: "정보 중심",
        2: "관심 유도",
        3: "강한 후킹",
        4: "퍼포먼스 광고",
        5: "극강 후킹",
    }[intensity]


def build_hook_text(angle: str, product_ctx: dict[str, Any], intensity: int, variant: int = 0) -> str:
    product = product_ctx["product"]
    pain = product_ctx["pain_point"]
    point = product_ctx["selling_points"][variant % min(3, len(product_ctx["selling_points"]))]
    target = product_ctx["target"]
    templates: dict[str, list[str]] = {
        "problem_attack": [
            f"{pain} 때문에 {product} 찾고 계시다면, {point}부터 보세요.",
            f"아직도 {pain}을 참고 계세요? {product}에서 진짜 볼 건 {point}입니다.",
            f"{product} 써도 {pain}이 반복된다면, {point}를 먼저 확인해보세요.",
        ],
        "loss_aversion": [
            f"이 기준 모르고 {product} 사면 돈 두 번 쓸 수 있습니다. 핵심은 {point}입니다.",
            f"{product} 가격만 보고 고르면 놓치기 쉬운 게 있습니다. 바로 {point}입니다.",
            f"{pain} 때문에 제품을 또 바꾸기 전에, {product}의 {point}부터 확인하세요.",
        ],
        "curiosity": [
            f"왜 요즘 {product} 고를 때 {point}를 먼저 보는지 10초면 이해됩니다.",
            f"처음 보면 평범한 {product}인데, {point}에서 차이가 납니다.",
            f"{target}이 {product}에서 자꾸 확인하는 한 가지, 바로 {point}입니다.",
        ],
        "comparison": [
            f"비싼 {product}보다 먼저 비교할 것, {point}입니다.",
            f"{product}끼리 비교할 때 스펙표보다 먼저 볼 건 {point}입니다.",
            f"비슷해 보이는 {product}, 결국 차이는 {point}에서 드러납니다.",
        ],
        "contrarian": [
            f"{product}, 기능이 많다고 무조건 좋은 건 아닙니다. {point}가 먼저입니다.",
            f"{product}는 비싸다고 답이 아닙니다. 실제로는 {point}가 더 중요합니다.",
            f"다들 {product}의 겉모습부터 보지만, 저는 {point}부터 봅니다.",
        ],
        "discovery": [
            f"처음엔 별거 아닌 줄 알았는데, {point} 때문에 {product} 보는 기준이 바뀝니다.",
            f"{product}에서 의외로 만족도를 가르는 건 {point}였습니다.",
            f"이 {product}를 다시 보게 만든 포인트는 딱 하나, {point}입니다.",
        ],
        "proof": [
            f"{product} 광고 문구 말고 실제로 확인할 건 {point}입니다.",
            f"말로만 좋은 {product} 말고, {point}가 실제로 어떻게 작동하는지 보세요.",
            f"{product} 살 때 후기보다 먼저 직접 확인할 수 있는 건 {point}입니다.",
        ],
    }
    text = templates[angle][variant % len(templates[angle])]
    if intensity == 1:
        replacements = {"돈 두 번 쓸 수 있습니다": "후회할 수 있습니다", "아직도": "만약"}
        for old, new in replacements.items():
            text = text.replace(old, new)
    elif intensity == 5 and angle in {"problem_attack", "loss_aversion"}:
        text = "딱 10초만 보세요. " + text
    return text


def generate_hooks(product_ctx: dict[str, Any], ctx: dict[str, Any], n: int = 30, intensity: int = 4, min_score: float = MIN_CREATIVE_SCORE) -> list[Hook]:
    signals = ctx.get("hook_signals", []) if ctx.get("connected") else []
    signal_by_angle: dict[str, dict[str, Any]] = {}
    for signal in signals:
        angle = signal["angle"]
        if angle not in signal_by_angle or float(signal.get("quality") or 0) > float(signal_by_angle[angle].get("quality") or 0):
            signal_by_angle[angle] = signal

    candidates: list[Hook] = []
    for cycle in range(12):
        for angle in ANGLE_ORDER:
            text = build_hook_text(angle, product_ctx, intensity, cycle)
            signal = signal_by_angle.get(angle)
            bonus = min(3.0, float(signal.get("quality") or 0) / 100 * 3.0) if signal else 0.0
            score, parts = score_hook(text, angle, product_ctx, intensity, bonus)
            if score < min_score:
                continue
            candidates.append(Hook(
                rank=0,
                text=text,
                category=angle,
                angle=angle,
                score=score,
                hook_strength=parts["hook_strength"],
                scroll_stop=parts["scroll_stop"],
                curiosity_gap=parts["curiosity_gap"],
                purchase_desire=parts["purchase_desire"],
                clarity=parts["clarity"],
                credibility=parts["credibility"],
                risk=parts["risk"],
                curiosity=parts["curiosity_gap"],
                relevance=parts["purchase_desire"],
                differentiation=parts["hook_strength"],
                db_source_id=(signal.get("source_id") if signal else None),
                db_hook_id=(signal.get("hook_id") if signal else None),
            ))

    unique: dict[str, Hook] = {}
    for hook in candidates:
        if hook.text not in unique or hook.score > unique[hook.text].score:
            unique[hook.text] = hook
    pool = sorted(unique.values(), key=lambda item: (item.score, item.credibility, -len(item.text)), reverse=True)

    selected: list[Hook] = []
    used_angles: set[str] = set()
    for hook in pool:
        if hook.angle not in used_angles:
            selected.append(hook)
            used_angles.add(hook.angle)
        if len(selected) >= min(len(ANGLE_ORDER), n):
            break
    for hook in pool:
        if hook not in selected:
            selected.append(hook)
        if len(selected) >= n:
            break
    if len(selected) < min(3, n):
        raise RuntimeError("80점 이상 Hook을 충분히 생성하지 못했습니다. 입력 정보를 점검하세요.")
    for rank, hook in enumerate(selected[:n], 1):
        hook.rank = rank
    return selected[:n]


def choose_cta(intensity: int) -> str:
    return {
        1: "제품 정보와 사용 조건을 확인해보세요.",
        2: "관심 있다면 상세 페이지에서 핵심 기능을 비교해보세요.",
        3: "비슷한 불편이 있다면 가격과 상세 조건을 한번 확인해보세요.",
        4: "지금 쓰는 제품과 비교해보고, 조건이 맞는지 상세 페이지에서 확인해보세요.",
        5: "계속 같은 불편을 겪고 있다면, 지금 핵심 기능과 가격부터 비교해보세요.",
    }[intensity]


def allocate_times(duration: int) -> list[tuple[int, int]]:
    weights = [12, 18, 30, 24, 16]
    starts = [0]
    cumulative = 0
    for weight in weights[:-1]:
        cumulative += weight
        starts.append(round(duration * cumulative / sum(weights)))
    ends = starts[1:] + [duration]
    return list(zip(starts, ends))


def build_script(product_ctx: dict[str, Any], hook: Hook, duration: int, angle: str, intensity: int) -> list[dict[str, str]]:
    product = product_ctx["product"]
    point = product_ctx["primary_selling_point"]
    pain = product_ctx["pain_point"]
    motive = product_ctx["buyer_motive"]
    cta = choose_cta(intensity)
    proof_prefix = "사용자가 제공한 특징을 기준으로 " if product_ctx["claim_verification_required"] else ""
    content = [
        ("HOOK", hook.text, hook.text, f"{product}을 첫 프레임에서 크게 보여주고 문제 상황을 1초 안에 제시한다."),
        ("PROBLEM", f"{pain}. 그래서 {product}를 고를 때는 겉모습보다 실제 불편을 줄이는 기준이 중요합니다.", "문제부터 정확히", f"{pain}이 드러나는 실제 사용 상황을 짧게 보여준다."),
        ("SOLUTION", f"이 제품에서 가장 먼저 볼 포인트는 {point}입니다. {motive}에 직접 연결되는지 확인해보세요.", f"핵심: {point}", product_ctx["demo_action"]),
        ("PROOF", f"{proof_prefix}광고 문구보다 실제 작동과 사용 과정을 확인하는 게 좋습니다. {point}가 체감되는지 직접 보세요.", "말보다 실제 사용", product_ctx["proof_action"]),
        ("CTA", cta, "가격 · 조건 · 핵심 기능 확인", f"{product}과 핵심 특징 {point}를 한 화면에 정리한 엔드카드."),
    ]
    timeline = allocate_times(duration)
    beats: list[dict[str, str]] = []
    for (role, spoken, onscreen, visual), (start, end) in zip(content, timeline):
        beats.append({
            "time": f"{start}-{end}s",
            "role": role,
            "spoken": spoken,
            "onscreen": onscreen,
            "visual": visual,
            "angle": angle,
        })
    return beats


def score_script(hook: Hook, beats: list[dict[str, str]], product_ctx: dict[str, Any]) -> dict[str, float]:
    all_text = " ".join(beat["spoken"] for beat in beats)
    has_point = product_ctx["primary_selling_point"] in all_text
    has_product = product_ctx["product"] in all_text
    risk = risk_score(all_text)
    hook_strength = hook.hook_strength
    scroll_stop = hook.scroll_stop
    curiosity_gap = hook.curiosity_gap
    purchase_desire = 95.0 if has_point else 82.0
    clarity = 94.0 if has_product and all(beat["spoken"] for beat in beats) else 84.0
    credibility = 94.0 if has_point and risk == 0 else 82.0
    total = (
        hook_strength * .30 + scroll_stop * .20 + curiosity_gap * .15 + purchase_desire * .15 + clarity * .10 + credibility * .10 - risk * .30
    )
    return {
        "hook_strength": round(hook_strength, 1),
        "scroll_stop_power": round(scroll_stop, 1),
        "curiosity_gap": round(curiosity_gap, 1),
        "purchase_desire": round(purchase_desire, 1),
        "clarity": round(clarity, 1),
        "credibility": round(credibility, 1),
        "risk": round(risk, 1),
        "total": round(max(0.0, min(100.0, total)), 1),
    }


def run_creative_competition(product_ctx: dict[str, Any], hooks: list[Hook], intensity: int, min_score: float) -> list[dict[str, Any]]:
    by_angle: dict[str, Hook] = {}
    for hook in hooks:
        by_angle.setdefault(hook.angle, hook)
    competition_angles = ("loss_aversion", "curiosity", "problem_attack", "comparison", "contrarian")
    contenders: list[dict[str, Any]] = []
    for angle in competition_angles:
        hook = by_angle.get(angle) or hooks[0]
        script = build_script(product_ctx, hook, 30, angle, intensity)
        scores = score_script(hook, script, product_ctx)
        contenders.append({
            "copywriter": ANGLE_PROFILES[angle]["copywriter"],
            "angle": angle,
            "angle_label": ANGLE_PROFILES[angle]["label"],
            "hook": asdict(hook),
            "script_30s": script,
            "scores": scores,
            "qualified": scores["total"] >= min_score,
        })
    contenders.sort(key=lambda item: item["scores"]["total"], reverse=True)
    return contenders


def model_prompt(model: str, product_ctx: dict[str, Any], beat: dict[str, str]) -> str:
    base = (
        f"Vertical 9:16 Korean short-form performance ad for {product_ctx['product']}. "
        f"Product category: {product_ctx['category_label']}. Target audience: {product_ctx['target']}. "
        f"Scene timing: {beat['time']}. Purpose: {beat['role']}. Visual action: {beat['visual']} "
        f"Environment: {product_ctx['environment']}. On-screen text concept: {beat['onscreen']}. "
        "Authentic product-focused commercial, strong first frame, realistic use demonstration, consistent product packaging, "
        "no unsupported superlatives, no fabricated reviews, no fake scarcity, no medical claims unless independently verified."
    )
    if model == "kling":
        return base + " Camera: controlled handheld-to-close-up push-in, subtle parallax, realistic hand motion, smooth social-ad pacing."
    if model == "veo":
        return base + " Camera/audio: cinematic close-up, gentle dolly movement, realistic room ambience and coherent continuity across cuts."
    return base + " Motion: concise product interaction, dynamic but stable camera movement, clear first-frame problem/benefit contrast."


def generate(
    product: str,
    *,
    category: str = "",
    features: str | list[str] | None = None,
    must_emphasize: str | list[str] | None = None,
    pain_point: str = "",
    target: str = "일반 소비자",
    description: str = "",
    intensity: int = 4,
    min_score: float = MIN_CREATIVE_SCORE,
) -> dict[str, Any]:
    if not (product or "").strip():
        raise ValueError("product is required")
    if intensity not in (1, 2, 3, 4, 5):
        raise ValueError("intensity must be 1..5")
    log_status(f"[1/6] 상품 분석: {product}")
    product_ctx = product_profile(product, category, features, must_emphasize, pain_point, target, description)
    ctx = db_context()
    log_status(f"[2/6] 카테고리={product_ctx['category_label']} / 강조={product_ctx['primary_selling_point']}")
    hooks = generate_hooks(product_ctx, ctx, 30, intensity, min_score)
    top3 = hooks[:3]
    log_status(f"[3/6] Hook 30개 생성 완료 / TOP1={top3[0].score}점")
    competition = run_creative_competition(product_ctx, hooks, intensity, min_score)
    qualified = [item for item in competition if item["qualified"]]
    winner = (qualified or competition)[0]
    winning_hook = Hook(**winner["hook"])
    winning_angle = winner["angle"]
    log_status(f"[4/6] Creative Competition 우승={winner['angle_label']} / {winner['scores']['total']}점")

    scripts: dict[str, list[dict[str, str]]] = {}
    prompts_by_duration: dict[str, dict[str, list[str]]] = {}
    for duration in (15, 30, 45):
        beats = build_script(product_ctx, winning_hook, duration, winning_angle, intensity)
        key = f"{duration}s"
        scripts[key] = beats
        prompts_by_duration[key] = {
            model: [model_prompt(model, product_ctx, beat) for beat in beats]
            for model in ("kling", "veo", "seedance")
        }
    log_status("[5/6] 15초 / 30초 / 45초 대본 생성 완료")

    selected_refs = {
        "scripts": (ctx.get("scripts") or [None])[0] if ctx.get("connected") else None,
        "product_demo": (ctx.get("product_demo") or [None])[0] if ctx.get("connected") else None,
    }
    data = {
        "version": "2.4",
        "product": product_ctx["product"],
        "product_analysis": product_ctx,
        "ad_settings": {
            "intensity": intensity,
            "intensity_label": intensity_tone(intensity),
            "minimum_score": min_score,
            "discard_below_score": True,
        },
        "db_integration": {
            "connected": ctx.get("connected", False),
            "database": str(DB),
            "counts": ctx.get("counts", {}),
            "commercial_policy": "COMMERCIAL_OK + TRANSFORM_ONLY only; RESEARCH_ONLY/BLOCKED/UNKNOWN excluded from direct generation",
            "selected_references": selected_refs,
            "hook_reference_ids": [
                {"hook_id": h.db_hook_id, "source_id": h.db_source_id, "category": h.category} for h in top3
            ],
            "top3_diversity": {
                "unique_hook_ids": len({h.db_hook_id for h in top3 if h.db_hook_id is not None}),
                "unique_categories": len({h.category for h in top3}),
            },
        },
        "hooks": [asdict(hook) for hook in hooks],
        "top3": [asdict(hook) for hook in top3],
        "creative_competition": competition,
        "winner": {
            "copywriter": winner["copywriter"],
            "angle": winning_angle,
            "angle_label": winner["angle_label"],
            "scores": winner["scores"],
        },
        "scripts_by_duration": scripts,
        "script_15s": scripts["15s"],
        "script_30s": scripts["30s"],
        "script_45s": scripts["45s"],
        "cta": choose_cta(intensity),
        "video_prompts_by_duration": prompts_by_duration,
        "video_prompts": prompts_by_duration["30s"],
        "claim_note": "사용자가 제공한 수치·성능·효능 특징은 광고 집행 전에 상품 상세페이지/공식 자료로 사실 확인이 필요합니다.",
    }
    log_status("[6/6] 생성 완료")
    return data


def render_md(data: dict[str, Any]) -> str:
    product = data["product"]
    analysis = data["product_analysis"]
    settings = data["ad_settings"]
    out = [
        f"# Script Generator V2.4 — {product}", "",
        "## 상품 분석",
        f"- 카테고리: **{analysis['category_label']}** (`{analysis['category']}`)",
        f"- 타깃: {analysis['target']}",
        f"- 핵심 Pain Point: {analysis['pain_point']}",
        f"- 반드시 강조: {analysis['must_emphasize'] or '미입력 → AI 기본값 사용'}",
        f"- Selling Points: {analysis['selling_points']}",
        f"- 광고 강도: {settings['intensity']} / 5 · {settings['intensity_label']}",
        f"- 품질 Gate: **{settings['minimum_score']}점 미만 폐기**", "",
        "## TOP 3 Hooks",
    ]
    for hook in data["top3"]:
        out.append(f"{hook['rank']}. **{hook['text']}** — {hook['score']}점 · {ANGLE_PROFILES[hook['angle']]['label']}")
    out += ["", "## Creative Competition"]
    for index, item in enumerate(data["creative_competition"], 1):
        marker = "🏆" if item["angle"] == data["winner"]["angle"] else "-"
        out.append(f"{marker} {index}. {item['copywriter']} / {item['angle_label']} — **{item['scores']['total']}점**")
    out += ["", f"**우승:** {data['winner']['angle_label']} · {data['winner']['scores']['total']}점", ""]

    for duration in (15, 30, 45):
        out += [f"## {duration}초 대본", ""]
        for beat in data[f"script_{duration}s"]:
            out += [
                f"### {beat['time']} · {beat['role']}",
                f"- 대사: {beat['spoken']}",
                f"- 자막: {beat['onscreen']}",
                f"- 화면: {beat['visual']}", "",
            ]
    out += ["## CTA", data["cta"], "", "## 광고 집행 전 확인", data["claim_note"], ""]
    for model in ("kling", "veo", "seedance"):
        out += [f"## {model.upper()} · 30초 장면별 Prompt", ""]
        for index, prompt in enumerate(data["video_prompts"][model], 1):
            out += [f"### Shot {index}", "```text", prompt, "```", ""]
    return "\n".join(out)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Category-neutral performance ad Script Generator V2.4")
    parser.add_argument("product")
    parser.add_argument("--category", default="", help="카테고리 직접 지정(선택)")
    parser.add_argument("--features", default="", help="상품 특징. 쉼표/세미콜론/| 구분")
    parser.add_argument("--must-emphasize", default="", help="반드시 강조할 Selling Point")
    parser.add_argument("--pain-point", default="", help="고객이 겪는 핵심 문제")
    parser.add_argument("--target", default="일반 소비자", help="타깃 고객")
    parser.add_argument("--description", default="", help="상품 설명")
    parser.add_argument("--intensity", type=int, choices=(1, 2, 3, 4, 5), default=4, help="광고 강도")
    parser.add_argument("--min-score", type=float, default=MIN_CREATIVE_SCORE, help="최소 광고 품질 점수")
    parser.add_argument("--outdir", default="outputs")
    parser.add_argument("--require-db", action="store_true", help="Content DB 미연결 시 실패")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = generate(
            args.product,
            category=args.category,
            features=args.features,
            must_emphasize=args.must_emphasize,
            pain_point=args.pain_point,
            target=args.target,
            description=args.description,
            intensity=args.intensity,
            min_score=args.min_score,
        )
        if args.require_db and not data["db_integration"]["connected"]:
            raise RuntimeError("Content DB is not connected or empty. Run collector/build_indexes first.")
        out = Path(args.outdir)
        out.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", args.product)
        json_path = out / f"{safe}_script_v2.json"
        md_path = out / f"{safe}_script_v2.md"
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(render_md(data), encoding="utf-8")
        print("DB connected:", data["db_integration"]["connected"])
        print("Category:", data["product_analysis"]["category_label"])
        print("Winner:", data["winner"])
        print("Generated:", md_path)
        LOGGER.info("Generated %s", md_path)
        return 0
    except Exception as exc:
        tb = traceback.format_exc()
        print("ERROR:", exc)
        print(tb)
        LOGGER.error("Script Generator V2.4 failed: %s\n%s", exc, tb)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
