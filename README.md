# License plate recognition
#### *Declaration: this system used [Muhammad-Zeerak-Khan](https://github.com/Muhammad-Zeerak-Khan/Automatic-License-Plate-Recognition-using-YOLOv8/blob/main/license_plate_detector.pt) YOLOv8 specially for license plate recognition.* 

System Architecture
This system is intentionally decoupled into a lightweight client-side capture node and a heavy, headless server-side inference engine in real time.


Tech Usage
* **Deployment:** Docker/Launcher for local
* **Computer Vision:** OpenCV (Headless)
* **Object Detection:** YOLOv8 
* **OCR:** EasyOCR
* **Networking:** Python Sockets (TCP)

 **Headless Execution:** Designed to run in headless Linux environment(Docker, Cloud environment).
### Pipeline  
1. **Ingestion Layer (`main.py`):** Receives raw byte-streams via TCP socket, decodes the `.jpg` payload using OpenCV, and hands it to the AI Engine.
2. **Detection Layer (`modules/ai.py`):** YOLOv8 scans the frame for vehicles and outputs bounding box coordinates and confidence scores.
3. **Tracking Layer (`modules/tracker.py`):** Assigns persistent IDs to detected boxes using Euclidean distance logic. Crucial optimization: Prevents the OCR engine from re-processing the same vehicle across multiple frames.
4. **Sanitization Layer (`modules/processing.py`):** * Crops the bounding box.
   * Applies Grayscale, CLAHE (Contrast Limiting), and Bilateral Filtering.
   * Executes Morphological Deskewing to flatten the image matrix for the OCR reader.
5. **Extraction & Validation (`modules/ai.py`):** EasyOCR extracts the raw text from the sanitized image. A custom Regex validation function (`clean_vn_plate`) corrects common machine-vision hallucinations and verifies Vietnamese formatting rules before logging.


# Usage 
### **Docker:**

1. **Build the Image:**
```bash
   docker build -t lpr-engine .
```
2. **Run the Container(Port 8000):**
```bash 
docker run -p 8000:8000 lpr-engine python -u main.py --host 0.0.0.0 --port 8000
```
3. **Client side: Ipwebcame/local webcam/rasberrypi with camera module**
```bash 
python pi_stream.py --server_ip "SERVER_IP" --port 8000 --camera "0"
``` 
Replace `SERVER_IP` with actual server ip, 127.0.0.1 if run locally

