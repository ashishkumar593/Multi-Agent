"""Discrete node execution functions for LangGraph workflow."""
from typing import Any
from src.backend.agents.analyst import AnalystAgent
from src.backend.agents.critic import CriticAgent
from src.backend.agents.planner import PlannerAgent
from src.backend.agents.search import SearchAgent
from src.backend.agents.state import ResearchState
from src.backend.agents.writer import WriterAgent
from src.backend.rag.retriever import HybridRetriever

class GraphNodes:
    """Encapsulates node execution logic for the research state machine."""

    def __init__(self, retriever: HybridRetriever | None = None):
        self.planner = PlannerAgent()
        self.search = SearchAgent(retriever=retriever)
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()

    def plan_node(self, state: ResearchState) -> dict[str, Any]:
        """Planner node: Decomposes research topic into sub-questions."""
        plan = self.planner.plan(state["topic"], state.get("scope", "comprehensive"))
        return {"plan": plan, "status": "planning"}

    def search_node(self, state: ResearchState) -> dict[str, Any]:
        """Search node: Retrieves evidence across web and document indices."""
        plan = state["plan"]
        if not plan:
            return {"errors": ["Cannot search without a research plan."]}
        new_evidence = self.search.gather_evidence_sync(plan)
        current_evidence = list(state.get("evidence", []))
        current_evidence.extend(new_evidence)
        return {
            "evidence": current_evidence,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "status": "searching",
        }

    def analyst_node(self, state: ResearchState) -> dict[str, Any]:
        """Analyst node: Extracts factual claims and evaluates cross-source contradictions."""
        plan = state["plan"]
        evidence = state.get("evidence", [])
        if not plan:
            return {"errors": ["Missing plan in analysis step."]}
        analysis = self.analyst.analyze(plan, evidence)
        return {"analysis": analysis, "status": "analyzing"}

    def writer_node(self, state: ResearchState) -> dict[str, Any]:
        """Writer node: Drafts structured report with verified citations."""
        plan = state["plan"]
        analysis = state["analysis"]
        evidence = state.get("evidence", [])
        if not plan or not analysis:
            return {"errors": ["Cannot write report without plan and analysis."]}
        draft = self.writer.draft_report(plan, analysis, evidence)
        return {"draft_report": draft, "status": "writing"}

    def critic_node(self, state: ResearchState) -> dict[str, Any]:
        """Critic node: Fact-checks report and audits citations."""
        draft = state.get("draft_report")
        evidence = state.get("evidence", [])
        if not draft:
            return {"errors": ["No draft report to critique."]}
        feedback = self.critic.review(draft, evidence)
        new_status = "completed" if feedback.approved else "reviewing"
        return {"critic_feedback": feedback, "status": new_status}
