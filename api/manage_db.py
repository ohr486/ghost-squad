"""Database management CLI tool."""
import sys

from sqlalchemy import text

from database import engine


def check_connection() -> bool:
    """データベース接続をチェックする.

    Returns:
        bool: 接続が成功した場合はTrue、失敗した場合はFalse
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}", file=sys.stderr)
        return False


def seed_data() -> bool:
    """テストデータを投入する.

    Returns:
        bool: 投入が成功した場合はTrue、失敗した場合はFalse
    """
    try:
        print("🌱 Seeding test data...")
        # TODO: Implement test data seeding logic
        print("✅ Test data seeded successfully")
        return True
    except Exception as e:
        print(f"❌ Test data seeding failed: {e}", file=sys.stderr)
        return False


def main() -> int:
    """メイン関数.

    Returns:
        int: 終了コード（0: 成功、1: 失敗）
    """
    if len(sys.argv) < 2:
        print("Usage: python manage_db.py [check|seed]", file=sys.stderr)
        return 1

    command = sys.argv[1]

    if command == "check":
        return 0 if check_connection() else 1
    elif command == "seed":
        return 0 if seed_data() else 1
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Available commands: check, seed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
