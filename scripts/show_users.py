from database.db import get_user_summaries, init_db, count_report_logs, using_postgres


def main():
    init_db()
    print("Database:", "PostgreSQL" if using_postgres() else "SQLite")
    print("Report logs:", count_report_logs())
    users = get_user_summaries()
    print("Users:", len(users))
    print("-" * 60)
    for user in users:
        display_name = user.get("display_name") or "(no display name stored)"
        print(f"User ID: {user['user_id']}")
        print(f"Display: {display_name}")
        print(f"Created: {user.get('created_at')}")
        print(f"Last seen: {user.get('last_seen_at')}")
        watchlist = user.get("watchlist") or []
        if watchlist:
            print("Watchlist:")
            for item in watchlist:
                print(f"  - {item.get('stock_code')} {item.get('stock_name') or ''}")
        else:
            print("Watchlist: empty")
        print("-" * 60)


if __name__ == "__main__":
    main()
