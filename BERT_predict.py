import json
import websocket
import time
from transformers import BertTokenizer
from transformers import TFBertModel
from tensorflow.keras.models import load_model
import numpy as np

def send_text_via_websocket(url, text, time):
    # 设置要发送的JSON数据
    json_data = {
        "msg": 11000,
        "msgId": 0,
        "data": {
            "id": 0,
            "text": text,
            "textFrameColor": 0x000000,
            "textColor": 0xFFFFFF,
            "duration": time
        }
    }

    # 将JSON数据转换为字符串
    json_str = json.dumps(json_data)

    # 创建WebSocket连接
    ws = websocket.WebSocket()
    ws.connect(url)

    # 发送JSON数据
    ws.send(json_str)

    # 关闭WebSocket连接
    ws.close()

websocket_url = "ws://127.0.0.1:10086/api"
ws = websocket.WebSocket()
ws.connect(websocket_url)
send_text_via_websocket(websocket_url, "正在连接...", 10000)
# 加载.h5模型
model_path = 'BERT_12.h5'
model = load_model(model_path, custom_objects={'TFBertModel': TFBertModel})

# 加载tokenizer
vocab_path = 'chinese-pert-large/vocab.txt'
tokenizer = BertTokenizer.from_pretrained(vocab_path, do_lower_case=False)
#send_text_via_websocket(websocket_url, "连接成功！", 2000)
# 定义一个函数，将文本转化为BERT可识别的输入格式
def prep_data(text, max_length):
    encoded_input = tokenizer.encode_plus(text,
                                          add_special_tokens=True,
                                          max_length=max_length,
                                          padding='max_length',
                                          truncation=True,
                                          return_attention_mask=True,
                                          return_token_type_ids=False,
                                          return_tensors='tf')
    input_ids = np.array(encoded_input['input_ids'])
    attention_mask = np.array(encoded_input['attention_mask'])
    return input_ids, attention_mask

# 设置一个文本长度的上限
max_length = 32
previous_text = ""

while True:
    # 读取文件中的文本

        with open("E:/BERT/chatgpt.txt", "r") as file:
        current_text = file.readline().strip()

    current_text = input("请输入：")
    # 判断当前文本与上一次读取的文本是否相同
    if current_text != previous_text:
        previous_text = current_text

        # 创建WebSocket连接

        websocket_url = "ws://127.0.0.1:10086/api"
        ws = websocket.WebSocket()
        ws.connect(websocket_url)

        # 将文本转化为BERT的输入格式
        input_ids, attention_mask = prep_data(current_text, max_length)

        # 使用模型进行预测
        prediction = model.predict([input_ids, attention_mask])
        print("输出：", prediction)

        # 提取最大概率对应的类别
        max_index = np.argmax(prediction)
        output = None

        if max_index in [0, 1, 2] and prediction[0][max_index] > 0.55:
            output = max_index
        if max_index == 4 and prediction[0][max_index] > 0.55:
            output = 3
        if max_index == 5 and 0.55 < prediction[0][max_index] < 0.75:
            output = 4
        elif max_index == 5 and prediction[0][max_index] >= 0.75:
            output = 5

        # 输出结果
        if output is not None:
            print("输出：", output)

            # 发送WebSocket消息
            json_data = {
                "msg": 13300,
                "msgId": 1,
                "data": {
                    "id": 0,
                    "expId": int(output)  # 将output转换为整数类型
                }
            }
            json_str = json.dumps(json_data)
            ws.send(json_str)

            # 延时三秒后发送第二个WebSocket消息
            time.sleep(3)
            json_data2 = {
                "msg": 13302,
                "msgId": 1,
                "data": 0
            }
            json_str2 = json.dumps(json_data2)
            ws.send(json_str2)

        # 关闭WebSocket连接
        ws.close()

    # 延时0.1秒后继续读取文本进行判断
    time.sleep(0.1)
