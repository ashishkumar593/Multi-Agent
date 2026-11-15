"""LangGraph multi-agent research workflow orchestration."""
from typing import Any, Callable
from src.backend.agents.state import ResearchState
from src.backend.graph.checkpoint import get_checkpointer
from src.backend.graph.edges import should_continue_after_critic
from src.backend.graph.nodes import GraphNodes
from src.backend.rag.retriever import HybridRetriever

class ResearchWorkflow:
    """Multi-agent StateGraph orchestrator connecting Planner, Search, Analyst, Writer, and Critic."""

    def __init__(self, retriever: HybridRetriever | None = None):
        self.nodes = GraphNodes(retriever=retriever)
        self.checkpointer = get_checkpointer()
        self.app = self._build_graph()

    def _build_graph(self) -> Any:
        try:
            from langgraph.graph import END, START, StateGraph

            workflow = StateGraph(ResearchState)
            workflow.add_node("planner", self.nodes.plan_node)
            workflow.add_node("search", self.nodes.search_node)
            workflow.add_node("analyst", self.nodes.analyst_node)
            workflow.add_node("writer", self.nodes.writer_node)
            workflow.add_node("critic", self.nodes.critic_node)

            workflow.add_edge(START, "planner")
            workflow.add_edge("planner", "search")
            workflow.add_edge("search", "analyst")
            workflow.add_edge("analyst", "writer")
            workflow.add_edge("writer", "critic")

            workflow.add_conditional_edges(
                "critic",
                should_continue_after_critic,
                {
                    "search": "search",
                    "writer": "writer",
                    "end": END,
                },
            )
            return workflow.compile(checkpointer=self.checkpointer)
        except ImportError:
            # Standalone fallback orchestrator when langgraph is not installed
            return None

    def run_sync(
        self,
        topic: str,
        scope: str = "comprehensive",
        max_iterations: int = 2,
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> ResearchState:
        """Run workflow synchronously through nodes with iterative feedback loops."""
        state: ResearchState = {
            "research_id": f"res_{abs(hash(topic)) % 1000000}",
            "topic": topic,
            "scope": scope,
            "plan": None,
            "evidence": [],
            "analysis": None,
            "draft_report": None,
            "critic_feedback": None,
            "iteration_count": 0,
            "max_iterations": max_iterations,
            "status": "starting",
            "errors": [],
        }

        # 1. PLANNER
        self._notify(progress_callback, "planner", "Decomposing topic into sub-questions...")
        updates = self.nodes.plan_node(state)
        state.update(updates)  # type: ignore

        # Iteration Loop
        while state["iteration_count"] < state["max_iterations"]:
            # 2. SEARCH
            self._notify(
                progress_callback,
                "search",
                f"Gathering evidence (Iteration {state['iteration_count'] + 1}/{state['max_iterations']})...",
            )
            updates = self.nodes.search_node(state)
            state.update(updates)  # type: ignore

            # 3. ANALYST
            self._notify(progress_callback, "analyst", "Synthesizing claims and cross-referencing contradictions...")
            updates = self.nodes.analyst_node(state)
            state.update(updates)  # type: ignore

            # 4. WRITER
            self._notify(progress_callback, "writer", "Drafting structured cited research report...")
            updates = self.nodes.writer_node(state)
            state.update(updates)  # type: ignore

            # 5. CRITIC
            self._notify(progress_callback, "critic", "Fact-checking claims and validating citation integrity...")
            updates = self.nodes.critic_node(state)
            state.update(updates)  # type: ignore

            next_step = should_continue_after_critic(state)
            if next_step == "end":
                self._notify(progress_callback, "complete", "Report verified and approved by Critic.")
                break
            elif next_step == "search":
                self._notify(progress_callback, "critic", "Critic flagged missing evidence. Executing targeted re-search...")
            elif next_step == "writer":
                self._notify(progress_callback, "critic", "Critic requested revision. Re-drafting sections...")

        if state.get("status") != "completed":
            state["status"] = "completed_with_limitations"
            self._notify(progress_callback, "complete", "Maximum iterations reached. Report compiled with limitations.")

        return state

    async def run(
        self,
        topic: str,
        scope: str = "comprehensive",
        max_iterations: int = 2,
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> ResearchState:
        """Async wrapper for research workflow execution."""
        return self.run_sync(topic, scope, max_iterations, progress_callback)

    def _notify(
        self, callback: Callable[[str, str], None] | None, agent_name: str, message: str
    ) -> None:
        if callback:
            try:
                callback(agent_name, message)
            except Exception:
                pass
