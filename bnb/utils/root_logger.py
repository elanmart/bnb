import logging
import logging.handlers


def get_root_logger(level='debug'):
    if isinstance(level, str):
        level = level.upper()

    logging.getLogger('git').setLevel('WARNING')
    logging.getLogger('rpyc').setLevel('WARNING')
    logging.getLogger('paramiko').setLevel('WARNING')
    logging.getLogger('plumbum').setLevel('WARNING')

    rootLogger    = logging.getLogger()
    socketHandler = logging.handlers.SocketHandler('localhost', logging.handlers.DEFAULT_TCP_LOGGING_PORT)

    rootLogger.setLevel(level)
    rootLogger.addHandler(socketHandler)

    return rootLogger
