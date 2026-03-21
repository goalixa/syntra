from agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):

    def __init__(self):
        super().__init__("planner")

    def plan(self, prompt: str):

        # later AI will create plan
        return {
            "task": prompt,
            "steps": [
                "analyze request",
                "determine required tools"
            ]
        }
