from types import coroutine
from collections import defaultdict

class AsyncEventLoop:
  def __init__(self):
    self.coroutines = []

    # once the child coroutine finishes, the corresponding item is removed
    # that tells us the parent (when calling join) that the child coroutine already finished 
    AsyncEventLoop.parent_coroutine = {}

    # when the child coroutine finishes, it wakes up the parent if the parent has aleady called join
    # parent, when calling join, puts itself into the watching list (only if the child has not yet finished)
    AsyncEventLoop.watch_for_finish = {}
  
  @coroutine
  def switch():
    yield ("switch", None)
  
  @coroutine
  def spawn(coroutine):
    yield ("spawn", coroutine)
    return coroutine
  
  @coroutine
  def join(coroutine):
    yield ("join", coroutine)
  
  def append_task(self, coroutine):
    self.coroutines.append(coroutine)
  
  def run(self):
    while self.coroutines:
      next_iteration_coroutines = []
      for coroutine in self.coroutines:
        try:
          result = coroutine.send(None)
          if result[0] == "switch":
            next_iteration_coroutines.append(coroutine)
          elif result[0] == "spawn":
            AsyncEventLoop.parent_coroutine[result[1]] = coroutine

            next_iteration_coroutines.append(result[1])
            next_iteration_coroutines.append(coroutine)
          elif result[0] == "join":
            if result[1] in AsyncEventLoop.parent_coroutine.keys():
              AsyncEventLoop.watch_for_finish[result[1]] = coroutine
            else:
              next_iteration_coroutines.append(coroutine)
        except StopIteration:
          if coroutine in AsyncEventLoop.parent_coroutine.keys():
            if coroutine in AsyncEventLoop.watch_for_finish.keys():
              next_iteration_coroutines.append(AsyncEventLoop.watch_for_finish.pop(coroutine))
            AsyncEventLoop.parent_coroutine.pop(coroutine)
        self.coroutines = next_iteration_coroutines



scheduler = AsyncEventLoop()

async def countdown(n):
  while n > 0:
    print("Countdown ", n)
    await AsyncEventLoop.switch()
    n = n - 1

# test for two cases
async def main():
  # child_handler = await AsyncEventLoop.spawn(countdown(5))
  child_handler = await AsyncEventLoop.spawn(countdown(5))
  
  for i in range(10):
    print("before " + str(i))
    await AsyncEventLoop.switch()
  
  await AsyncEventLoop.join(child_handler)

  print("after")

scheduler.append_task(main())
scheduler.run()