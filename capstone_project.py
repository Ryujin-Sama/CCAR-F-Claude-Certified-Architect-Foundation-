import anthropic
import json
from datetime import datetime

# The client is the connection point to Anthropic's Messages API. Authentication
# is expected to be configured in the environment rather than stored in this file.
client = anthropic.Anthropic()
# Keep the model name in one place so every subagent uses the same model and the
# model can be changed without editing each API call individually.
MODEL = "claude-haiku-4-5"

# These dictionaries act as a small in-memory database for the demonstration.
# Customer IDs are the keys, while each value contains the fields returned by the
# customer lookup tool. A real application would replace this with a database.
FAKE_DB = {
    "C001":{"name":"Alex", "email":"alex@gmail.com", "plan":"elite"},
    "C002":{"name":"Bob", "email":"BobMarley@gmail.com","plan":"Gold"}
}

# Orders are also stored in memory. Each order links back to a customer through
# customer_id, which lets the refund subagent verify ownership before refunding.
FAKE_ORDERS = {
    "0100":{"customer_id":"C001", "item":"Iphone 16", "amount":100000.00, "status":"delivered"},
    "0101":{"customer_id":"C002", "item":"Pixel 7", "amount":150000.00, "status":"refunded"}
}

def get_customer(customer_id: str) -> dict:
    # Look up the requested customer. The first return handles the current data;
    # the second return documents the intended not-found response but is currently
    # unreachable because the function returns immediately above it.
    customer = FAKE_DB.get(customer_id)
    return{"Found":True, "customer_id": customer_id, **customer}
    return{"Found":False, "error":f"No Customer with the id{customer_id}"}

def lookup_order(order_id: str) -> dict:
    # Return a normalized result containing both the requested ID and the order
    # fields. Returning an explicit error object keeps tool responses predictable
    # for the language model when the order does not exist.
    order = FAKE_ORDERS.get(order_id)
    if order:
        return{"Found": True, "order_id":order_id, **order}
    return{"Found":False, "error":f"No Order with id {order_id}"}

def process_refund(order_id: str, amount: float) ->dict:
    # This function represents the side-effecting operation in the example.
    # Validate the order before issuing a refund, and reject duplicate refunds.
    order = FAKE_ORDERS.get(order_id)
    if not order:
        return {"Success": False, "error":"Order not found"}
    if order["status"] == "refunded":
        return {"Success" : False, "error" :"Order already refunded"}
    return {"Success": True, "refund_id": f"REF-{order_id}", "amount": amount}

# The model only knows tool names and schemas. This registry is the trusted local
# dispatch table that maps a tool name selected by the model to Python code.
TOOL_REGISTRY = {
    "get_customer": get_customer,
    "lookup_order": lookup_order,
    "process_refund": process_refund
}

# These JSON-compatible definitions tell Claude which tools are available, what
# each tool does, and exactly which arguments must be supplied in a tool call.
# The schemas are sent with every Messages API request made by the agent loop.
TOOLS = [
    {
        "name":"get_customer",
        "description":"Fetch customer record by customer ID. Return name, email and plan tier.",
        "input_schema": {
            "type":"object",
            "properties":{
                "customer_id":{"type":"string", "description":"Customer Id, e.g. C001" }
            },
            "required":["customer_id"]
        }
    },
    {
        "name":"lookup_order",
        "description":"Fetch order details by order ID. Returns item, amount, status, and linked Customer ID.",
        "input_schema": {
            "type":"object",
            "properties":{
                "order_id":{"type":"string", "description":"Order Id, e.g. 0100"}
            },
            "required":["order_id"]
        }
    },
    {
        "name":"process_refund",
        "description":"Issue a refund for an order. Only call this after verifying the customer exist and order belongs to them.",
        "input_schema": {
            "type":"object",
            "properties":{
                "order_id":{"type":"string"},
                "amount":{"type":"number", "description":"Amount to refund in INR"}
            },
            "required":["order_id", "amount"]
        }
    }
]

def run_agentic_loop(system_prompt: str, user_message: str, tools: list) -> str:
    # Messages API conversations are represented as an ordered list. The loop
    # starts with the user's task and appends assistant tool requests plus the
    # corresponding tool results until Claude produces a final text response.
    messages = [{"role" : "user", "content":user_message}]
    print(f"\n [LOOP] Starting. User: {user_message[:60]}....")

    while True:
        # Claude may either finish the task or request one or more tools. Supplying
        # the accumulated messages preserves the complete reasoning context across
        # multiple API round trips.
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        print(f" [LOOP] stop_reason = {response.stop_reason}")
        if response.stop_reason == "end_turn":
            # A final response can contain several content blocks. Select the
            # first block that exposes text and return it to the calling subagent.
            final_text = next((b.text for b in response.content if hasattr(b, "text")),"")
            print(f" [LOOP] Done. Response: {final_text[:80]}.....")
            return final_text

        if response.stop_reason == "tool_use":
            # Preserve Claude's tool-use message before sending results back. The
            # API requires the assistant request and user tool results to remain in
            # the conversation in this order.
            messages.append({"role":"assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # Execute only registered local functions. The model proposes
                    # the name and arguments, while this application performs the
                    # actual function call and serializes its result as JSON.
                    print(f" [TOOL] Calling {block.name}({block.input})")
                    result = TOOL_REGISTRY[block.name](**block.input)
                    print(f" [TOOL] Result: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id":block.id,
                        "content": json.dumps(result)
                    })

            messages.append({"role":"user", "content": tool_results})

def run_subagent(role: str, task_prompt: str, tools: list) -> dict:
    # A subagent is a focused agent with a role-specific prompt and a restricted
    # tool list. Restricting tools helps each subagent stay within its responsibility
    # instead of allowing every agent to perform every operation.
    print(f"\n SubAgent [{role}] starting...")
    # Extract a short human-readable task description for the system prompt. The
    # complete task_prompt is still passed to the agent loop unchanged below.
    job_desc = task_prompt.split('Task:')[-1].split('\n')[0].strip() if 'Task' in task_prompt else 'complete your assigned Task'
    system_prompt = f"""You are the {role} subagent in a customer support system.
    Your Job: {job_desc}
    Be Concise, Return factual results only. DO NOT make up data."""

    # Run the same reusable tool-calling loop with this subagent's instructions.
    result_text = run_agentic_loop(system_prompt, task_prompt, tools)

    # Return a structured finding so the coordinator can pass reliable context to
    # the next subagent and later include both results in the final summary.
    return {
        "subagent_role": role,
        "task" : task_prompt[:100],
        "result": result_text,
        "status":"complete"
    }

def coordinator(customer_id: str, order_id: str) -> str:
    # The coordinator owns the high-level workflow. It decomposes the case into
    # verification and refund tasks, passes the first finding forward, and then
    # combines both subagent responses for the caller.
    print("\n" + "="*60)
    print("COORDINATOR: Decomposing Task")
    print("="*60)

    # Verify the customer before allowing the refund workflow to proceed. This
    # subagent receives only the customer lookup tool.
    verification_task = f"""Task: Look up customer {customer_id} and confirm if they exist.
    Return their name and plan tier."""

    verification_finding = run_subagent(
        role="Customer Verifier",
        task_prompt=verification_task,
        tools=[TOOLS[0]]
    )

    # Make the first subagent's structured output visible and include it in the
    # second task as prior context rather than starting the refund analysis blind.
    print("\n [COORDINATOR] Passing structured finding to next subAgent:")
    print(f" {json.dumps(verification_finding, indent=2)}")

    # The refund subagent gets both order lookup and refund tools. Its instructions
    # require it to verify ownership before calling the side-effecting refund tool.
    refund_task = f"""Task : Process a refund for order {order_id}.
    PRIOR VERIFICATION (from Customer Verified subagent):
    {json.dumps(verification_finding, indent = 2)}
    
    Steps:
    1. Lookup the order.
    2. Confirm if it belongs to the customer {customer_id}
    3. If confirmed, process the refund for the order    
"""

    refund_finding = run_subagent(
        role="Refund processor",
        task_prompt=refund_task,
        tools=[TOOLS[1], TOOLS[2]]
    )

    # Present one human-readable result containing both independent findings.
    print("\n" + "="*60)
    print("COORDINATOR: Aggregating results")
    print("="*60)

    final_summary = f"""
    Customer support case resolved.
    Verification: {verification_finding['result']}
    Refund: {refund_finding['result']}
    """
    print(final_summary)
    return final_summary

if __name__ == "__main__":
    # Run the example only when this file is executed directly. Importing the file
    # elsewhere will define the tools and functions without starting an API call.
    print("""

Scenario: Customer C001 wants a refund for order 0100.
The coordinator will:
    1. Spawn a Customer Verified subagent
    2. Pass it's structured finding forward
    3. Spawn a refund Proceessor Subagent
    4. Aggregate the results

Each Subagent will run it's own agentic loop
""")

coordinator(customer_id="C001", order_id="0100")

print("\n Try changing customer_id to 'C999' to see error handling.")
print("\n Try order_id to '0101' to see 'already refunded' cases")