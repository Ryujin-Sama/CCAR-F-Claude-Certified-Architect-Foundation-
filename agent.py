# Import the Anthropic client library so the script can communicate with Claude.
# The json module is used to format tool results as JSON strings.
# os is imported but not currently used in this script; it is left here for possible future expansion.
import anthropic
import json
import os

# Create a single Anthropic client instance that will be reused for all requests.
# This object handles authentication and request creation behind the scenes.
client = anthropic.Anthropic()

# Define the list of tools that the model may choose to call during its reasoning process.
# Each tool description helps Claude understand when it should use the tool.
tools = [
    {
        # The name of the tool as it will be referenced by the model.
        "name": "lookup_order",

        # A human-readable description of what the tool does and when to use it.
        "description": (
            "Look up an order by its ID."
            "Returns current status, estimated delivery date, and carrier name."
            "Use this when the customer asks where their order is or when it will arrive."
        ),

        # Define the expected input structure for the tool.
        # This helps the model generate valid arguments when it decides to call the tool.
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The numeric order ID (e.g., 123456)"
                }
            },
            "required": ["order_id"]
        }
    }
]

# This function acts as a bridge between the model's tool call and the actual implementation.
# It receives the tool name and the arguments supplied by Claude, then returns a result string.
def execute_tool(tool_name: str, tool_input: dict) -> str:
    # Handle the specific tool supported by this agent.
    if tool_name == "lookup_order":
        # Extract the order ID from the input dictionary.
        # If no value is provided, use an empty string as a safe default.
        order_id = tool_input.get("order_id", "")

        # Mock order data used for demonstration purposes.
        # In a real application, this data would come from a database or an external API.
        mock_orders = {
            "4821": {"status": "Shipped", "estimated_delivery": "2024-06-15", "carrier": "UPS"},
            "9910": {"status": "Delivered", "estimated_delivery": "2024-06-10", "carrier": "FedEx"}
        }

        # Simulate a database lookup by checking whether the provided order ID exists in the mock dataset.
        # In a production version, this section would query a real persistence layer.
        if order_id in mock_orders:
            return json.dumps(mock_orders[order_id])
        else:
            return json.dumps({"error": f"Order {order_id} not found."})

    # If the model requests a tool that is not implemented here, return a clear error message.
    return json.dumps({"error": f"Tool {tool_name} not recognized."})

# This is the main agent loop.
# It sends the user's message to Claude, allows the model to decide whether it needs a tool call,
# and then continues the conversation until either a final answer is produced or the loop limit is reached.
def run_agent(user_message: str) -> str:
    """
    Run the agentic loop until Claude provides a final answer.
    The agent can use the 'lookup_order' tool to answer user queries about their orders.
    Returns the final text response.
    """

    # Start the conversation with the user's message.
    # Each message object includes a role and the content supplied by that role.
    messages = [
        {"role": "user", "content": user_message}
    ]

    # Limit the number of iterations to prevent infinite loops.
    # This is a safety guard in case the model keeps requesting tools without reaching a final answer.
    MAX_ITERATIONS = 50
    iteration = 0

    # Repeat the loop until the maximum number of iterations is reached.
    while iteration < MAX_ITERATIONS:
        iteration += 1

        # Send the current conversation history to Claude.
        # The request includes the available tools so the model can decide whether to use them.
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        # If Claude finishes the turn normally, look for a text block in the response and return it.
        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        # If Claude decides to use a tool, append the assistant's message to the conversation history.
        # Then execute each requested tool and feed the result back to the model as a user message.
        if response.stop_reason == "tool_use":
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # Print a small log line to show which tool is being invoked.
                    print(f" -> Calling tool: {block.name}{{block.input}}")

                    # Execute the tool implementation and capture the returned JSON string.
                    result = execute_tool(block.name, block.input)

                    # Print the tool output for debugging and transparency.
                    print(f" -> Tool result: {result}")

                    # Store the tool result in a format expected by the Anthropic API.
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Send the tool results back to Claude so it can continue reasoning and produce the final answer.
            messages.append({
                "role": "user",
                "content": tool_results
            })

    # If the agent exceeds the allowed iterations without finishing, return an error message.
    return "Error: Agent did not complete within the maximum number of iterations."

# This block runs only when the file is executed directly as a script.
# It demonstrates the agent with a sample question about an order status.
if __name__ == "__main__":
    print("Running agent ....")
    answer = run_agent("Where is my order #4821?")
    print(f"\nFinal answer: {answer}")