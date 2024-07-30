#!/bin/bash
source ./venv/bin/activate
exec ./venv/bin/gunicorn textblog.wsgi -b "127.0.0.1:8001" --log-file - --timeout 20 
