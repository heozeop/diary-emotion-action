#!/bin/bash
set -e

# Python script를 비동기로 실행
python3 -c "import asyncio; from diary_emotion_action.main import main; asyncio.run(main())" 
