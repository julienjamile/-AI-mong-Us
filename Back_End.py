import gen_ai as ai
import random

#Questions for the game
questions = [
    "Describe yourself using only 3 words",
    "Who’s your celebrity crush and why?",
    "What is your biggest pet peeve?",
    "What’s an irrational fear you have?",
    "What’s the craziest dream you’ve had?",
    "What’s the meaning of life?",
    "If you were a food, what would you be and why?",
    "What's something you hate that others enjoy?",
    "Where is your dream vacation spot?",
    "What's your favorite movie or series of all time?",
    "If you could visit one time period, past or future, what would you pick?",
    "What's one thing you can't live without?",
    "Are you a robot?",
    "What's the last thing that made you laugh really hard?",
    "If you could relive one moment, what would it be?",
    "What's your go-to excuse when you don't want to go out?",
    "What's your most embarrassing moment?",
    "What's your usual routine before sleeping?",
    "What's something you did yesterday?",
    "What's something you did this week that was not school-related?",
    "What's your motto in life?",
    "What's your plan after this?",
    "Describe love.",
    "What's your usual morning routine?",
    "What is the one thing that never fails to make you smile?",
    "If you could be a background character in any movie, which one would it be?",
    "What is a 'green flag' you look for in a friend?",
    "What is the first thing you notice when you meet someone new?",
    "If you had to delete every app on your phone except for one, which would you keep?",
    "What is a small thing that usually makes your day better?"

]


#Class Initializaiton

class Player:
    def __init__(self, nickname, id, answer):
        self.nickname = nickname
        self.id = id
        self.answer = answer

class AI_Player:
    def __init__(self, answer):
            self.answer = answer

def generateAnswer(question, player_answers):
    return ai.generate_gen_ai_answer(player_answers, question)

#Added a function for validation of 3-6 players count. Revised.

def validate_player_count(player_count):
    """Validate that player count is between 3 and 6 inclusive."""
    if not isinstance(player_count, int):
        raise TypeError("Player count must be an integer.")
    if player_count < 3 or player_count > 6:
        raise ValueError(f"Invalid player count. Must be between 3 and 6 players. You provided: {player_count}")
    return True


#Checked
def validate_nickname(nickname):
    """Return True when nickname is a non-empty trimmed string."""
    return isinstance(nickname, str) and nickname.strip() != ""

#Checked
def add_nickname(nickname):
    """Add a validated nickname to the nickname list."""
    nicknames = []
    if not validate_nickname(nickname):
        raise ValueError("Nickname must be a non-empty string.")
    nickname = nickname.strip()
    if nickname in nicknames:
        raise ValueError("Nickname already exists.")
    nicknames.append(nickname)
    return nicknames

#Checked and Revised
def collect_nicknames(player_count):
    """Collecting of player_count nicknames from console input."""
    nicknames = []
    while len(nicknames) < player_count:
        nickname = input(f"Enter nickname for player {len(nicknames) + 1}: ")
        try:
            add_nickname(nicknames, nickname)
        except ValueError as err:
            print(err)
            continue
    return nicknames

#Checked
def assign_player_ids(nicknames):
    ids = list(range(1, len(nicknames) + 1))
    print(ids)
    random.shuffle(ids) 
    return {player_id: nickname for player_id, nickname in enumerate(ids, nicknames)}

#Checked
def is_valid_answer(answer):
    """Validate answer length: 10 to 20 words."""
    if not isinstance(answer, str):
        return False
    words = answer.strip().split()
    return 10 <= len(words) <= 20

#Checked
def collect_player_answer(player, answer):
    """Store a validated answer for a player."""
    if not is_valid_answer(answer):
        raise ValueError("Answer must contain between 10 and 20 words.")
    player.answer = answer
    return player

#Checked
def collect_all_answers(players, answers_by_id):
    """Assign answers to players from a mapping of player IDs."""
    for player in players:
        if player.id in answers_by_id:
            collect_player_answer(player, answers_by_id[player.id])
        else:
            raise KeyError(f"Missing answer for player ID {player.id}")
    return players


def get_player_answers(players):
    """Return a list of all human player answers."""
    return [player.answer for player in players if player.answer]

#Revised
def randomize_answers(vote_options, ai_original_id=None):
    """Randomize the order of answers and preserve the randomized AI option ID."""
    player_ids = list(vote_options.keys())
    random.shuffle(player_ids)
    randomized = {}
    ai_new_id = None
    for new_id, old_id in enumerate(player_ids, 1):
        randomized[new_id] = vote_options[old_id]
        if old_id == ai_original_id:
            ai_new_id = new_id
    return randomized, ai_new_id

#Revised
def build_vote_options(players, ai_answer=None):
    """Create an ID-based answer list for voting with randomized order, including the Gen AI impostor if provided."""
    vote_options = {player.id: player.answer for player in players}
    ai_id = None
    if ai_answer is not None:
        ai_id = max(vote_options.keys(), default=0) + 1
        vote_options[ai_id] = ai_answer
    randomized, ai_new_id = randomize_answers(vote_options, ai_original_id=ai_id)
    return randomized, ai_new_id

#Checked
def tally_votes(vote_list):
    """Count votes and return a mapping of player IDs to vote totals."""
    totals = {}
    for voted_id in vote_list:
        totals[voted_id] = totals.get(voted_id, 0) + 1
    return totals

#Checked
def determine_vote_winner(vote_totals):
    """Return the ID with the highest vote count; ties return a list of tied IDs."""
    if not vote_totals:
        return None
    highest = max(vote_totals.values())
    winners = [player_id for player_id, count in vote_totals.items() if count == highest]
    return winners if len(winners) > 1 else winners[0]

#Revised
def eliminate_player(players, eliminated_id):
    """Remove and return remaining players after eliminating the specified player."""
    remaining = [player for player in players if player.id != eliminated_id]
    if len(remaining) == len(players):
        raise ValueError(f"No player found with ID {eliminated_id}")
    return remaining

#Revised
def reset_game_state(game_state):
    """Clear all game data structures to prepare for a new game or replay."""
    if game_state is not None:
        game_state.clear()
    return {}

def create_round(question, nicknames, player_answers_by_id):
    """Build a single round state from nicknames, question, and player answers."""
    players = assign_player_ids(nicknames)
    collect_all_answers(players, player_answers_by_id)
    ai_answer = AI_Player(ai.generate_gen_ai_answer(get_player_answers(players), question)).answer
    vote_options, _ = build_vote_options(players, ai_answer)
    return {
        "question": question,
        "players": players,
        "ai_answer": ai_answer,
        "vote_options": vote_options,
    }


# Revised
def randomizePlayerOrder(players):
    """Shuffle player order for randomized team or turn assignments."""
    random.shuffle(players)
    return players

def randomizeQuestion(questions):
    """Randomly select a question from the available questions pool."""
    return random.choice(questions)


#BACK-end Debugging






