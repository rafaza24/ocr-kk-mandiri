#!/bin/sh
PORT_VAL="${PORT:-5000}"
echo "🚀 Starting Server on Port ${PORT_VAL}..."
exec gunicorn --bind "0.0.0.0:${PORT_VAL}" --timeout 120 --workers 1 app:app
