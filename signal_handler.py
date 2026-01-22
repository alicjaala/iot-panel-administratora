import signal

class SignalHandler:
    def __init__(self):
        self.is_running: bool = True
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
    
    def _shutdown(self, sig: int, frame) -> None:
        print(f"\nReceived {signal.Signals(sig).name}, shutting down")
        self.is_running = False
