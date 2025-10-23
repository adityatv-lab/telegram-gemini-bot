#!/usr/bin/env bash
# Force reinstall dependencies each build
pip install --upgrade pip
pip install -r requirements.txt
python bot.py
