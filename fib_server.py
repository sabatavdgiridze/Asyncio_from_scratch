import socket
import threading
import concurrent.futures
import collections
import select
from typing import Any

coroutines_queue = collections.deque()

coroutines_waiting_for_receive = {}
coroutines_waiting_for_send = {}
coroutines_waiting_for_future = {}

future_notify_socket, future_resolved_socket = socket.socketpair()


def future_done(future):
  coroutines_queue.append(coroutines_waiting_for_future.pop(future))
  future_notify_socket.send(b"future_resolved")

def future_monitoring():
  while True:
    yield ("receiving", future_resolved_socket)
    future_resolved_socket.recv(len(b"future_resolved"))

coroutines_queue.append(future_monitoring())

def run_event_queue():
  while any([coroutines_queue, coroutines_waiting_for_receive, coroutines_waiting_for_send]):
    while not coroutines_queue:
      sockets_can_receive, sockets_can_send, [] = select.select(
                                                list(coroutines_waiting_for_receive.keys()),
                                                list(coroutines_waiting_for_send.keys()),
                                                []
      )
      
      for receiving_socket in sockets_can_receive:
        coroutines_queue.append(coroutines_waiting_for_receive.pop(receiving_socket))
      
      for sending_socket in sockets_can_send:
        coroutines_queue.append(coroutines_waiting_for_send.pop(sending_socket))

    
    current_coroutine = coroutines_queue.popleft()
    try:
      why_stopped, which_resource = next(current_coroutine)
      if why_stopped == "receiving":
        coroutines_waiting_for_receive[which_resource] = current_coroutine
      elif why_stopped == "sending":
        coroutines_waiting_for_send[which_resource] = current_coroutine
      elif why_stopped == "waiting for future":
        coroutines_waiting_for_future[which_resource] = current_coroutine
        which_resource.add_done_callback(future_done)

    except StopIteration:
      pass


class Async_Socket(object):
  def __init__(self, socket):
    self.socket = socket
  
  def accept(self):
    yield ("receiving", self.socket)
    client_socket, client_address = self.socket.accept()
    return (Async_Socket(client_socket), client_address)

  def recv(self, max_size):
    yield ("receiving", self.socket)
    return self.socket.recv(max_size)
  
  def send(self, data):
    yield ("sending", self.socket)
    return self.socket.send(data)
  
  def __getattr__(self, name):
    return getattr(self.socket, name)




n_threads = 4
threads_pool = concurrent.futures.ThreadPoolExecutor(n_threads)

def fib_server(address):
  # create a socket and bind it to the given address
  socket_stream = Async_Socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
  socket_stream.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  socket_stream.bind(address)
  socket_stream.listen()
  while True:
    client_socket, client_address = yield from socket_stream.accept() #non-blocking
    
    print("Connection from: ", client_address)
    coroutines_queue.append(fibonacci_handler(client_socket))

def fibonacci_handler(client_socket):
  while True:
    MAX_LENGTH = 100
    request = yield from client_socket.recv(MAX_LENGTH) # non-blocking

    if not request:
      break

    result_future = threads_pool.submit(fibonacci, int(request))
    
    yield ("waiting for future", result_future)
    result = result_future.result() # blocking

    yield from client_socket.send(str(result).encode("ascii") + b"\n") # non-blocking
  
  print("Connection closed")

def fibonacci(n):
  return 1 if n <= 2 else fibonacci(n - 1) + fibonacci(n - 2)

coroutines_queue.append(fib_server(("localhost", 30000)))
run_event_queue()