"""Database readiness adapter; probe implementation follows the red HTTP seam."""


async def check_database_ready() -> bool:
    return False
