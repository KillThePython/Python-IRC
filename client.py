import socket
import sys
import threading
import argparse
import curses
from curses import wrapper
from curses.textpad import Textbox


class IRCClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nickname = None
        self.stdscr = None
        self.chat_win = None
        self.input_win = None
        self.input_box = None
        self.messages = []

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.add_message(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            self.add_message(f"Failed to connect: {e}")
            sys.exit(1)

    def send_message(self, message):
        self.socket.send(message.encode('utf-8'))
        self.add_message(f"You: {message}")

    def receive_messages(self):
        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    self.add_message("Disconnected from server")
                    sys.exit()
                self.add_message(data)
            except:
                self.add_message("Error receiving message")
                sys.exit()

    def add_message(self, message):
        self.messages.append(message)
        self.refresh_chat_window()

    def refresh_chat_window(self):
        self.chat_win.clear()
        height, width = self.chat_win.getmaxyx()
        start = max(0, len(self.messages) - height)
        for i, msg in enumerate(self.messages[start:]):
            wrapped_lines = [msg[j:j + width] for j in range(0, len(msg), width)]
            for line in wrapped_lines:
                if i < height:
                    self.chat_win.addstr(i, 0, line)
                    i += 1
        self.chat_win.refresh()

    def setup_windows(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

        height, width = self.stdscr.getmaxyx()
        self.chat_win = curses.newwin(height - 4, width - 2, 1, 1)
        self.input_win = curses.newwin(1, width - 4, height - 2, 2)

        self.chat_win.scrollok(True)
        self.input_win.scrollok(True)

        self.stdscr.clear()
        self.stdscr.border()
        self.stdscr.refresh()

        self.input_box = Textbox(self.input_win)

    def run(self):
        self.setup_windows()
        self.connect()

        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        while True:
            self.input_win.clear()
            self.input_box.edit()
            message = self.input_box.gather().strip()

            if message.lower() == 'quit':
                self.socket.close()
                break
            elif message:
                self.send_message(message)


def main(stdscr):
    curses.echo()
    parser = argparse.ArgumentParser(description="IRC Client")
    parser.add_argument("--host", default="localhost", help="IRC server host")
    parser.add_argument("--port", type=int, default=6667, help="IRC server port")
    args = parser.parse_args()

    client = IRCClient(args.host, args.port)
    client.stdscr = stdscr
    client.run()


if __name__ == "__main__":
    wrapper(main)