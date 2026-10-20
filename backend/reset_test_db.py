"""显式清空并重建当前测试数据库。仅用于本项目测试开发阶段。"""
import argparse

from app import app, db, init_db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="确认删除全部测试数据")
    args = parser.parse_args()
    if not args.yes:
        parser.error("此操作会删除全部测试数据，请增加 --yes")
    with app.app_context():
        db.drop_all()
        init_db()
    print("测试数据库已清空并重建。")


if __name__ == "__main__":
    main()
