"""No accounts or session cookies: a single local workspace."""
from fastapi import Request


def get_workspace_id(request: Request):
    return 1
