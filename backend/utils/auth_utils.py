from fastapi import HTTPException


def validate_admin_creation_restriction(role: str, sub_role: str | None, username: str) -> None:
    """
    Strictly enforce: Admin creation is allowed ONLY ONCE during seed setup.
    No other admin should be created in any way.
    """
    role_check = role.strip().lower()
    sub_role_check = (sub_role or "").strip().lower()
    username_check = username.strip().lower()

    if role_check == "admin" or sub_role_check == "admin" or username_check == "admin":
        raise HTTPException(
            status_code=400,
            detail="Admin creation is strictly restricted. Only one primary admin account is permitted in the system."
        )
