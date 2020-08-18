from lib.tetromins.I import ITetromin
from lib.tetromins.J import JTetromin
from lib.tetromins.L import LTetromin
from lib.tetromins.O import OTetromin
from lib.tetromins.S import STetromin
from lib.tetromins.T import TTetromin
from lib.tetromins.Z import ZTetromin

tetromin_list = [
    ITetromin,
    JTetromin,
    LTetromin,
    OTetromin,
    STetromin,
    TTetromin,
    ZTetromin
]

tetromin_map = {
    'I': ITetromin,
    'J': JTetromin,
    'L': LTetromin,
    'O': OTetromin,
    'S': STetromin,
    'T': TTetromin,
    'Z': ZTetromin
}
