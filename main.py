import asyncio
import logging
import pathlib
import pickle
import uuid
from datetime import timedelta

import dotenv
import uvicorn

import config
import fa_app
import tg_app


def setup_logging(cfg: config.Config):
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=cfg.log_level
    )


def get_secret_key() -> str:
    try:
        with open(pathlib.Path(__file__).parent / 'data' / 'secret_key.pickle', 'rb') as fin:
            key = pickle.load(fin)
            return key
    except FileNotFoundError:
        logging.info('secret key file not found, generating new key')
    except Exception as e:
        logging.warning('failed to get secret key', exc_info=e)

    key = str(uuid.uuid4())
    with open(pathlib.Path(__file__).parent / 'data' / 'secret_key.pickle', 'wb') as fout:
        pickle.dump(key, fout)
    logging.info(f'Создан секретный ключ: {key}')

    return key


def load_config() -> config.Config:
    raw_values = dotenv.dotenv_values()
    return config.Config(
        log_level=raw_values.get('LOG_LEVEL', 'INFO').upper(),
        host=raw_values.get('HOST', '127.0.0.1'),
        port=int(raw_values.get('PORT', '8000')),
        server_active_period=timedelta(
            seconds=int(raw_values.get('SERVER_ACTIVE_PERIOD_SEC', '10')),
        ),
    )


async def main():
    cfg = load_config()
    setup_logging(cfg)

    secret_key = get_secret_key()
    tgac = tg_app.TGAppController(secret_key, cfg.server_active_period)

    tg = tgac.get_tg_app()
    fa = fa_app.create_app(tgac, secret_key)

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=fa,
            host=cfg.host,
            port=cfg.port,
        )
    )

    async with tg:
        await tg.start()
        await tg.updater.start_polling()

        await webserver.serve()

        await tg.updater.stop()
        await tg.stop()


if __name__ == '__main__':
    asyncio.run(main())
