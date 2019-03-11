import logging
import zigate

LOGGER = logging.getLogger(__name__)


class ZiGate:
    def __init__(self):
        self._zigate = None
        self._callbacks = {}

    async def connect(self, device, baudrate=115200):
        assert self._zigate is None
        if '.' in device:  # supposed I.P:PORT
            host_port = device.split(':', 1)
            host = host_port[0]
            port = None
            if len(host_port) == 2:
                port = int(host_port[1])
            LOGGER.info('Configuring ZiGate WiFi {} {}'.format(host, port))
            self._zigate = zigate.ZiGateWiFi(host, port, auto_start=False)
        else:
            LOGGER.info('Configuring ZiGate USB {}'.format(device))
            self._zigate = zigate.ZiGate(device, auto_start=False)
        self._interpret_response = self._zigate.interpret_response  # keep link
        self._zigate.interpret_response = self.interpret_response

    def __getattr__(self, name):
        return self._zigate.__getattribute__(name)

    def close(self):
        return self._zigate.close()

    def set_application(self, app):
        self._app = app

    def add_callback(self, cb):
        id_ = hash(cb)
        while id_ in self._callbacks:
            id_ += 1
        self._callbacks[id_] = cb
        return id_

    def remove_callback(self, id_):
        return self._callbacks.pop(id_)

    def handle_callback(self, *args):
        for callback_id, handler in self._callbacks.items():
            try:
                handler(*args)
            except Exception as e:
                LOGGER.exception("Exception running handler", exc_info=e)

    def interpret_response(self, response):
        if response.msg == 0x8000:  # status response handle by zigate instance
            self._interpret_response(response)
        else:
            self.handle_callback(response)
