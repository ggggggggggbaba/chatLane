# -*- coding: UTF-8 -*-
import json
import uvicorn
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from chat_api import Member
from zhconv import convert
from httpx import AsyncClient, Proxy, HTTPError
import secrets
import asyncio

# Config
Members_list = {"eva": ["123", "../members/eva.json"]}

app = FastAPI()
app.mount("/static", StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(
    SessionMiddleware,
    secret_key="laneeee"
)
def get_session(request: Request):
    return request.session


@app.get("/login")
def login(request: Request, username: str, password: str, session=Depends(get_session)):
    if username in Members_list.keys():
        if password == Members_list[username][0]:
            session["messages"] = []
            session["username"] = username
            return templates.TemplateResponse("index.html", {"request": request})
    return RedirectResponse("/?messages=账号或密码错误")

# stream route
@app.get("/stream")
async def stream_response(request: Request, data: str = "", session=Depends(get_session)):
    #-1:重新登陆， #0:请求错误 、#1：成功
    return_dict={"status":"0", "messages":"", "content":""}
    try:
        prompt = json.loads(data)["prompt"]
        mb = Member(session["username"])
        mb.load_member()
        mb.add_content(prompt, role="user")
    except:
        return_dict["status"] = "-1"
        return_dict["messages"]="请先登陆"
        return StreamingResponse(content=json.dumps(return_dict), media_type='text/event-stream')
    if not mb.check_member():
        return_dict["messages"] = "该账户无法享受服务"
        return StreamingResponse(content=json.dumps(return_dict), media_type='text/event-stream')

    response = StreamingResponse(chat_stream(session, mb), media_type='text/event-stream')
    return response


async def chat_stream(session, mb):
    # print(session)
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer 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'
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": mb.messages,
        "stream": True,
        "max_tokens": 1024
    }
    proxies = "http://127.0.0.1:16005"
    content=""
    try:
        async with AsyncClient(headers=headers, proxies=proxies) as client:
            # async with client.post(url, json=data) as response:            
            async with client.stream("POST", url=url, json=data) as stream:
                tail = ""
                buffer=bytes()
                async for chunk in stream.aiter_bytes(512):
                    buffer+=chunk
                    try:
                        decode_chunk = buffer.decode('utf-8')
                    except UnicodeDecodeError as e:
                        print(f"buffer.decode UnicodeDecodeError")
                        continue
                    decode_chunk = tail+decode_chunk
                    packages = decode_chunk.split('\n')
                    tail = packages[-1]
                    content_chunk = chunk_parse(packages[:-1])
                    content+=content_chunk
                    yield content_chunk
                    # await asyncio.sleep(0) # 强制异步上下文转换来处理其他任务
                    buffer = bytes()
                await asyncio.sleep(0)
                content_chunk = chunk_parse(tail)
                content+=content_chunk
                yield content_chunk
    except HTTPError as e: # 在这里进行自定义处理
      content_chunk = "openai 相应超时"
      yield content_chunk
      print(f"openai 相应超时，自定义处理，Error occurred: {e}")
    mb.add_content(content, role="assistant")
    mb.save_member()

def chunk_parse(packages):
      content = ""
      for i in range(len(packages)):
        res_content = packages[i]
        if "data" == res_content[:4]:  
          json_str = res_content.split(": ", 1)[1]
          if "[DONE]" == json_str:
            continue
          try:
            response_dict = json.loads(json_str)
          except ValueError:
              print("Error: Unable to parse JSON from content:", content)
              print("Error: Unable to parse JSON from res_content:", res_content)
              continue
          if 'content' in response_dict['choices'][0]['delta'].keys():
            content+=response_dict['choices'][0]['delta']['content']

          # print("index= ",i, " content= ",response_dict)
      return content

async def chat(request, mb , prompt):
    mb.add_content(prompt, "user")
    response = mb.chat()
    content = mb.parse_response(response)
    # print(content)
    request.session.update({"member_str": mb.class2jsonstr()})
    for i in range(0, len(content), 100):
        yield content[i:i+100].encode()
        


@app.post("/chat_audio")
async def chat_audio(request: Request, audio: UploadFile=File(..., media_type="audio/webm")):
    # 必须传入ogg或者webm格式，wav和mp3都没办法正确保存
    member_str = request.session["member_str"]
    member = json.loads(member_str)
    mb = Member(member["name"])
    mb.update(member)

    contents = await audio.read()
    with open(audio.filename, "wb") as f:
        f.write(contents)
    
    with open(audio.filename, "rb") as audio:
        transcript = mb.speech2text(audio)
    text = transcript["text"] 
    text = convert(text, 'zh-cn') # 繁体中文转简体中文
    return chat(request, json.dumps({"prompt":text}))

@app.get("/test")
def test(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})

@app.get("/")
def homepage(request: Request, messages: str = ""):
    return templates.TemplateResponse("homepage.html", {"request": request, "messages": messages})


if __name__ == '__main__':
    uvicorn.run(app="index:app", host="127.0.0.1", port=8080, reload=True)
