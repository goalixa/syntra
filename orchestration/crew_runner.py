from agents.planner_agent import PlannerAgent
from agents.devops_agent import DevOpsAgent


def run_ai_task(prompt: str):

    planner = PlannerAgent()
    devops = DevOpsAgent()

    plan = planner.plan(prompt)

    result = devops.execute(plan)

    return result

