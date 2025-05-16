import pygame
import sys
import pyttsx3
import random # Used here just to pick a random puzzle

# --- Configuration ---
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 800 # Increased height for rules/messages
GRID_SIZE = 9
CELL_SIZE = (SCREEN_WIDTH - 40) // GRID_SIZE # Adjust size based on screen width with padding
GRID_POS_X = 20
GRID_POS_Y = 20 # Start grid a bit lower to make space at the top

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
LIGHT_BLUE = (173, 216, 230) # For selected cell

# Font sizes
FONT_SIZE_LARGE = 40
FONT_SIZE_MEDIUM = 24
FONT_SIZE_SMALL = 18

# Game States
STATE_NAME_ENTRY = 0
STATE_RULES = 1 # New state to show rules
STATE_GAME = 2
STATE_WIN = 3

# --- Pre-defined Puzzles ---
# You can add more puzzles here. 0 represents an empty cell.
PUZZLES = [
    [ # Easy Puzzle 1
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ],
    [ # Medium Puzzle 2
        [0, 0, 0, 2, 6, 0, 7, 0, 1],
        [6, 8, 0, 0, 7, 0, 0, 9, 0],
        [1, 9, 0, 0, 0, 4, 5, 0, 0],
        [8, 2, 0, 1, 0, 0, 0, 4, 0],
        [0, 0, 4, 6, 0, 2, 9, 0, 0],
        [0, 5, 0, 0, 0, 3, 0, 2, 8],
        [0, 0, 9, 3, 0, 0, 0, 7, 4],
        [0, 4, 0, 0, 5, 0, 0, 3, 6],
        [7, 0, 3, 0, 1, 8, 0, 0, 0]
    ]
]


# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Accessible Sudoku")

# Font setup
font_large = pygame.font.SysFont('Arial', FONT_SIZE_LARGE)
font_medium = pygame.font.SysFont('Arial', FONT_SIZE_MEDIUM)
font_small = pygame.font.SysFont('Arial', FONT_SIZE_SMALL)

# Text-to-Speech Engine
try:
    tts_engine = pyttsx3.init()
    # Adjust rate/volume if needed
    # tts_engine.setProperty('rate', 150)
    # tts_engine.setProperty('volume', 0.9)
except Exception as e:
    print(f"Warning: pyttsx3 initialization failed: {e}")
    tts_engine = None # Disable TTS if it fails

def say(text):
    """Helper function to speak text using the TTS engine."""
    if tts_engine:
        tts_engine.say(text)
        # Using runAndWait() blocks the main loop. For non-blocking speech,
        # you'd run this in a separate thread, but for simple announcements it's okay.
        tts_engine.runAndWait()

# --- Sudoku Logic Functions ---

def is_valid_move(board, num, row, col):
    """Checks if placing 'num' at (row, col) is valid according to Sudoku rules."""
    # Check row
    for c in range(GRID_SIZE):
        if board[row][c] == num and c != col: # Check other cells in the row
            return False

    # Check column
    for r in range(GRID_SIZE):
        if board[r][col] == num and r != row: # Check other cells in the column
            return False

    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for r in range(3):
        for c in range(3):
            if board[r + start_row][c + start_col] == num and (r + start_row != row or c + start_col != col):
                 return False

    return True # It's valid!

def is_board_complete(board):
    """Checks if there are any empty cells (0s) left on the board."""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                return False
    return True

def is_game_won(board):
    """Checks if the board is complete AND all numbers are valid."""
    if not is_board_complete(board):
        return False # Not complete yet

    # Check validity of every cell
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            num = board[r][c]
            if num != 0 and not is_valid_move(board, num, r, c):
                return False # Found an invalid number placement

    return True # Complete and all placements are valid!

# --- Drawing Functions ---

def draw_text(surface, text, x, y, color=BLACK, font=font_medium, center=False):
    """Helper to draw text."""
    txt_surface = font.render(text, True, color)
    if center:
        txt_rect = txt_surface.get_rect(center=(x, y))
        surface.blit(txt_surface, txt_rect)
    else:
        surface.blit(txt_surface, (x, y))


def draw_grid(surface, board, original_board, selected_cell):
    """Draw the Sudoku grid, numbers, and highlight the selected cell."""
    # Draw grid lines
    for i in range(GRID_SIZE + 1):
        thickness = 3 if i % 3 == 0 else 1 # Thicker lines for 3x3 boxes
        # Vertical lines
        pygame.draw.line(surface, BLACK,
                         (GRID_POS_X + i * CELL_SIZE, GRID_POS_Y),
                         (GRID_POS_X + i * CELL_SIZE, GRID_POS_Y + GRID_SIZE * CELL_SIZE),
                         thickness)
        # Horizontal lines
        pygame.draw.line(surface, BLACK,
                         (GRID_POS_X, GRID_POS_Y + i * CELL_SIZE),
                         (GRID_POS_X + GRID_SIZE * CELL_SIZE, GRID_POS_Y + i * CELL_SIZE),
                         thickness)

    # Highlight selected cell
    if selected_cell:
        r, c = selected_cell
        pygame.draw.rect(surface, LIGHT_BLUE,
                         (GRID_POS_X + c * CELL_SIZE, GRID_POS_Y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE), 0)


    # Draw numbers
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            num = board[r][c]
            if num != 0:
                num_text = str(num)

                # Determine color based on original board and validity
                if original_board[r][c] != 0:
                    color = BLACK # Original numbers are black
                    font_to_use = font_large
                else:
                    # Player-entered numbers
                    # Check validity of THIS number at THIS position against the current board state
                    if is_valid_move(board, num, r, c):
                         color = BLUE # Valid moves in blue
                    else:
                         color = RED # Invalid moves in red

                    font_to_use = font_large # Use large font for entered numbers too


                # Center the number in the cell
                text_x = GRID_POS_X + c * CELL_SIZE + CELL_SIZE // 2
                text_y = GRID_POS_Y + r * CELL_SIZE + CELL_SIZE // 2
                draw_text(surface, num_text, text_x, text_y, color, font_to_use, center=True)


def draw_rules(surface):
    """Draw the Sudoku rules text."""
    rules_text = [
        "SUDOKU RULES:",
        "",
        "Fill the grid so that every row, every column,",
        "and every 3x3 box contains the digits 1 through 9.",
        "Each number must appear only once in its row,",
        "column, and box.",
        "",
        "Click on a cell to select it.",
        "Use numbers 1-9 on your keyboard to enter a digit.",
        "Use Backspace or Delete to clear a cell.",
        "",
        "Press ENTER to start the game!"
    ]
    y_offset = 100 # Starting Y position for rules
    for line in rules_text:
        draw_text(surface, line, SCREEN_WIDTH // 2, y_offset, BLACK, font_small, center=True)
        y_offset += 25 # Spacing between lines

# --- Game Variables ---
game_state = STATE_NAME_ENTRY
player_name = ""
selected_cell = None # (row, col) of the currently selected cell

original_board = None # To store the initial puzzle state
player_board = None # To store the player's current state (including their inputs)

# --- Helper to load a puzzle ---
def load_puzzle():
    global original_board, player_board
    chosen_puzzle = random.choice(PUZZLES)
    original_board = [row[:] for row in chosen_puzzle] # Deep copy
    player_board = [row[:] for row in chosen_puzzle]   # Start player board with original numbers

# --- Main Game Loop ---
running = True
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Name Entry State ---
        if game_state == STATE_NAME_ENTRY:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if player_name.strip(): # Proceed only if name is not empty
                        print(f"Player name entered: {player_name}")
                        say(f"Welcome {player_name}")
                        game_state = STATE_RULES # Go to rules state after name
                    else:
                        say("Please enter your name.")
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.unicode: # Handle regular characters
                    # Only add characters that are printable and not control chars
                    if event.unicode.isalnum() or event.unicode.isspace():
                         player_name += event.unicode

        # --- Rules State ---
        elif game_state == STATE_RULES:
             if event.type == pygame.KEYDOWN:
                  if event.key == pygame.K_RETURN:
                       load_puzzle() # Load a random puzzle
                       say("Game starting. Good luck!")
                       game_state = STATE_GAME

        # --- Game State ---
        elif game_state == STATE_GAME:
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                # Check if click is within the grid area
                if GRID_POS_X <= x < GRID_POS_X + GRID_SIZE * CELL_SIZE and \
                   GRID_POS_Y <= y < GRID_POS_Y + GRID_SIZE * CELL_SIZE:
                    # Calculate which cell was clicked
                    col = (x - GRID_POS_X) // CELL_SIZE
                    row = (y - GRID_POS_Y) // CELL_SIZE
                    selected_cell = (row, col)
                    print(f"Selected cell: ({row}, {col})")
                else:
                    selected_cell = None # Clicked outside the grid

            if event.type == pygame.KEYDOWN and selected_cell:
                row, col = selected_cell
                # Only allow input if the cell is not part of the original puzzle
                if original_board[row][col] == 0:
                    # Handle number keys 1-9
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        num = event.key - pygame.K_0 # Convert key code to integer 1-9
                        player_board[row][col] = num
                        print(f"Entered {num} at ({row}, {col})")

                        # Check for win condition after every valid number entry
                        if is_board_complete(player_board) and is_game_won(player_board):
                             game_state = STATE_WIN
                             say(f"Congratulations {player_name}! You solved the puzzle!")
                             print("Game Won!")

                    # Handle delete/backspace to clear cell
                    elif event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                        player_board[row][col] = 0
                        print(f"Cleared cell ({row}, {col})")


        # --- Win State ---
        elif game_state == STATE_WIN:
            # Could add a button to play again, or just display the message
            pass # Currently just displays the win message

    # --- Drawing ---
    screen.fill(WHITE) # Background color

    if game_state == STATE_NAME_ENTRY:
        draw_text(screen, "Enter your name:", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, BLACK, font_medium, center=True)
        # Draw input box (simple underline or rectangle)
        input_box_y = SCREEN_HEIGHT // 2
        input_box_width = 300
        input_box_x = SCREEN_WIDTH // 2 - input_box_width // 2
        pygame.draw.line(screen, BLACK, (input_box_x, input_box_y + 5), (input_box_x + input_box_width, input_box_y + 5), 2)
        draw_text(screen, player_name, SCREEN_WIDTH // 2, input_box_y - 30, BLACK, font_medium, center=True)
        draw_text(screen, "(Press Enter)", SCREEN_WIDTH // 2, input_box_y + 30, DARK_GRAY, font_small, center=True)


    elif game_state == STATE_RULES:
        draw_rules(screen)

    elif game_state == STATE_GAME or game_state == STATE_WIN:
        # Draw Sudoku Grid
        draw_grid(screen, player_board, original_board, selected_cell)

        # Display instructions/messages below the grid
        messages_y_start = GRID_POS_Y + GRID_SIZE * CELL_SIZE + 20
        draw_text(screen, f"Player: {player_name}", GRID_POS_X, messages_y_start, BLACK, font_medium)

        if game_state == STATE_GAME:
             draw_text(screen, "Select a cell and type a number (1-9)", GRID_POS_X, messages_y_start + 40, DARK_GRAY, font_small)
             draw_text(screen, "Incorrect numbers are shown in Red.", GRID_POS_X, messages_y_start + 70, DARK_GRAY, font_small)

        elif game_state == STATE_WIN:
            draw_text(screen, f"Congratulations {player_name}! You solved it!", SCREEN_WIDTH // 2, messages_y_start + 40, BLUE, font_large, center=True)
            draw_text(screen, "Press ESC to Quit", SCREEN_WIDTH // 2, messages_y_start + 100, DARK_GRAY, font_small, center=True)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                 running = False # Allow quitting from win screen

    pygame.display.flip()

# --- Cleanup ---
if tts_engine:
     # pyttsx3 does its own cleanup on exit
     pass # tts_engine.stop() might stop active speech, but runAndWait() blocks anyway

pygame.quit()
sys.exit()