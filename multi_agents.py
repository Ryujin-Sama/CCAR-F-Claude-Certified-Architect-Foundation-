# `coordinator_config` defines the coordinator agent's model, its
# system role prompt, available tool definitions, and which tools
# the coordinator is allowed to invoke. Use this dict as a template
# for setting up a coordinator that delegates work to specialized
# subagents (e.g., the `Task` tool below).
coordinator_config = {
    "model":"claude-haiku-4-5",
    "system":"""You are a research coordinator.
    Decompose tasks and delegate to specialized subagents.
    Specify research goals and quality criteria.
    Do NOT provide step-by-step procedures.""",

    "tools": [
        {
            "type":"task",
            "name":"Task",
        },
    ],
    "allowedTools":["Task", "compile_report"]
}

# Example payload for invoking a `Task` subagent. The `input` field
# contains a focused research prompt, allowed helper tools for the
# subagent, and the model to use. This shows how the coordinator
# would structure a `tool_use` call when delegating a single task.
task_tool_call = {
    "type": "tool_use",
    "id":"tu_web_search_001",
    "name": "Task",
    "input":{
        "description": "Web Search Specialist",

        "prompt": """Research goal: Find 5-8 recent papers (2022-2025)
        on offshore wind energy environmental impacts in the EU.
        Quality criteria: peer-reviewed, include key findings,
        flag conflicting conclusions. Return as structured JSON.""",

        "allowed_tools": ["web_search", "read_url"],

        "model":"claude-haiku-4-5"
    }
}

# Example coordinator assistant response demonstrating delegation.
# The `content` list mixes text and `tool_use` entries; each
# `tool_use` represents a request to spawn a specialized subagent
# (e.g., environmental, economic, policy researchers) with its own
# input payload. This structure is illustrative and can be adapted
# for orchestration frameworks that accept tool-based actions.
coordinator_response = {
    "role": "assistant",
    "content":[
        {"type": "text", "text": "Researching in parallel across 3 domains."}

        {"type": "tool_use", "id":"tu_env", "name":"Task",
         "input":{
            "description": "Environmental Researcher",...}},

        {"type": "tool_use", "id":"tu_econ", "name":"Task",
         "input":{
            "description": "Economic Data Researcher",...}},

        {"type": "tool_use", "id":"tu_policy", "name":"Task",
         "input":{
            "description": "EU Policy Analyst",...}},
    ]
}