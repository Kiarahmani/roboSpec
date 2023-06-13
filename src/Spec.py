import numpy as np


class Spec:
    def __init__(self, tp, x1, y1, x2, y2, w, color):
        assert tp in {'include', 'exclude'}
        # center line begin point
        self.x1 = x1
        self.y1 = y1
        # center line end point
        self.x2 = x2
        self.y2 = y2
        self.a = (y2-y1)/(x2-x1)  # center line slope
        self.b = y1-x1*self.a  # center line intercept
        self.w = w

        # calculate the border lines
        self.c1 = self.b+w/2  # y-intercept of first line
        self.c2 = self.b-w/2  # y-intercept of second line
        self.x_series = np.linspace(x1, x2, 1000)
        self.y1_series = self.a * self.x_series + self.c1
        self.y2_series = self.a * self.x_series + self.c2
        self.tp = tp
        self.color = color

    def __str__(self):
        return f'{self.tp}[p1=({self.x1},{self.y1}), p2=({self.x2},{self.y2}), m={round(self.a,2)}, w={self.w}]'

    def get_color(self):
        return self.color

    def get_max_valid_y(self, x):
        return self.a * x + self.c1
    
    def get_min_valid_y(self,x):
        return self.a * x + self.c2

    def is_sat(self, x, y):
        max_y = self.get_max_valid_y(x)
        min_y = self.get_min_valid_y(x)
        
        if not x in range(self.x1, self.x2):
            return True  # the given point is outside of the specified region

        if self.tp == 'include':
            return y <= max_y and y >= min_y
        elif self.tp == 'exclude':
            return not (y <= max_y and y >= min_y)
        else:
            raise Exception('unexpected spec type')

    def get_coordinates(self):
        return self.x_series, self.y1_series, self.y2_series
