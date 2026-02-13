# python version, preferably 3.9 or higher
FROM python:3.9-slim

# install dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


# pip install
RUN pip install --upgrade pip

# avoiding timeout issues by installing torch seperately
RUN pip install --no-cache-dir --default-timeout=1000 torch torchvision

# install the rest of the dependencies
RUN pip install --no-cache-dir --default-timeout=1000 \
    numpy \
    opencv-python-headless \
    ultralytics \
    easyocr

# copy the code into docker image
COPY . .

# run with cmd+args
CMD ["python", "main.py", "--server_ip", "0.0.0.0"]