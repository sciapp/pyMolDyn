
class PosBoolType(object):
    def __init__(self, pos):
        self.pos = pos
        
    def __getitem__(self, item):
        return self.pos[item]
    
    def __nonzero__(self):
        return self.pos[0] == -1
    
    def __str__(self):
        return "(%d, %d)" % self.pos
        
