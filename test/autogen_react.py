import os
from typing import Annotated

from tavily import TavilyClient

from autogen import AssistantAgent, UserProxyAgent, config_list_from_json, register_function
from autogen.agentchat.contrib.capabilities import teachability
from autogen.cache import Cache
from autogen.coding import DockerCommandLineCodeExecutor, LocalCommandLineCodeExecutor

config_list = [
    {"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]},
    {"model": "gpt-3.5-turbo", "api_key": os.environ["OPENAI_API_KEY"]},
]
# You can also use the following method to load the config list from a file or environment variable.
# config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")
# local_llm_config = {
#     "config_list": [
#         {
#             "model": "llama3.2",  # Loaded with LiteLLM command
#             "api_key": "NotRequired",  # Not needed
#             "base_url": "http://0.0.0.0:4000",  # Your LiteLLM URL
#             "price": [0, 0],  # Put in price per 1K tokens [prompt, response] as free!
#         }
#     ],
#     "cache_seed": None,  # Turns off caching, useful for testing different models
# }


local_llm_config = {
    "config_list": [
        {
            "api_type": "ollama",
            "model": "llama3.2",
            "client_host": "http://0.0.0.0:11434",
        }
    ],
    "cache_seed": None,  # Turns off caching, useful for testing different models
}


tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def search_tool(query: Annotated[str, "The search query"]) -> Annotated[str, "The search results"]:
    return tavily.get_search_context(query=query, search_depth="advanced")


# NOTE: this ReAct prompt is adapted from Langchain's ReAct agent: https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/agents/react/agent.py#L79
ReAct_prompt = """
Answer the following questions as best you can. You have access to tools provided.

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take
Action Input: the input to the action
Observation: the result of the action
... (this process can repeat multiple times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
Question: {input}
"""

# Define the ReAct prompt message. Assuming a "question" field is present in the context


def react_prompt_message(sender, recipient, context):
    return ReAct_prompt.format(input=context["question"])


# Setting up code executor.
os.makedirs("coding", exist_ok=True)
# Use docker executor for running code in a container if you have docker installed.
# code_executor = DockerCommandLineCodeExecutor(work_dir="coding")
code_executor = LocalCommandLineCodeExecutor(work_dir="coding")

user_proxy = UserProxyAgent(
    name="User",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=10,
    code_execution_config={"executor": code_executor},
)

assistant = AssistantAgent(
    name="Assistant",
    system_message="Only use the tools you have been provided with. Reply TERMINATE when the task is done.",
    llm_config=local_llm_config,
)

# Register the search tool.
register_function(
    search_tool,
    caller=assistant,
    executor=user_proxy,
    name="search_tool",
    description="Search the web for the given query",
)

# Cache LLM responses. To get different responses, change the cache_seed value.
with Cache.disk(cache_seed=43) as cache:
    result = user_proxy.initiate_chat(
        assistant,
        message=react_prompt_message,
        question="What is the result of super bowl 2024?",
        cache=cache,
    )
    print(result.chat_history)