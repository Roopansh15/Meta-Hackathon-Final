FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Gradio's default port
EXPOSE 7860

# Ensure Gradio listens on all interfaces so HF Spaces can route traffic
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Entry point
CMD ["python", "app.py"]
