import streamlit as st
import requests


def zhongyi_process(input: str):
    """
    中义云处理函数
    :param input: 用户输入
    :return: 处理结果
    """
    # 构建请求数据
    data = {
        "input": input
    }
    # 发送 POST 请求
    response = requests.get("http://localhost:8000/zhongyi_process", json=data)
    # 解析响应数据
    result_dict = response.json()
    return result_dict["output"]


# 页面设置
st.set_page_config(page_title="中医对话机器人", page_icon="💬", layout="centered")
st.title("💬 中医对话机器人")
st.write("和智能机器人进行对话")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 展示历史消息
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# 输入框
if prompt := st.chat_input("请输入您的问题..."):
    # 显示用户消息
    with st.chat_message("user"):
        st.write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
    output = zhongyi_process(prompt)
    with st.chat_message("assistant"):
        st.markdown(output)
        st.session_state.messages.append({"role": "assistant", "content": output})
