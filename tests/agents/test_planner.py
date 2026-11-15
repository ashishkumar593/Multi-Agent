"""Unit tests for Planner Agent."""
from backend.agents.planner import PlannerAgent

def test_planner_subquestions():
    planner = PlannerAgent()
    plan = planner.plan(topic="Autonomous Vehicle Safety Standards", scope="technical")
    assert plan.topic == "Autonomous Vehicle Safety Standards"
    assert len(plan.sub_questions) >= 4
    for sq in plan.sub_questions:
        assert sq.question
        assert sq.priority in (1, 2, 3)
