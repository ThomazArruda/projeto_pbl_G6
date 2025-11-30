import socket

UDP_IP = "0.0.0.0"
UDP_PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Escutando UDP em {UDP_IP}:{UDP_PORT}...")
print("Pressione Ctrl+C para sair.")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        print(f"Recebido de {addr}: {data.decode('utf-8')}")
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Erro: {e}")
