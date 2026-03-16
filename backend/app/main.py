from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def root():
    return {'message': 'Shared AI Storytelling RPG API'}

