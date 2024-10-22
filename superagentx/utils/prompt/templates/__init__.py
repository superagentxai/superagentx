
REACT_TOOLS_INSTRUCTIONS = '''Answer the following questions as best you can. 

{role}

Use the following format: 
Intermediate Steps: Observe the question carefully and list out number of actions and its 
corresponding all tools [{tool_names}]. 

{format_instructions}

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat {max_repeat_times} times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
'''

# Initialize the engine's scratchpad (initial thoughts)
agent_scratchpad = ""
