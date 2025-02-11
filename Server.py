import socket
import re
"""
Implements and logic by Ron Avraham - ronavraham1999@gmail.com, Rei Shaul - reishaul1@gmail.com

This module implements a TCP server using the sliding window protocol for reliable message reception.

Key Features:
- Reads configuration (maximum message size, timeout, and window size) from a file or user input.
- Manages client-server communication to receive segmented messages and send acknowledgments.
- Implements acknowledgment handling for in-order and out-of-order messages.
- Detects missing messages and sends the last acknowledged sequence.

Functions:
- `read_input_file`: Reads key-value pairs from a file into a dictionary.
- `handle_clients`: Main server function to manage client connections and implement
 the sliding window protocol.

Usage:
Run the script to start the server. It listens for a connection, handles message reception using the sliding window protocol, and sends appropriate acknowledgments to the client.
"""


def read_input_file(filename):
    """Reads key-value pairs from a file and returns them as a dictionary."""
    try:
        with open(filename, 'r') as file:
            data = {}
            for line in file:
                if ':' in line:
                    key, value = line.strip().split(":", 1)
                    data[key.strip()] = value.strip()
            return data
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return {}
    except ValueError:
        print(f"Error: Invalid format in file {filename}.")
        return {}

def get_time_out(data):
    return int(data.get("timeout", 0))

def get_window_size(data):
    return int(data.get("window_size", 0))

def get_message(data, max_message_size):
    message = data.get("message", "")
    return message[:max_message_size]

def get_maximum_msg_size(data):
    return int(data.get("maximum_msg_size", 0))

def handle_clients():
    """Handles server-side operations, including communication with the client."""
    global MAX_MESSAGE_SIZE
    SERVER_HOST = 'localhost'
    SERVER_PORT = 13002

    # Create and configure the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(1)

    print(f"Server is running and listening on {SERVER_HOST}:{SERVER_PORT}")
    # Accept a new connection
    connection_with_client, client_address = server_socket.accept()
    print(f"Connection established with {client_address}")

    choice = input("Do you want to get the Maximum message size from a file or by insert an input? (file/input): ").strip().lower()

    if choice == "input":
        MAX_MESSAGE_SIZE = int(input("Enter the maximum message size in bytes: "))
        msg = input("Enter the message: ")
        window_size = input("Enter the window size: ")
        time_out = input("Enter the timeout (in seconds): ")

    elif choice == "file":
        name = input("Enter the name of the file you want to read from:")
        file_ = read_input_file(name)
        MAX_MESSAGE_SIZE = get_maximum_msg_size(file_)
        window_size = get_window_size(file_)
        time_out = get_time_out(file_)

    elif choice == "q":
        print("Server wishes to disconnect.")
        connection_with_client.send(choice.encode('utf-8'))
        connection_with_client.close()
        exit(0)

    else:
        print("Invalid input.")

    messages_received = []
    ack_count = 0
    last_ack = -1
    stores_ack=[]

    data = connection_with_client.recv(1024)
    if not data:
        print(f"Client {client_address} has disconnected before sending")
    client_message = data.decode("utf-8")

    if client_message == "MAX_MESSAGE_SIZE":
        connection_with_client.send(f"{MAX_MESSAGE_SIZE}".encode())
        print(f"Sent max message size: {MAX_MESSAGE_SIZE} bytes")

    while True:
        data = connection_with_client.recv(1024)

        if not data:
            print(f"Client {client_address} has disconnected before sending")
            break

        client_message = data.decode("utf-8")

        count_n=client_message.count("\n")
        split_message = client_message.split("\n")[:-1]
        for i in range(count_n):

            client_message=split_message[i]

            match = re.match(r"M(\d+):", client_message)
            if match:
                sequence = int(match.group(1))
            else:
                print("No match found!")

            stores_ack.append(sequence)
            stores_ack.sort()

            if int(sequence)>ack_count:
                print("Some message didn't arrive")
                print(f"Message received: {client_message}")
                messages_received.append(client_message)
                for i in range(len(stores_ack)):
                    if i == stores_ack[i]:
                        last_ack = i
                    else:
                        break
                ack_count = last_ack +1#
                connection_with_client.send(f" ACK: Message received: M{last_ack}\n".encode())

            if sequence == ack_count:#the regular case that the messages arrived inorder
                last_ack=sequence
                messages_received.append(client_message)
                print(f" ACK: Message received: {client_message.split(":",1)[0]}")

                connection_with_client.send(f" ACK: Message received: {client_message.split(":",1)[0]}\n".encode())
                ack_count += 1

                print(f"Message received: {client_message}")
                print(f"Sent Ack for message: {client_message}")#that ack is sent only if it is inorder

            elif sequence > ack_count:
                print(f"Message out of received: {client_message}")
                connection_with_client.send(f" ACK: Message received: M{last_ack}\n".encode())


    connection_with_client.close()
    print(f"Closing connection with {client_address}")

    server_socket.close()
    print("Server has been stopped")

if __name__ == "__main__":
    handle_clients()





