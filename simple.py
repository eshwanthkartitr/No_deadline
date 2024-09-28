import curses
import random
import time
import pygame

# Initialize pygame mixer for sound
pygame.mixer.init()

# Load sound effects
try:
    eat_sound = pygame.mixer.Sound("eat.wav")
    eat_sound.set_volume(0.1) 
    game_over_sound = pygame.mixer.Sound("over.wav")
    pygame.mixer.music.load("theme.wav")  # Load theme music
except pygame.error:
    print("Warning: Sound files not found. Game will run without sound.")
    eat_sound = game_over_sound = None

def play_sound(sound, duration=None):
    if sound:
        if duration:
            sound.play(maxtime=int(duration * 1000))  # Convert seconds to milliseconds
        else:
            sound.play()

def play_theme_music():
    if not pygame.mixer.music.get_busy():  # Check if music is not already playing
        pygame.mixer.music.set_volume(0.3)  # Set volume to 30%
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely

def stop_theme_music():
    if pygame.mixer.music:
        pygame.mixer.music.stop()

def create_food(sh, sw, snake):
    while True:
        food = [random.randint(1, sh-2), random.randint(1, sw-2)]
        if food not in snake:
            return food

def draw_border(w, sh, sw):
    w.attron(curses.color_pair(3))
    w.border('║', '║', '-', '-', '+', '+', '+', '+')
    w.attroff(curses.color_pair(3))

def is_safe_move(snake, new_head, sh, sw, has_border):
    if new_head in snake[1:]:
        return False
    y, x = new_head
    if has_border:
        return 1 <= y < sh-1 and 1 <= x < sw-1
    return True

def move_ai_snake(snake, food, sh, sw, has_border):
    head = snake[0]
    moves = [
        (curses.KEY_UP, [-1, 0]),
        (curses.KEY_DOWN, [1, 0]),
        (curses.KEY_LEFT, [0, -1]),
        (curses.KEY_RIGHT, [0, 1])
    ]
    
    possible_moves = []
    for key, [dy, dx] in moves:
        new_head = [(head[0] + dy) % sh, (head[1] + dx) % sw]
        if is_safe_move(snake, new_head, sh, sw, has_border):
            possible_moves.append((key, new_head))
    
    if possible_moves:
        possible_moves.sort(key=lambda m: abs(m[1][0] - food[0]) + abs(m[1][1] - food[1]))
        return possible_moves[0][0]
    
    return random.choice([curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT])

def snake_game(stdscr, mode, difficulty):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Snake
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Food
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Border
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Score
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)   # AI snake

    sh, sw = stdscr.getmaxyx()
    w = curses.newwin(sh, sw, 0, 0)
    w.keypad(1)
    w.timeout(difficulty['speed'])

    snake = [[sh//2, sw//2], [sh//2, sw//2-1], [sh//2, sw//2-2]]
    food = create_food(sh, sw, snake)

    key = curses.KEY_RIGHT
    score = 0
    start_time = time.time()

    while True:
        draw_border(w, sh, sw)
        
        score_str = f'SCORE {score:04d}'
        w.addstr(0, sw//2 - len(score_str)//2, score_str, curses.color_pair(4) | curses.A_BOLD)
        
        elapsed_time = int(time.time() - start_time)
        time_str = f'TIME {elapsed_time:04d}'
        w.addstr(0, sw - len(time_str) - 1, time_str, curses.color_pair(4) | curses.A_BOLD)
        
        next_key = w.getch()
        if next_key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            key = next_key

        if mode == 'vs_computer':
            key = move_ai_snake(snake, food, sh, sw, difficulty['has_border'])

        y, x = snake[0]
        if key == curses.KEY_DOWN:
            y = (y + 1) % sh
        elif key == curses.KEY_UP:
            y = (y - 1) % sh
        elif key == curses.KEY_LEFT:
            x = (x - 1) % sw
        elif key == curses.KEY_RIGHT:
            x = (x + 1) % sw

        new_head = [y, x]

        if not is_safe_move(snake, new_head, sh, sw, difficulty['has_border']):
            play_sound(game_over_sound)  # Play game over sound
            return score, "GAME OVER - YOU CRASHED", elapsed_time

        snake.insert(0, new_head)

        if snake[0] == food:
            play_sound(eat_sound, 1.5)  # Play eat sound for 5 seconds
            score += 1
            food = create_food(sh, sw, snake)
        else:
            tail = snake.pop()
            w.addch(tail[0], tail[1], ' ')

        w.attron(curses.color_pair(1) if mode == 'free' else curses.color_pair(5))
        w.addch(snake[0][0], snake[0][1], '■')
        for body in snake[1:]:
            w.addch(body[0], body[1], '□')
        w.attroff(curses.color_pair(1) if mode == 'free' else curses.color_pair(5))

        w.attron(curses.color_pair(2))
        w.addch(food[0], food[1], '●')
        w.attroff(curses.color_pair(2))

def display_game_over(stdscr, score, game_over_code, elapsed_time):
    sh, sw = stdscr.getmaxyx()
    w = curses.newwin(sh, sw, 0, 0)
    w.keypad(1)
    w.timeout(-1)  # Wait indefinitely for user input

    while True:
        w.clear()
        w.border('║', '║', '-', '-', '+', '+', '-', '-')
        
        title = "GAME OVER!"
        w.addstr(sh//2 - 4, sw//2 - len(title)//2, title, curses.color_pair(3) | curses.A_BOLD)
        
        score_str = f"FINAL SCORE: {score:04d}"
        w.addstr(sh//2 - 2, sw//2 - len(score_str)//2, score_str, curses.color_pair(4) | curses.A_BOLD)
        
        w.addstr(sh//2, sw//2 - len(game_over_code)//2, game_over_code, curses.color_pair(5) | curses.A_BOLD)
        
        time_str = f"TOTAL TIME: {elapsed_time:04d} SEC"
        w.addstr(sh//2 + 2, sw//2 - len(time_str)//2, time_str, curses.color_pair(4) | curses.A_BOLD)
        
        replay_str = "Press 'R' to replay or 'Q' to quit"
        w.addstr(sh//2 + 4, sw//2 - len(replay_str)//2, replay_str, curses.color_pair(3))
        
        w.refresh()
        
        key = w.getch()
        if key in [ord('r'), ord('R')]:
            return True
        elif key in [ord('q'), ord('Q')]:
            return False

def show_menu(stdscr):
    sh, sw = stdscr.getmaxyx()
    w = curses.newwin(sh, sw, 0, 0)
    w.keypad(1)
    w.timeout(-1)

    while True:
        w.clear()
        w.border('║', '║', '-', '-', '+', '+', '+', '+')
        
        title = "SNAKE GAME"
        w.addstr(sh//2 - 6, sw//2 - len(title)//2, title, curses.color_pair(3) | curses.A_BOLD)
        
        options = [
            "1. Free Mode",
            "2. Become the computer",
            "3. High Scores",
            "4. Quit"
        ]
        
        for i, option in enumerate(options):
            w.addstr(sh//2 - 2 + i, sw//2 - len(option)//2, option, curses.color_pair(4))
        
        w.refresh()
        
        key = w.getch()
        if key in [ord('1'), ord('2'), ord('3'), ord('4')]:
            return key

def set_difficulty(stdscr, mode):
    difficulties = {
        'free': {'speed': 150, 'has_border': False},
        'easy': {'speed': 150, 'has_border': False},
        'medium': {'speed': 100, 'has_border': True},
        'hard': {'speed': 1, 'has_border': True}
    }
    
    if mode == 'free':
        return difficulties['free']
    
    sh, sw = stdscr.getmaxyx()
    w = curses.newwin(sh, sw, 0, 0)
    w.keypad(1)
    w.timeout(-1)

    while True:
        w.clear()
        w.border('║', '║', '-', '-', '+', '+', '+', '+')
        
        title = "Select Difficulty:"
        w.addstr(sh//2 - 4, sw//2 - len(title)//2, title, curses.color_pair(3) | curses.A_BOLD)
        
        options = [
            "1. Easy",
            "2. Medium",
            "3. Hard"
        ]
        
        for i, option in enumerate(options):
            w.addstr(sh//2 - 2 + i, sw//2 - len(option)//2, option, curses.color_pair(4))
        
        w.refresh()
        
        key = w.getch()
        if key == ord('1'):
            return difficulties['easy']
        elif key == ord('2'):
            return difficulties['medium']
        elif key == ord('3'):
            return difficulties['hard']

def update_high_scores(score):
    with open('high_scores.txt', 'a+') as f:
        f.write(f"{score}\n")

def display_high_scores(stdscr):
    sh, sw = stdscr.getmaxyx()
    w = curses.newwin(sh, sw, 0, 0)
    w.keypad(1)
    w.timeout(-1)

    try:
        with open('high_scores.txt', 'r') as f:
            scores = []
            for line in f:
                try:
                    score = int(line.strip())
                    scores.append(score)
                except ValueError:
                    continue  # Skip lines that cannot be converted to an integer
            scores = sorted(scores, reverse=True)[:5]
    except FileNotFoundError:
        scores = []

    while True:
        w.clear()
        w.border('║', '║', '-', '-', '+', '+', '+', '+')
        
        title = "HIGH SCORES"
        w.addstr(sh//2 - 6, sw//2 - len(title)//2, title, curses.color_pair(3) | curses.A_BOLD)
        
        for i, score in enumerate(scores):
            score_str = f"{i+1}. {score:04d}"
            w.addstr(sh//2 - 2 + i, sw//2 - len(score_str)//2, score_str, curses.color_pair(4))
        
        back_str = "Press any key to go back"
        w.addstr(sh//2 + 4, sw//2 - len(back_str)//2, back_str, curses.color_pair(3))
        
        w.refresh()
        
        key = w.getch()
        if key:
            break

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)

    play_theme_music()  # Start playing theme music

    while True:
        choice = show_menu(stdscr)
        if choice == ord('1'):
            mode = 'free'
            difficulty = set_difficulty(stdscr, mode)
        elif choice == ord('2'):
            mode = 'vs_computer'
            difficulty = set_difficulty(stdscr, mode)
        elif choice == ord('3'):
            display_high_scores(stdscr)
            continue
        elif choice == ord('4'):
            break

        if choice in [ord('1'), ord('2')]:

            score, game_over_code, elapsed_time = snake_game(stdscr, mode, difficulty)
            update_high_scores(score)
            play_again = display_game_over(stdscr, score, game_over_code, elapsed_time)
            if play_again:
                play_theme_music()  # Resume theme music after the game
            else:
                break

    # Ensure all sounds have stopped playing before exiting
    stop_theme_music()
    pygame.mixer.stop()

if __name__ == "__main__":
    curses.wrapper(main)