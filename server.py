# \n is used to replace a comma in messages


import socket
import threading
import re
import os
import subprocess
from select import select
from datetime import datetime

# threading is used to allow moderator input while the server is up and shutdown the server

# server socket parameters
IP = "0.0.0.0"
PORT = 12345
MAX_LEN = 1024

# incidcates to the server wither to run or to stop
run_flag = True

# lists
client_sockets = []
client_names = {}  # {addr, name}

messages_to_send_public = []  # (data, addr)
messages_to_send_private = []  # (data, d_addr, s_name)

admins = []

muted_users = []  # addr
users_to_kick = []  # addr


def print_server_commands():
    """
    prints the command list to the moderator
    :return: None
    """
    print(
        f"Server is running on {(IP, PORT)}\nServer commands:\np Prints a list of the connected clients\nq Shuts down the server\na Shows admins\nc Clears the screen\nl Prints the list of commands")


def print_clients():
    """
    prints the client list to the moderator
    :return: None
    """
    global client_sockets

    output = ""
    for i in range(len(client_sockets)):
        addr = client_sockets[i].getpeername()
        output += f"#{str(i + 1)} {client_names[addr]} {addr}\n"
    if output == "":
        print("No clients are connected at the moment")
    else:
        print(output)
    print(str(client_names) + "\n" + str(muted_users) + "\n" + str(users_to_kick))


def print_admins(s_addr=None):
    """
    creates a string of the admin names to the server moderator or a client
    :param s_addr: optional. indicates the source request (a moderator or a client)
    :type  s_addr: tuple/None
    :return: None
    """
    if len(admins) > 0:
        output = "Admins: "
        for name in admins:
            output += name + ", "
    else:
        output = "No admins are connected at the moment"
    if s_addr is None:
        print(output)
    else:
        messages_to_send_private.append((output[output.find(" ") + 1:], s_addr, "@List of admins"))


def clear_screen():
    """
    clears the screen
    :return: None
    """
    if os.name == "nt":
        subprocess.run("cls", shell=True)
    else:
        subprocess.run("clear", shell=True)


def broadcast_welcome(username):
    """
    welcomes a user in public
    :param username: the name of the new user
    :type username: str
    :return: None
    """
    if username in admins:
        admin_indicator = "@"
    else:
        admin_indicator = ""
    message = f"{admin_indicator}{username} has connected!"
    for s in client_sockets:
        s.send(f"{len(message)},{message}".encode())


def broadcast_goodbye(username):
    """
    sends a public farewell message
    :param username: the leaving user
    :type username: str
    :return: None
    """
    if username in admins:
        admin_indicator = "@"
    else:
        admin_indicator = ""
    output = f"{admin_indicator}{username} has left"
    for s in client_sockets:
        s.send(f"{len(output)},{output}".encode())


def kick_user(name):
    """
    kicks a user
    :param name:the name of the user to kick
    :type name: str
    :return: None
    """
    addr = find_addr_by_name(name)
    # searching the client's socket
    for s in client_sockets:
        if s.getpeername() == addr:
            users_to_kick.append(addr)
            messages_to_send_public.append((f"{name} was kicked out", (IP, PORT)))
            return


def find_addr_by_name(name):
    """
    converts address a name to address (tuple)
    :param name: name to convert
    :type name: str
    :return: returns the address connected to the given name (otherwise returns None)
    """
    l_names = list(client_names.values())
    l_addrs = list(client_names.keys())
    # index raises an error when the value is not found
    try:
        index_name = l_names.index(name)  # index addr = index name
    except:
        return None
    return l_addrs[index_name]


def remove_user(addr, s):
    """
    removes users from the desiered lists
    :param addr: address of the user to remove
    :type addr: tuple
    :param s: socket of the user to remove
    :type s: socket
    :return: None
    """
    users_to_kick.remove(addr)
    del client_names[addr]
    client_sockets.remove(s)
    try:
        muted_users.remove(addr)
    except:
        pass
    s.close()


def send_public_messages():
    """
    sends the public messages to the open sockets
    :return: None
    """
    for m, origin in messages_to_send_public:
        if origin != (IP, PORT):
            user_source = client_names[origin]
        else:
            user_source = ""  # sent by the server
        if user_source in admins:
            admin_indicator = "@"
        else:
            admin_indicator = ""
        for s in client_sockets:
            addr = s.getpeername()
            if origin != addr:
                now = datetime.now().strftime("%H:%M")
                message = f"[{now}] {admin_indicator}{user_source}: " + m.replace(",", "\n")
                s.send(f"{len(message)},{message}".encode())
                if addr in users_to_kick:
                    remove_user(addr, s)
        messages_to_send_public.remove((m, origin))


def send_private_messages():
    """
        sends the private messages to the open sockets
        :return: None
    """
    for data, d_addr, s_name in messages_to_send_private:
        for s in client_sockets:
            if s.getpeername() == d_addr:
                now = datetime.now().strftime("%H:%M")
                if s_name == "ERROR" or s_name == "@List of admins":
                    decorator = "!"
                else:
                    decorator = "ᵜ"
                if s_name in admins:
                    admin_indicator = "@"
                else:
                    admin_indicator = ""
                message = f"[{now}] {decorator}{admin_indicator}{s_name}{decorator}: " + data.replace(",", "\n")
                s.send(f"{len(message)},{message}".encode())
                break
        messages_to_send_private.remove((data, d_addr, s_name))


def process_command(data, s):
    """
    process an incoming data
    :param data: incoming data
    :type data: list
    :param s: source's socket
    :type s:socket
    :return: None
    """
    # checking if the data is a message
    is_muted = data[1] in muted_users
    if int(data[2]) == 1:
        if data[4] == "quit":
            addr = s.getpeername()
            print(f"{client_names[addr]} has disconnected {addr} ")
            client_sockets.remove(s)
            broadcast_goodbye(client_names.pop(addr))
            s.close()
        elif not is_muted:
            if data[4].startswith("!"):
                if len(re.findall(r".+\s+.+", data[4])) > 0:
                    # checking whether the user exists of not
                    d_name = data[4][1: data[4].find(" ")]
                    addr = find_addr_by_name(d_name)
                    if addr is not None:
                        # checking if user is not muted
                        message = data[4][data[4].find(" "):]
                        messages_to_send_private.append((message, addr, data[1]))
                    else:
                        messages_to_send_private.append(("user not found", s.getpeername(), "ERROR"))
                else:
                    messages_to_send_private.append(("specify a message to send", s.getpeername(),
                                                     "ERROR"))
            else:
                messages_to_send_public.append((data[4], s.getpeername()))
        else:
            messages_to_send_private.append(("you are muted", s.getpeername(), "ERROR"))
    elif int(data[2]) == 2:
        if data[1] in admins:
            if len(data) > 4 and len(re.findall(r"^[^@\s]+$", data[4])):
                if data[4] in client_names.values():
                    admins.append(data[4])
                    messages_to_send_public.append((f"{data[4]} is now admin", (IP, PORT)))
                else:
                    messages_to_send_private.append(("user not found", s.getpeername(), "ERROR"))
            else:
                messages_to_send_private.append(("please specify a valid name", s.getpeername(), "ERROR"))
        else:
            messages_to_send_private.append(("you are not allowed to do that", s.getpeername(), "ERROR"))
    elif int(data[2]) == 3:
        if data[1] in admins:
            if len(re.findall(r"^[^@\s]+\b$", data[4])) > 0:
                if data[4] in client_names.values():
                    kick_user(data[4])
                else:
                    messages_to_send_private.append(("user not found", s.getpeername(), "ERROR"))
            else:
                messages_to_send_private.append(("please specify a valid name", s.getpeername(), "ERROR"))
        else:
            messages_to_send_private.append(("you are not allowed to do that", s.getpeername(), "ERROR"))
    elif int(data[2]) == 4:
        if data[1] in admins:
            if len(re.findall(r"^[^@\s]+$", data[4])) > 0:
                if data[4] in client_names.values():
                    muted_users.append(data[4])
                    messages_to_send_private.append(("you were muted", find_addr_by_name(data[4]), "ERROR"))
                else:
                    messages_to_send_private.append(("user not found", s.getpeername(), "ERROR"))
            else:
                messages_to_send_private.append(("please specify a valid name", s.getpeername(), "ERROR"))
        else:
            messages_to_send_private.append(("you are not allowed to do that", s.getpeername(), "ERROR"))
    elif int(data[2]) == 5:
        print_admins(s.getpeername())


def server():
    """
    main server function.
    contains the listenning part
    :return: None
    """
    global client_sockets
    global IP
    global PORT
    global MAX_LEN

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print_server_commands()

    while run_flag:
        rlist, wlist, _ = select([server_socket] + client_sockets, client_sockets, [], 3)

        for s in rlist:
            # checking for new incoming connection
            if s is server_socket:
                new_client_socket, new_client_address = s.accept()
                # two separated lists - sockets and name
                client_sockets.append(new_client_socket)
                data = new_client_socket.recv(MAX_LEN).decode().split(",")
                client_names[new_client_address] = data[1]
                if admins == []:
                    admins.append(data[1])
                print(f"New client ({data[1]}) has connected: {str(new_client_address)}")
                broadcast_welcome(data[1])
            else:
                # handling a command
                try:
                    # fixing the disconnection error - disconnecting the client properly
                    data = s.recv(MAX_LEN).decode().split(",")

                except:
                    client_sockets.remove(s)
                    name_temp = client_names.pop(s.getpeername())
                    broadcast_goodbye(name_temp)
                    print(f"{name_temp} has disconnected {s.getpeername()} ")
                    continue
                data = list(map(lambda c: c.replace("\n", ","), data))
                process_command(data, s)

        send_public_messages()
        send_private_messages()

    # server shutdown process
    for s in client_sockets:
        s.close()
    server_socket.close()
    print("Server is down")


def main():
    """
    main function
    :return: None
    """
    global run_flag

    clear_screen()
    t = threading.Thread(target=server)
    t.start()
    while run_flag:
        command = input().lower()
        if command == "p":
            print_clients()
        elif command == "q":
            run_flag = False
            print("Shutting down the server")
        elif command == "a":
            print_admins()
        elif command == "c":
            clear_screen()
        elif command == "l":
            print_server_commands()
        else:
            print("No command found")


if __name__ == "__main__":
    main()
