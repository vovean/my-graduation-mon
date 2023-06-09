from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Config:
    bot_token: str

    '''
    Допустимые уровни:
        CRITICAL
        FATAL
        ERROR
        WARN
        WARNING
        INFO
        DEBUG
        NOTSET
    '''
    log_level: str
    host: str
    port: int
    server_active_period: timedelta
