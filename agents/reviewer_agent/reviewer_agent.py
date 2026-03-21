from agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):

    def __init__(self):
        super().__init__("reviewer")

    def review(self, result: str):

        return {
            "approved": True,
            "result": result
        }
