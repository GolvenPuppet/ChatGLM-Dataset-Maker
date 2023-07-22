import pickle
import os
import json
from typing import Union
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

allAnswers = [];
tempTalks = [];

def saveAnswers(answers):
    #防止同时读写
    if os.path.exists("lock"):
        return False
    with open("lock", "w") as lock_file:
        lock_file.write("")
    with open("data.pkl", "wb") as file:
        pickle.dump(answers, file)
    if os.path.exists("lock"):
        os.remove("lock")
    all_answers=answers
    return True

def readAnswers():
    if os.path.exists("data.pkl"):
        with open("data.pkl", "rb") as file:
            #从数据库同步回答
            answers = pickle.load(file)
    else:
        answers = []
    return answers

def save_answers_as_json(answers, file_path):
    data = []
    #print("answers",answers)
    if 0: #(自定义输出,暂时不用)
        for question, answer in answers.items():#根据情况修改输出格式
            item = {
                "instruction": question,
                "input": "",
                "output": answer
            }
            data.append(item)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    else:
        with open(file_path, "w", encoding="utf-8") as file:
            for talks in answers:
                print(talks)
                history = [];
                for talk in talks:
                    item = { "prompt": talk[0], "response": talk[1],"history":history };
                    file.write(json.dumps(item, ensure_ascii=False) + "\n")
                    history.append(talk);
                #print (answers)
            
                

#多轮对话
#{"prompt": "长城h3风扇不转。继电器好的。保险丝好的传感器新的风扇也新的这是为什么。就是继电器缺一个信号线", "response": "用电脑能读数据流吗？水温多少", "history": []}
#{"prompt": "95", "response": "上下水管温差怎么样啊？空气是不是都排干净了呢？", "history": [["长城h3风扇不转。继电器好的。保险丝好的传感器新的风扇也新的这是为什么。就是继电器缺一个信号线", "用电脑能读数据流吗？水温多少"]]}
#{"prompt": "是的。上下水管都好的", "response": "那就要检查线路了，一般风扇继电器是由电脑控制吸合的，如果电路存在断路，或者电脑坏了的话会出现继电器不吸合的情况！", "history": [["长城h3风扇不转。继电器好的。保险丝好的传感器新的风扇也新的这是为什么。就是继电器缺一个信号线", "用电脑能读数据流吗？水温多少"], ["95", "上下水管温差怎么样啊？空气是不是都排干净了呢？"]]}

#return Index
def addTalks(prompt,response,isEnd=False):
    global tempTalks;
    global allAnswers;
    index = len(tempTalks)
    tempTalks.append([prompt,response])
    #print(tempTalks)
    if isEnd:
        allAnswers.append(tempTalks);
        tempTalks = []
    return index
def getAnswersLen():
    global allAnswers;
    return len(allAnswers)

def main():
    #addTalks("长城h3风扇不转。继电器好的。保险丝好的传感器新的风扇也新的这是为什么。就是继电器缺一个信号线","用电脑能读数据流吗？水温多少")
    #addTalks("95","上下水管温差怎么样啊？空气是不是都排干净了呢？")
    #addTalks("是的。上下水管都好的","那就要检查线路了，一般风扇继电器是由电脑控制吸合的，如果电路存在断路，或者电脑坏了的话会出现继电器不吸合的情况！",True)
    #save_answers_as_json(allAnswers, "kkk.json")
    #saveAnswers(allAnswers);
    global allAnswers;
    allAnswers =  readAnswers()
    #print(allAnswers)
    
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_file = open("index.html", 'r', encoding='UTF-8').read()
    return html_file


class Talk(BaseModel):
    prompt: str
    response: str
    isEnd: Union[bool, None] = None

class answerIndex(BaseModel):
    index: int

class answer(BaseModel):
    answer: list

class answerWi(BaseModel):
    index: int
    answer: list


@app.post("/addTalk/")
def create_item(talk: Talk):
    talk_dict = talk.dict()
    return {"Index": addTalks(talk.prompt,talk.response,talk.isEnd)}

@app.post("/getAnswersLen/")
def api_getAnswersLen():
    global allAnswers;
    #print(allAnswers)
    return {"Len": getAnswersLen()}


@app.post("/getAnswer/")
def api_getAnswer(index: answerIndex):
    print(index)
    global allAnswers;
    if(index.index >= len(allAnswers)):
        return {"code": 301}
    #print(allAnswers)
    return {"code": 200,"answer": allAnswers[index.index]}

@app.post("/delAnswer/")
def api_delAnswer(index: answerIndex):
    print(index)
    global allAnswers;
    if(index.index >= len(allAnswers)):
        return {"code": 301}
    #print(allAnswers)
    del allAnswers[index.index] 
    return {"code": 200}

@app.post("/addAnswer/")
def api_addAnswer(answer2: answer):
    
    global allAnswers;
    allAnswers.append(answer2.answer)
    saveAnswers(allAnswers);
    return {"code": 200,"Len": getAnswersLen()}

@app.post("/saveAnswer/")
def api_saveAnswer(answer2: answerWi):
    
    global allAnswers;
    allAnswers[answer2.index] = answer2.answer;
    saveAnswers(allAnswers);
    return {"code": 200}

@app.post("/outAnswer/")
def api_outAnswer():
    
    save_answers_as_json(allAnswers, "export.json")
    return {"code": 200}

if __name__ == "__main__":
    main()
    uvicorn.run(app, host='0.0.0.0', port=8000, workers=1)
