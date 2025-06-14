#!/bin/bash

# Voice Assistant Startup Script
echo "Starting Voice Assistant..."

# Activate conda environment
source /Volumes/ExternalHD/applications/miniconda3/bin/activate speechy

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Warning: Ollama server not detected at localhost:11434"
    echo "Please ensure Ollama is installed and running:"
    echo "  ollama serve"
    echo ""
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the application
python main.py