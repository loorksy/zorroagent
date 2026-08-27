"""B3.6 execution: saved rec required; chat cannot include execute tool; tables split."""

from app.agent.runtime import ANALYSIS_TOOL_NAMES, tool_specs
from app.bots.loop import execution_table_for
from app.db.models import DemoExecution, Execution, Recommendation


def test_execute_not_an_agent_tool():
    names = [t["name"] for t in tool_specs()]
    assert "execute" not in names
    assert all("execut" not in n.lower() for n in ANALYSIS_TOOL_NAMES)


def test_execution_table_is_not_recommendation_table():
    assert Execution.__tablename__ == "executions"
    assert DemoExecution.__tablename__ == "demo_executions"
    assert Recommendation.__tablename__ == "recommendations"
    assert Execution.__tablename__ != Recommendation.__tablename__
    assert execution_table_for("demo") != execution_table_for("live")
