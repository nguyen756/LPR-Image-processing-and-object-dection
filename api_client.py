import cv2
import requests
import time
server_url = "http://127.0.0.1:8000/detect"
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    _, img_encoded = cv2.imencode('.jpg', frame)
    files = {'image': ('frame.jpg', img_encoded.tobytes(), 'image/jpeg')}
    
    try:
        response = requests.post(server_url, files=files)
        print("Server response:", response.json())
    except Exception as e:
        print("Error during request:", e)

    time.sleep(2)
    if cv2.waitKey(2000) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()