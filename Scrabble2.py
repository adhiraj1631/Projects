import string
import pyttsx3
import enchant
import tkinter as tk
from tkinter import messagebox, simpledialog, font
import random
import time
import threading

BOARD_SIZE = 15
CENTER_SQUARE = (7, 7)

CELL_COLORS = {
    'normal': 'white',
    'center': 'lightblue',
    'placed_player': 'yellow',
    'placed_ai': 'lightgreen',
    'selected': 'cyan'
}


class ScrabbleGame:
    def __init__(self):
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()

        # Configure voice settings - try to find a female voice if available
        voices = self.engine.getProperty('voices')
        selected_voice_id = None
        for voice in voices:
            if any(keyword in voice.name.lower() for keyword in
                   ['female', 'zira', 'david', 'mark', 'helen', 'samantha']):
                selected_voice_id = voice.id
                break
        if selected_voice_id:
            self.engine.setProperty('voice', selected_voice_id)

        # Set speech rate
        self.engine.setProperty('rate', 170)

        # Initialize speech thread
        self.speech_thread = threading.Thread(target=self.engine.runAndWait)
        self.speech_thread.daemon = True
        self.speech_thread.start()

        # Initialize dictionary
        try:
            self.dictionary = enchant.Dict("en_US")
        except enchant.errors.DictNotFoundError:
            messagebox.showerror("Dictionary Error", "US English dictionary not found.")
            self.dictionary = None

        # Initialize game board
        self.board = [['' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        # Initialize letter data and tile bag
        self.load_letter_data()
        self.tile_bag = self.initialize_tile_bag()

        # Initialize player data
        self.player_name = ""
        self.player_score = 0
        self.ai_score = 0
        self.player_reached_50 = False  # Flag to track if player has reached 50 points
        self.ai_reached_50 = False  # Flag to track if AI has reached 50 points

        # Initialize racks
        self.player_rack = []
        self.ai_rack = []
        self.first_move = True
        self.game_over = False
        self.current_turn = "player"

        # Initialize placement state
        self.placement_state = 'idle'
        self.current_word_to_place = ""
        self.current_start_row = None
        self.current_start_col = None
        self._original_cell_color = None

        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("Accessible Scrabble")
        self.root.geometry('1000x800')
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)

        self.setup_gui()

    def speak(self, text):
        """Function to make the AI speak text"""
        if text:
            self.engine.say(text)
            # This is non-blocking since engine.runAndWait() is in a separate thread

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        is_fullscreen = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not is_fullscreen)

    def load_letter_data(self):
        """Load letter distribution and point values"""
        self.letter_distribution_initial = {
            'A': 9, 'B': 2, 'C': 2, 'D': 4, 'E': 12, 'F': 2, 'G': 3, 'H': 2,
            'I': 9, 'J': 1, 'K': 1, 'L': 4, 'M': 2, 'N': 6, 'O': 8, 'P': 2,
            'Q': 1, 'R': 6, 'S': 4, 'T': 6, 'U': 4, 'V': 2, 'W': 2, 'X': 1,
            'Y': 2, 'Z': 1, '*': 2
        }
        self.letter_points = {
            'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
            'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3,
            'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8,
            'Y': 4, 'Z': 10, '*': 0
        }
        self.letter_distribution = self.letter_distribution_initial.copy()

    def initialize_tile_bag(self):
        """Create and shuffle the tile bag"""
        bag = []
        for letter, count in self.letter_distribution.items():
            bag.extend([letter] * count)
        random.shuffle(bag)
        return bag

    def draw_tiles(self, count):
        """Draw tiles from the bag"""
        drawn_tiles = []
        for _ in range(count):
            if self.tile_bag:
                tile = self.tile_bag.pop()
                drawn_tiles.append(tile)
            else:
                break
        return drawn_tiles

    def setup_gui(self):
        """Set up the game GUI"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        main_frame = tk.Frame(self.root, bg='lightgray')
        main_frame.grid(sticky='nsew', padx=10, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        title_label = tk.Label(main_frame, text="Accessible Scrabble",
                               font=('Arial', 28, 'bold'), bg='lightgray')
        title_label.grid(row=0, column=0, pady=(0, 10), sticky='n')

        game_frame = tk.Frame(main_frame, bg='white')
        game_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        game_frame.grid_rowconfigure(0, weight=1)
        game_frame.grid_columnconfigure(0, weight=1)

        board_frame = tk.Frame(game_frame, bg='white')
        board_frame.grid(row=0, column=0, sticky='nsew')

        for i in range(BOARD_SIZE):
            board_frame.grid_rowconfigure(i, weight=1)
            board_frame.grid_columnconfigure(i, weight=1)

        self.board_buttons = []
        board_font = font.Font(family='Arial', size=10, weight='bold')

        for row in range(BOARD_SIZE):
            row_buttons = []
            for col in range(BOARD_SIZE):
                bg_color = CELL_COLORS['normal']
                if (row, col) == CENTER_SQUARE:
                    bg_color = CELL_COLORS['center']

                btn = tk.Button(board_frame, text='',
                                command=lambda r=row, c=col: self.cell_clicked(r, c),
                                bg=bg_color, relief=tk.RAISED, borderwidth=1,
                                font=board_font, width=2, height=1)
                btn.grid(row=row, column=col, sticky='nsew', padx=0, pady=0)
                row_buttons.append(btn)
            self.board_buttons.append(row_buttons)

        control_frame = tk.Frame(game_frame, bg='lightgray')
        control_frame.grid(row=1, column=0, sticky='ew', pady=10, padx=10)
        control_frame.grid_columnconfigure((0, 1, 2), weight=1)

        rack_label = tk.Label(control_frame, text="Your Rack:", bg='lightgray', font=('Arial', 12, 'bold'))
        rack_label.grid(row=0, column=0, columnspan=3, pady=(5, 0), sticky='w')

        rack_frame = tk.Frame(control_frame, bg='white', relief=tk.SUNKEN, borderwidth=2)
        rack_frame.grid(row=1, column=0, columnspan=3, sticky='ew', padx=10, pady=(0, 5))
        rack_frame.grid_columnconfigure(list(range(7)), weight=1)

        self.rack_buttons = []
        rack_font = font.Font(family='Arial', size=14, weight='bold')
        for i in range(7):
            btn = tk.Button(rack_frame, text=' ', bg='lightyellow', font=rack_font,
                            width=3, height=1, relief=tk.RAISED)
            btn.grid(row=0, column=i, padx=2, pady=2, sticky='nsew')
            self.rack_buttons.append(btn)

        action_frame = tk.Frame(control_frame, bg='lightgray')
        action_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(5, 0))
        action_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        tk.Label(action_frame, text="Word:", bg='lightgray', font=('Arial', 12)).grid(row=0, column=0, sticky='w',
                                                                                      padx=(10, 5))
        self.word_entry = tk.Entry(action_frame, width=25, font=('Arial', 14))
        self.word_entry.grid(row=0, column=1, sticky='ew', padx=5)

        tk.Button(action_frame, text="Prepare Placement", command=self.prepare_word_placement,
                  font=('Arial', 10, 'bold')).grid(row=0, column=2, padx=5)
        tk.Button(action_frame, text="Get Hint", command=self.get_hint, font=('Arial', 10)).grid(row=0, column=3,
                                                                                                 padx=5)

        info_frame = tk.Frame(control_frame, bg='lightgray')
        info_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=(5, 0))
        info_frame.grid_columnconfigure(0, weight=1)

        self.status_label = tk.Label(info_frame, text="Enter word and click 'Prepare Placement', then click board cell",
                                     bg='lightgray', font=('Arial', 10))
        self.status_label.grid(row=0, column=0, sticky='w')

        self.score_label = tk.Label(info_frame, text=f"Player Score: {self.player_score} | AI Score: {self.ai_score}",
                                    bg='lightgray', font=('Arial', 12, 'bold'))
        self.score_label.grid(row=1, column=0, sticky='w', pady=(5, 0))

        game_control_frame = tk.Frame(control_frame, bg='lightgray')
        game_control_frame.grid(row=4, column=0, columnspan=3, sticky='ew', pady=(5, 0))
        game_control_frame.grid_columnconfigure((0, 1), weight=1)

        # Add Quit button with prominent styling
        quit_button = tk.Button(game_control_frame, text="Quit Game", command=self.quit_game,
                                font=('Arial', 12, 'bold'), bg='#ff6b6b', fg='white',
                                padx=15, pady=5)
        quit_button.grid(row=0, column=1, sticky='e', padx=10, pady=5)

    def quit_game(self):
        """Handle game quit functionality"""
        self.game_over = True

        if self.player_score > self.ai_score:
            winner_message = f"Congratulations, {self.player_name}! You win!"
        elif self.ai_score > self.player_score:
            winner_message = "The AI wins! Better luck next time, human."
        else:
            winner_message = "It's a tie!"

        self.speak(winner_message)

        final_score_message = f"Final Scores:\n{self.player_name}: {self.player_score}\nAI: {self.ai_score}"
        self.speak(final_score_message)

        time.sleep(2)

        messagebox.showinfo("Game Over", f"{winner_message}\n\n{final_score_message}")

        self.root.destroy()

    def get_player_name(self):
        """Get the player's name"""
        name = simpledialog.askstring("Player Name", "Enter your name:", initialvalue="Player")

        if name:
            self.player_name = name.strip()
        else:
            self.player_name = "Player"

        # Welcome player with AI voice
        welcome_message = f"Hello, {self.player_name}! Welcome to Accessible Scrabble! I'll be your AI assistant throughout the game."
        self.speak(welcome_message)

    def get_hint(self):
        """Provide a hint to the player"""
        if self.current_turn != "player":
            self.speak("It's not your turn right now.")
            messagebox.showwarning("Not Your Turn", "It's not your turn to get a hint.")
            return

        hints = [
            "Try to use high-scoring letters like Q, Z, or X.",
            "Look for opportunities to connect to existing words on the board.",
            "Remember, longer words often score more points!",
            "Use the special squares like double or triple letter/word scores.",
            "Check if you can form multiple words in one turn by connecting letters in two directions.",
            "Don't be afraid to exchange tiles if you have a bad rack.",
            f"You have {len(self.tile_bag)} tiles left in the bag."
        ]
        hint = random.choice(hints)

        self.speak(f"Here's a hint: {hint}")
        messagebox.showinfo("Game Hint", hint)

    def ai_move(self):
        """Handle AI's turn"""
        if self.game_over or self.current_turn != "ai":
            return

        self.speak("It's my turn now. I'm thinking about my move.")

        possible_words = ["CAT", "DOG", "PLAY", "GAME", "WORD", "HOUSE", "CAR", "BOOK", "FUN", "SCRABBLE", "TILE",
                          "BOARD", "SCORE", "HINT"]
        random.shuffle(possible_words)

        placed_word = None
        placed_row = -1
        placed_col = -1
        placed_direction = ''
        ai_word_score = 0

        potential_starts = []
        if self.first_move:
            potential_starts = [(CENTER_SQUARE[0], CENTER_SQUARE[1])]
        else:
            occupied_cells = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.board[r][c] != '']
            for er, ec in occupied_cells:
                potential_starts.append((er, ec))
                if er > 0 and self.board[er - 1][ec] == '': potential_starts.append((er - 1, ec))
                if er < BOARD_SIZE - 1 and self.board[er + 1][ec] == '': potential_starts.append((er + 1, ec))
                if ec > 0 and self.board[er][ec - 1] == '': potential_starts.append((er, ec - 1))
                if ec < BOARD_SIZE - 1 and self.board[er][ec + 1] == '': potential_starts.append((er, ec + 1))

            potential_starts = list(set(potential_starts))
            random.shuffle(potential_starts)

        for word in possible_words:
            for start_row, start_col in potential_starts:
                if self.is_valid_placement(word, start_row, start_col, 'H', is_player=False):
                    placed_word = word
                    placed_row = start_row
                    placed_col = start_col
                    placed_direction = 'H'
                    break
                if self.is_valid_placement(word, start_row, start_col, 'V', is_player=False):
                    placed_word = word
                    placed_row = start_row
                    placed_col = start_col
                    placed_direction = 'V'
                    break
            if placed_word:
                break

        if placed_word:
            self.update_board_with_word(placed_word, placed_row, placed_col, placed_direction, is_player=False)

            ai_word_score = sum(self.letter_points.get(letter, 0) for letter in placed_word)
            self.ai_score += ai_word_score

            # Check if AI has reached 50 points milestone
            if not self.ai_reached_50 and self.ai_score >= 50:
                self.ai_reached_50 = True
                self.root.after(1000, lambda: self.speak(
                    f"I've reached 50 points! I'm doing well, but the game is still on!"))

            self.score_label.config(text=f"{self.player_name} Score: {self.player_score} | AI Score: {self.ai_score}")

            self.root.after(500, lambda: self.speak(f"I placed the word {placed_word} for {ai_word_score} points."))
            self.root.after(1500, lambda: self.speak(f"My score is now {self.ai_score}."))

            self.first_move = False

        else:
            self.root.after(1000, lambda: self.speak("Hmm, I couldn't find a good word this turn."))

        self.current_turn = "player"
        self.status_label.config(text="Your turn. Enter word and click 'Prepare Placement'")
        self.speak("It's your turn now.")

    def prepare_word_placement(self):
        """Prepare to place a word on the board"""
        if self.current_turn != "player":
            self.speak("It's not your turn right now.")
            messagebox.showwarning("Not Your Turn", "It's not your turn.")
            return

        word = self.word_entry.get().strip().upper()

        if not word:
            self.speak("Please enter a word to play.")
            messagebox.showerror("Invalid Input", "Please enter a word")
            return

        if not all(c in string.ascii_uppercase + '*' for c in word):
            self.speak("Words can only contain letters A to Z.")
            messagebox.showerror("Invalid Characters", "Words can only contain letters A-Z or a blank tile (*).")
            return

        if self.dictionary:
            word_for_dict_check = word.replace('*', 'A').lower()
            if not self.dictionary.check(word_for_dict_check):
                self.speak("Oops! That word is not in the dictionary.")
                messagebox.showerror("Invalid Word", f"'{word}' is not in the dictionary")
                return

        self.current_word_to_place = word
        self.placement_state = 'selecting_start'
        self.status_label.config(text=f"Click the board cell where '{word}' should start.")
        self.speak(f"Okay, you want to play '{word}'. Now click on the board where the word should start.")

    def cell_clicked(self, row, col):
        """Handle board cell click"""
        if self.current_turn != "player":
            self.speak("It's not your turn.")
            return

        if self.placement_state == 'selecting_start':
            if self.board[row][col] != '':
                first_letter_needed = self.current_word_to_place[0]
                existing_letter = self.board[row][col].upper()

                if existing_letter != first_letter_needed and first_letter_needed != '*':
                    self.speak(
                        f"The first letter of your word, '{first_letter_needed}', does not match the letter already on the board at row {row + 1}, column {col + 1}, which is '{existing_letter}'. Please choose a different starting cell or word.")
                    messagebox.showwarning("Placement Error",
                                           f"The first letter of your word ('{first_letter_needed}') must match the letter on the board at ({row + 1},{col + 1}) if the cell is occupied.")
                    self.reset_placement_state()
                    return

            self.current_start_row = row
            self.current_start_col = col
            self.placement_state = 'awaiting_direction'

            self._original_cell_color = self.board_buttons[row][col].cget('bg')
            self.board_buttons[row][col].config(bg=CELL_COLORS['selected'])

            self.status_label.config(
                text=f"Starting at ({row + 1},{col + 1}). Is '{self.current_word_to_place}' horizontal (H) or vertical (V)?")
            self.speak(
                f"You selected row {row + 1}, column {col + 1} as the start. Is '{self.current_word_to_place}' horizontal or vertical? Type H or V.")

            self.root.after(100, self.ask_direction)

        elif self.placement_state == 'awaiting_direction':
            self.speak("Please specify horizontal or vertical placement first.")

        elif self.placement_state == 'idle':
            if self.board[row][col] != '':
                self.speak(f"Cell at row {row + 1}, column {col + 1} contains the letter {self.board[row][col]}.")
            else:
                self.speak(f"Cell at row {row + 1}, column {col + 1} is empty.")

    def ask_direction(self):
        """Ask for word placement direction"""
        direction = simpledialog.askstring("Placement Direction",
                                           f"Place '{self.current_word_to_place}' horizontally (H) or vertically (V)?\nClick 'Cancel' to restart placement.",
                                           parent=self.root)

        if self.current_start_row is not None and self.current_start_col is not None and hasattr(self,
                                                                                                 '_original_cell_color') and self._original_cell_color is not None:
            self.board_buttons[self.current_start_row][self.current_start_col].config(bg=self._original_cell_color)

        if direction is None:
            self.speak("Placement cancelled.")
            self.reset_placement_state()
            self.status_label.config(text="Placement cancelled. Enter word and click 'Prepare Placement'")
            return

        direction = direction.strip().upper()

        if direction in ['H', 'V']:
            self.try_place_player_word(self.current_word_to_place,
                                       self.current_start_row,
                                       self.current_start_col,
                                       direction)
        else:
            self.speak("Invalid direction. Please type 'H' for horizontal or 'V' for vertical. Restarting placement.")
            messagebox.showerror("Invalid Direction", "Please enter 'H' for Horizontal or 'V' for Vertical.")
            self.reset_placement_state()

    def try_place_player_word(self, word, start_row, start_col, direction):
        """Try to place a player's word on the board"""
        if self.current_start_row is not None and self.current_start_col is not None and hasattr(self,
                                                                                                 '_original_cell_color') and self._original_cell_color is not None:
            self.board_buttons[self.current_start_row][self.current_start_col].config(bg=self._original_cell_color)

        self.speak(
            f"Attempting to place '{word}' at row {start_row + 1}, column {start_col + 1}, direction {direction}.")

        word_length = len(word)
        placed_letters_info = []

        has_new_tile = False
        lands_on_existing_letter_correctly = False

        for i in range(word_length):
            r = start_row + (i if direction == 'V' else 0)
            c = start_col + (i if direction == 'H' else 0)

            if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                self.speak("Word goes off the board.")
                messagebox.showerror("Placement Error", "Word goes off the board.")
                self.reset_placement_state()
                return False

            letter_needed = word[i]
            existing_letter = self.board[r][c].upper()

            if existing_letter != '':
                if letter_needed == '*' or existing_letter != letter_needed:
                    self.speak(
                        f"Cannot place '{letter_needed}' at row {r + 1}, column {c + 1} because cell is occupied with '{existing_letter}' and letters must match or the cell must be empty for a blank tile.")
                    messagebox.showerror("Placement Error",
                                         f"Cannot place '{letter_needed}' at ({r + 1},{c + 1}). Cell is occupied with '{existing_letter}'.")
                    self.reset_placement_state()
                    return False
                placed_letters_info.append({'letter': existing_letter, 'row': r, 'col': c, 'is_new': False})
                lands_on_existing_letter_correctly = True
            else:
                placed_letters_info.append({'letter': letter_needed, 'row': r, 'col': c, 'is_new': True})
                has_new_tile = True

        if word_length < 2:
            self.speak("Word must be at least two letters long.")
            messagebox.showerror("Placement Error", "Word must be at least two letters long.")
            self.reset_placement_state()
            return False

        if self.first_move:
            uses_center = any((l['row'], l['col']) == CENTER_SQUARE for l in placed_letters_info)
            if not uses_center:
                self.speak("The first word must cover the center star square.")
                messagebox.showerror("Placement Error", "First word must cover the center square.")
                self.reset_placement_state()
                return False
        else:
            connected_by_adjacency = False
            for l in placed_letters_info:
                r, c = l['row'], l['col']

                if l['is_new']:
                    if direction == 'H':
                        if (r > 0 and self.board[r - 1][c] != '') or \
                                (r < BOARD_SIZE - 1 and self.board[r + 1][c] != ''):
                            connected_by_adjacency = True
                    elif direction == 'V':
                        if (c > 0 and self.board[r][c - 1] != '') or \
                                (c < BOARD_SIZE - 1 and self.board[r][c + 1] != ''):
                            connected_by_adjacency = True
                if connected_by_adjacency:
                    break

            if not lands_on_existing_letter_correctly and not connected_by_adjacency:
                self.speak("The word must connect to an existing word on the board.")
                messagebox.showerror("Placement Error", "Word must connect to an existing word.")
                self.reset_placement_state()
                return False

        temp_rack = list(self.player_rack)
        letters_from_rack_needed = [l['letter'] for l in placed_letters_info if l['is_new']]
        letters_actually_removed_from_rack = []

        can_supply_letters = True
        for letter_needed in letters_from_rack_needed:
            if letter_needed != '*' and letter_needed in temp_rack:
                temp_rack.remove(letter_needed)
                letters_actually_removed_from_rack.append(letter_needed)
            elif '*' in temp_rack:
                temp_rack.remove('*')
                letters_actually_removed_from_rack.append('*')
            else:
                can_supply_letters = False
                break

        if not can_supply_letters:
            self.speak(f"You do not have the required letters in your rack to play '{word}'.")
            messagebox.showerror("Placement Error",
                                 f"You do not have the required letters in your rack or a blank tile to play '{word}'.")
            self.reset_placement_state()
            return False

        if not has_new_tile:
            self.speak("Your word must use at least one new tile from your rack.")
            messagebox.showerror("Placement Error", "Your word must use at least one new tile from your rack.")
            self.reset_placement_state()
            return False

        for letter_info in placed_letters_info:
            r, c, letter, is_new = letter_info['row'], letter_info['col'], letter_info['letter'], letter_info['is_new']
            if is_new:
                self.board[r][c] = letter.upper()
                self.board_buttons[r][c].config(
                    text=self.board[r][c],
                    bg=CELL_COLORS['placed_player'],
                    disabledforeground='black',
                    state=tk.DISABLED
                )

        word_score = 0
        for letter in word:
            word_score += self.letter_points.get(letter, 0)

        self.player_score += word_score

        # Check if player has reached 50 points milestone
        if not self.player_reached_50 and self.player_score >= 50:
            self.player_reached_50 = True
            congratulation_message = f"Wow, {self.player_name}! You've reached 50 points! Excellent playing!"
            self.speak(congratulation_message)
            messagebox.showinfo("Achievement", congratulation_message)

        self.score_label.config(text=f"{self.player_name} Score: {self.player_score} | AI Score: {self.ai_score}")

        for letter_removed in letters_actually_removed_from_rack:
            try:
                self.player_rack.remove(letter_removed)
            except ValueError:
                print(f"Error removing letter {letter_removed} from rack. Rack: {self.player_rack}")

        tiles_to_draw_count = len(letters_actually_removed_from_rack)
        if tiles_to_draw_count > 0:
            new_tiles = self.draw_tiles(tiles_to_draw_count)
            self.player_rack.extend(new_tiles)
            self.speak(f"You drew {len(new_tiles)} new tiles.")

        if not self.player_rack and not self.tile_bag:
            self.game_over = True
            self.speak("You used all your tiles! The game is over.")
            self.root.after(2000, self.quit_game)

        self.update_rack_display()

        self.speak(f"You played '{word}' for {word_score} points.")
        self.speak(f"Your score is now {self.player_score}.")

        self.word_entry.delete(0, tk.END)

        self.first_move = False

        self.reset_placement_state()
        self.status_label.config(text="Your turn ended. Waiting for AI...")

        if not self.game_over:
            self.current_turn = "ai"
            self.root.after(2000, self.ai_move)

        return True

    def update_board_with_word(self, word, start_row, start_col, direction, is_player=True):
        """Update the board with a placed word"""
        place_color = CELL_COLORS['placed_player'] if is_player else CELL_COLORS['placed_ai']

        for i in range(len(word)):
            r = start_row + (i if direction == 'V' else 0)
            c = start_col + (i if direction == 'H' else 0)
            letter = word[i]

            if self.board[r][c] == '':
                self.board[r][c] = letter.upper()

            self.board_buttons[r][c].config(
                text=self.board[r][c],
                bg=place_color,
                disabledforeground='black',
                state=tk.DISABLED
            )

    def reset_placement_state(self):
        """Reset the word placement state"""
        if self.placement_state == 'awaiting_direction' and self.current_start_row is not None and self.current_start_col is not None and hasattr(
                self, '_original_cell_color') and self._original_cell_color is not None:
            r, c = self.current_start_row, self.current_start_col
            if self.board[r][c] == '':
                self.board_buttons[r][c].config(bg=self._original_cell_color)

        if hasattr(self, '_original_cell_color'):
            self._original_cell_color = None

        self.placement_state = 'idle'
        self.current_word_to_place = ""
        self.current_start_row = None
        self.current_start_col = None

    def is_valid_placement(self, word, start_row, start_col, direction, is_player):
        """Check if word placement is valid"""
        word_length = len(word)
        if word_length < 2:
            return False

        has_new_tile = False
        lands_on_existing_letter_correctly = False

        for i in range(word_length):
            r = start_row + (i if direction == 'V' else 0)
            c = start_col + (i if direction == 'H' else 0)

            if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                return False

            letter_needed = word[i]
            existing_letter = self.board[r][c].upper()

            if existing_letter != '':
                if letter_needed == '*' or existing_letter != letter_needed:
                    return False
                lands_on_existing_letter_correctly = True
            else:
                has_new_tile = True

        if self.first_move:
            uses_center = False
            for i in range(word_length):
                r = start_row + (i if direction == 'V' else 0)
                c = start_col + (i if direction == 'H' else 0)
                if (r, c) == CENTER_SQUARE:
                    uses_center = True
                    break
            if not uses_center:
                return False
        else:
            connected_by_adjacency = False
            for i in range(word_length):
                r = start_row + (i if direction == 'V' else 0)
                c = start_col + (i if direction == 'H' else 0)

                if self.board[r][c] == '':
                    if direction == 'H':
                        if (r > 0 and self.board[r - 1][c] != '') or \
                                (r < BOARD_SIZE - 1 and self.board[r + 1][c] != ''):
                            connected_by_adjacency = True
                    elif direction == 'V':
                        if (c > 0 and self.board[r][c - 1] != '') or \
                                (c < BOARD_SIZE - 1 and self.board[r][c + 1] != ''):
                            connected_by_adjacency = True
                if connected_by_adjacency:
                    break

            if not lands_on_existing_letter_correctly and not connected_by_adjacency:
                return False

        if not has_new_tile:
            return False

        return True

    def run(self):
        """Run the game"""
        self.get_player_name()

        # Add a short delay, then display rules with AI voice
        self.root.after(1000, self.display_rules)

        self.fill_racks()
        self.update_rack_display()

        self.current_turn = "player"
        rule_line_count = 7
        speak_delay_estimate = 2000 + rule_line_count * 2000 + 1000

        # Enhanced starting message with AI personality
        self.root.after(speak_delay_estimate, lambda: self.speak(
            f"Alright {self.player_name}, I've set up the board and your tiles. You'll go first! Try to create meaningful words and score as many points as possible. Good luck!"))
        self.root.after(speak_delay_estimate + 500,
                        lambda: self.status_label.config(text="Your turn. Enter word and click 'Prepare Placement'"))

        self.root.mainloop()

    def fill_racks(self):
        """Fill player and AI racks with tiles"""
        tiles_to_draw_player = 7 - len(self.player_rack)
        if tiles_to_draw_player > 0:
            new_tiles = self.draw_tiles(tiles_to_draw_player)
            self.player_rack.extend(new_tiles)

        tiles_to_draw_ai = 7 - len(self.ai_rack)
        if tiles_to_draw_ai > 0:
            new_tiles_ai = self.draw_tiles(tiles_to_draw_ai)
            self.ai_rack.extend(new_tiles_ai)

    def update_rack_display(self):
        """Update the display of player's rack"""
        for btn in self.rack_buttons:
            btn.config(state=tk.NORMAL, text='')

        for i, btn in enumerate(self.rack_buttons):
            if i < len(self.player_rack):
                btn.config(text=self.player_rack[i])
            else:
                btn.config(text=' ')

    def display_rules(self):
        """Display and speak the game rules"""
        rules_text = """Accessible Scrabble Game Rules:
1. Create words on the board using letters from your rack and letters already on the board.
2. The first word must cover the center star square.
3. Subsequent words must connect to existing words on the board.
4. All formed words must be valid dictionary words.
5. Score points based on letter values and bonus squares.
6. To play a word: Enter the word in the box, click 'Prepare Placement', then click the cell on the board where the word starts, and finally enter 'H' or 'V' for direction.
7. The game ends when all tiles are drawn and one player uses their last tile, or players pass consecutively."""

        self.speak("Let me explain the game rules to you. I'll be your AI assistant throughout this Scrabble game.")
        rule_lines = rules_text.strip().split('\n')
        delay = 2000
        for line in rule_lines:
            if line.strip():
                self.root.after(delay, lambda l=line.strip(): self.speak(l))
                delay += 2000

        # Add an encouraging message after the rules
        self.root.after(delay, lambda: self.speak(
            f"Don't worry if you forget any rules - I'm here to help! When you reach 50 points, I'll give you a special congratulation. If you need to end the game early, just click the Quit button. Enjoy playing, {self.player_name}!"))

        messagebox.showinfo("Game Rules", rules_text)


def main():
    game = ScrabbleGame()
    game.run()


if __name__ == "__main__":
    main()