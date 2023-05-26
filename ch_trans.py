# -*- coding: utf-8 -*-

import subprocess
import os
import glob
import time
import asyncio
import edge_tts
import logging
from inference.infer_tool import Svc
import io
import numpy as np
import soundfile
from pathlib import Path
from inference import infer_tool
from inference import slicer
import datetime
import openai
import time
from pydub import AudioSegment
import threading
# 导入 tkinter 和 ttk
import tkinter as tk
from tkinter import ttk
import websocket
import json
import yaml
import codecs


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
def send_motion_via_websocket(url, interval, total_triggers):
    # 设置要发送的JSON数据
    json_data1 = {
        "msg": 13200,
        "msgId": 1,
        "data": {
            "id": 0,
            "type": 0,
            "mtn": "speak:open"
        }
    }
    # 将JSON数据转换为字符串
    json_str1 = json.dumps(json_data1)

    # 创建WebSocket连接
    ws = websocket.WebSocket()
    ws.connect(url)
    # 发送JSON数据多次
    for _ in range(int(total_triggers)):
        # 发送JSON数据
        ws.send(json_str1)
        # 等待指定的时间间隔
        time.sleep(interval)
    # 关闭WebSocket连接
    ws.close()

def get_input_from_gui(prompt_message):
    # 创建一个新窗口
    win = tk.Tk()
    win.geometry('270x120')  # 设置窗口大小
    win.attributes('-alpha', 0.7)
    win.title("对话框")  # 设置窗口标题
    # 获取屏幕宽度和高度
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    # 计算窗口位置
    window_width = 288
    window_height = 605
    position_top = screen_height - window_height
    position_right = screen_width - window_width

    # 设置窗口在屏幕上的位置
    win.geometry(f"+{position_right}+{position_top}")

    # 创建一个标签显示提示信息
    prompt_label = tk.Label(win, text=prompt_message)
    prompt_label.pack()

    # 创建一个输入框
    input_text = tk.Text(win, width=30, height=3)  # 设置文本框宽度和高度
    input_text.pack()

    # 创建一个标签显示状态信息
    status_label = tk.Label(win, text="")
    status_label.pack()

    # 当点击按钮时，关闭窗口并获取输入内容
    def submit_and_close(event=None):  # 事件参数在绑定回车键时需要，但在按钮点击时不需要
        status_label.config(text="正在训练，请稍等…")
        win.update()  # 更新窗口以显示新的状态信息
        win.quit()  # 关闭消息循环

    style2 = ttk.Style()
    style2.configure('RoundedButtonStyle', borderwidth=0, relief="raised", background='#cccccc')

    # 创建圆角按钮
    submit_button = ttk.Button(win,width=20, text='提交', style='TButton', command=submit_and_close)
    submit_button.pack()

    # 绑定回车键到提交函数
    win.bind('<Return>', submit_and_close)

    # 开始消息循环
    win.mainloop()

    # 获取输入内容并清空输入框
    input_value = input_text.get('1.0', 'end-1c')
    input_text.delete('1.0', tk.END)

    # 返回输入的值和窗口实例，以便稍后销毁窗口
    return input_value, win

logging.getLogger('numba').setLevel(logging.WARNING)
chunks_dict = infer_tool.read_temp("inference/chunks_temp.json")


def load_model(model_path, config_path, cluster_model_path):
    enhance = False  # 默认值为False，根据需求进行修改

    svc_model = Svc(model_path, config_path, None, cluster_model_path, enhance)
    infer_tool.mkdir(["raw", "results"])

    return svc_model

def get_latest_file(path, file_types):
    files = []
    for file_type in file_types:
        files.extend(glob.glob(os.path.join(path, f'*.{file_type}')))

    if files:
        latest_file = max(files, key=os.path.getctime)
        return latest_file

    return None

def play_music(file_path):
    subprocess.Popen(['powershell', '-c', '(New-Object Media.SoundPlayer "{}").PlaySync()'.format(file_path)],
                       shell=True)

def train_audio(svc_model, clean_names, trans, spk_list, slice_db, wav_format, noice_scale,
                pad_seconds, clip, linear_gradient_retain, enhancer_adaptive_key, f0_filter_threshold):
    infer_tool.fill_a_to_b(trans, clean_names)
    with codecs.open('config_trans.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    for clean_name, tran in zip(clean_names, trans):
        raw_audio_path = f"raw/{clean_name}"
        if "." not in raw_audio_path:
            raw_audio_path += ".wav"
        infer_tool.format_wav(raw_audio_path)
        wav_path = Path(raw_audio_path).with_suffix('.wav')
        chunks = slicer.cut(wav_path, db_thresh=slice_db)
        audio_data, audio_sr = slicer.chunks2audio(wav_path, chunks)

        for spk in spk_list:
            audio = []
            for (slice_tag, data) in audio_data:
                print(f'#=====segment start, {round(len(data) / audio_sr, 3)}s======')

                length = int(np.ceil(len(data) / audio_sr * svc_model.target_sample))
                if slice_tag:
                    print('jump empty segment')
                    _audio = np.zeros(length)
                    audio.extend(list(infer_tool.pad_array(_audio, length)))
                    continue
                per_size = int(clip * audio_sr)
                datas = infer_tool.split_list_by_n(data, per_size) if per_size != 0 else [data]

                for k, dat in enumerate(datas):
                    per_length = int(np.ceil(len(dat) / audio_sr * svc_model.target_sample)) if clip != 0 else length
                    if clip != 0:
                        print(f'###=====segment clip start, {round(len(dat) / audio_sr, 3)}s======')

                    # padd
                    pad_len = int(audio_sr * pad_seconds)
                    auto_predict = config['Parameters']['auto_predict']
                    cluster_ratio = config['Parameters']['cluster_ratio']
                    dat = np.concatenate([np.zeros([pad_len]), dat, np.zeros([pad_len])])
                    raw_path = io.BytesIO()
                    soundfile.write(raw_path, dat, audio_sr, format="wav")
                    raw_path.seek(0)
                    out_audio, out_sr = svc_model.infer(
                        spk, tran, raw_path,
                        cluster_infer_ratio=cluster_ratio,
                        auto_predict_f0=auto_predict,
                        noice_scale=noice_scale,
                        enhancer_adaptive_key=enhancer_adaptive_key,
                        cr_threshold=f0_filter_threshold,
                    )
                    _audio = out_audio.cpu().numpy()
                    pad_len = int(svc_model.target_sample * pad_seconds)
                    _audio = _audio[pad_len:-pad_len]
                    _audio = infer_tool.pad_array(_audio, per_length)
                    audio.extend(list(_audio))
            key = f"{tran}key"
            # 获取当前时间
            current_time = datetime.datetime.now()
            # 格式化为所需的字符串形式（年月日时分秒）
            time_str = current_time.strftime("%Y%m%d%H%M%S")
            # 构建带有时间的文件名
            filename = f"{clean_name}_{key}_{spk}_{time_str}.{wav_format}"
            # 完整的文件路径
            res_path = f"./results/{filename}"
            # 保存文件
            soundfile.write(res_path, audio, svc_model.target_sample, format=wav_format)


def chat_with_gpt(last,prompt):
    with codecs.open('config_trans.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    # 在这里替换成您的 OpenAI API 密钥
    key = config['Parameters']['api_key']
    openai.api_key = key
    content = config['Parameters']['content']
    # 构建请求
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "(上一句为"+last+")" + content},
            {"role": "user", "content": prompt},
        ]
    )
    result = response['choices'][0]['message']['content'].strip()


    return result

def get_music_length(file_path):
    audio = AudioSegment.from_file(file_path)
    length_in_seconds = len(audio) / 1000  # 将毫秒转换为秒
    return length_in_seconds

async def main():
    with codecs.open('config_trans.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    x = config['Parameters']['iterations']
    y = config['Parameters']['speaker']
    websocket_url = config['Parameters']['websocket']
    svc_model = load_model(f"logs/44k/G_{x}.pth", "configs/config.json", "logs/44k/kmeans_10000.pt")
    voice = "zh-CN-XiaoyiNeural"
    z = input("请选择你需要转换的声音类型：\n1.女\n2.男\n3.英语\n")
    # 根据输入的演唱人名称设置声音选项
    print("输入成功")
    if z == "女" or z == "1":
        voice = "zh-CN-XiaoyiNeural"
    elif z == "男" or z == "2":
        voice = "zh-CN-YunxiNeural"
    elif z == "英语" or z == "3":
        voice = "en-US-MichelleNeural"
    text2 = ""

    while True:
        text1, out_window= get_input_from_gui("你想对胡桃说点什么呢: ")
        text = chat_with_gpt(str(text2),str(text1))
        text2 = text1
        output_file = "tts.wav"
        communicate = edge_tts.Communicate(text, voice, rate="+6%")
        await communicate.save("raw/tts.wav")
        #svc_model, clean_names, trans, spk_list, slice_db, wav_format, noice_scale
        #pad_seconds, clip, linear_gradient_retain, enhancer_adaptive_key, f0_filter_threshold
        train_audio(svc_model, [output_file], [0], [y], -40, "wav", 0.4, 0.5, 0, 0.75, 0, 0.05)

        # 获取最新的音乐文件并播放
        latest_music = get_latest_file("results", ["wav", "mp3", "ogg"])

        if latest_music:
            print(text)
            # 存储结果到文件
            with open('E:/BERT/chatgpt.txt', 'w') as file:
                file.write(text)
            interval = 1.4
            music_length = get_music_length(latest_music)
            total_triggers = music_length/interval + 1 # 向下取整，计算总共需要触发的次数
            thread1 = threading.Thread(target=send_motion_via_websocket, args=(websocket_url,interval,total_triggers,))

            # 创建并启动新线程执行音乐播放
            thread2 = threading.Thread(target=play_music, args=(latest_music,))
            thread2.start()
            thread1.start()
            send_text_via_websocket(websocket_url, text, music_length*1000)
            out_window.destroy()
            # 等待线程结束
            thread2.join()
            thread1.join()
if __name__ == "__main__":
    asyncio.run(main())
