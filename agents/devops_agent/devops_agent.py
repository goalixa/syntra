from agents.base_agent import BaseAgent


class DevOpsAgent(BaseAgent):

    def __init__(self):
        super().__init__("devops")

    def execute(self, plan: dict):

        task = plan["task"]

        return f"DevOps agent executed task: {task}"
