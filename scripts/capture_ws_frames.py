import asyncio
import websockets
import json

async def capture():
    uri = "wss://api.gemini.com/v1/marketdata/btcusd"
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        with open("/opt/hybrid-trading-bot/tests/fixtures/realws_frames_generic.jsonl", "w") as f:
            for i in range(50):
                message = await websocket.recv()
                print(f"Captured frame {i+1}/50")
                f.write(message + "\n")
                f.flush()

if __name__ == "__main__":
    asyncio.run(capture())
