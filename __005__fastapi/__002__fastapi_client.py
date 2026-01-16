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
    # 发送 get 请求
    response = requests.get("http://localhost:8000/zhongyi_process", json=data)
    # 解析响应数据
    result_dict = response.json()
    return result_dict["output"]


if __name__ == '__main__':
    print(zhongyi_process("我今天吃什么"))
