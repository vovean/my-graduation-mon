from datetime import datetime, timedelta

__all__ = ['set_active_now', 'get_servers']

active_servers: dict[str, datetime] = dict()


def set_active_now(server_ip: str) -> bool:
    """
    Sets server status to active recording current time

    :return: Whether this server_ip is new or already known
    """
    is_known = server_ip in active_servers
    active_servers[server_ip] = datetime.now()

    return not is_known


def get_servers(active_timeout_sec: timedelta) -> dict[str, bool]:
    """
    Maps server IPs with their activity status: active/inactive

    :return:
    """
    result = dict()
    for server, last_active in active_servers.items():
        result[server] = last_active + active_timeout_sec > datetime.now()

    return result
