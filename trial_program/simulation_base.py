import socket
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from datetime import datetime

log_file = 'log.txt'

def log_message(message):
    with open(log_file, 'a') as file:  # 追記モードでファイルを開く
        file.write(message + '\n')  # メッセージを書き込む

# クライアント
def client_program(server_ip, server_port):
    # ソケットの作成
    client_socket = socket.socket()
    client_socket.connect((server_ip, server_port))

    # 古典通信の例
    message = "Hello from Client!"
    client_socket.send(message.encode())
    log_message(f"(Client)Sent: {message}")

    # 量子通信の例
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)  # アダマールゲート
    circuit.measure(0, 0)

    # シミュレータを使用して実行
    simulator = AerSimulator()
    transpiled_circuit = transpile(circuit, simulator)
    job = simulator.run(transpiled_circuit, shots=1024)  
    result = job.result()

    quantum_result = result.get_counts(circuit)
    log_message(f"(Client)Quantum result: {quantum_result}")

    client_socket.close()

# サーバ
def server_program(port):
    server_socket = socket.socket()
    server_socket.bind(('127.0.0.1', port)) #ソケットにローカルアドレスを紐付け。0.0.0.0は外部からの接続も受け入れる
    server_socket.listen(1) #ソケットを接続待ちに(最大同時接続数は1)
    log_message("(Server)Waiting for connection...")

    conn, address = server_socket.accept() #conn：データの送受信を担当
    log_message(f"(Server)Connection from: {address}")

    # 古典通信の受信
    data = conn.recv(1024).decode()
    log_message(f"(Server)Received: {data}")

    conn.close()
    server_socket.close()

# 中継器
def relay_program(port, next_server_ip, next_server_port):
    relay_socket = socket.socket()
    relay_socket.bind(('0.0.0.0', port))
    relay_socket.listen(1)
    log_message("(Repeater)Relay waiting for connection...")

    conn, address = relay_socket.accept()
    log_message(f"(Repeater)Relay connected from: {address}")

    # 古典通信の受信
    data = conn.recv(1024).decode()
    log_message(f"(Repeater)Relay received: {data}")

    # 次のサーバへデータを送信
    next_server_socket = socket.socket()
    next_server_socket.connect((next_server_ip, next_server_port))
    log_message(f"(Repeater)next server : ({next_server_ip}, {next_server_port})")
    next_server_socket.send(data.encode())
    log_message(f"(Repeater)Relay sent to next server: {data}")

    relay_socket.close()
    next_server_socket.close()
    conn.close()

# サーバプログラムを実行
if __name__ == '__main__':
    import threading

    # 現在の日時を取得
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # ログメッセージに日時を追加
    log_message(f"\n time: {current_time}")

    server_thread = threading.Thread(target=server_program, args=(5001,))
    relay_thread = threading.Thread(target=relay_program, args=(6000, '127.0.0.1', 5001))

    server_thread.start()
    relay_thread.start()

    # クライアントプログラムを実行
    client_program('127.0.0.1', 6000)

    # relay_thread.join()
    # server_thread.join()
    
