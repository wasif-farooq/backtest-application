FROM debian:bullseye

# Install Python, pip, and mingw-w64 (cross-compiler for Windows)
RUN apt-get update && apt-get install -y \
	python3 python3-pip mingw-w64

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip3 install pyinstaller

# Build Windows executable
RUN pyinstaller --onefile --name app.exe main.py

# Output directory for the build
CMD ["cp", "/app/dist/app.exe", "/output"]

