import json

import uvicorn
from fastapi import Request, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette_session import SessionMiddleware
import html
from chat_api import Member

# Config
Members_list = {"eva": ["123", "../members/eva.json"]}

app = FastAPI()
app.mount("/static", StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(
    SessionMiddleware,
    secret_key="secret",
    cookie_name="cookie22",
)


@app.get("/login")
def login(request: Request, username: str, password: str):
    if username in Members_list.keys():
        if password == Members_list[username][0]:
            mb = Member(username)
            member_str=mb.class2jsonstr()
            request.session.update({"member_str": member_str})
            return templates.TemplateResponse("index.html", {"request": request, "member_str":member_str})

    return RedirectResponse("/?messages=账号或密码错误")


@app.get("/chat")
def chat(request: Request, data: str = ""):
    #-1:重新登陆， #0:请求错误 、#1：成功
    print("欢迎来到lane的chatGPT")
    return_dict={"status":"0", "messages":"", "content":""}
    try:
        prompt = json.loads(data)["prompt"]
        member_str = request.session["member_str"]
        member = json.loads(member_str)
        mb = Member(member["name"])
        mb.update(member)
    except:
        return_dict["status"] = "-1"
        return_dict["messages"]="请先登陆"
        return json.dumps(return_dict)

    if not mb.check_member():
        return_dict["messages"] = "该账户无法享受服务"
        return json.dumps(return_dict)
    mb.add_content(prompt, "user")
    response = mb.chat()
    content = mb.parse_response(response)
    request.session.update({"member_str": mb.class2jsonstr()})
    return_dict["status"] = "1"
    return_dict["content"] = content
    return json.dumps(return_dict)


@app.get("/")
def homepage(request: Request, messages: str = ""):
    return templates.TemplateResponse("homepage.html", {"request": request, "messages": messages})


if __name__ == '__main__':
    uvicorn.run(app="index:app", host="127.0.0.1", port=8080, reload=True)
