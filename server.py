import time
import os

from supabase import create_client, Client
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
import uvicorn

from modules.ai import LPR_Engine
from modules import processing
import config.config as config

app = FastAPI()
print("Loading AI Engine")
engine = LPR_Engine()
print(f"{engine} Engine Loaded")

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/detect")
async def detect_plate(image: UploadFile = File(...)):
    # 1. Catch the raw bytes from the web
    contents = await image.read()
    # 2. Convert the bytes into a flat, 1D mathematical array
    nparr = np.frombuffer(contents, np.uint8)
    # 3. Use OpenCV to decode that array into a 3D image matrix
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # 4. The Bouncer: Did they upload an image, or a cat video?
    if img is None:
        return {"error": "Uploaded file is not a valid image."}
        
    try: 
        detections = engine.detect_vehicle(img)
        results = []
        for i, det in enumerate(detections):
                x1, y1, x2, y2, conf = det
                plate_crop = img[y1:y2, x1:x2]
                if plate_crop.shape[0] == 0 or plate_crop.shape[1] == 0:
                    continue
                plate_crop_processed = processing.preprocess_for_ocr(plate_crop)
                #cv2.imshow("Plate Crop", plate_crop_processed)
                is_split, parts = processing.split_plate(plate_crop_processed)
                raw_text = engine.read_text(parts)
                clean_text = engine.clean_vn_plate(raw_text)
                if clean_text:
                    print(f"PLATE FOUND: {clean_text}")
                    try:
                        data={"plate_number": clean_text, "confidence": float(conf)}
                        supabase.table("captured_plates").insert(data).execute()
                        print(f"Inserted into database: {data}")
                    except Exception as e:
                        print(f"Failed to insert data: {e}")
                    img = processing.draw_result(img, clean_text, (x1,y1,x2,y2))
                    timestamp = int(time.time())
                    filename = f"{config.SAVE_FOLDER}/{clean_text}_{timestamp}.png"
                    # bounce back to client
                    results.append({
                        "plate_number": clean_text,
                        "confidence": float(conf)
                    })
                
                else:
                    if config.PRINT_LOGS:
                        print(f"REJECT: '{raw_text}'")
        # return the results as JSON
        return {
            "status": "ok",
            "detections": len(results),
            "detected_plates": results
        }
    except Exception as e:
        return {"error": f"Detection failed: {e}"}

    

if __name__ == "__main__":
    uvicorn.run("api_test:app", host="0.0.0.0", port=8000, reload=True)
