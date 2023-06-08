import numpy as np


class Spec:
    def __init__(self, tp, x1, y1, x2, y2, w, color):
        assert tp in {'include', 'exclude'}
        self.x1 = x1
        self.x2 = x2
        self.a = (y2-y1)/(x2-x1) # slope
        b = y1-x1*self.a  # intercept
        # calculate intercept of the edges
        self.c1 = b+w/2  # y-intercept of first line
        self.c2 = b-w/2  # y-intercept of second line 
        self.x = np.linspace(x1, x2, 1000)
        self.y1 = self.a * self.x + self.c1
        self.y2 = self.a * self.x + self.c2
        self.tp = tp
        self.color = color


    def get_color(self):
        return self.color

    def is_sat(self, x, y):
        max_y = self.a * x + self.c1
        min_y = self.a * x + self.c2

        if not x in range(self.x1, self.x2):
            return True # the given point is outside of the specified region

        if self.tp == 'include':
            return y <= max_y and y >= min_y
        elif self.tp == 'exclude':
            return not (y <= max_y and y >= min_y)
        else:
            raise Exception('unexpected spec type')

    def get_coordinates(self):
        return self.x, self.y1, self.y2