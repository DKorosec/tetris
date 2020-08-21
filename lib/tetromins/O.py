from lib.tetromins.tetromin import Tetromin


class OTetromin(Tetromin):
    def __init__(self):
        super().__init__([
            [
                [1, 1],
                [1, 1]
            ]
        ], 'yellow2')
