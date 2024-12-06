import socket
import json

# ルーティングテーブルを読み込む
def load_routing_table(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# 中継器プログラム
def relay_program(port, routing_table_file):
    # ルーティングテーブルをロード
    routing_table = load_routing_table(routing_table_file)
    
    # 中継用ソケットを作成
    relay_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    relay_socket.bind(('0.0.0.0', port))
    relay_socket.listen(1)
    print(f"Relay waiting for connection on port {port}...")

    conn, address = relay_socket.accept()
    print(f"Relay connected to: {address}")
    
    # クライアントからデータを受信
    data = conn.recv(1024).decode()
    print(f"Relay received: {data}")

    # 受け取ったデータをどのノードに送るかを決める
    node = data.split(":")[0]  # 例: "node1"
    
    # ルーティングテーブルを参照して次のホップの情報を取得
    if node in routing_table:
        next_node = routing_table[node]
        next_ip = next_node['next_hop_ip']
        next_port = next_node['next_hop_port']
        
        # 次のノードにデータを送信
        next_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        next_server_socket.connect((next_ip, next_port))
        next_server_socket.send(data.encode())
        print(f"Relay sent data to {next_ip}:{next_port}")
        
        next_server_socket.close()
    else:
        print(f"Node {node} not found in routing table.")
    
    # ソケットを閉じる
    conn.close()

# 例としてポート5000で待機し、routing_table.jsonを参照
if __name__ == '__main__':
    relay_program(5001, 'routing_table.json')
