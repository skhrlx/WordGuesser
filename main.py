import random
from flask import Flask, jsonify, request
import threading
import time

app = Flask(__name__)

class WordGuessGame:
    def __init__(self, filename):
        self.word_list = self.load_word_list(filename)
        self.score = 0
        self.max_score = 0
        self.hp = 10
        self.correct_streak = 0
        self.total_rounds = 0
        self.current_word = None
        self.scrambled_word = None
        self.word_set_time = None
        self.half_word = None
        self.choose_new_word()

    def load_word_list(self, filename):
        try:
            with open(filename, 'r') as file:
                words = file.read().splitlines()
            return words
        except FileNotFoundError:
            print(f"Error: The file {filename} was not found.")
            return []

    def scramble_word(self, word):
        word_list = list(word)
        random.shuffle(word_list)
        return ''.join(word_list)

    def manage_hp(self, amount):
        self.hp += amount
        if self.hp <= 0:
            self.hp = 0
            print("You've run out of HP! Your score has been reset to 0.")
            if self.score > self.max_score:
                self.max_score = self.score
            self.score = 0
            return False
        return True

    def verify_word(self, guess):
        if guess == self.current_word:
            print("Correct!")
            if self.score > self.max_score:
                self.max_score = self.score
            self.score += 1
            self.correct_streak += 1
            if self.correct_streak == 5:
                print("You answered 5 words correctly in a row! +1 HP!")
                self.manage_hp(1)
                self.correct_streak = 0
            self.choose_new_word()
            return True
        else:
            print(f"Wrong! The correct word was: {self.current_word}")
            self.correct_streak = 0
            return False

    def restart_game(self):
        if self.score > self.max_score:
            self.max_score = self.score
        print(f"Game Over! Final Score: {self.score}")
        print("Restarting the game...\n")
        self.score = 0
        self.hp = 10
        self.correct_streak = 0

    def choose_new_word(self):
        word = random.choice(self.word_list)
        scrambled = self.scramble_word(word)

        self.current_word = word
        self.scrambled_word = scrambled
        self.word_set_time = time.time()

    def get_game_state(self):
        return {
            "score": self.score,
            "max_score": self.max_score,
            "hp": self.hp,
            "correct_streak": self.correct_streak,
            "total_rounds": self.total_rounds,
            "current_word": self.current_word,
            "half_world": self.half_word,
            "scrambled_word": self.scrambled_word
        }

    def check_word_timeout(self):
        if self.word_set_time and time.time() - self.word_set_time > 600:
            self.choose_new_word()

    def get_remaining_time(self):
        if self.word_set_time:
            elapsed_time = time.time() - self.word_set_time
            remaining_time = 600 - elapsed_time
            if remaining_time < 0:
                return "00:00"
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            return f"{minutes:02}:{seconds:02}"
        return "10:00"

    def get_tip(self):
        if self.word_set_time:
            elapsed_time = time.time() - self.word_set_time
            remaining_time = 600 - elapsed_time
            
            if remaining_time <= 300:
                self.half_word = self.current_word[:len(self.current_word)//2]
                return self.half_word
        return None

game = WordGuessGame("words.txt")

@app.route('/game_state', methods=['GET'])
def game_state():
    game.check_word_timeout()
    game_state = game.get_game_state()
    game_state["remaining_time"] = game.get_remaining_time()
    
    game_state["half_world"] = game.get_tip()

    return jsonify(game_state)

@app.route('/verify_word', methods=['GET', 'POST'])
def verify_word():
    if request.method == 'POST':
        data = request.get_json()
        guess = data.get('guess')
    elif request.method == 'GET':
        guess = request.args.get('guess')

    if not guess:
        return jsonify({"error": "No guess provided"}), 400

    if game.current_word is None:
        return jsonify({"error": "No word to guess. Start a game first."}), 400

    if game.verify_word(guess.lower()):
        return jsonify({"message": "Correct!", "next_word": game.scrambled_word}), 200
    else:
        return jsonify({"message": "Wrong!", "correct_word": game.current_word}), 300

def start_flask():
    app.run(debug=True, use_reloader=False, threaded=True)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()
    flask_thread.join()
