import socket
import json
import re
from datetime import datetime
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

log_file = 'log.txt'
client_log = './client/client_log.txt'
sockets = []

def log_message(message):
    with open(log_file, 'a') as file:  # 追記モードでファイルを開く
        file.write(message + '\n')  # メッセージを書き込む

def date_log_message(message):
    # 現在の時刻を取得（時刻のみ）
    current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    # ログメッセージに時刻を追加
    log_entry = f"{current_time} - {message}"
    
    # ログファイルに追記
    with open(client_log, 'a') as file:
        file.write(log_entry + '\n')  # メッセージを書き込む
# def close_all_sockets():
#     # 管理しているすべてのソケットを閉じる
#     for s in sockets:
#         try:
#             s.close()
#             print(f"Closed socket: {s}")
#         except Exception as e:
#             print(f"Error closing socket: {e}")

def load_json(file_path): 
    """
    jsonファイルを送るために変換する関数
    :param file_path: 送信するJSONデータのファイル名
    """
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)  # JSONファイルを辞書として読み込む
        return json_data
    except Exception as e:
        return Exception
    
def save_json_to_file(json_data, file_name): 
    """
    受け取ったJSONデータをファイルに保存する関数
    :param json_data: 保存するJSONデータ（Pythonの辞書型）
    :param file_name: 保存するファイル名
    """
    try:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_file_name = f"{file_name}_{current_time}.json"
        with open(new_file_name, 'w') as file:
            json.dump(json_data, file, indent=4)  # JSONデータをインデント付きで保存
        log_message(f"(Client)JSON data saved to {new_file_name}")
    except Exception as e:
        log_message(f"Error saving JSON data to {new_file_name}: {e}")

def extract_data_from_json(json, key):
    """
    JSONデータから指定されたキーの値を抜き出して返す関数。

    :param json: JSONデータ
    :param keys: 抜き出したいキーのリスト
    :return: 指定されたキーに対応する値を持つ辞書
    """
    try:
        if key in json:
            extracted_data = str(json[key])
            return extracted_data
        else:
            return f"Key '{key}' not found in JSON data"


    except Exception as e:
        print(f"Error reading or parsing the JSON file: {e}")
        return None

def client_program(server_ip, server_port):
    date_log_message(f"\n time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    stage = 1 # 通信のステージ
    # ソケットの作成
    client_socket = socket.socket()
    client_socket.connect((server_ip, server_port))

    while True:
        match stage:
            case 1: #request送信
                #ターミナルからメッセージを入力
                message = input("Enter filepath / message to send to server (or 'exit' to quit): ")

                if message.lower() == 'exit':
                    client_socket.send(message.encode())
                    log_message("(Client) Connection closed.")
                    date_log_message("(Client) Connection closed.")
                    break

                try:
                    # file pathのjsonファイルを読み込む
                    request_file = f"./client/{message}"
                    json_data = load_json(request_file)

                    # サーバに情報を送信
                    if json_data is not None:
                    # JSONデータをバイト列に変換して送信
                        json_bytes = json.dumps(json_data).encode('utf-8')
                        client_socket.send(json_bytes)
                        log_message(f"(Client)Sent JSON data: {json_data}")
                        date_log_message(f"(Client)Sent JSON data: {json_data}")
                        response = client_socket.recv(1024).decode()
                        if response.lower() == "request data received successfully! calculate estimated execution time...":
                            log_message("(Client) Wait for estimated execution time")
                            date_log_message("(Client) Wait for estimated execution time")
                            stage = 2
                            log_message(f"(Client) Moved to stage {stage}")
                            date_log_message(f"(Client) Moved to stage {stage}")
                        continue
                
                except Exception as e:
                    client_socket.send(message.encode())
                    log_message(f"(Client)Sent: {message}")
                    date_log_message(f"(Client)Sent: {message}")
                    
                response = client_socket.recv(1024).decode()
                log_message(f"(Client) Received from Server: {response}")
                date_log_message(f"(Client) Received from Server: {response}")
            
            case 2: #OK or NO
                response = client_socket.recv(1024).decode()
                log_message(f"(Client) Received from Server: {response}")
                date_log_message(f"(Client) Received from Server: {response}")
                result = re.search(r"(\d+)", response)
                if result:
                    while True:
                        # estimated_time = result.group(1)
                        message = input("Enter OK / NO : ")
                        if message.lower() == 'ok':
                            client_socket.send(message.encode())
                            log_message("(Client) Approved") 
                            date_log_message("(Client) Approved")
                            response = client_socket.recv(1024).decode()
                            if response.lower() == 'distribute rulesets':
                                stage = 3
                                message = 'OK'
                                client_socket.send(message.encode())
                                log_message(f"(Client) Moved to stage {stage}")
                                date_log_message(f"(Client) Moved to stage {stage}")
                                break 

                        elif message.lower() == 'no':
                            client_socket.send(message.encode())
                            log_message("(Client) Rejected")
                            date_log_message("(Client) Rejected")
                            response = client_socket.recv(1024).decode()
                            stage = 1
                            log_message(f"(Client) Moved to stage {stage}")
                            date_log_message(f"(Client) Moved to stage {stage}")
                            message = 'OK'
                            client_socket.send(message.encode())
                            break

                        # elif message.lower() == 'exit': #一応入れてるだけ　多分いらない
                        #     client_socket.send(message.encode())
                        #     log_message("(Client) Connection closed.")
                        #     break

                else:
                    log_message("(Client) No time found in the response")
                    date_log_message("(Client) No time found in the response")
                    stage = 1
                    log_message(f"(Client) Moved to stage {stage}")
                    date_log_message(f"(Client) Moved to stage {stage}")
                    break

            case 3: #RuleSet受け入れ
                response = client_socket.recv(1024)
                log_message(f"(Client) Got data: {response.decode()}")
                date_log_message(f"(Client) Got data: {response.decode()}")
                if response.lower() == 'error':
                    log_message("(Client) Retry from beginning.")
                    date_log_message("(Client) Retry from beginning.")
                    stage = 1
                    log_message(f"(Client) Moved to stage {stage}")
                    date_log_message(f"(Client) Moved to stage {stage}")
                    continue

                size = int(response.decode())
                log_message(f"(Client) Got data size: {size}")
                date_log_message(f"(Client) Got data size: {size}")

                try:
                    total_data = b""
                    while len(total_data) < size:
                            data = client_socket.recv(1024)
                            total_data += data

                    # 受け取ったデータをJSONとして解析
                    json_data = json.loads(total_data.decode())
                    # raise Exception("Intentional exception for debugging.") # デバッグ用エラー
                    target = extract_data_from_json(json_data, 'owner_addr')
                    log_message(f"(Client) RuleSet target is {target}")
                    date_log_message(f"(Client) RuleSet target is {target}")
                    
                    if target.lower() == '0':
                        save_json_to_file(json_data, "./client/ruleset/ruleset")
                        message = "Received RuleSet"
                        client_socket.send(message.encode())
                        log_message(f"(Client) Received RuleSet: {json_data}")
                        date_log_message(f"(Client) Received RuleSet: {json_data}")
                        stage = 4
                        log_message(f"(Client) Moved to stage {stage}")
                        date_log_message(f"(Client) Moved to stage {stage}")
                        continue
                
                except Exception as e:
                    message = "Resend RuleSet"
                    client_socket.send(message.encode())
                    log_message("(Client) Failed to received RuleSet. Please resend")
                    date_log_message("(Client) Failed to received RuleSet. Please resend")
                    continue
            
            case 4: # テレポーテーション(アプリケーション)実行部分
                #　あとで実装する
                message = input("Enter message to send to server(or 'exit' to quit): ")
                client_socket.send(message.encode())
                if message.lower() == 'exit':
                    log_message("(Client) Connection closed.")
                    date_log_message("(Client) Connection closed.")
                    break
                else:
                    log_message(f"(Client) Sent: {message}")
                    date_log_message(f"(Client) Sent: {message}")
                    response = client_socket.recv(1024).decode()
                    log_message(f"(Client) Received from Server: {response}")
                    date_log_message(f"(Client) Received from Server: {response}")

        # サーバからの応答を受け取る
        # response = client_socket.recv(1024).decode()
        # log_message(f"(Client) Received from Server: {response}")


    client_socket.close()

    # # 量子通信の例
    # circuit = QuantumCircuit(1, 1)
    # circuit.h(0)  # アダマールゲート
    # circuit.measure(0, 0)

    # # シミュレータを使用して実行
    # simulator = AerSimulator()
    # transpiled_circuit = transpile(circuit, simulator)
    # job = simulator.run(transpiled_circuit, shots=1024)  #
    # result = job.result()

    # quantum_result = result.get_counts(circuit)
    # log_message(f"(Client)Quantum result: {quantum_result}")
    

