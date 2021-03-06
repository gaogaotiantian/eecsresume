# Black and White
class BlackWhite():
    def __init__(self):
        self.grid = []
        self.valid = False
        self.width = 0
        self.height = 0
    def evaluate(self, questions, answers):
        # This will return a tuple (score, results, err_msg)
        # If score is None, then err_msg is guaranteed to be a string
        # explaining about what happened

        # questions is expected to be separated by \n=\n
        # each row in the grid is separated by \n
        # a valid question could be: 
        # 111
        # 000
        # 111
        # =
        # 000
        # 101
        # 010

        # answers is expected to be separated by \n
        # a valid answer could be: 
        # rrdd
        # ddrr

        ret_score = 0
        final_moves = 0
        ret_results = []
        # strip all the spaces first
        questions = questions.replace(" ","").replace("\r","").split("=")
        answers   = answers.replace(" ","").replace("\r","").split("\n")

        if len(questions) != len(answers):
            return None, None, "Answer number is incorrect. Expected {} answer, got {}".format(len(questions), len(answers))

        for i in range(len(questions)):
            question = questions[i].strip()
            answer = answers[i]
            if not self.load_string(question):
                return None, None, "Question is not formatted well"
            score, finalGrid, moves, err_msg = self.solve(answer)
            if score == None:
                return None, None, "Answer wrong on {}, {}".format(i+1, err_msg)
            else:
                ret_score += score
                final_moves += moves
                ret_results.append("{}({})".format(score,moves))
        ret_results.append("{}({})".format(ret_score,final_moves))

        return ret_score, " | ".join(ret_results), None

    def load_string(self, s):
        lst = s.split("\n")
        self.height = len(lst)
        self.width = len(lst[0])
        self.grid = []
        for row in lst:
            if len(row) != self.width:
                self.valid = False
                return False
            new = []
            for c in row.strip():
                if c == '0':
                    new.append(0)
                elif c == '1':
                    new.append(1)
                else:
                    print("error")
                    print(c)
                    self.valid = False
                    return False
            self.grid.append(new)
        self.valid = True
        return True

    def solve(self, s):
        # Returns a tuple
        # (score, final_grid, current_move, error_message)
        if not self.valid:
            return None, None, None, "Grid is not valid"
        tempGrid = [row[:] for row in self.grid]
        currx = 0
        curry = 0
        currMove = 0
        for action in s:
            currMove += 1
            if action == 'l':
                d = (-1,0)
            elif action == 'r':
                d = (1,0)
            elif action == 'u':
                d = (0,-1)
            elif action == 'd':
                d = (0,1)
            else:
                return None, None, None, "Invalid move, {}".format(currMove)
            currx += d[0]
            curry += d[1]
            
            if 0 <= currx < self.width and 0 <= curry < self.height:
                tempGrid[curry][currx] = 1 - tempGrid[curry][currx]
            else:
                return None, None, None, "Move out of grid, {}".format(currMove)
        return self.count(tempGrid) - self.count(self.grid), tempGrid, currMove, None

    def count(self, grid):
        return sum(lst.count(1) for lst in grid)

    def print_string(self, grid = None):
        ret = ""
        if grid == None:
            grid = self.grid
        ret = "\n".join(["".join([str(c) for c in row]) for row in grid])
        return ret

    def print(self, grid = None):
        print(self.print_string(grid))

class MountainOcean:
    def __init__(self):
        self.grid = []
        self.valid = False
        self.width = 0
        self.height = 0
    def evaluate(self, questions, answers):
        pass
        # This will return a tuple (score, results, err_msg)
        # If score is None, then err_msg is guaranteed to be a string
        # explaining about what happened

        # questions is expected to be separated by \n=\n
        # each row in the grid is separated by \n
        # a valid question could be: 
        # bbc
        # bba
        # abb
        # =
        # dcc
        # bae
        # cdb

        # answers is expected to be separated by \n
        # a valid answer could be: 
        # rrld
        # ddrr

        ret_score = 0
        final_moves = 0
        ret_results = []
        # strip all the spaces first
        questions = questions.replace(" ","").replace("\r","").split("=")
        answers   = answers.replace(" ","").replace("\r","").split("\n")

        if len(questions) != len(answers):
            return None, None, "Answer number is incorrect. Expected {} answer, got {}".format(len(questions), len(answers))

        for i in range(len(questions)):
            question = questions[i].strip()
            answer = answers[i]
            if not self.load_string(question):
                return None, None, "Question is not formatted well"
            score, finalGrid, moves, err_msg = self.solve(answer)
            if score == None:
                return None, None, "Answer wrong on {}, {}".format(i+1, err_msg)
            else:
                ret_score += score
                final_moves += moves
                ret_results.append("{}".format(score))
        ret_results.append("{}".format(ret_score))

        return ret_score, " | ".join(ret_results), None

    def load_string(self, s):
        lst = s.split('\n')
        self.height = len(lst)
        self.width = len(lst[0])
        self.grid = []
        for row in lst:
            if len(row) != self.width:
                self.valid = False
                return False
            new = []
            for c in row.strip():
                if 'a' <= c <= 'z':
                    new.append(ord(c) - ord('a'))
                else:
                    print("error")
                    print(c)
                    self.valid = False
                    return False
            self.grid.append(new)
        self.valid = True
        return True

    def solve(self, s):
        # Returns a tuple
        # (score, final_grid, current_move, error_message)
        if not self.valid:
            return None, None, None, "Grid is not valid"
        tempGrid = [row[:] for row in self.grid]
        currx = 0
        curry = 0
        currMove = 0
        for action in s:
            currMove += 1
            d = {'l':(-1,0), 'r':(1,0), 'u':(0,-1), 'd':(0,1)}.get(action, None)
            if d == None:
                return None, None, None, "Invalid move, {}".format(currMove)
            currx += d[0]
            curry += d[1]
            
            if 0 <= currx < self.width and 0 <= curry < self.height:
                if tempGrid[curry][currx] == 0:
                    return None, None, None, "Moved into ocean, {}".format(currMove)
                tempGrid[curry][currx] -= 1
            else:
                return None, None, None, "Move out of grid, {}".format(currMove)
        return self.count(self.grid) - self.count(tempGrid), tempGrid, currMove, None

    def count(self, grid):
        return sum(sum(lst) for lst in grid)

    def print_string(self, grid = None):
        ret = ""
        if grid == None:
            grid = self.grid
        ret = "\n".join(["".join([str(c) for c in row]) for row in grid])
        return ret

    def print(self, grid = None):
        print(self.print_string(grid))

class Challenge():
    def __init__(self):
        pass
    
    def evaluate(self, link, questions, answers):
        # return a tuple (score, results, err_msg)
        # if score is None, then read err_msg
        if link.lower() == 'black_and_white':
            q = BlackWhite()
            return q.evaluate(questions, answers)
        elif link.lower() == "mountain_ocean":
            q = MountainOcean()
            return q.evaluate(questions, answers)
        return None, None, "Unknown Link"


if __name__ == '__main__':
    c = Challenge()
    print(c.evaluate("mountain_ocean", "bbb\nccc\nddd\n=\nabb\nbbd\nbdd\n","rrdd\nddrr"))
