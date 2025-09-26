from fastapi import FastAPI, Request, Response
import logging
from google.protobuf.message import DecodeError
import opamp_pb2 as opamp
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opamp-server")

app = FastAPI()

@app.post("/v1/opamp")
async def opamp_handler(request: Request):
    try:
        body = await request.body()
        logger.info(f"Received {len(body)} bytes from collector")

        # Decode incoming AgentToServer message
        msg = opamp.AgentToServer()
        msg.ParseFromString(body)
        logger.info(f"Decoded OpAMP message: {msg}")

        # Build minimal ServerToAgent response
        resp = opamp.ServerToAgent()
        resp.instance_uid = b"server-1234"  # required

        # Send protobuf response
        return Response(content=resp.SerializeToString(),
                        media_type="application/x-protobuf")

    except DecodeError as e:
        logger.error(f"Failed to parse Protobuf: {e}")
        return {"error": "invalid protobuf"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)