import socket
import select


class IRCServer:
    def __init__(self, host='0.0.0.0', port=6667):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.clients = {}
        self.channels = {}

    def run(self):
        print(f"Server running on {self.host}:{self.port}")
        while True:
            read_sockets, _, _ = select.select([self.socket] + list(self.clients.keys()), [], [])
            for sock in read_sockets:
                if sock == self.socket:
                    client_socket, address = self.socket.accept()
                    self.new_client(client_socket)
                else:
                    try:
                        data = sock.recv(1024).decode('utf-8').strip()
                        if data:
                            self.handle_command(sock, data)
                        else:
                            self.remove_client(sock)
                    except:
                        self.remove_client(sock)

    def new_client(self, client_socket):
        self.clients[client_socket] = {'nick': None, 'channels': []}
        client_socket.send(
            "Please set your nickname using /nick <nickname>\n".encode('utf-8'))

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            nick = self.clients[client_socket]['nick']
            for channel in self.clients[client_socket]['channels']:
                if channel in self.channels:
                    self.channels[channel].remove(client_socket)
            del self.clients[client_socket]
            client_socket.close()
            print(f"Client {nick} disconnected")

    def handle_command(self, client_socket, message):
        if message.startswith('/'):
            command = message.split()[0][1:]
            if command == 'nick':
                self.set_nickname(client_socket, message.split()[1])
            elif command == 'join':
                self.join_channel(client_socket, message.split()[1])
            elif command == 'privmsg':
                self.send_private_message(client_socket, message.split()[1], ' '.join(message.split()[2:]))
        else:
            self.broadcast_message(client_socket, message)

    def set_nickname(self, client_socket, nickname):
        self.clients[client_socket]['nick'] = nickname
        client_socket.send(f"Nickname set to {nickname}\n".encode('utf-8'))

    def join_channel(self, client_socket, channel):
        if channel not in self.channels:
            self.channels[channel] = set()
            client_socket.send(f"Created new channel {channel}\n".encode('utf-8'))
        else:
            client_socket.send(f"Joined existing channel {channel}\n".encode('utf-8'))
        self.channels[channel].add(client_socket)
        self.clients[client_socket]['channels'].append(channel)
        self.broadcast_channel_message(channel, f"{self.clients[client_socket]['nick']} has joined {channel}")

    def send_private_message(self, sender_socket, recipient, message):
        for client_socket, client_info in self.clients.items():
            if client_info['nick'] == recipient:
                client_socket.send(
                    f"Private message from {self.clients[sender_socket]['nick']}: {message}\n".encode('utf-8'))
                return
        sender_socket.send(f"User {recipient} not found\n".encode('utf-8'))

    def broadcast_message(self, sender_socket, message):
        sender_nick = self.clients[sender_socket]['nick']
        for channel in self.clients[sender_socket]['channels']:
            for client_socket in self.channels[channel]:
                if client_socket != sender_socket:
                    client_socket.send(f"{channel} <{sender_nick}> {message}\n".encode('utf-8'))

    def broadcast_channel_message(self, channel, message):
        for client_socket in self.channels[channel]:
            client_socket.send(f"{channel}: {message}\n".encode('utf-8'))


if __name__ == "__main__":
    server = IRCServer()
    server.run()
