https://github.com/websocket-client/websocket-client
from websocket import create_connection

ws = create_connection("ws://127.0.0.1:8000/ws/dashboard/1/")
ws.recv()
ws.send('1')
