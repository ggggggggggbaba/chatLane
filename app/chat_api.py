import openai
import json


openai.api_key = "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"
model_list = ["gpt-3.5-turbo", "text-davinci-003"]
ChatLane_SMART = False
ChatLane_STOP = "exit"
ChatLane_PIECE = 0.002  # 美元
ChatLane_Member_NAME = "eva"
Member_map = {"eva": "../members/eva.json"}


class Member:
    name = ""
    json_path = ""
    max_token = 1024
    used_token = 0
    cur_used_token = 0
    messages = []
    max_communication = 3
    piece = 0.002

    def __init__(self, name):
        self.name = name
        self.json_path = Member_map[self.name]
        self.load_member()
        self.cur_used_token = 0
        self.messages = self.init_messages(ChatLane_SMART)

    def init_messages(self, ChatLane_SMART):
        messages = []
        if ChatLane_SMART:
            messages = [{"role": "system", "content": "You are a  helpful assistant."}]
        return messages

    def print_member(self):
        print("本轮对话消耗了{0}个令牌，消费了{1}美元，总计消耗了{2}个令牌，最大可用{3}个令牌".format(self.cur_used_token,
                                                                     self.cur_used_token * ChatLane_PIECE,
                                                                     self.used_token,
                                                                     self.max_token))

    def check_member(self):
        if self.used_token > self.max_token:
            print("已超过本日可使用限制")
            return False
        return True

    def load_member(self):
        with open(self.json_path, "r") as f:
            js = json.load(f)
            self.max_token = js["max_token"]
            self.used_token = js["used_token"]

    def save_member(self):
        member_map = {
            "max_token": self.max_token,
            "used_token": self.used_token
        }
        with open(self.json_path, "w") as f:
            json.dump(member_map, f)

    # chatGPT_v1只能进行一句话的问答，无法有多句话的对话，token数量比chatGPT_v2要少，但是单价要贵10%
    def chat(self):
        model_engine = model_list[0]
        completion = openai.ChatCompletion.create(
            model=model_engine,
            messages=self.messages,
            max_tokens=1024,  # 控制response中最大可用令牌
            n=1,
            temperature=0.5, # 控制输出的随机性
            top_p=1,
        )
        return completion
    
    def speech2text(self, audio):
        transcript = openai.Audio.transcribe("whisper-1", audio)
        return  transcript

    def add_content(self, prompt, role="user"):
        if len(self.messages) > self.max_communication * 2:
            if self.messages[0]["role"] == "system":
                self.messages = [self.messages[0]] + self.messages[3:]
            else:
                self.messages = self.messages[2:]
        self.messages.append({"role": role, "content": prompt})
            



    def parse_response(self, response):
        total_tokens = response.usage.total_tokens
        response_content = response.choices[0].message.content
        self.used_token += total_tokens
        self.cur_used_token += total_tokens  # 参考https://platform.openai.com/docs/guides/chat/introduction
        self.save_member()
        self.add_content(response_content, "assistant")
        return response_content

    def class2jsonstr(self):
        d = {
            "name": self.name,
            "max_token": self.max_token,
            "used_token": self.used_token,
            "cur_used_token": self.cur_used_token,
            "messages": self.messages,
        }
        jstr = json.dumps(d)
        return jstr

    def update(self, d):
        # d = json.loads(member_str)
        self.__dict__.update(d)

def get_prompt():
    prompt = ChatLane_STOP
    try:
        prompt = input()
        prompt.encode('utf-8')
    except:
        print("无法转换成中文编码，请检查输入, 退出请输入 exit ")
        return get_prompt()
    return prompt
