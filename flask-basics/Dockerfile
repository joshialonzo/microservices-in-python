FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install the dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src src

# Run the application
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=5 \
    CMD curl --fail http://localhost:5000/health || exit 1
ENTRYPOINT [ "python", "./src/app.py" ]
