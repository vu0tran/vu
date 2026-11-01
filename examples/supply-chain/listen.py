import socket, sys
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", 9999)); s.listen()
c, _ = s.accept(); data = c.recv(1000).decode()
print("attacker's server got: " + data, flush=True)
