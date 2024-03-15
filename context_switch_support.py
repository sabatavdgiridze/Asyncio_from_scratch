from collections import deque

class Scheduler:
  def __init__(self):
    self.coroutines = deque()
    self.current = None
  
  def new_task(self, coroutine):
    self.coroutines.append(coroutine)
  
  def run(self):
    while self.coroutines:
      self.current = self.coroutines.popleft()
      try:
        self.current.send(None)
        self.coroutines.append(self.current)
      except StopIteration:
        pass

scheduler = Scheduler()

class Awaitable:
  def __await__(self):
    yield

def switch():
  return Awaitable()

import time

async def countdown(n):
  while n > 0:
    print("Down", n)
    time.sleep(1)
    await switch()
    n = n - 1

async def countup(n):
  x = 1
  while x <= n:
    print("Up", x)
    time.sleep(1)
    await switch()
    x = x + 1

scheduler.new_task(countdown(5))
scheduler.new_task(countup(5))
scheduler.run()
