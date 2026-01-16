from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from common.config import Config

conf = Config()

# ============ 配置llm区域 ============
my_llm = ChatOpenAI(
    api_key="",
    base_url="https://99b0a2d64a44455f9d382aebd8894519--8000.ap-shanghai2.cloudstudio.club/v1/",
    model="Qwen/Qwen2.5-1.5B-Instruct/"
)

if __name__ == '__main__':
    # response = my_llm.invoke("介绍一下中国历史。")
    # print(response.content)

    for chunk in my_llm.stream("介绍一下中国历史。"):
        print(chunk.content, end="", flush=True)