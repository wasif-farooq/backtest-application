# Use Ubuntu as the base image
FROM ubuntu:20.04

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary tools and dependencies
RUN dpkg --add-architecture i386 && \
	apt-get update && apt-get install -y \
	software-properties-common \
	wget \
	gnupg2 \
	apt-transport-https \
	build-essential \
	python3 \
	python3-pip \
	python3-dev \
	qt5-default \
	qttools5-dev-tools \
	qttools5-dev \
	libqt5svg5-dev \
	dpkg \
	zip \
	mingw-w64 \
	wine64 \
	wine32:i386 && \
	rm -rf /var/lib/apt/lists/*

# Install pyinstaller
RUN pip3 install pyinstaller

# Create a working directory
WORKDIR /app

# Copy application files into the container
COPY . /app

# Install Python dependencies from requirements.txt
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt

# Set Wine configuration
RUN winecfg

# Command to build the Windows executable
CMD ["pyinstaller", "--onefile", "--windowed", "your_script.py"]

