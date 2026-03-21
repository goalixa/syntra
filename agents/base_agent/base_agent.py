class BaseAgent:

    def __init__(self, name: str):
        self.name = name

    def run(self, task: str):
        raise NotImplementedError
