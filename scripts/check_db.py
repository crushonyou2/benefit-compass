"""비밀값을 출력하지 않고 Neon 스키마 상태를 읽기 전용으로 확인한다."""
import os
import pathlib

from dotenv import load_dotenv
import psycopg2

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def main():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise SystemExit("DATABASE_URL 없음")

    try:
        connection = psycopg2.connect(database_url, connect_timeout=10)
        connection.set_session(readonly=True, autocommit=True)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT current_setting('server_version_num')::int,
                   EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector'),
                   to_regclass('public.policy') IS NOT NULL,
                   to_regclass('public.policy_chunk') IS NOT NULL
        """)
        version, vector, policy_table, chunk_table = cursor.fetchone()
        print("db_connection=OK")
        print(f"postgres_major={version // 10000}")
        print(f"vector_extension={vector}")
        print(f"policy_table={policy_table}")
        print(f"policy_chunk_table={chunk_table}")
        if policy_table:
            cursor.execute("SELECT count(*) FROM policy")
            print(f"policy_rows={cursor.fetchone()[0]}")
            cursor.execute("SELECT source, count(*) FROM policy GROUP BY source ORDER BY source")
            for source, count in cursor.fetchall():
                print(f"policy_source[{source}]={count}")
        if chunk_table:
            cursor.execute("SELECT count(*) FROM policy_chunk")
            print(f"policy_chunk_rows={cursor.fetchone()[0]}")
            cursor.execute("SELECT count(*) FROM policy_chunk WHERE embedding IS NULL")
            print(f"missing_embeddings={cursor.fetchone()[0]}")
        cursor.close()
        connection.close()
    except Exception as exc:
        print("db_connection=FAILED")
        print(f"error_type={type(exc).__name__}")
        print(f"pgcode={getattr(exc, 'pgcode', None)}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
