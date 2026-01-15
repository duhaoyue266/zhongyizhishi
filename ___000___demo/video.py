from http import HTTPStatus
from dashscope import VideoSynthesis
import dashscope
import os

# 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：https://dashscope-intl.aliyuncs.com/api/v1
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

# 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
# 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
api_key = os.getenv("DASHSCOPE_API_KEY")

def sample_sync_call_t2v():
    # call sync api, will return the result
    print('please wait...')
    rsp = VideoSynthesis.call(api_key='sk-646ca50dc7d543baa1f2592cd6c799d1',
                              model='wan2.5-t2v-preview',
                              prompt='''夜晚，赛博朋克质感的洛杉矶中心城区，摩天楼间燃着橙红色大火，浓烟翻滚。
一位身穿 24 号紫金球衣、剪影极具辨识度的篮球战士，脚踏燃烧屋顶，左手提消防水带，右手抓篮球。
他后撤步跃起，在空中完成标志性的后仰跳投——篮球划出紫金火焰轨迹，穿越火浪，精准击中高空悬停的直升机水箱拉杆，“嘭”一声释放巨型水幕，火势瞬间被压成低伏蓝焰。
镜头高速环绕 360°，水花与火星交织成黑曼巴纹样的光影，最后定格在战士背对镜头、单手指天的剪影，背景只剩一轮月光与袅袅白烟。
超写实 8K，IMAX 全画幅，35 mm 胶片质感，HDR 高对比，冷蓝+紫金双色光源，体积光，慢动作 120 fps，鼓点心跳式音效，史诗级氛围。''',
                              audio_url='https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250923/hbiayh/%E4%BB%8E%E5%86%9B%E8%A1%8C.mp3',
                              size='832*480',
                              duration=10,
                              negative_prompt="",
                              prompt_extend=True,
                              watermark=False,
                              seed=12345)
    print(rsp)
    if rsp.status_code == HTTPStatus.OK:
        print(rsp.output.video_url)
    else:
        print('Failed, status_code: %s, code: %s, message: %s' %
              (rsp.status_code, rsp.code, rsp.message))


if __name__ == '__main__':
    sample_sync_call_t2v()