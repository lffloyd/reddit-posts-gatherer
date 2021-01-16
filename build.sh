#!/bin/bash

# pip install -r src/requirements.txt && \
#     pip install -r tests/requirements.txt
# pytest
sam validate --template template.yaml
sam build --use-container
# sam local invoke GatherPostsFunction --event events/event.json
