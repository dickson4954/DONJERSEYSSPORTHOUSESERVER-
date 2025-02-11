#!/bin/bash

# Update package list and install required dependencies
apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libtiff5-dev \
    python3-dev \
    python3-pip \
    build-essential \
    gcc \
    pkg-config

# Ensure pip is up-to-date
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
