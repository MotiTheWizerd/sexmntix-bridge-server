
import sys
import json
import logging

# Set up logging to stderr (which is redirected to file)
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
logger = logging.getLogger("echo_server")

logger.info("Echo server starting...")

while True:
    try:
        line = sys.stdin.readline()
        if not line:
            logger.info("EOF received, exiting.")
            break
        
        logger.info(f"Received: {line.strip()}")
        
        try:
            request = json.loads(line)
            # Respond to initialize
            if request.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {
                            "name": "echo-server",
                            "version": "1.0.0"
                        }
                    }
                }
                print(json.dumps(response), flush=True)
                logger.info("Sent initialize response")
            # Respond to ping
            elif request.get("method") == "ping":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {}
                }
                print(json.dumps(response), flush=True)
                logger.info("Sent ping response")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        break
