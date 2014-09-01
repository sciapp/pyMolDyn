from config import configuration


class Control:

    def __init__(self):
        self.config = configuration.Configuration()
        self.config.read()
        

if __name__ == '__main__':
    c = configuration.Configuration()
    c.read()
    print c.GL_WINDOW_SIZE