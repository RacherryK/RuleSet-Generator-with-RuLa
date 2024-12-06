import threading
from datetime import datetime
from client.client import client_program
from server.server import server_program
from repeater.repeater import relay_program

log_file = 'log.txt'

def log_message(message):
    with open(log_file, 'a') as file:  # 追記モードでファイルを開く
        file.write(message + '\n')  # メッセージを書き込む

def run_all():
    # サーバプログラムをポート5001で待機
    server_thread = threading.Thread(target=server_program, args=(5001,))
    server_thread.start()

    # 中継器プログラムをポート6001で待機
    relay_thread = threading.Thread(target=relay_program, args=(6001, '127.0.0.1', 5001))
    relay_thread.start()

    # クライアントプログラムを実行
    client_program('127.0.0.1', 6001)

    # サーバと中継器が終了するのを待つ
    server_thread.join()
    # relay_thread.join()

if __name__ == '__main__':
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # ログメッセージに日時を追加
    log_message(f"\n time: {current_time}")
    run_all()
