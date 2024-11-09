from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel
from . import schemas
#Instance ( Fast api app instance)
app = FastAPI()


@app.get('/')
def start():
    return {'Hello its working'}

@app.get('/blog')
def index(limit = 10 , published : bool = True):
    #only get to publishe blogs
    if published :
        return {'data':f'{limit} published blog from the database'}
    else:
        return {'data' : f'{limit} blogs from the db'}
@app.get('/about')
def about():
    return {'data' :{'about page'}}

@app.get('/blog/{id}')
def show(id: int):
    return {'data' : id}


@app.get('/blog/{id}/comments')
def comments(id , limit=10):
    #Fetch comments of blog with id = id
    return {'data':{'1','2'}}


class Blog(BaseModel):
    title :str
    body: str
    published : Optional[bool]
    



@app.post('/blog')
def create_blog(request: Blog):
    return request
    return {'data':"Blogg is created"}

