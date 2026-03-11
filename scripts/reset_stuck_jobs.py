"""Reset stuck claimed jobs to queued so connectors can re-claim them."""
import os
import sys

try:
    import psycopg2
except ImportError:
    print("Run: pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://meshmind:meshmind@localhost:5432/meshmind")


def main() -> None:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        UPDATE jobs
        SET status = 'queued', agent_id = NULL, claimed_at = NULL, error = NULL, updated_at = now()
        WHERE status = 'claimed' AND completed_at IS NULL
        RETURNING id, source_id
    """)
    rows = cur.fetchall()
    conn.commit()
    print(f"Reset {len(rows)} stuck job(s): {rows}")
    conn.close()


if __name__ == "__main__":
    main()
