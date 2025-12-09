import json
from pathlib import Path
from typing import List, Dict, Any

INPUT_DIR = Path("en_word")          # 원본 JSON 폴더 (n1.json ~ n5.json)
OUTPUT_ROOT = Path("en_word_out")    # 루트 출력 폴더
OUTPUT_ROOT.mkdir(exist_ok=True)


def flatten_and_extract(data: Any) -> List[Dict[str, str]]:
    """
    원본 구조: [ [ {..}, {..}, ... ], [ {..}, ... ], ... ]
    -> 한 리스트로 평탄화 + 필요한 필드만 추출
    """
    result: List[Dict[str, str]] = []

    if not isinstance(data, list):
        return result

    for inner in data:
        if not isinstance(inner, list):
            continue

        for item in inner:
            if not isinstance(item, dict):
                continue

            result.append({
                "yomikata": item.get("yomikata", ""),
                "word": item.get("word", ""),
                "mean": item.get("mean", ""),
            })

    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    lst를 chunk_size 단위로 나눠서 2차원 리스트로 반환
    예: [1,2,3,4,5], size=2 -> [[1,2],[3,4],[5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def process_level(level: int, chunk_size: int = 10):
    in_path = INPUT_DIR / f"n{level}.json"

    if not in_path.exists():
        print(f"[WARN] {in_path} 없음, 스킵")
        return

    print(f"[INFO] n{level} 처리 시작: {in_path}")

    # ★ 레벨별 출력 폴더 (en_word_out/n1, en_word_out/n2, ...)
    level_out_dir = OUTPUT_ROOT / f"n{level}"
    level_out_dir.mkdir(parents=True, exist_ok=True)

    # 1) 원본 JSON 읽기
    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # 2) 평탄화 + 필요한 필드만 추출
    flat_list = flatten_and_extract(data)
    print(f"[INFO] n{level}: 총 단어 수 = {len(flat_list)}")

    if not flat_list:
        print(f"[WARN] n{level}: 데이터 없음, 스킵")
        return

    # 3) 10개씩 chunk 로 나누기
    chunks = chunk_list(flat_list, chunk_size)

    # 4) 각 chunk를 레벨 폴더 안에 별도 파일로 저장
    for idx, chunk in enumerate(chunks, start=1):
        out_path = level_out_dir / f"n{level}_{idx}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)

        print(f"[DONE] -> {out_path} (항목 {len(chunk)}개)")


def main():
    # n1 ~ n5 까지 처리
    for level in range(1, 6):
        process_level(level, chunk_size=120)


if __name__ == "__main__":
    main()
