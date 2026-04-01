from flask import Flask, request, jsonify
import queue
import threading

app = Flask(__name__)

BOARD_SIZE = 100
WIN_LENGTH = 5
move_queue = queue.Queue(maxsize=50)
board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
game_over = False
winner = None

def check_winner(r, c, symbol):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        for i in range(1, WIN_LENGTH):
            nr, nc = r + dr * i, c + dc * i
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == symbol:
                count += 1
            else: break
        for i in range(1, WIN_LENGTH):
            nr, nc = r - dr * i, c - dc * i
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == symbol:
                count += 1
            else: break
        if count >= WIN_LENGTH:
            return True
    return False

def worker():
    global game_over, winner
    while True:
        move = move_queue.get()
        if move is None: break

        r, c, symbol = move['r'], move['c'], move['symbol']

        if not game_over and board[r][c] == " ":
            board[r][c] = symbol
            print(f"Поставлено {symbol} на [{r},{c}]")
            if check_winner(r, c, symbol):
                game_over = True
                winner = symbol
                print(f"Гру закінчено! Переміг {symbol}")

        move_queue.task_done()

threading.Thread(target=worker, daemon=True).start()

@app.route('/move', methods=['POST'])
def handle_move():
    if game_over:
        return jsonify({"status": "error", "message": f"Game over. Winner: {winner}"}), 400

    data = request.json
    try:
        move_queue.put_nowait({
            'r': data['r'],
            'c': data['c'],
            'symbol': data['symbol'].upper()
        })
        return jsonify({"status": "queued", "message": "Move accepted into queue"}), 202
    except queue.Full:
        return jsonify({"status": "error", "message": "Queue is full (50 requests limit)"}), 503

@app.route('/board', methods=['GET'])
def get_board():
    return jsonify({"board": board, "winner": winner})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)