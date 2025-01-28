#!/bin/bash

# Build live version
cp entrypoint-live.sh entrypoint.sh
docker build -t gmeet-live -f Dockerfile .

# Build pre-recorded version
cp entrypoint-prerecorded.sh entrypoint.sh
docker build -t gmeet-prerecorded -f Dockerfile .