class BestLine:
    def __init__(self, moves, score, sharpness):
        self.moves = moves
        self.score = score
        self.sharpness = sharpness
    
    def to_dict(self):
        return {
            "moves": self.moves,
            "score": self.score,
            "sharpness": self.sharpness
        }