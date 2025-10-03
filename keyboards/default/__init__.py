# keyboards/default/__init__.py
"""Default (Reply) keyboards"""
from .admin_menu import admin_menu
from .confirm_menu import confirm_menu
from .user_menu import (
    main_user_menu,
    get_mavzu_keyboard,
    get_dars_keyboard
)
from .cancel_menu import cancel_menu

__all__ = [
    'admin_menu',
    'confirm_menu',
    'main_user_menu',
    'get_mavzu_keyboard',
    'get_dars_keyboard',
    'cancel_menu'
]