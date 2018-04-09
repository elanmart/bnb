""" See: https://docs.python.org/3/howto/logging-cookbook.html#sending-and-receiving-logging-events-across-a-network """


import pickle
import logging
import logging.handlers
import socketserver
import struct

import time
import gc
import os
import coloredlogs


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            chunk = self.connection.recv(4)

            if len(chunk) < 4:
                break

            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)

            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))

            obj    = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)

            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):

        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)

        logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


def _run():
    tcpserver = None

    try:
        time.sleep(2)
        gc.collect()

        # # handler   = logging.StreamHandler()
        # # formatter = coloredlogs.ColoredFormatter('%(relativeCreated)5d -- %(name)-15s -- %(levelname)-8s -- %(message)s')
        # #
        # # handler.setFormatter(formatter)
        # logging.basicConfig(handlers=[handler])

        logging.basicConfig(format='%(asctime)s -- %(name)-15s -- %(levelname)-8s -- %(message)s')

        tcpserver = LogRecordSocketReceiver()
        tcpserver.serve_until_stopped()

    finally:

        if tcpserver is not None:
            tcpserver.server_close()



def main():
    while True:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            _run()
        except KeyboardInterrupt:
            gc.collect()
            time.sleep(1)


if __name__ == '__main__':
    main()
