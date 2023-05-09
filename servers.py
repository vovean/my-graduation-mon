from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ServerInfo:
    server: str
    last_active: datetime
    notified_on_inactive: bool = False

    def is_active(self, activity_period: timedelta) -> bool:
        return self.last_active + activity_period > datetime.now()


DEFAULT, SERVER_NEW, SERVER_ACTIVE_AGAIN = 0, 1, 2


class Manager:
    def __init__(self, active_period: timedelta):
        self.active_period = active_period
        self.servers: dict[str, ServerInfo] = dict()

    def set_server_active(self, server_ip: str) -> int:
        """
        Sets server status to active recording current time

        :return: Whether this server_ip is new or already known
        """
        is_new = server_ip not in self.servers
        was_inactive = False
        if not is_new:
            was_inactive = self.servers[server_ip].notified_on_inactive

        self.servers[server_ip] = ServerInfo(
            server=server_ip,
            last_active=datetime.now()
        )

        if is_new:
            return SERVER_NEW
        if was_inactive:
            return SERVER_ACTIVE_AGAIN
        return DEFAULT

    def get_servers(self) -> dict[str, bool]:
        """
        Maps server IPs with their activity status: active/inactive
        """
        result = dict()
        for server, info in self.servers.items():
            result[server] = info.is_active(self.active_period)

        return result

    def get_inactive_not_notified(self) -> list[str]:
        res = []
        for server, info in self.servers.items():
            if not info.is_active(self.active_period) and not info.notified_on_inactive:
                res.append(server)

        return res

    def set_inactive_notified(self, servers: list[str]):
        for server in servers:
            self.servers[server].notified_on_inactive = True
