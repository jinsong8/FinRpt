import os
from datetime import datetime
from typing import Callable, Dict, Literal, Optional, Union

from typing_extensions import Annotated

import autogen
from autogen import (
    Agent,
    AssistantAgent,
    ConversableAgent,
    GroupChat,
    GroupChatManager,
    UserProxyAgent,
    config_list_from_json,
    register_function,
)
from autogen.agentchat.contrib import agent_builder
from autogen.cache import Cache
from autogen.coding import DockerCommandLineCodeExecutor, LocalCommandLineCodeExecutor

config_list = autogen.config_list_from_json(env_or_file="OAI_CONFIG_LIST")
# # You can also use the following method to load the config list from a file or environment variable.
# # config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")


task = (
    f"Today is {datetime.now().date()}. Write a blogpost about the stock price performance of Nvidia in the past month."
)
print(task)


# # Create planner agent.
# planner = AssistantAgent(
#     name="planner",
#     llm_config={
#         "config_list": config_list,
#         "cache_seed": None,  # Disable legacy cache.
#     },
#     system_message="You are a helpful AI assistant. You suggest a feasible plan "
#     "for finishing a complex task by decomposing it into 3-5 sub-tasks. "
#     "If the plan is not good, suggest a better plan. "
#     "If the execution is wrong, analyze the error and suggest a fix.",
# )

# # Create a planner user agent used to interact with the planner.
# planner_user = UserProxyAgent(
#     name="planner_user",
#     human_input_mode="NEVER",
#     code_execution_config=False,
# )

# # The function for asking the planner.


# def task_planner(question: Annotated[str, "Question to ask the planner."]) -> str:
#     with Cache.disk(cache_seed=4) as cache:
#         planner_user.initiate_chat(planner, message=question, max_turns=1, cache=cache)
#     # return the last message received from the planner
#     return planner_user.last_message()["content"]


# # Create assistant agent.
# assistant = AssistantAgent(
#     name="assistant",
#     system_message="You are a helpful AI assistant. "
#     "You can use the task planner to decompose a complex task into sub-tasks. "
#     "Make sure your follow through the sub-tasks. "
#     "When needed, write Python code in markdown blocks, and I will execute them."
#     "Give the user a final solution at the end. "
#     "Return TERMINATE only if the sub-tasks are completed.",
#     llm_config={
#         "config_list": config_list,
#         "cache_seed": None,  # Disable legacy cache.
#     },
# )

# # Setting up code executor.
# os.makedirs("planning", exist_ok=True)
# # Use DockerCommandLineCodeExecutor to run code in a docker container.
# # code_executor = DockerCommandLineCodeExecutor(work_dir="planning")
# code_executor = LocalCommandLineCodeExecutor(work_dir="planning")

# # Create user proxy agent used to interact with the assistant.
# user_proxy = UserProxyAgent(
#     name="user_proxy",
#     human_input_mode="ALWAYS",
#     is_termination_msg=lambda x: "content" in x
#     and x["content"] is not None
#     and x["content"].rstrip().endswith("TERMINATE"),
#     code_execution_config={"executor": code_executor},
# )

# # Register the function to the agent pair.
# register_function(
#     task_planner,
#     caller=assistant,
#     executor=user_proxy,
#     name="task_planner",
#     description="A task planner than can help you with decomposing a complex task into sub-tasks.",
# )


# # Use Cache.disk to cache LLM responses. Change cache_seed for different responses.
# with Cache.disk(cache_seed=1) as cache:
#     # the assistant receives a message from the user, which contains the task description
#     user_proxy.initiate_chat(
#         assistant,
#         message=task,
#         cache=cache,
#     )


user_proxy = UserProxyAgent(
    name="Admin",
    system_message="A human admin. Give the task, and send instructions to writer to refine the blog post.",
    code_execution_config=False,
)

planner = AssistantAgent(
    name="Planner",
    system_message="""Planner. Given a task, please determine what information is needed to complete the task.
Please note that the information will all be retrieved using Python code. Please only suggest information that can be retrieved using Python code.
""",
    llm_config={"config_list": config_list, "cache_seed": None},
)

engineer = AssistantAgent(
    name="Engineer",
    llm_config={"config_list": config_list, "cache_seed": None},
    system_message="""Engineer. You write python/bash to retrieve relevant information. Wrap the code in a code block that specifies the script type. The user can't modify your code. So do not suggest incomplete code which requires others to modify. Don't use a code block if it's not intended to be executed by the executor.
Don't include multiple code blocks in one response. Do not ask others to copy and paste the result. Check the execution result returned by the executor.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
""",
)

writer = AssistantAgent(
    name="Writer",
    llm_config={"config_list": config_list, "cache_seed": None},
    system_message="""Writer. Please write blogs in markdown format (with relevant titles) and put the content in pseudo ```md``` code block. You will write it for a task based on previous chat history. Don't write any code.""",
)

os.makedirs("paper", exist_ok=True)
code_executor = UserProxyAgent(
    name="Executor",
    system_message="Executor. Execute the code written by the engineer and report the result.",
    description="Executor should always be called after the engineer has written code to be executed.",
    human_input_mode="ALWAYS",
    code_execution_config={
        "last_n_messages": 3,
        "executor": LocalCommandLineCodeExecutor(work_dir="paper"),
    },
)

groupchat = GroupChat(
    agents=[user_proxy, engineer, code_executor, writer, planner],
    messages=[],
    max_round=20,
    speaker_selection_method="auto",
)
manager = GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list, "cache_seed": None})

# Use Cache.disk to cache LLM responses. Change cache_seed for different responses.
with Cache.disk(cache_seed=41) as cache:
    chat_history = user_proxy.initiate_chat(
        manager,
        message=task,
        cache=cache,
    )


# user_proxy = UserProxyAgent(
#     name="Admin",
#     system_message="A human admin. Give the task, and send instructions to writer to refine the blog post.",
#     code_execution_config=False,
# )

# planner = AssistantAgent(
#     name="Planner",
#     system_message="""Planner. Given a task, please determine what information is needed to complete the task.
# Please note that the information will all be retrieved using Python code. Please only suggest information that can be retrieved using Python code.
# """,
#     llm_config={"config_list": config_list, "cache_seed": None},
# )

# engineer = AssistantAgent(
#     name="Engineer",
#     llm_config={"config_list": config_list, "cache_seed": None},
#     system_message="""Engineer. You write python/bash to retrieve relevant information. Wrap the code in a code block that specifies the script type. The user can't modify your code. So do not suggest incomplete code which requires others to modify. Don't use a code block if it's not intended to be executed by the executor.
# Don't include multiple code blocks in one response. Do not ask others to copy and paste the result. Check the execution result returned by the executor.
# If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
# """,
# )

# writer = AssistantAgent(
#     name="Writer",
#     llm_config={"config_list": config_list, "cache_seed": None},
#     system_message="""Writer. Please write blogs in markdown format (with relevant titles) and put the content in pseudo ```md``` code block. You will write it for a task based on previous chat history. """,
# )

# code_executor = UserProxyAgent(
#     name="Executor",
#     system_message="Executor. Execute the code written by the engineer and report the result.",
#     human_input_mode="ALWAYS",
#     code_execution_config={
#         "last_n_messages": 3,
#         "executor": LocalCommandLineCodeExecutor(work_dir="paper"),
#     },
# )


# def custom_speaker_selection_func(last_speaker: Agent, groupchat: GroupChat):
#     """Define a customized speaker selection function.
#     A recommended way is to define a transition for each speaker in the groupchat.

#     Returns:
#         Return an `Agent` class or a string from ['auto', 'manual', 'random', 'round_robin'] to select a default method to use.
#     """
#     messages = groupchat.messages

#     if len(messages) <= 1:
#         # first, let the engineer retrieve relevant data
#         return planner

#     if last_speaker is planner:
#         # if the last message is from planner, let the engineer to write code
#         return engineer
#     elif last_speaker is user_proxy:
#         if messages[-1]["content"].strip() != "":
#             # If the last message is from user and is not empty, let the writer to continue
#             return writer

#     elif last_speaker is engineer:
#         if "```python" in messages[-1]["content"]:
#             # If the last message is a python code block, let the executor to speak
#             return code_executor
#         else:
#             # Otherwise, let the engineer to continue
#             return engineer

#     elif last_speaker is code_executor:
#         if "exitcode: 1" in messages[-1]["content"]:
#             # If the last message indicates an error, let the engineer to improve the code
#             return engineer
#         else:
#             # Otherwise, let the writer to speak
#             return writer

#     elif last_speaker is writer:
#         # Always let the user to speak after the writer
#         return user_proxy

#     else:
#         # default to auto speaker selection method
#         return "auto"


# groupchat = GroupChat(
#     agents=[user_proxy, engineer, writer, code_executor, planner],
#     messages=[],
#     max_round=20,
#     speaker_selection_method=custom_speaker_selection_func,
# )
# manager = GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list, "cache_seed": None})

# with Cache.disk(cache_seed=41) as cache:
#     groupchat_history_custom = user_proxy.initiate_chat(
#         manager,
#         message=task,
#         cache=cache,
#     )


# # Setting up code executor.
# os.makedirs("coding", exist_ok=True)
# code_executor = LocalCommandLineCodeExecutor(work_dir="coding")


# def run_meta_prompting(expert_name: str, expert_identity: str, task: str) -> str:
#     """
#     Run Meta-prompting to solve the task.
#     The method is adapted from "Meta-Prompting: Enhancing Language Models with Task-Agnostic Scaffolding".
#     Paper available at https://arxiv.org/abs/2401.12954
#     """
#     print("Running meta prompting...")
#     print("Querying expert: ", expert_name)

#     expert = AssistantAgent(
#         name=expert_name,
#         human_input_mode="NEVER",
#         llm_config={"config_list": config_list, "cache_seed": None},
#         system_message='You are an AI assistant that helps people find information. Please answer the following question. Once you have determined the final answer, please present it using the format below:\n\n>> FINAL ANSWER:\n"""\n[final answer]\n"""',
#         max_consecutive_auto_reply=1,
#     )

#     user_proxy = UserProxyAgent(
#         name="proxy",
#         human_input_mode="NEVER",
#         default_auto_reply="TERMINATE",
#         code_execution_config={"executor": code_executor},
#         max_consecutive_auto_reply=1,
#     )
#     task += "\nYou have access to python code interpreter. Suggest python code block starting with '```python' and the code will be automatically executed. You can use code to solve the task or for result verification. You should always use print statement to get the value of a variable."
#     user_proxy.initiate_chat(expert, message=expert_identity + "\n" + task, silent=True)

#     expert_reply = user_proxy.chat_messages[expert][1]["content"]
#     proxy_reply = user_proxy.chat_messages[expert][2]["content"]

#     if proxy_reply != "TERMINATE":
#         code_result = proxy_reply[proxy_reply.find("Code output:") + len("Code output:") :].strip()
#         expert_reply += f"\nThis is the output of the code blocks when executed:\n{code_result}"
#     else:
#         expert_reply.replace(
#             "FINAL ANSWER:",
#             f"{expert_name}'s final answer:\n",
#         )

#     return expert_reply


# class MetaAgent(ConversableAgent):
#     SYSTEM_MESSAGE = """You are Meta-Expert, an extremely clever expert with the unique ability to collaborate with multiple experts (such as Expert Problem Solver, Expert Mathematician, Expert Essayist, etc.) to tackle any task and solve any complex problems. Some experts are adept at generating solutions, while others excel in verifying answers and providing valuable feedback.
# As Meta-Expert, your role is to oversee the communication between the experts, effectively using their skills to answer a given question while applying your own critical thinking and verification abilities.
# To communicate with a expert, call function "meta_prompting" with the expert's name, identity information and the task that needs to be solved. The function will return a response from the expert.
# Ensure that your instructions are clear and unambiguous, and include all necessary information within the triple quotes. You should assign personas to the experts (e.g., "You are a physicist specialized in...").
# You can interact with only one expert at a time, and break complex problems into smaller, solvable tasks. Each interaction is treated as an isolated event, so include all relevant details in every call.
# Refrain from repeating the very same questions to experts. Examine their responses carefully and seek clarification if required, keeping in mind they don't recall past interactions.
# Upon the completion of all tasks and verifications, you should conclude the result and reply "TERMINATE".
# """
#     TOOL = {
#         "type": "function",
#         "function": {
#             "name": "meta_prompting",
#             "description": "Solve a task by querying an expert. Provide the expert identity and the task that needs to be solved, and the function will return the response of the expert.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "task": {
#                         "type": "string",
#                         "description": "[REQUIRED] The task that needs to be solved by the expert.",
#                     },
#                     "expert_name": {
#                         "type": "string",
#                         "description": "[REQUIRED] Name of the expert. Should follow the format: Expert xxx.",
#                     },
#                     "expert_identity": {
#                         "type": "string",
#                         "description": "[REQUIRED] A high-quality description about the most capable and suitable expert to answer the instruction. In second person perspective. For example, You are a linguist, well-versed in the study of language and its structures. You are equipped with a good understanding of grammar rules and can differentiate between nouns, verbs, adjectives, adverbs, etc. You can quickly and accurately identify the parts of speech in a sentence and explain the role of each word in the sentence. Your expertise in language and grammar is highly valuable in analyzing and understanding the nuances of communication.",
#                     },
#                 },
#             },
#         },
#     }

#     def __init__(
#         self,
#         name: str,
#         system_message: Optional[str] = None,
#         llm_config: Optional[Union[Dict, Literal[False]]] = None,
#         is_termination_msg: Optional[Callable[[Dict], bool]] = None,
#         max_consecutive_auto_reply: Optional[int] = None,
#         human_input_mode: Literal["ALWAYS", "NEVER", "TERMINATE"] = "NEVER",
#         code_execution_config: Optional[Union[Dict, Literal[False]]] = False,
#         description: Optional[
#             str
#         ] = "A helpful AI assistant that can build a group of agents at a proper time to solve a task.",
#         **kwargs,
#     ):
#         super().__init__(
#             name=name,
#             system_message=self.SYSTEM_MESSAGE,
#             llm_config=llm_config,
#             is_termination_msg=is_termination_msg,
#             max_consecutive_auto_reply=max_consecutive_auto_reply,
#             human_input_mode=human_input_mode,
#             code_execution_config=code_execution_config,
#             description=description,
#             **kwargs,
#         )
#         self.update_tool_signature(self.TOOL, is_remove=False)


# proxy = UserProxyAgent(
#     name="proxy",
#     human_input_mode="NEVER",
#     code_execution_config=False,
#     max_consecutive_auto_reply=1,
#     default_auto_reply="Continue. If you think the task is solved, please reply me only with 'TERMINATE'.",
# )
# proxy.register_function(function_map={"meta_prompting": lambda **args: run_meta_prompting(**args)})

# agent = MetaAgent(
#     name="Meta-Expert",
#     llm_config={"config_list": config_list, "cache_seed": None},
#     human_input_mode="NEVER",
#     max_consecutive_auto_reply=15,
# )

# with Cache.disk(cache_seed=41) as cache:
#     proxy.initiate_chat(agent, message=task, cache=cache)