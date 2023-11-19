from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import autogen
import asyncio
from autogen import UserProxyAgent
from autogen.agentchat.agent import Agent


config_list = autogen.config_list_from_models(
    model_list=["gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"], exclude="aoai"
)

llm_config = {
    "config_list": config_list,
}


class UserAgent(UserProxyAgent):
    def __init__(
        self,
        name,
        send_queue: asyncio.Queue,  
        receive_queue: asyncio.Queue,
        is_group_chat: bool = False,
        **kwargs,
    ):
        super().__init__(name, **kwargs)
        self.send_queue = send_queue
        self.receive_queue = receive_queue
        self.is_group_chat = is_group_chat

    def run_code(self, code, **kwargs):
        self.receive_queue.put_nowait(
            {"message": f"Running following code:\n```py\n{code}\n```\n"}
        )

        return super().run_code(code, **kwargs)


    async def a_get_human_input(self, prompt: str) -> str:
        if self.is_group_chat:
            await self.receive_queue.put({"message": prompt})
        else:
            await self.receive_queue.put({"message": prompt})
        try:
            input_content = await asyncio.wait_for(self.send_queue.get(), timeout=300)
            if input_content == "continue":
                return None
        except asyncio.TimeoutError:
            print("User didn't respond within 5 minutes, leaving chat.")
            return "exit"

        return input_content

    async def a_receive(
        self,
        message: Dict | str,
        sender: Agent,
        request_reply: bool | None = None,
        silent: bool | None = False,
    ):
        if self.is_group_chat:
            await self.receive_queue.put(
                {
                    "message": f"**➢➢➢{message['name']}**:\n{message['content']}\n",
                }
            )
        else:
            await self.receive_queue.put({"message": message})
        return await super().a_receive(message, sender, request_reply, silent)


def agents(send_queue, receive_queue):
    user_proxy = UserAgent(
        name="user_proxy",
        code_execution_config={"work_dir": "coding"},
        receive_queue=receive_queue,
        send_queue=send_queue,
    )

    assistant = autogen.AssistantAgent(
        name="assistant",
        llm_config={"config_list": config_list},
    )

    return user_proxy, assistant


def group_agents(send_queue, receive_queue):
    user_proxy = UserAgent(
        name="user_proxy",
        system_message="A human admin.",
        code_execution_config={"last_n_messages": 3, "work_dir": "group"},
        receive_queue=receive_queue,
        send_queue=send_queue,
        is_group_chat=True,
    )

    assistant = autogen.AssistantAgent(
        name="coder",
        llm_config={"config_list": config_list},
    )

    critic = autogen.AssistantAgent(
        name="Critic",
        system_message="""Critic. You are a helpful assistant highly skilled in evaluating the quality of a given visualization code by providing a score from 1 (bad) - 10 (good) while providing clear rationale. YOU MUST CONSIDER VISUALIZATION BEST PRACTICES for each evaluation. Specifically, you can carefully evaluate the code across the following dimensions
- bugs (bugs):  are there bugs, logic errors, syntax error or typos? Are there any reasons why the code may fail to compile? How should it be fixed? If ANY bug exists, the bug score MUST be less than 5.
- Data transformation (transformation): Is the data transformed appropriately for the visualization type? E.g., is the dataset appropriated filtered, aggregated, or grouped  if needed? If a date field is used, is the date field first converted to a date object etc?
- Goal compliance (compliance): how well the code meets the specified visualization goals?
- Visualization type (type): CONSIDERING BEST PRACTICES, is the visualization type appropriate for the data and intent? Is there a visualization type that would be more effective in conveying insights? If a different visualization type is more appropriate, the score MUST BE LESS THAN 5 and never use plt.show().
- Data encoding (encoding): Is the data encoded appropriately for the visualization type?
- aesthetics (aesthetics): Are the aesthetics of the visualization appropriate for the visualization type and the data?

YOU MUST PROVIDE A SCORE for each of the above dimensions.
{bugs: 0, transformation: 0, compliance: 0, type: 0, encoding: 0, aesthetics: 0}
Do not suggest code. 
Finally, based on the critique above, suggest a concrete list of actions that the coder should take to improve the code.
""",
        llm_config=llm_config,
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, assistant, critic], messages=[], max_round=20
    )

    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    return user_proxy, manager
