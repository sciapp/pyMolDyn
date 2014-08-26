class Configuration:

    # standard configuration
    RESULT_DIR      = '../results/'
    GL_WINDOW_SIZE  = (800, 800)
    WINDOW_POSITION = (-1, -1)
    STD_RESOLUTION  = 64


    class Colors:
        CAVITY          = (0.2, 0.4, 1)
        DOMAIN          = (0, 1, 0.5)
        ALT_CAVITY      = (0.9, 0.4, 0.2)
        BACKGROUND      = (0.0, 0.0, 0.0)
        BOUNDING_BOX    = (1.0, 1.0, 1.0)

    class OpenGL:
       # CAMERA_POSITION =
       # OFFSET          = (0.0, 0.0, 0.0)
        ATOM_RADIUS     = 2.8

    def __init__(self):
        pass
