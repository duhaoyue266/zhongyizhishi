from pathlib import Path
import sys

from fastapi import FastAPI

# # 将项目根目录加入 sys.path，确保可以导入兄弟包 __004__langgraph
# ROOT_DIR = Path(__file__).resolve().parent.parent
# if str(ROOT_DIR) not in sys.path:
#     sys.path.insert(0, str(ROOT_DIR))

from __004__langgraph.langgraph_more_nodes import zhongyi_response

app = FastAPI()


@app.get("/zhongyi_process")
async def zhongyi_process(data: dict):
    input = data.get("input", "")
    output = zhongyi_response(input)
    data["output"] = output
    return data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
