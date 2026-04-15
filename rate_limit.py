"""Token Bucket Rate Limiter"""
import time
import threading

class RateLimiter:
    def __init__(self, rate=10, per=1.0):
        self.rate = rate
        self.per = per
        self.tokens = float(rate)
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def allow(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.per))
            self.last_update = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    def wait(self):
        while not self.allow():
            time.sleep(0.01)