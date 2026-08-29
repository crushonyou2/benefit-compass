"""
Youth official URL 16건 targeted fix — P1 staging validation용.

- 현재 production DB의 youth missing_links 615 중 16건은 ingestion bug (aplyUrlAddr non-http를 truthy로 선택)
- 코드 `ingest_youth._official_url(aplyUrlAddr, refUrlAddr1)`는 이미 수정됨
- 이 스크립트는 DB raw에서 올바른 URL을 재계산해 dry-run / execute를 지원한다.

사용법:
  python ingest/fix_youth_urls.py --dry-run
  python ingest/fix_youth_urls.py --execute --staging-url $STAGING_DATABASE_URL
  (기본 DATABASE_URL은 .env의 production, --staging-url 지정 시 staging에만 적용)

검증:
  - 변경 전/후 missing_links
  - 16건 각각 before/after
  - refUrlAddr2는 사용하지 않음 (P0 결정 유지)
"""
import argparse
import json
import os
import pathlib
import sys

from dotenv import load_dotenv
import psycopg2

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# reuse fixed logic
sys.path.insert(0, str(ROOT / "ingest"))
from ingest_youth import _official_url  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Youth URL 16건 targeted fix")
    p.add_argument("--dry-run", action="store_true", help="변경 없이 진단만 (기본은 dry-run)")
    p.add_argument("--execute", action="store_true", help="실제 UPDATE 실행")
    p.add_argument("--staging-url", type=str, default=None, help="staging DATABASE_URL (지정 시 해당 DB에만 적용)")
    p.add_argument("--output", type=pathlib.Path, default=pathlib.Path("eval/fix_youth_urls_report.json"))
    return p.parse_args()


def get_db_url(staging_url):
    if staging_url:
        return staging_url.strip()
    return os.getenv("DATABASE_URL", "").strip()


def find_bug_rows(cur):
    cur.execute("""
        SELECT id, source_id, apply_url,
               raw->>'aplyUrlAddr' as aply,
               raw->>'refUrlAddr1' as ref1,
               raw->>'refUrlAddr2' as ref2
        FROM policy
        WHERE source='youth'
          AND (apply_url IS NULL OR apply_url !~ '^https?://')
          AND (raw->>'refUrlAddr1' ~ '^https?://')
        ORDER BY source_id
    """)
    return cur.fetchall()


def main():
    args = parse_args()
    if args.dry_run and args.execute:
        raise SystemExit("--dry-run과 --execute는 동시에 지정할 수 없습니다")
    # default to dry-run if neither specified
    do_execute = bool(args.execute)
    db_url = get_db_url(args.staging_url)
    if not db_url:
        raise SystemExit("DATABASE_URL 없음 — .env 또는 --staging-url 확인")

    conn = psycopg2.connect(db_url)
    conn.set_session(autocommit=False)
    cur = conn.cursor()

    # before counts
    cur.execute("SELECT count(*) FROM policy WHERE source='youth' AND (apply_url IS NULL OR apply_url !~ '^https?://')")
    before_missing = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM policy WHERE source='youth'")
    youth_total = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM policy WHERE source='gov24'")
    gov24_total = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM policy_chunk")
    chunk_total = cur.fetchone()[0]

    bug_rows = find_bug_rows(cur)
    details = []
    updates = []
    for pid, source_id, old_url, aply, ref1, ref2 in bug_rows:
        new_url = _official_url(aply, ref1)  # ref2 미사용 — P0 결정
        details.append({
            "id": pid,
            "source_id": source_id,
            "old_apply_url": old_url,
            "aplyUrlAddr": aply,
            "refUrlAddr1": ref1,
            "refUrlAddr2": ref2,
            "new_apply_url": new_url,
            "would_fix": new_url is not None and new_url.startswith(("https://", "http://")),
        })
        if new_url:
            updates.append((new_url, pid))

    recoverable = sum(1 for d in details if d["would_fix"])
    expected_after = before_missing - recoverable

    print(f"youth total={youth_total} gov24={gov24_total} chunks={chunk_total}")
    print(f"before missing_links (youth)={before_missing}")
    print(f"bug rows found={len(bug_rows)} recoverable={recoverable} expected_after={expected_after}")
    for d in details:
        print(f"  {d['source_id']}: {d['old_apply_url']!r} -> {d['new_apply_url']!r} (aply={d['aplyUrlAddr']!r} ref1={d['refUrlAddr1']!r})")

    report = {
        "youth_total": youth_total,
        "gov24_total": gov24_total,
        "chunk_total": chunk_total,
        "before_missing": before_missing,
        "bug_rows": len(bug_rows),
        "recoverable": recoverable,
        "expected_after": expected_after,
        "details": details,
        "executed": False,
    }

    if do_execute:
        if not updates:
            print("실행할 업데이트 없음")
        else:
            for new_url, pid in updates:
                cur.execute("UPDATE policy SET apply_url=%s, updated_at=now() WHERE id=%s", (new_url, pid))
            # 검증
            cur.execute("SELECT count(*) FROM policy WHERE source='youth' AND (apply_url IS NULL OR apply_url !~ '^https?://')")
            after_missing = cur.fetchone()[0]
            print(f"after missing_links (youth)={after_missing}")
            report["after_missing"] = after_missing
            report["executed"] = True
            # coverage / duplicate / embedding 검증 (read-only)
            cur.execute("SELECT count(*) FROM policy_chunk WHERE embedding IS NULL")
            missing_embeddings = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM (SELECT source, source_id FROM policy GROUP BY source, source_id HAVING count(*)>1) d")
            dup_policies = cur.fetchone()[0]
            cur.execute("""
                SELECT count(*) FROM policy p
                WHERE NOT EXISTS (SELECT 1 FROM policy_chunk c WHERE c.policy_id=p.id)
            """)
            orphan_policies = cur.fetchone()[0]
            cur.execute("""
                SELECT count(*) FROM policy_chunk c
                WHERE NOT EXISTS (SELECT 1 FROM policy p WHERE p.id=c.policy_id)
            """)
            orphan_chunks = cur.fetchone()[0]
            report["validation"] = {
                "missing_embeddings": missing_embeddings,
                "duplicate_policies": dup_policies,
                "policies_without_chunks": orphan_policies,
                "orphan_chunks": orphan_chunks,
            }
            print(f"validation: missing_embeddings={missing_embeddings} dup={dup_policies} no_chunk={orphan_policies} orphan_chunk={orphan_chunks}")
            conn.commit()
            print(f"COMMIT: {len(updates)}건 UPDATE 적용")
    else:
        # dry-run: rollback
        conn.rollback()
        print("DRY-RUN: 변경 없음 (rollback)")

    cur.close()
    conn.close()

    # provenance
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report → {args.output}")


if __name__ == "__main__":
    main()
