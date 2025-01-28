#!/bin/bash

# Build live version
docker build -t gmeet-live -f Dockerfile.live .

# Build pre-recorded version
docker build -t gmeet-prerecorded -f Dockerfile.prerecorded .