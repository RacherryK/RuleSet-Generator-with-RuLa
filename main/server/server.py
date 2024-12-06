import socket
import json
from datetime import datetime
import time
import os
import re
import subprocess

log_file = 'log.txt'
server_log = './server/server_log.txt'

def log_message(message):
    with open(log_file, 'a') as file:  # 追記モードでファイルを開く
        file.write(message + '\n')  # メッセージを書き込む

def date_log_message(message):
    # 現在の時刻を取得（時刻のみ）
    current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    # ログメッセージに時刻を追加
    log_entry = f"{current_time} - {message}"
    
    # ログファイルに追記
    with open(server_log, 'a') as file:
        file.write(log_entry + '\n')  # メッセージを書き込む

def load_json(file_path):
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
        new_file_name = f"./server/{file_name}_{current_time}.json"
        with open(new_file_name, 'w') as file:
            json.dump(json_data, file, indent=4)  # JSONデータをインデント付きで保存
        log_message(f"(Server)JSON data saved to {new_file_name}")
        date_log_message(f"(Server)JSON data saved to {new_file_name}")
    except Exception as e:
        log_message(f"Error saving JSON data to {new_file_name}: {e}")
        date_log_message(f"Error saving JSON data to {new_file_name}: {e}")

def get_latest_file(directory):
    """
    指定されたディレクトリ内で最新の 'received_{current_time}.json' ファイルを選択する関数。
    
    :param directory: ファイルが保存されているディレクトリのパス
    :return: 最新のファイルのパス、もしファイルがなければNoneを返す
    """
    # ディレクトリ内のすべてのファイルを取得
    files = os.listdir(directory)
    
    # 'received_{current_time}.json' にマッチするファイルのみを選択
    pattern = r"received_request_(\d{8}_\d{6})\.json"  # タイムスタンプの形式にマッチする正規表現
    matching_files = []

    for file in files:
        match = re.match(pattern, file)
        if match:
            matching_files.append(file)
    
    # マッチしたファイルがない場合
    if not matching_files:
        return None
    
    def extract_timestamp(file_name):
        # ファイル名からタイムスタンプ部分を抽出し、datetimeオブジェクトに変換
        timestamp_str = re.search(r"(\d{8}_\d{6})", file_name).group(1)
        return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    
    # 最新のファイルを選択（datetimeオブジェクトを基に比較）
    latest_file = max(matching_files, key=extract_timestamp)

    #log_message(f"(Server) Latest request file is {os.path.join(directory, latest_file)}")
    return os.path.join(directory, latest_file)

def save_request(directory, file_name):
    """
    received_requestファイルからapplication_dataのみを抜き取ってリクエストに保存する関数
    :param directory: 保存するrequestファイルが保存されているディレクトリ
    :param file_name: 新しく保存するファイルパス
    """
    try:
        data = load_json(get_latest_file(directory))
        # applicatin dataを抜き取る
        application_data = data.get("Application_data", {})
        new_file_name = f"{file_name}"

        #抜き取ったapplication dataを保存
        with open(new_file_name, 'w') as file:
            json.dump(application_data, file, indent=4)  # JSONデータをインデント付きで保存
        log_message(f"(Server)JSON data saved to {new_file_name}")
        date_log_message(f"(Server)JSON data saved to {new_file_name}")
    except Exception as e:
        log_message(f"Error saving JSON data to {new_file_name}: {e}")
        date_log_message(f"Error saving JSON data to {new_file_name}: {e}")

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

def server_program(port):
    stage = 1 # 通信のステージ
    # ready = 0 # applicationスタート準備完了フラッグ

    # ソケット接続待ち
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', port))  # ソケットにローカルアドレスを紐付け。0.0.0.0は外部からの接続も受け入れる
    server_socket.listen(1)  # ソケットを接続待ちに(最大同時接続数は1)
    log_message("(Server)Waiting for connection...")
    date_log_message("(Server)Waiting for connection...")

    # 接続受け入れ
    conn, address = server_socket.accept()  # conn：データの送受信を担当
    log_message(f"(Server)Connection from Repeater: {address}\n")
    date_log_message(f"(Server)Connection from Repeater: {address}\n")

    while True:
        # 古典通信の受信
        data = conn.recv(1024).decode('utf-8')

        # exit命令を受けて接続切断
        if data.lower() == 'exit':
            log_message("(Server) Connection closed.")
            date_log_message("(Server) Connection closed.")
            break

        match stage:
            case 1: #request受け入れ
                try:
                    json_data = json.loads(data)  # 受け取ったデータをJSONとして解析
                    save_json_to_file(json_data, "received/received_request")
                    log_message(f"(Server) Received JSON data: {json_data}")
                    date_log_message(f"(Server) Received JSON data: {json_data}")

                    # 応答メッセージを送信
                    # ここでもらったJSONがRequestの形に沿っているか、判定する機能が必要
                    response = "Request data received successfully! Calculate estimated execution time..."
                    conn.send(response.encode()) 
                    log_message(f"(Server) Sent response: {response}")
                    date_log_message(f"(Server) Sent response: {response}")
                    # 推定終了時間の計算(計算式を決めうちして後で実装)
                    time.sleep(2)
                    estimated_time = 5
                    response = f"Estimated execution time (min) : {estimated_time}"
                    conn.send(response.encode())
                    log_message(f"(Server) Sent result : {response}")
                    date_log_message(f"(Server) Sent result : {response}")
                    # RuLaに接続してRuleSet生成開始(RuleSetにタグを付与) このタグは、パスセレクションの時に与える？(つまりこのシミュレーション内では、すでに与えられたタグ)
                    stage = 2
                    log_message(f"(Server) Moved to stage {stage}")
                    date_log_message(f"(Server) Moved to stage {stage}")
                    continue
        
                except json.JSONDecodeError:
                    log_message(f"(Server)Received: {data}")
                    date_log_message(f"(Server)Received: {data}")
                    #クライアントへ返答を送信
                    response = f"ACK ({data})"
                    conn.send(response.encode())
                    log_message(f"(Server) Sent response: {response}")
                    date_log_message(f"(Server) Sent response: {response}")
            
            case 2: #承認分岐
                if data.lower() == 'ok':
                    response = "Distribute RuleSets"
                    conn.send(response.encode())
                    log_message(f"(Server) Sent Response: {response}")
                    date_log_message(f"(Server) Sent Response: {response}")
                    stage = 3
                    log_message(f"(Server) Moved to stage {stage}")
                    date_log_message(f"(Server) Moved to stage {stage}")
                    continue

                elif data.lower() == 'no':
                    response = "Resend the request"
                    conn.send(response.encode())
                    log_message(f"(Server) Sent Response: {response}")
                    date_log_message(f"(Server) Sent Response: {response}")
                    stage = 1
                    log_message(f"(Server) Moved to stage {stage}")
                    date_log_message(f"(Server) Moved to stage {stage}")
                    conn.recv(1024)
                    continue

                # okかno以外来ないはずだからいらないかも↓
                else:
                    log_message(f"(Server)Received: {data}")
                    date_log_message(f"(Server)Received: {data}")
                    #クライアントへ返答を送信
                    response = f"ACK ({data})"
                    conn.send(response.encode())
                    log_message(f"(Server) Sent response: {response}")
                    date_log_message(f"(Server) Sent response: {response}")
                    continue

            case 3: #RuleSet配布
                #Clientに配布
                #生成したRuleSetは配る用のディレクトリに入れて、その中に入ってるRuleSetを一つずつ配布
                #ACKにタイマーをセットして、一定時間ACKが帰ってこなければ再送する(あとで実装)

                #RuLaに投げて、RuleSet作る
                save_request("./server/received", "../rula/modified-rula/src/request.json")
                log_message("(Server) success save request to RuLa")
                date_log_message("(Server) success save request to RuLa")
                subprocess.run(["bash", "./script.sh"], capture_output=True, text=True)

                #できたRuleSetのowner_addrを見て自分に保存or配布
                node = 3
                skip = False
                for i in range(node):
                    count_try = 0 #resendを最大5回にするため
                    while True:
                        ruleset = load_json(f"./server/for_distribute/node{i}.json")
                        if ruleset is not None:
                            target = extract_data_from_json(ruleset, 'owner_addr')
                            log_message(f"(Server) Target is node{target}")
                            date_log_message(f"(Server) Target is node{target}")
                            if target == '2':
                                save_json_to_file(ruleset, "ruleset/ruleset")
                                log_message(f"(Server) Received RuleSet: {json_data}")
                                date_log_message(f"(Server) Received RuleSet: {json_data}")
                                break
                            else:
                                size = os.path.getsize(f"./server/for_distribute/node{i}.json")
                                string_size = str(size)
                                conn.send(string_size.encode())
                                log_message(f"(Server) The size of node{i} RuleSet is {size}")
                                date_log_message(f"(Server) The size of node{i} RuleSet is {size}")
                                ruleset_bytes = json.dumps(ruleset).encode('utf-8')
                                conn.sendall(ruleset_bytes)
                                log_message(f"(Server) Sent RuleSet for node{i}: {ruleset}")
                                date_log_message(f"(Server) Sent RuleSet for node{i}: {ruleset}")
                        # RuleSetが読み込めなかった時の処理書く　load_json をtry文にしたほうがいいかも？
                    
                        data = conn.recv(1024).decode('utf-8') #受け取ったかどうかの返事待ち
                        log_message(f"(Server)Received: {data}")
                        date_log_message(f"(Server)Received: {data}")
                        if data.lower() == 'received ruleset':
                            break

                        elif data.lower() == 'resend ruleset':
                            log_message("(Server) Resend RuleSet")
                            date_log_message("(Server) Resend RuleSet")
                            count_try += 1
                            if count_try >= 5:
                                log_message("(Server) Error occurred. Retry from beginning")
                                date_log_message("(Server) Error occurred. Retry from beginning")
                                response = "Error"
                                conn.send(response.encode())
                                break 
                    
                    if count_try >= 5:
                        skip = True
                        stage = 1
                        log_message(f"(Server) Moved to stage {stage}")
                        date_log_message(f"(Server) Moved to stage {stage}")
                        break
                
                if skip:
                    continue

                log_message("(Server) Finish to send RuleSets")
                date_log_message("(Server) Finish to send RuleSets")
                stage = 4
                log_message(f"(Server) Moved to stage {stage}")
                date_log_message(f"(Server) Moved to stage {stage}")

            case 4: #テレポーテーション(アプリケーション)実行部分 
                log_message(f"(Server)Received: {data}")
                date_log_message(f"(Server)Received: {data}")
                #クライアントへ返答を送信
                response = f"ACK ({data})"
                conn.send(response.encode())
                log_message(f"(Server) Sent response: {response}")
                date_log_message(f"(Server) Sent response: {response}")

        # try:
        #     json_data = json.loads(data)  # 受け取ったデータをJSONとして解析
        #     save_json_to_file(json_data, "received_request.json")
        #     log_message(f"(Server) Received JSON data: {json_data}")

        #     # 応答メッセージを送信
        #     response = "Request data received successfully! Calculate estimated execution time..."
        #     conn.send(response.encode()) 
        #     log_message(f"(Server) Sent response: {response}")
        #     # 推定終了時間の計算(計算式を決めうちして後で実装)
        #     estimated_time = 5
        #     response = f"Estimated execution time (min) : {estimated_time}"
        #     conn.send(response.encode())
        #     log_message(f"(Server) Sent result : {response}")
        #     # RuLaに接続してRuleSet生成開始(RuleSetにtarget_ip & target_portを付与)
        #     wait = 1
        #     continue
        
        # except json.JSONDecodeError:
        #     log_message(f"(Server)Received: {data}")
        #     #クライアントへ返答を送信
        #     response = "OK"
        #     conn.send(response.encode())
        #     log_message(f"(Server) Sent response: {response}")
    

    conn.close()
    server_socket.close()
