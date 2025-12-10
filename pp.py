import json
from pathlib import Path
from typing import Any, Dict, List

# 원본 폴더 (통합 전)
INPUT_DIR = Path("en_word")

# 분해해서 수정한 파일들이 있는 폴더
CHUNK_DIR_ROOT = Path("en_word_out")

# 통합 결과를 저장할 폴더 (새로 생성)
MERGED_DIR = Path("en_word_merged")
MERGED_DIR.mkdir(exist_ok=True)


def flatten_original_items(data: Any) -> List[Dict[str, Any]]:
    """
    원본 구조: [ [ {..}, {..}, ... ], [ {..}, ... ], ... ]
    -> 실제 딕셔너리 객체(참조)를 평탄화해서 리스트로 반환
       (실제 참조를 쓰기 때문에 여기서 수정하면 원본 구조에도 반영됨)
    """
    result: List[Dict[str, Any]] = []

    if not isinstance(data, list):
        return result

    for inner in data:
        if not isinstance(inner, list):
            continue
        for item in inner:
            if isinstance(item, dict):
                result.append(item)

    return result


def load_updated_flat_list(level: int) -> List[Dict[str, Any]]:
    """
    en_word_out/n{level}/ 아래의 n{level}_*.json 을 전부 읽어서
    하나의 리스트로 합친다. (분해된 조각들을 다시 평탄화)
    """
    level_dir = CHUNK_DIR_ROOT / f"n{level}"
    if not level_dir.exists():
        print(f"[WARN] 조각 폴더 없음: {level_dir}")
        return []

    # n1_1.json, n1_2.json ... 순으로 정렬
    def file_index(p: Path) -> int:
        # ex) 'n1_3.json' -> 3
        try:
            return int(p.stem.split("_")[1])
        except Exception:
            return 0

    chunk_files = sorted(level_dir.glob(f"n{level}_*.json"), key=file_index)

    updated_flat: List[Dict[str, Any]] = []

    for path in chunk_files:
        with path.open("r", encoding="utf-8") as f:
            try:
                chunk_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON 파싱 실패: {path} -> {e}")
                continue

        if not isinstance(chunk_data, list):
            print(f"[WARN] 리스트가 아닌 데이터 스킵: {path}")
            continue

        for item in chunk_data:
            if isinstance(item, dict):
                updated_flat.append(item)

    print(f"[INFO] n{level}: 조각에서 읽은 총 단어 수 = {len(updated_flat)}")
    return updated_flat


def merge_level(level: int):
    in_path = INPUT_DIR / f"n{level}.json"
    if not in_path.exists():
        print(f"[WARN] 원본 없음, 스킵: {in_path}")
        return

    print(f"\n[INFO] ==== n{level} 통합 시작 ====")

    # 1) 원본 JSON 읽기
    with in_path.open("r", encoding="utf-8") as f:
        original_data = json.load(f)

    # 2) 원본에서 단어 딕셔너리를 평탄화 (참조 유지)
    original_flat = flatten_original_items(original_data)
    print(f"[INFO] n{level}: 원본 단어 수 = {len(original_flat)}")

    # 3) en_word_out에서 편집된 mean 포함 리스트 읽기
    updated_flat = load_updated_flat_list(level)

    if len(original_flat) != len(updated_flat):
        print(f"[ERROR] 길이가 다름! (원본: {len(original_flat)}, 조각: {len(updated_flat)})")
        print("       데이터가 빠졌거나 추가된 것일 수 있으니 먼저 확인 필요.")
        # 필요하면 여기서 return 대신 min(...)까지만 덮어쓰도록 변경 가능
        return

    # 4) 순서대로 mean만 덮어쓰기
    for i, (orig, upd) in enumerate(zip(original_flat, updated_flat), start=1):
        # 안전하게 yomikata/word도 한번 확인해보고 싶으면 아래 주석 해제
        if orig.get("word") != upd.get("word") or orig.get("yomikata") != upd.get("yomikata"):
            print(f"[WARN] {i}번째 항목 매칭 안됨: 원본({orig.get('word')}, {orig.get('yomikata')}) "
                  f"!= 수정본({upd.get('word')}, {upd.get('yomikata')})")
            continue

        # if orig["mean"] == upd.get("mean", ""):
        #     print(f"[WARN] {i}번째 항목 Mean 동일: 원본({orig.get('mean')}"
        #           f"!= 수정본({upd.get('mean')}")

        orig["mean"] = upd.get("mean", "")

    # 5) 통합 결과 저장 (원본 구조 유지)
    out_path = MERGED_DIR / f"n{level}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(original_data, f, ensure_ascii=False, indent=2)

    print(f"[DONE] n{level} -> {out_path} 로 저장 완료")


def main():
    # n1 ~ n5 까지 통합
    for level in range(1, 6):
        merge_level(level)


if __name__ == "__main__":
    main()
