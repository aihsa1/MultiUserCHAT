import socket
import sys
import threading
import os
import re
import msvcrt
import time
import argparse

input_lst = []


def initial_connection():
    """
    establishes the connection
    :return: client's socket and name
    :rtype: tuple
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="name of the client",
                        type=str, required=True)
    parser.add_argument("--ip", help="IP address of the server",
                        default="127.0.0.1")
    args = parser.parse_args()

    PORT = 12345

    try:
        # name = sys.argv[1]  # name
        name = args.name
        IP = args.ip
    except:
        print("Enter your name and IP when you run the client")
        sys.exit(0)
    if len(re.findall(r"[!@\s]", name)) > 0:
        print("ERROR:A valid name cannot contain @, whitespaces nor exclamation marks")
        sys.exit(0)

    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

    with open("client_welcome.txt", "r") as f:
        print(r"{}".format(f.read()))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((IP, PORT))
    except:
        print("Unable to connect")
        sys.exit(0)
    # connection establishment
    client_socket.send(
        ",".join([str(len(name)), name, str(0)]).encode())  # code 0 is used to connecting and disconnecting
    data = client_socket.recv(1024).decode().split(",")[1]
    print(data + "\n->", end="")
    return client_socket, name


def input_chars():
    """
    Input function.
    The goal of this function is to prevent collision between the input and the recieved message
    :return: User's message (input)
    :rtype: str
    """
    # flush is used to output and clear the stdout buffer (otherwise it won't be printed as intended)
    lk = threading.Lock()
    global input_lst
    input_lst = []
    while True:
        if msvcrt.kbhit():
            lk.acquire()
            char = msvcrt.getch()
            # \x08 is backspace in binary
            if char in b"\r" or char in b"\n":
                sys.stdout.write("\n->")
                sys.stdout.flush()
                lk.release()
                return
            elif char == b'\x08':
                if len(input_lst) > 0:
                    sys.stdout.write(char.decode() * len(input_lst))
                    sys.stdout.write(" " * len(input_lst))
                    sys.stdout.write(char.decode() * len(input_lst))
                    input_lst = input_lst[:-1]
                    sys.stdout.write("".join(input_lst))
            else:
                # concatenating printable characters only
                try:
                    char_decoded = char.decode()
                except:
                    char_decoded = ""
                if char in [b'\000', b'\xe0']:
                    # msvcrt calls itself one more time when it gets a special character
                    _ = msvcrt.getch()
                else:
                    input_lst += char_decoded
                    sys.stdout.write("".join(input_lst)[-1])
            sys.stdout.flush()
            lk.release()
        time.sleep(0.05)


def write(client_socket, name):
    """
    handles the client functionality
    :param client_socket: client's socket object
    :type client_socket: socket
    :param name: client's name
    :type name: str
    :return: None
    """
    stay = True
    while stay:
        input_chars()
        # replace comma with newline (comma is a special character)
        command = "".join(input_lst).replace(",", "\n")
        if command == "quit":
            code = 1
            stay = not stay
            data = ",".join([str(len(name)), name, str(
                code), str(len(command)), command])
        elif command.startswith("inviteMan"):
            code = 2
            if " " in command:
                name2 = command.split(" ", 1)[1]
            else:
                name2 = ""
            data = ",".join(
                [str(len(name)), name, str(code), str(len(name2)), name2])
        elif command.startswith("getout"):
            code = 3
            if " " in command:
                name2 = command.split(" ", 1)[1]
            else:
                name2 = ""
            data = ",".join(
                [str(len(name)), name, str(code), str(len(name2)), name2])
        elif len(re.findall(r"^shsh\b", command)) > 0:
            code = 4
            if " " in command:
                name2 = command.split(" ", 1)[1]
            else:
                name2 = ""
            data = ",".join(
                [str(len(name)), name, str(code), str(len(name2)), name2])
        elif command == "view-managers":
            code = 5
            data = ",".join([str(len(name)), name, str(code)])
        else:
            # valid for public messages and private messages
            code = 1
            data = ",".join([str(len(name)), name, str(
                code), str(len(command)), command])
        client_socket.send(data.encode())

    client_socket.close()


def main():
    """
    main function (calls the other function).
    this function is used for listening for incoming data
    :return: None
    """
    client_socket, name = initial_connection()

    t_write = threading.Thread(target=write, args=(
        client_socket, name), daemon=True)
    t_write.start()

    while t_write.is_alive():
        try:
            data = client_socket.recv(1024).decode().split(",")[
                1].replace("\n", ",")
        except:
            # disconnected from the server
            sys.exit(0)
        print(f"\n{data}\n->", end="")
        print("".join(input_lst), end="")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
