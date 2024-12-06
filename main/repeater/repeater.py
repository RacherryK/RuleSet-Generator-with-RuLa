import socket
import json
from datetime import datetime
import os

log_file = 'log.txt'
repeater_log = './repeater/repeater_log.txt'

def log_message(message):
    with open(log_file, 'a') as file:  # 追記モードでファイルを開く
        file.write(message + '\n')  # メッセージを書き込む

def date_log_message(message):
    # 現在の時刻を取得（時刻のみ）
    current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    # ログメッセージに時刻を追加
    log_entry = f"{current_time} - {message}"
    
    # ログファイルに追記
    with open(repeater_log, 'a') as file:
        file.write(log_entry + '\n')  # メッセージを書き込む

def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)  # JSONファイルを辞書として読み込む
        return json_data
    except Exception as e:
        return Exception

def merge_json(data1, data2, output_file):

    # 統合するための辞書を作成
    merged_data = {
        "Application_data": data1,
        "Repeater_data": data2
    }
    
    # 結果を新しいJSONファイルに書き込む
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_file_name = f"./path/{output_file}_{current_time}.json"
    with open(new_file_name, 'w', encoding='utf-8') as out:
        json.dump(merged_data, out, ensure_ascii=False, indent=4)
    return merged_data

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
        log_message(f"(Repeater)JSON data saved to {new_file_name}")
        date_log_message(f"(Repeater)JSON data saved to {new_file_name}")
    except Exception as e:
        log_message(f"Error saving JSON data to {new_file_name}: {e}")
        date_log_message(f"Error saving JSON data to {new_file_name}: {e}")

def transfer_message_from_server(n_from, n_to):
    """
    サーバからのメッセージを受信し、クライアントに転送する関数
    :param n_from: 送信者とのソケット接続
    :param n_to: 受信者とのソケット接続
    """
    try:
        # サーバからのレスポンスを受け取る
        response = n_from.recv(1024).decode()
        log_message(f"(Repeater) Received response from server: {response}")
        date_log_message(f"(Repeater) Received response from server: {response}")
            
        # クライアントへレスポンスを転送
        n_to.send(response.encode())
        log_message(f"(Repeater) Sent response to client: {response}")
        date_log_message(f"(Repeater) Sent response to client: {response}")
    except Exception as e:
        log_message(f"(Repeater) Error during message transfer: {e}")
        date_log_message(f"(Repeater) Error during message transfer: {e}")

def transfer_message_from_client(n_from, n_to, exit_flag):
    """
    クライアントからのメッセージを受信し、サーバに転送する関数
    :param n_from: 送信者とのソケット接続
    :param n_to: 受信者とのソケット接続
    """
    try:
        # クライアントからのレスポンスを受け取る
        response = n_from.recv(1024).decode()
        log_message(f"(Repeater) Received response from client: {response}")
        date_log_message(f"(Repeater) Received response from client: {response}")
        if response.lower() == 'exit':
            n_to.send(response.encode())
            log_message("(Repeater) Connection closed.")
            date_log_message("(Repeater) Connection closed.")
            exit_flag[0] = True
            return 

        # サーバへレスポンスを転送
        n_to.send(response.encode())
        log_message(f"(Repeater) Sent response to server: {response}")
        date_log_message(f"(Repeater) Sent response to server: {response}")
    except Exception as e:
        log_message(f"(Repeater) Error during message transfer: {e}")
        date_log_message(f"(Repeater) Error during message transfer: {e}")

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
    
def get_file_size(file_path):
    try:
        # ファイルの情報を取得
        file_info = os.stat(file_path)
        # ファイルサイズをバイト単位で取得
        return file_info.st_size
    except FileNotFoundError:
        print(f"Error: The file at '{file_path}' does not exist.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def relay_program(port, next_server_ip, next_server_port):
    stage = 1 # 通信のステージ
    exit_flag = [False] # exitを受け入れるためのフラグ
    #前後のノードとの接続確認

    #C側ノードからの接続待ち
    relay_socket = socket.socket()
    relay_socket.bind(('0.0.0.0', port))
    relay_socket.listen(1)
    log_message("(Repeater)Relay waiting for connection from client...")
    date_log_message("(Repeater)Relay waiting for connection from client...")

    #S側ノードへの接続要求
    next_server_socket = socket.socket()
    next_server_socket.connect((next_server_ip, next_server_port))

    #C側ノードからの接続受け入れ
    conn, address = relay_socket.accept()
    log_message(f"(Repeater)Relay connected to Client: {address}\n")
    date_log_message(f"(Repeater)Relay connected to Client: {address}\n")

    while True:
        match stage:
            case 1: #request受けて、自身の情報と共に送信
                # 古典通信の受信
                data = conn.recv(1024)

                # exit命令を受けて、サーバへ接続切断要求し自身の接続も切断
                if data.decode().lower() == 'exit':
                    next_server_socket.send(data)
                    log_message("(Repeater) Connection closed.")
                    date_log_message("(Repeater) Connection closed.")
                    break

                try: # JSONデータを受け取った場合
                    client_data = json.loads(data.decode('utf-8'))
                    log_message(f"(Repeater) Received JSON data: {client_data}")
                    date_log_message(f"(Repeater) Received JSON data: {client_data}")

                    # 自分自身が持っているJSONデータとマージ
                    my_data = load_json('./repeater/repeater_information.json')
                    json_data = merge_json(client_data, my_data, 'path_information.json')

                    #S側へマージしたデータを送信
                    json_bytes = json.dumps(json_data).encode('utf-8')
                    next_server_socket.send(json_bytes)
                    log_message(f"(Repeater) Sent JSON to server: {json_data}")
                    date_log_message(f"(Repeater) Sent JSON to server: {json_data}")
                    stage = 2
                    log_message(f"(Repeater) Moved to stage {stage}")
                    date_log_message(f"(Repeater) Moved to stage {stage}")

                except json.JSONDecodeError:
                    log_message(f"(Repeater) Recieved message from client: {data.decode()}")
                    date_log_message(f"(Repeater) Recieved message from client: {data.decode()}")
                    # S側ノードへデータを送信
                    next_server_socket.send(data)
                    log_message(f"(Repeater) Sent to server: {data.decode()}")
                    date_log_message(f"(Repeater) Sent to server: {data.decode()}")

                # 単に転送する部分は関数化したほうが見やすいかも
                transfer_message_from_server(next_server_socket, conn)
                # # S側ノードからの応答受信
                # response = next_server_socket.recv(1024).decode()
                # log_message(f"(Repeater) Received response from server: {response}")

                # # C側ノードへ転送
                # conn.send(response.encode())
                # log_message(f"(Repeater) Sent response to client: {response}")
            
            case 2: # estimation time転送＆承認メッセージ転送
                transfer_message_from_server(next_server_socket, conn) #estimated time 送信
                transfer_message_from_client(conn, next_server_socket, exit_flag) # ok or no

                # S側ノードからの応答受信 (RuleSet配るのかどうか)
                response = next_server_socket.recv(1024).decode()
                log_message(f"(Repeater) Received response from server: {response}")
                date_log_message(f"(Repeater) Received response from server: {response}")
                if response.lower() == 'distribute rulesets':
                    stage = 3
                    log_message(f"(Repeater) Moved to stage {stage}")
                    date_log_message(f"(Repeater) Moved to stage {stage}")
                    
                elif response.lower() == 'resend the request':
                    stage = 1
                    log_message(f"(Repeater) Moved to stage {stage}")
                    date_log_message(f"(Repeater) Moved to stage {stage}")

                # C側ノードへ転送
                conn.send(response.encode())
                log_message(f"(Repeater) Sent response to client: {response}")
                date_log_message(f"(Repeater) Sent response to client: {response}")

                transfer_message_from_client(conn, next_server_socket, exit_flag)
            
            case 3: #RuleSet受け取り
                #どうやってjsonの行き先を判別するか？→RuleSetに書いてあるtargetを抜き出して、client/repeaterを判別
                #どうやって配り終わりを判別?→自分がサーバから何番目のノードかを知っていれば、自分が転送すべきRSの数がわかる
                node = 2 #このノード数は最初に取得する
                skip = False # ループを抜けるためのフラッグ
                for i in range(node):
                    count_try = 0 #resendを最大5回にするため
                    while True:
                        data = next_server_socket.recv(1024)
                        log_message(f"(Repeater) Got response: {data.decode()}")
                        date_log_message(f"(Repeater) Got response: {data.decode()}")

                        if data.decode().lower() == 'error':
                            log_message("(Repeater) Retry from beginning.")
                            date_log_message("(Repeater) Retry from beginning.")
                            conn.send(data)
                            skip = True
                            break

                        size = int(data.decode())
                        log_message(f"(Repeater) Got data size: {size}")
                        date_log_message(f"(Repeater) Got data size: {size}")

                        try:
                            total_data = b""
                            while len(total_data) < size:
                                data = next_server_socket.recv(1024)
                                total_data += data

                            ruleset = json.loads(total_data.decode())
                            log_message(f"(Repeater) Received JSON data: {ruleset}")
                            date_log_message(f"(Repeater) Received JSON data: {ruleset}")
                            target = extract_data_from_json(ruleset, 'owner_addr')
                            log_message(f"(Repeater) RuleSet target is {target}")
                            date_log_message(f"(Repeater) RuleSet target is {target}")

                            if target.lower() == '1':
                                save_json_to_file(ruleset, "./repeater/ruleset/ruleset")
                                data = "Received RuleSet"
                                next_server_socket.send(data.encode())
                                log_message(f"(Repeater) Received RuleSet: {ruleset}")
                                date_log_message(f"(Repeater) Received RuleSet: {ruleset}")
                                break

                            elif target.lower() == '0':
                                log_message("(Repeater) Transfer RuleSet to Client")
                                date_log_message("(Repeater) Transfer RuleSet to Client")
                                string_size = str(size)
                                conn.send(string_size.encode())
                                log_message(f"(Repeater) The size of node{target} RuleSet is {size}")
                                date_log_message(f"(Repeater) The size of node{target} RuleSet is {size}")
                                conn.sendall(total_data)
                                log_message("(Repeater) Finish transferring RuleSet to Client")
                                date_log_message("(Repeater) Finish transferring RuleSet to Client")
                                message = conn.recv(1024).decode() #clientが受け取ったかの返事待ち
                                if message.lower() == 'received ruleset':
                                    next_server_socket.send(message.encode())
                                    break
                                else:
                                    next_server_socket.send(message.encode())

                        except json.JSONDecodeError:
                            count_try += 1
                            if count_try >= 5:
                                skip = True
                                log_message("(Repeater) Error occured. Retry from beginning.")
                                date_log_message("(Repeater) Error occured. Retry from beginning.")
                                break
                            message = "Resend RuleSet"
                            next_server_socket.send(message.encode())
                            log_message("(Repeater) Failed to received RuleSet. Please resend")
                            date_log_message("(Repeater) Failed to received RuleSet. Please resend")
                            continue

                        except Exception as e:
                            continue
                    
                    if skip:
                        break
                
                if skip:
                    stage = 1
                    log_message(f"(Repeater) Moved to stage {stage}")
                    date_log_message(f"(Repeater) Moved to stage {stage}")
                    continue
                    
                
                log_message("(Repeater) Finish to transport RuleSets")
                date_log_message("(Repeater) Finish to transport RuleSets")
                stage = 4
                log_message(f"(Repeater) Moved to stage {stage}")
                date_log_message(f"(Repeater) Moved to stage {stage}")
            
            case 4: #テレポーテーション(リピータはメッセージのやり取りするだけ)
                transfer_message_from_client(conn, next_server_socket, exit_flag)
                if exit_flag[0]:
                    break
                transfer_message_from_server(next_server_socket, conn)
                



    relay_socket.close()
    next_server_socket.close()
    conn.close()
