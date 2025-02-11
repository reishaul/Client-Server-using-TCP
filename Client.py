import socket
import re

"""
This module implements a TCP client using a sliding window protocol for reliable message transmission.

Key Features:
- Reads configuration (message, timeout, window size) from a file or user input.
- Splits messages into chunks based on maximum allowed size.
- Uses the sliding window protocol for reliable delivery with retransmission on timeout.

Functions:
- `read_input_file`: Reads key-value pairs from a file into a dictionary.
- `get_divide_message`: Splits a message into chunks of a given size.
- `sliding_window`: Sends message chunks using the sliding window protocol.
- `start_client`: Initializes the client, handles input, and starts communication.

Usage:
Run the script, choose input type (file or manual), provide necessary details 
and let the client communicate with the server.
"""


SERVER_HOST = 'localhost'
SERVER_PORT = 13002

"Reads the key-value pairs from a file and returns them as a dictionary."
def read_input_file(filename):
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

"Splits a string to parts,according to the buffer size."
def get_divide_message(data: str, buffer: int) -> list[str]:
    messages = []
    size = len(data)
    counter = 0

    for i in range(0, size, buffer):
        chunk = data[i:i + buffer]
        messages.append(f"M{counter}: {chunk}")
        counter += 1
    return messages

def get_time_out(data):
    return int(data.get("timeout", 0))

def get_window_size(data):
    return int(data.get("window_size", 0))

def get_message(data, max_message_size):
    message = data.get("message", "")
    return message

def get_maximum_msg_size(data):
    return int(data.get("maximum_msg_size", 0))

"Implements the sliding window protocol."
def sliding_window(client_socket: socket.socket, message_segments, window_size, timeout1):

    """additional variable for using"""
    next_seq = 0
    acked_seq = -1
    window = []#the message that isn't receive ack will be here
    timeout_counter = 0

    while acked_seq < len(message_segments) - 1:

        while (len(window) < window_size) and (next_seq < len(message_segments)):
            data = f"{message_segments[next_seq]}\n"

            client_socket.send(data.encode())

            print("Sent:", data)
            window.append(next_seq)
            next_seq += 1

        try:
            client_socket.settimeout(timeout1)
            ack = client_socket.recv(1024).decode()#get message from server
            count_n = ack.count("\n")
            split_ack = ack.split("\n")[:-1]

            for i in range(count_n):
                ack = split_ack[i]

                print(f"Received {ack}")
                match = re.search(r"M(\d+)", ack)

                if match:
                    ack_number = int(match.group(1))
                    if ack_number > acked_seq:
                        acked_seq = ack_number
                        while len(window) > 0 and window[0] <= ack_number:
                            window.pop(0)
                else:
                    print("Failed to parse ACK number from received message.")


        except socket.timeout:
            print("Timeout occurred. Resending messages in window...")
            timeout_counter+=1
            if timeout_counter>6:#if time out occurred more then six times- finish
                print("Timeout occurred too much, please try again")
                client_socket.close()
                exit(1)

            for seq in window: # Resend all unacknowledged messages
                data = f"{message_segments[seq]}\n"
                client_socket.send(data.encode())
                print(f"Resent: {data}")

    print("All messages sent and acknowledged.")


def start_client():
    """Starts the client, handles user input, and initiates communication with the server."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")

    choice = input("Do you want to get the Maximum message size from a file or by insert an input? (file/input): (or enter 'q' to quit): ").strip().lower()

    # Request the maximum message size from the server
    client_socket.send("MAX_MESSAGE_SIZE".encode())

    max_message_size = int(client_socket.recv(1024).decode())
    print(f"Maximum message size received from server: {max_message_size} bytes")

    if choice == "q":
        print("Client wishes to disconnect.")
        client_socket.send(choice.encode('utf-8'))
        client_socket.close()
        exit(0)

    elif choice == "input":
        data = input("Enter the message: ")
        window_size = int(input("Enter the window size: "))
        time_out = float(input("Enter the timeout (in seconds): "))

    elif choice == "file":
        name = input("Enter the name of the file you want to read from:")
        file_ = read_input_file(name)
        if not file_:
            print("File not found.")
        window_size = get_window_size(file_)
        time_out = get_time_out(file_)
        data = get_message(file_, max_message_size)

    else:
        print("Invalid choice or missing file argument.")
        return

    message_by_list = get_divide_message(data, max_message_size)

    sliding_window(client_socket, message_by_list, window_size, time_out)
    client_socket.close()


if __name__ == "__main__":
    start_client()


