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

# copy the code into docker image
COPY . .

# avoiding timeout issues by installing torch seperately
RUN pip install --no-cache-dir --default-timeout=1000 torch torchvision

# install the rest of the dependencies
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# run with cmd+args
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]