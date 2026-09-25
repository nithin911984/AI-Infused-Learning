from fastapi import FastAPI
from pydantic import BaseModel
import datetime

app = FastAPI(title="DeskBuddy Tools")

class Calc(BaseModel):
    expression: str

@app.post("/calculator")
def calculator(c: Calc):
    try:
        # demo only - never use eval in production!
        return {"result": eval(c.expression, {"__builtins__": {}})}
    except Exception as e:
        return {"error": str(e)}

@app.get("/datetime")
def now():
    return {"now": datetime.datetime.now().isoformat()}