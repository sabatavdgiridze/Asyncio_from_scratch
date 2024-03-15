from types import coroutine

class Queue:
  def __init__(self):
    self.queue = []
  
  @coroutine
  def get(self):
    while True:
      if self.queue:
        return self.queue.pop(0)
      else:
        yield ("get request", self)
  
  @coroutine
  def put(self, value):
    self.queue.append(value)
    yield ("put request", self)

@coroutine
def context_switch():
  yield ("switch", None)

class AsyncEventLoop:
  def __init__(self):
    self.task_queue = []
    self.waiting_queue_dict = {}

  def append_task(self, coroutine):
    self.task_queue.append(coroutine)
  
  def run(self):
    while self.task_queue:
      coroutine = self.task_queue.pop(0)
      try:
        result = coroutine.send(None)
        if result:
          if result[0] == "switch":
            self.task_queue.append(coroutine)
          elif result[0] == "get request":
            if result[1] in self.waiting_queue_dict:
              self.waiting_queue_dict[result[1]].append(coroutine)
            else:
              self.waiting_queue_dict[result[1]] = [coroutine]
          elif result[0] == "put request":
            waiting_coroutine = None
            if self.waiting_queue_dict[result[1]]:
              waiting_coroutine = self.waiting_queue_dict[result[1]].pop(0)
            if waiting_coroutine:
              self.task_queue.append(waiting_coroutine)
            self.task_queue.append(coroutine)

      except StopIteration:
        pass

async_queue = Queue()

async def consumer(n):
  for i in range(n):
    value = await async_queue.get()
    print("got " + str(value))

async def producer(n):
  for i in range(n):
    print("sent " + str(i))
    await async_queue.put(i)

scheduler = AsyncEventLoop()
scheduler.append_task(consumer(5))
scheduler.append_task(producer(5))
scheduler.run()