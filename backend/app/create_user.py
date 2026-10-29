from getpass import getpass
from sqlalchemy import text

from .database import SessionLocal
from .security import hash_password

ADMIN_USER_ID = 1000


def main():

    # 1. Get user details
    username = input("Username: ").strip()

    role = input("Role (admin/manager/analyst): ").strip().lower()

    if not username:
        raise ValueError("Username cannot be empty")

    if role not in ("admin", "manager", "analyst"):
        raise ValueError("Invalid role")

    # 2. Assign user ID
    if role == "admin":
        user_id = ADMIN_USER_ID
        warehouse_id = None

    else:
        warehouse_id = int(input("Warehouse ID: "))

        if warehouse_id < 1:
            raise ValueError("Invalid warehouse ID")

        user_id = warehouse_id

    # 3. Get password securely
    password = getpass("Password: ")
    confirm = getpass("Confirm password: ")

    if password != confirm:
        raise ValueError("Passwords do not match")

    if len(password) < 4:
        raise ValueError("Password must be at least 12 characters")

    hashed_password = hash_password(password)

    # 4. Insert user into MariaDB
    db = SessionLocal()

    try:
        if role == "admin":

            # Keep only one admin account
            existing_admin = db.execute(text("""
                    SELECT 1
                    FROM app_users
                    WHERE role = 'admin'
                    LIMIT 1
                """)).scalar_one_or_none()

            if existing_admin is not None:
                raise ValueError("An admin already exists")

            # Reserve an ID that is not a warehouse ID
            warehouse_conflict = db.execute(
                text("""
                    SELECT 1 FROM warehouse
                    WHERE warehouse_id = :warehouse_id
                """),
                {"warehouse_id": user_id},
            ).scalar_one_or_none()

            if warehouse_conflict is not None:
                raise ValueError("Admin ID conflicts with an existing warehouse")

        else:
            # Check that the warehouse exists
            warehouse_exists = db.execute(
                text("""
                    SELECT 1 FROM warehouse
                    WHERE warehouse_id = :warehouse_id
                """),
                {"warehouse_id": warehouse_id},
            ).scalar_one_or_none()

            if warehouse_exists is None:
                raise ValueError("Warehouse does not exist")

        # Insert user with explicit user_id
        db.execute(
            text("""
                INSERT INTO app_users
                    (user_id, username, password_hash, role)
                VALUES
                    (:user_id, :username, :password_hash, :role)
            """),
            {
                "user_id": user_id,
                "username": username,
                "password_hash": hashed_password,
                "role": role,
            },
        )

        # 5. Assign one warehouse to non-admin users
        if role != "admin":
            db.execute(
                text("""
                    INSERT INTO user_warehouse_access
                        (user_id, warehouse_id)
                    VALUES
                        (:user_id, :warehouse_id)
                """),
                {"user_id": user_id, "warehouse_id": warehouse_id},
            )

        db.commit()
        print(f"Created {role} user: {username} (ID: {user_id})")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
