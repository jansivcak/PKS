import socket
import struct
import threading


class MessageType:
    SYN = 1
    SYNACK = 2
    ACK_SYN = 3
    ACK = 4
    SEDA = 5
    KEEP_AL = 6
    ERROR = 7
    END = 8


class Handshake:
    def __init__(self, ip, client_port, sock_send):
        self.ip = ip
        self.client_port = client_port
        self.sock_send = sock_send

    def send_handshake(self):
        message_type = MessageType.SYN
        seq_number = 1
        total_fragments = 1
        checksum = 0
        packed_message = struct.pack('!BHHH', message_type, seq_number, total_fragments, checksum)
        self.sock_send.sendto(packed_message, (self.ip, self.client_port))

    def send_SYNACK(self):
        message_type = MessageType.SYNACK
        seq_number = 1
        total_fragments = 1
        checksum = 0
        packed_message = struct.pack('!BHHH', message_type, seq_number, total_fragments, checksum)
        self.sock_send.sendto(packed_message, (self.ip, self.client_port))

    def send_ACK_SYN(self):
        message_type = MessageType.ACK_SYN
        seq_number = 1
        total_fragments = 1
        checksum = 0
        packed_message = struct.pack('!BHHH', message_type, seq_number, total_fragments, checksum)
        self.sock_send.sendto(packed_message, (self.ip, self.client_port))
        print("Komunikacia nadviazana")


class resposne:
    def __init__(self, ip, client_port, sock_send):
        self.ip = ip
        self.client_port = client_port
        self.sock_send = sock_send

    def send_ACK(self):
        message_type = MessageType.ACK
        seq_number = 1
        total_fragments = 1
        checksum = 0
        packed_message = struct.pack('!BHHH', message_type, seq_number, total_fragments, checksum)
        self.sock_send.sendto(packed_message, (self.ip, self.client_port))


class P2PClient:
    def __init__(self, your_ip, client_ip, send_port, listen_port, sender_port) -> None:
        self.sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.your_ip = your_ip
        self.client_ip = client_ip
        self.handshake_pointer = False

        self.sock_listen.bind((your_ip, listen_port))
        self.sock_send.bind((your_ip, send_port))

        self.sender_port = sender_port
        self.your_ip = your_ip
        self.client_ip = client_ip

        self.handshake = Handshake(client_ip, sender_port, self.sock_send)
        self.response = resposne(client_ip, sender_port, self.sock_send)

        self.running = True

    def receive(self):
        while self.running:
            data, addr = self.sock_listen.recvfrom(1024)
            message_type, seq_number, total_fragments, checksum = struct.unpack('!BHHH',
                                                                                data[:struct.calcsize('!BHHH')])
            header_size = struct.calcsize('!BHHH')

            if message_type == MessageType.SYN:
                self.handshake.send_SYNACK()
            if message_type == MessageType.SYNACK:
                self.handshake.send_ACK_SYN()
                self.handshake_pointer = True
            if message_type == MessageType.ACK_SYN:
                print("Prijate potvrdenie handshaku")
                print("IP: ", addr[0], " Port: ", addr[1])
                self.handshake_pointer = True
            if message_type == MessageType.SEDA:
                message_content = data[header_size:].decode('utf-8')
                print("Prijata sprava: ", message_content)
                print("IP: ", addr[0], " Port: ", addr[1])
                self.response.send_ACK()
            if message_type == MessageType.ACK:
                print("Sprava bola poslana uspesne")
            if message_type == MessageType.END:
                print("Client na druhej strane ukončil komunikaciu")

    def send_handshake(self):
        self.handshake.send_handshake()
        self.handshake_pointer = True

    def send_message(self, message):
        if message == "quit":
            message_type = MessageType.END
            seq_number = 1
            total_fragments = 1
            checksum = 1
            header = struct.pack('!BHHH', message_type, seq_number, total_fragments, checksum)
            data = message.encode('utf-8')
            self.sock_send.sendto(header + data, (self.client_ip, self.sender_port))
        else:
            message_type = MessageType.SEDA
            seq_number = 1
            total_fragments = 1
            checksum = 1
            header = struct.pack('!BHHH', message_type, seq_number, total_fragments, checksum)
            data = message.encode('utf-8')
            self.sock_send.sendto(header + data, (self.client_ip, self.sender_port))

    def quit(self):
        self.running = False
        self.sock_send.close()
        self.sock_listen.close()
        print("Klient odpojený")


if __name__ == "__main__":

    your_ip = input("Zadaj svoju ip adresu:")
    client_ip = input("Zadaj ip adresu ktoru chces kontaktovat:")
    client_port_send = int(input("Zadaj port na odosielanie:"))
    client_port_listen = int(input("Zadaj port na pocuvanie:"))
    client_port_sender = int(input("Zadaj port na komunikaciu:"))

    client = P2PClient(your_ip, client_ip, client_port_send, client_port_listen, client_port_sender)
    receiver_thread = threading.Thread(target=client.receive)
    receiver_thread.daemon = True
    receiver_thread.start()

    while True:
        command = input("Pre inicializaciu Hanshake - SYN:")
        if client.handshake_pointer == True:
            break
        elif command == "SYN":
            client.send_handshake()
            break
        else:
            print("Default")


    while True:
        message = input("Zadajte správu na odoslanie: ")
        client.send_message(message)
        if message == "quit":
            break

    client.quit()