import os

from multiprocessing.managers import BaseManager  # Add this import statement
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from werkzeug.utils import secure_filename
import asyncio
app = FastAPI()
origins = ["*"]  # Add your allowed origins here
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize manager connection
# NOTE: you might want to handle the password in a less hardcoded way
manager = BaseManager(('', 5602), b'password')
manager.register('query_index')
manager.register('insert_into_index')
manager.register('get_documents_list')
manager.connect()


class QueryResponse(BaseModel):
    text: str
    sources: list

@app.websocket("/ws")
async def query_index(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        if data is None:
            await websocket.send_json(
                {
                    "detail": "No text found. Please include a ?text=blah parameter in the URL"
                }
            )
            continue
        
        response = manager.query_index(data)._getvalue()
        response_json = QueryResponse(
            text=str(response),
            sources=[
                {
                    "text": str(x.source_text),
                    "similarity": round(x.similarity, 2),
                    "doc_id": str(x.doc_id),
                    "start": x.node_info['start'],
                    "end": x.node_info['end']
                } for x in response.source_nodes
            ]
        )
        await websocket.send_json(response_json)
@app.get("/query")
async def query_index(text: str = None):
    global manager
    if text is None:
        return JSONResponse(
            content={"detail": "No text found. Please include a ?text=blah parameter in the URL"},
            status_code=400,
        )
    
    response = manager.query_index(text)._getvalue()
    response_json = QueryResponse(
        text=str(response),
        sources=[
            {
                "text": str(x.source_text),
                "similarity": round(x.similarity, 2),
                "doc_id": str(x.doc_id),
                "start": x.node_info['start'],
                "end": x.node_info['end']
            } for x in response.source_nodes
        ]
    )
    return response_json


@app.post("/uploadFile")
async def upload_file(file: UploadFile = File(...), filename_as_doc_id: bool = None):
    global manager
    try:
        content = await file.read()
        filename = secure_filename(file.filename)
        filepath = os.path.join('documents', os.path.basename(filename))
        with open(filepath, "wb") as f:
            f.write(content)

        if filename_as_doc_id:
            manager.insert_into_index(filepath, doc_id=filename)
        else:
            manager.insert_into_index(filepath)
    except Exception as e:
        # Cleanup temp file
        if os.path.exists(filepath):
            os.remove(filepath)
        return JSONResponse(content={"detail": f"Error: {str(e)}"}, status_code=500)

    # Cleanup temp file
    if os.path.exists(filepath):
        os.remove(filepath)

    return JSONResponse(content={"detail": "File inserted!"}, status_code=200)


@app.get("/getDocuments")
async def get_documents():
    document_list = manager.get_documents_list()._getvalue()

    return JSONResponse(content=document_list, status_code=200)


@app.get("/")
async def home():
    return "Hello, World! Welcome to the llama_index docker image!"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5601)
