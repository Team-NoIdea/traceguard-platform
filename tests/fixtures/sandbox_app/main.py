from fastapi import FastAPI
app = FastAPI()
@app.get("/items")
def items(id: str = "1"):
    return {"id": int(id)}

@app.get("/calculate")
def calculate(value: str = "1"):
    return eval(value)
