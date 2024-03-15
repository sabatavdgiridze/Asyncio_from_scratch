import time
from collections import deque

class Scheduler:
  def __init__(self):
    self.task_queue = deque()
    
    self.sleeping = []
    self.priority_index = 1 # implementation detail, helps in sorting
  
  def create_task(self, coroutine):
    self.task_queue.append(coroutine)
  
  def run(self):
    while any([self.task_queue, self.sleeping]):
      next_iteration_task_queue = []
      for coroutine in self.task_queue:
        try:
          result = coroutine.send(None)
          if result[0] == "switch":
            next_iteration_task_queue.append(coroutine)
          elif result[0] == "sleep":
            self.sleeping.append((time.time() + result[1], self.priority_index, coroutine))
            self.sleeping.sort()

            self.priority_index += 1

        except StopIteration:
          pass
      
      if not next_iteration_task_queue and self.sleeping:
        delta_time = max(0, self.sleeping[0][0] - time.time())
        time.sleep(delta_time)
      
      while self.sleeping and self.sleeping[0][0] <= time.time():
        next_iteration_task_queue.append(self.sleeping.pop(0)[2])
      self.task_queue = next_iteration_task_queue

from types import coroutine

@coroutine
def sleep(duration):
  yield ("sleep", duration)

@coroutine
def switch():
  yield ("switch", None)


scheduler = Scheduler()

async def countdown(n):
  while n > 0:
    print("Count down", n)
    await sleep(2)
    n = n - 1

async def countup(n):
  x = 1
  while x <= n:
    print("Count up", x)
    await sleep(4)
    x = x + 1

scheduler.create_task(countdown(20))
scheduler.create_task(countup(10))

scheduler.run()