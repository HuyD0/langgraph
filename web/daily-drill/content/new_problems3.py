"""Agents-on-Databricks exercises."""
import json
P = []
def add(**k): P.append(k)

add(id="tool_schema", title="Describe a Tool for the Model", topic="agents", difficulty="medium", fn="tool_schema",
 prompt="A model can only call a tool it has been told about. Turn a Unity Catalog function into the tool description that chat models read.\n\nYou get the function's `name`, its `description`, and `params`, a list of `[name, sql_type, comment]` like `[\"order_id\", \"STRING\", \"The order number\"]`. Map SQL types to JSON types: `STRING` → `\"string\"`, `INT` and `BIGINT` → `\"integer\"`, `DOUBLE` and `FLOAT` → `\"number\"`, `BOOLEAN` → `\"boolean\"`.\n\nReturn `{\"type\": \"function\", \"function\": {\"name\": ..., \"description\": ..., \"parameters\": {\"type\": \"object\", \"properties\": {...}, \"required\": [...]}}}`, where each property is `{\"type\": json_type, \"description\": comment}` and every parameter is required, in order.",
 pattern="A lookup table for the type mapping, then build a nested dict one level at a time.",
 target="one step per parameter",
 realworld="`UCFunctionToolkit` in `databricks_langchain` builds exactly this from a function in Unity Catalog, using the function's and parameters' comments as the descriptions. Vague comments make the model call the wrong tool or pass bad arguments, so the comment is part of your prompt.",
 starter="def tool_schema(name, description, params):\n    # your code here\n    pass\n",
 solution="TYPES = {\"STRING\": \"string\", \"INT\": \"integer\", \"BIGINT\": \"integer\", \"DOUBLE\": \"number\", \"FLOAT\": \"number\", \"BOOLEAN\": \"boolean\"}\n\ndef tool_schema(name, description, params):\n    properties = {}\n    required = []\n    for pname, sql_type, comment in params:\n        properties[pname] = {\"type\": TYPES[sql_type], \"description\": comment}\n        required.append(pname)\n    return {\"type\": \"function\", \"function\": {\"name\": name, \"description\": description,\n            \"parameters\": {\"type\": \"object\", \"properties\": properties, \"required\": required}}}\n",
 cases=[("lookup_order", "Look up an order's status and delivery date", [["order_id", "STRING", "The order number, like A-1042"]],
         {"type": "function", "function": {"name": "lookup_order", "description": "Look up an order's status and delivery date", "parameters": {"type": "object", "properties": {"order_id": {"type": "string", "description": "The order number, like A-1042"}}, "required": ["order_id"]}}}, True),
        ("ping", "Check the service is up", [], {"type": "function", "function": {"name": "ping", "description": "Check the service is up", "parameters": {"type": "object", "properties": {}, "required": []}}}),
        ("refund", "Refund part of an order", [["order_id", "STRING", "Order number"], ["amount", "DOUBLE", "Dollars to refund"], ["notify", "BOOLEAN", "Email the customer"], ["reason_code", "INT", "1 damaged, 2 late"]],
         {"type": "function", "function": {"name": "refund", "description": "Refund part of an order", "parameters": {"type": "object", "properties": {"order_id": {"type": "string", "description": "Order number"}, "amount": {"type": "number", "description": "Dollars to refund"}, "notify": {"type": "boolean", "description": "Email the customer"}, "reason_code": {"type": "integer", "description": "1 damaged, 2 late"}}, "required": ["order_id", "amount", "notify", "reason_code"]}}})],
 guided="TYPES = {\"STRING\": \"string\", \"INT\": \"integer\", \"BIGINT\": \"integer\", \"DOUBLE\": \"number\", \"FLOAT\": \"number\", \"BOOLEAN\": \"boolean\"}\n\ndef tool_schema(name, description, params):\n    # Replace every ___ with real code, then run the tests.\n\n    properties = {}\n    required = []\n    for pname, sql_type, comment in params:\n        # Step 1: describe this parameter, using the TYPES lookup.\n        properties[pname] = {\"type\": ___, \"description\": comment}\n        # Step 2: every parameter is required.\n        ___\n    # Step 3: wrap it up in the shape models expect.\n    return {\"type\": \"function\", \"function\": {\"name\": name, \"description\": description,\n            \"parameters\": {\"type\": \"object\", \"properties\": properties, \"required\": required}}}\n",
 fills=["TYPES[sql_type]", "required.append(pname)"],
 learn=dict(concepts=[["A lookup table", "A dict that translates one name into another.", "TYPES = {'STRING': 'string'}\nTYPES['STRING']   # 'string'"], ["Unpacking three values", "Each param is a list of three, so the for line can name all three.", "for pname, sql_type, comment in params:\n    ..."]],
  byhand="One parameter: order_id, STRING, \"The order number\". Its property is {\"type\": \"string\", \"description\": \"The order number\"} and required is [\"order_id\"]. Wrap that in parameters, then in function, then add type \"function\" at the top.",
  why="One step per parameter.",
  gotchas=[["The comment is the prompt", "\"id\" tells the model nothing. \"The order number, like A-1042\" tells it the format, and fewer calls fail."], ["Give the agent least privilege", "A Unity Catalog function runs with the permissions it's granted. Grant the agent EXECUTE on the few functions it needs, not on a whole schema."]]))

add(id="route_request", title="Canary a New Agent Version", topic="shipping", difficulty="easy", fn="route_request",
 prompt="A serving endpoint can split traffic between versions: for example 90% to the current agent and 10% to the new one. `routes` is a list like `[{\"served_entity_name\": \"support_agent-3\", \"traffic_percentage\": 90}, {\"served_entity_name\": \"support_agent-4\", \"traffic_percentage\": 10}]`.\n\nGiven a numeric `request_id`, put it in a bucket from 0 to 99 with `request_id % 100`, then walk the routes in order adding up percentages: the first route whose running total is greater than the bucket gets the request. Return its `served_entity_name`. If the percentages don't add up to 100, return `None`.",
 pattern="Running total over a list: find the first point where the total passes the target.",
 target="one walk through the routes",
 realworld="Canary releases: send a small share of real traffic to the new agent version, watch its traces and evals, then move the split to 100% or back to 0%. On Databricks this is the endpoint's `traffic_config`.",
 starter="def route_request(routes, request_id):\n    # your code here\n    pass\n",
 solution="def route_request(routes, request_id):\n    if sum(r[\"traffic_percentage\"] for r in routes) != 100:\n        return None\n    bucket = request_id % 100\n    total = 0\n    for r in routes:\n        total += r[\"traffic_percentage\"]\n        if bucket < total:\n            return r[\"served_entity_name\"]\n    return None\n",
 cases=[([{"served_entity_name": "support_agent-3", "traffic_percentage": 90}, {"served_entity_name": "support_agent-4", "traffic_percentage": 10}], 1093, "support_agent-4", True),
        ([{"served_entity_name": "support_agent-3", "traffic_percentage": 90}, {"served_entity_name": "support_agent-4", "traffic_percentage": 10}], 1089, "support_agent-3"),
        ([{"served_entity_name": "a-1", "traffic_percentage": 100}], 57, "a-1"),
        ([{"served_entity_name": "a-1", "traffic_percentage": 50}, {"served_entity_name": "a-2", "traffic_percentage": 30}], 5, None),
        ([{"served_entity_name": "a-1", "traffic_percentage": 0}, {"served_entity_name": "a-2", "traffic_percentage": 100}], 0, "a-2"),
        ([], 3, None)],
 guided="def route_request(routes, request_id):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: the split must add up to 100.\n    if sum(r[\"traffic_percentage\"] for r in routes) != 100:\n        return None\n    # Step 2: a bucket from 0 to 99.\n    bucket = ___\n    total = 0\n    for r in routes:\n        total += r[\"traffic_percentage\"]\n        # Step 3: the first route whose running total passes the bucket.\n        if ___:\n            return r[\"served_entity_name\"]\n    return None\n",
 fills=["request_id % 100", "bucket < total"],
 learn=dict(concepts=[["sum over a list of dicts", "`sum(x for x in ...)` adds up values picked from each item.", "sum(r['traffic_percentage'] for r in routes)"], ["The remainder, %", "`1093 % 100` is 93: the last two digits.", "1093 % 100   # 93"]],
  byhand="Request 1093 lands in bucket 93. Version 3 covers buckets 0–89 (running total 90): 93 isn't below 90. Version 4 brings the total to 100: 93 is below 100, so version 4 gets it.",
  why="One walk through the routes.",
  gotchas=[["Same user, same version", "Bucket by a stable id (user or conversation), not a random number, so one person doesn't bounce between versions mid-conversation."], ["Canary needs a stop rule", "Decide in advance what makes you roll back: error rate, p95 latency, judge scores on canary traces. Then watch for it."]]))

def check():
    for p in P:
        for variant in ("solution", "guided"):
            code = p["solution"] if variant == "solution" else p["guided"].replace("# Replace every ___ with real code, then run the tests.", "#")
            if variant == "guided":
                for f in p["fills"]:
                    assert "___" in code, (p["id"], "too many fills"); code = code.replace("___", f, 1)
                assert "___" not in code, (p["id"], "unfilled")
            ns = {}; exec(code, ns); fn = ns[p["fn"]]
            for c in p["cases"]:
                sample = c[-1] is True
                body = c[:-1] if sample else c
                args, exp = list(body[:-1]), body[-1]
                got = fn(*json.loads(json.dumps(args)))
                assert got == exp, (p["id"], variant, args, exp, got)
    print("verified", len(P), "agent problems")
if __name__ == "__main__":
    check()
