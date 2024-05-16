from states import *
from threading import Lock

class StateManager:
    state: GameState = GameState()

global_state_manager = StateManager()
global_state_mutex = Lock()