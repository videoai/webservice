#!/bin/sh

# Remove old database
rm /tmp/test.db

# Create new database
python create_db.py

# Enrol some people
curl -L -F image=@test_data/Alberto_1.jpg -F "name=Alberto" http://localhost:5000/enrol
curl -L -F image=@test_data/Fred_1.jpg -F "name=Fred" http://localhost:5000/enrol
curl -L -F image=@test_data/Kieron_1.jpg -F "name=Kieron" http://localhost:5000/enrol
curl -L -F image=@test_data/Kjetil_1.jpg -F "name=Kjetil" http://localhost:5000/enrol
curl -L -F image=@test_data/Olivier_1.jpg -F "name=Olivier" http://localhost:5000/enrol

# make sure all processes are done
sleep 5

# Perform searches
curl -L -F image=@test_data/Fred_2.jpg http://localhost:5000/search
curl -L -F image=@test_data/Kieron_2.jpg http://localhost:5000/search
curl -L -F image=@test_data/Olivier_2.jpg http://localhost:5000/search

