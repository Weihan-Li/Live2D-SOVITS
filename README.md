# 基于SO-VITS和Live2DViewerEX的聊天AI

## 功能简介

结合chatgpt，[so-vits-svc](https://github.com/svc-develop-team/so-vits-svc/tree/4.1-Stable)，Live2DViewerEX软件及其[API](https://github.com/pavostudio/ExAPI)以及[中文BERT-wwm](https://github.com/ymcui/Chinese-BERT-wwm)制作的桌面聊天AI助手。

#### 可以实现：

- 运行后右下角出现live2d角色，带有播放器以及一个对话框
- 点击live2d角色的不同部位可以出现不同的反应，闲置时会有闲置动作及语音
- 在对话框中输入文本后等待几秒会得到这段文本的回应声音，伴随着出现在角色上的回应文本以及对应的角色表情

## 使用说明

### 准备工作

首先从https://github.com/svc-develop-team/so-vits-svc下载该包。注意其大小大约为15GB，需要预留足够的硬盘空间。

```
git clone https://github.com/svc-develop-team/so-vits-svc.git
```

接着在steam中下载Live2DViewerEX，并从https://github.com/pavostudio/ExAPI下载Live2DViewerEX的API库。

```
git clone https://github.com/pavostudio/ExAPI.git
```

下载后从steam打开Live2DViewerEX的根目录，并将下载好的ExAPI文件夹的所有内容移动到根目录下。（注意不要移动文件夹，而是其中的内容）

参考so-vits-svc下的指导，训练好你的声音模型，记录下你的speaker名称以及声音模型的迭代次数。声音模型在`logs\44k文件夹`下，speaker名称为之前命名并放在`dataset_raw`下的说话人名字（文件夹名去掉数字）。

### 安装步骤

在下载我们的包后，其中每个文件都需要进行一定的移动或改动。

#### so-vits下的改动

- 将`ffmpeg文件夹`、`ch_trans.py`、`config_trans.yaml`、`requirements.txt`移动到之前下载好的`so-vits-svc文件夹`中。

- 将`ffmpeg/bin`设置为环境变量。参考[ffmpeg详细安装教程](https://zhuanlan.zhihu.com/p/324472015)

- 安装依赖。在命令行中执行：

  ```
  pip install -r requirements.txt
  ```

  可以使用清华源：

  ```
  pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
  ```

  如果使用vpn，注意使用vpn时要设置命令行的proxy：

  ```
  set http_proxy=http://127.0.0.1:7890 
  set https_proxy=http://127.0.0.1:7890
  ```

- 修改`config_trans.yaml`，需要修改的参数如下表：

  | parameter     | 含义                              |
  | ------------- | --------------------------------- |
  | api_key       | chatgpt的API秘钥                  |
  | content       | 给AI预设的身份及提前告知的信息    |
  | iterations    | 声音模型的迭代次数                |
  | speaker       | 说话人名称                        |
  | cluster_ratio | 聚类模型的权重（没有聚类模型填0） |
  | auto_predict  | 是否启用f0自动预测                |
  
  要获取ChatGPT的API秘钥，可以通过 OpenAI 平台上的官方账号进行登录。
  
  首先，访问[https://platform.openai.com/](https://link.zhihu.com/?target=https%3A//platform.openai.com/) 登录账号。
  
  登录之后，点击右上角“Personal”，展开菜单，找到“View API keys”，进入页面后，点击“Create new secret key”按钮，来创建API秘钥。（每个秘钥在创建后只会显示一次，及时复制保存）

#### Live2DViewerEX下的改动

- 将`Hutao文件夹`移动到Live2DViewerEX的根目录下。
- 启动Live2DViewerEX，在其`控制面板-模型-Json文件`中选择`Hutao文件夹`下的`胡桃001.model3.json`并上传。（如果没有找到控制面板界面，请双击任务栏中的Live2DViewerEX图标）
- 双击控制面板中的json文件，将胡桃调整大小并放在左下角。
- 选择`控制面板-设定`，在右侧远程访问栏中将`启动服务`开启，端口号设置为10086；选择`控制面板-小部件`，开启音乐播放器。

### 使用方法

在命令行中cd到你的so-vits-svc文件夹，打开vpn，设置命令行的proxy：

```
set http_proxy=http://127.0.0.1:7890 
set https_proxy=http://127.0.0.1:7890
```

运行：

```
python ch_trans.py
```

等待一段时间后，你可以看到在live2d角色上出现一个对话框，这时你可以在对话框中输入文本。等待几秒会得到这段文本的回应声音，伴随着出现在角色上的回应文本。

### 拓展项

#### 说话时伴随角色表情的效果：

参考 https://github.com/Weihan-Li/BERT_emotion 进行安装，将其中的`BERT_predict.py`替换成在本项目中的`BERT_predict.py`。

修改代码69行的`"E:/BERT/chatgpt.txt"`为你的`chatgpt.txt`位置（应该在so-vits-svc文件夹中），cd到你的BERT_emotion文件夹下运行：

```
python BERT_predict.py
```

即可实现在说话开始会有相应的表情的效果。

#### 集成并一起打开的效果：

在这里提供几种思路：

1. 写成.bat文件或写成.vbs文件以实现一键打开。
2. 使用subprocess库，可以使用类似下面这种函数：

```python
run_command(command):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.Popen(command, shell=True, startupinfo=startupinfo)
```

并在命令行使用pyinstaller库或nuitka库进行打包，打包成exe格式。

```
pyinstaller --noconsole --onefile run.py
```

#### 使用自己的Live2d模型：

首先需要一个包括模型、动作以及表情json文件及live2d模型文件的完整live2d文件包。

参考教程：[手把手教你制作可触摸的Live2D桌面](https://www.bilibili.com/video/BV1s54y157cQ/?spm_id_from=333.337.search-card.all.click&vd_source=1fd2dd25e8d4b6aee066bbd0f2eb9e64)，给自己的模型添加动作以及表情。

`BERT_predict.py`中的

```
json_data = {
    "msg": 13300,
    "msgId": 1,
    "data": {
        "id": 0,
        "expId": int(output)  # 将output转换为整数类型
    }
}
```

中的`int(output)`可取值为 ***0,1,2,3,4,5*** ，请将你想设置为 ***生气、害怕、积极、悲伤、惊奇、非常惊讶*** 的六个表情按顺序设置在live2d工作室中的表情中。

将`ch_trans.py`中的

```
json_data1 = {
    "msg": 13200,
    "msgId": 1,
    "data": {
        "id": 0,
        "type": 0,
        "mtn": "speak:open"
    }
}
```

中的`"speak:open"`修改为你的`动作组-动作`中的说话动作。
