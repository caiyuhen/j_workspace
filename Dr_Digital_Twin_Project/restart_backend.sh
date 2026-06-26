#!/bin/bash
cd /home/user/Dr_Digital_Twin_Project
echo "user" | sudo -S docker compose up -d --build dr_digital_twin_backend
