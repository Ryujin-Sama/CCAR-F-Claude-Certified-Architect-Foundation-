# Let the model decide which available tool best fits the request.
tool_choice = {"type" : "auto"}

# Explicitly select a tool instead of relying on automatic tool selection.
# This assignment replaces the previous value, so `lookup_order` is the
# effective configuration used by the rest of the example.
tool_choice = {"type" : "tool", "name" : "lookup_order"}