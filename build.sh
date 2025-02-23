#!/bin/bash
set -e  # Exit on error

# Install system dependencies
apt-get update && apt-get install -y portaudio19-dev

# Install Python dependencies
pip install -r requirements.txt
