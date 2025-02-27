from fastapi import FastAPI, Response
from ImageProcessor.ImageProcessor import ImageProcessor
from ImageProcessor.CheckoutProcessor import CheckoutProcessor
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

image_processor = ImageProcessor()
analyzer = CheckoutProcessor()

checkout_analyzers = []

for i in range(2):
    checkout_analyzers.append(CheckoutProcessor(i))

# API 
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_frames(view):
    while True:
        if (view == 1):
            frame_bytes = image_processor.get_frame()
        else:
            frame_bytes = image_processor.get_aile_view()
        if frame_bytes is None:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def get_heatmap():
    frame_bytes = image_processor.get_heatmap()
    if frame_bytes is None:
        return None
    yield (b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(1), media_type='multipart/x-mixed-replace; boundary=frame')

@app.get("/aisle_view")
async def aisle_view():
    return StreamingResponse(generate_frames(2), media_type='multipart/x-mixed-replace; boundary=frame')

@app.get("/get_heatmap")
async def get_heatmap():
    result = image_processor.get_heatmap()
    return Response(content=result, media_type="image/jpeg")

@app.get("/get_trajectories")
async def get_trajectories():
    result = image_processor.get_common_paths()
    return Response(content=result, media_type="image/jpeg")

@app.get("/")
def read_root():
    return {"Message": "TCC-API"}

@app.get("/get_wait_time")
def get_wait_time():
    lines = {}
    for i, checkout_analyzer in enumerate(checkout_analyzers):
        count = checkout_analyzer.count_people()
        lines["Line " + str(i + 1)] = count*4
    
    return lines

@app.get("/get_sentiments")
def get_sentiments():
    lines = {}
    for i, checkout_analyzer in enumerate(checkout_analyzers):
        sentiments = checkout_analyzer.get_sentiments()
        lines["Line " + str(i + 1)] = sentiments
    return lines

# Entry point to run the server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
