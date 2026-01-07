"""Simple mock HTTP servers for testing WeChat and CXone integrations."""
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockCXoneHandler(BaseHTTPRequestHandler):
    """Mock CXone API server handler."""
    
    def do_POST(self):
        """Handle POST requests to mock CXone API."""
        parsed_path = urlparse(self.path)
        
        # Handle message posting
        if '/channels/' in parsed_path.path and '/messages' in parsed_path.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                payload = json.loads(body.decode('utf-8'))
                logger.info(f"[Mock CXone] Received message: {json.dumps(payload, indent=2)}")
                
                # Return mock response
                response = {
                    "id": "mock_cxone_message_id_123",
                    "status": "created",
                    "thread": payload.get("thread", {}),
                    "message": payload.get("message", {})
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                logger.error(f"[Mock CXone] Error processing request: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"[Mock CXone] {format % args}")


class MockWeChatHandler(BaseHTTPRequestHandler):
    """Mock WeChat API server handler."""
    
    def do_POST(self):
        """Handle POST requests to mock WeChat API."""
        parsed_path = urlparse(self.path)
        
        # Handle message sending (simulate WeChat API)
        if '/cgi-bin/message/custom/send' in parsed_path.path:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                payload = json.loads(body.decode('utf-8'))
                logger.info(f"[Mock WeChat] Received send request: {json.dumps(payload, indent=2)}")
                
                # Return mock WeChat API response
                response = {
                    "errcode": 0,
                    "errmsg": "ok",
                    "msgid": "mock_wechat_msgid_456"
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                logger.error(f"[Mock WeChat] Error processing request: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"[Mock WeChat] {format % args}")


def run_mock_cxone_server(port=8001):
    """Run mock CXone server on specified port."""
    server = HTTPServer(('localhost', port), MockCXoneHandler)
    logger.info(f"Mock CXone server running on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down mock CXone server")
        server.shutdown()


def run_mock_wechat_server(port=8002):
    """Run mock WeChat server on specified port."""
    server = HTTPServer(('localhost', port), MockWeChatHandler)
    logger.info(f"Mock WeChat server running on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down mock WeChat server")
        server.shutdown()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'cxone':
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8001
            run_mock_cxone_server(port)
        elif sys.argv[1] == 'wechat':
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8002
            run_mock_wechat_server(port)
        else:
            print("Usage: python mock_servers.py [cxone|wechat] [port]")
    else:
        # Run both servers in separate threads
        cxone_thread = threading.Thread(target=run_mock_cxone_server, args=(8001,), daemon=True)
        wechat_thread = threading.Thread(target=run_mock_wechat_server, args=(8002,), daemon=True)
        
        cxone_thread.start()
        wechat_thread.start()
        
        logger.info("Both mock servers running. Press Ctrl+C to stop.")
        try:
            while True:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            logger.info("Shutting down mock servers")

