from app.database import _make_connection, init_db


def main() -> None:
    init_db()
    conn = _make_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("Pinged your MySQL deployment. You successfully connected!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
