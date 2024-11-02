import os
import autogen
import chess
import chess.svg
from IPython.display import display
from typing_extensions import Annotated

from autogen import ConversableAgent, register_function

# Let's set our two player configs, specifying clients and models

# Anthropic's Sonnet for player white
player_white_config_list = autogen.config_list_from_json(env_or_file='OAI_CONFIG_LIST')

# Mistral's Mixtral 8x7B for player black (through Together.AI)
player_black_config_list = autogen.config_list_from_json(env_or_file='OAI_CONFIG_LIST')


# Initialize the board.
board = chess.Board()

# Keep track of whether a move has been made.
made_move = False


def get_legal_moves() -> Annotated[
    str,
    "Call this tool to list of all legal chess moves on the board, output is a list in UCI format, e.g. e2e4,e7e5,e7e8q.",
]:
    return "Possible moves are: " + ",".join([str(move) for move in board.legal_moves])


def make_move(
    move: Annotated[
        str,
        "Call this tool to make a move after you have the list of legal moves and want to make a move. Takes UCI format, e.g. e2e4 or e7e5 or e7e8q.",
    ]
) -> Annotated[str, "Result of the move."]:
    move = chess.Move.from_uci(move)
    board.push_uci(str(move))
    global made_move
    made_move = True
    # Display the board.
    display(
        chess.svg.board(board, arrows=[(move.from_square, move.to_square)], fill={move.from_square: "gray"}, size=200)
    )
    # Get the piece name.
    piece = board.piece_at(move.to_square)
    piece_symbol = piece.unicode_symbol()
    piece_name = (
        chess.piece_name(piece.piece_type).capitalize()
        if piece_symbol.isupper()
        else chess.piece_name(piece.piece_type)
    )
    return f"Moved {piece_name} ({piece_symbol}) from {chess.SQUARE_NAMES[move.from_square]} to {chess.SQUARE_NAMES[move.to_square]}."


player_white = ConversableAgent(
    name="Player_White",
    system_message="You are a chess player and you play as white, your name is 'Player_White'. "
    "First call the function get_legal_moves() to get list of legal moves. "
    "Then call the function make_move(move) to make a move. "
    "Then tell Player_Black you have made your move and it is their turn. "
    "Make sure you tell Player_Black you are Player_White.",
    llm_config={"config_list": player_white_config_list, "cache_seed": None},
)

player_black = ConversableAgent(
    name="Player_Black",
    system_message="You are a chess player and you play as black, your name is 'Player_Black'. "
    "First call the function get_legal_moves() to get list of legal moves. "
    "Then call the function make_move(move) to make a move. "
    "Then tell Player_White you have made your move and it is their turn. "
    "Make sure you tell Player_White you are Player_Black.",
    llm_config={"config_list": player_black_config_list, "cache_seed": None},
)


# Check if the player has made a move, and reset the flag if move is made.
def check_made_move(msg):
    global made_move
    if made_move:
        made_move = False
        return True
    else:
        return False


board_proxy = ConversableAgent(
    name="Board_Proxy",
    llm_config=False,
    # The board proxy will only terminate the conversation if the player has made a move.
    is_termination_msg=check_made_move,
    # The auto reply message is set to keep the player agent retrying until a move is made.
    default_auto_reply="Please make a move.",
    human_input_mode="NEVER",
)


register_function(
    make_move,
    caller=player_white,
    executor=board_proxy,
    name="make_move",
    description="Call this tool to make a move after you have the list of legal moves.",
)

register_function(
    get_legal_moves,
    caller=player_white,
    executor=board_proxy,
    name="get_legal_moves",
    description="Call this to get a legal moves before making a move.",
)

register_function(
    make_move,
    caller=player_black,
    executor=board_proxy,
    name="make_move",
    description="Call this tool to make a move after you have the list of legal moves.",
)

register_function(
    get_legal_moves,
    caller=player_black,
    executor=board_proxy,
    name="get_legal_moves",
    description="Call this to get a legal moves before making a move.",
)


player_white.register_nested_chats(
    trigger=player_black,
    chat_queue=[
        {
            # The initial message is the one received by the player agent from
            # the other player agent.
            "sender": board_proxy,
            "recipient": player_white,
            # The final message is sent to the player agent.
            "summary_method": "last_msg",
        }
    ],
)

player_black.register_nested_chats(
    trigger=player_white,
    chat_queue=[
        {
            # The initial message is the one received by the player agent from
            # the other player agent.
            "sender": board_proxy,
            "recipient": player_black,
            # The final message is sent to the player agent.
            "summary_method": "last_msg",
        }
    ],
)


# Clear the board.
board = chess.Board()

chat_result = player_black.initiate_chat(
    player_white,
    message="Let's play chess! Your move.",
    max_turns=10,
)