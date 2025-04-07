from config.Config import get_config
from flask import Response
import os

def add_cors_headers(response, status_code=200):
    """
    Add CORS headers to the response
    
    Args:
        response: Flask response object
        status_code: HTTP status code (default: 200)
        
    Returns:
        Response with CORS headers
    """
    if isinstance(response, Response):
        config = get_config()
        # Use environment variable if available, otherwise fallback to config
        allowed_origin = os.getenv('ALLOWED_ORIGIN', 
                                  config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Origin', allowed_origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.status_code = status_code
        return response
    else:
        resp = Response(response)
        # Use environment variable if available, otherwise fallback to '*'
        allowed_origin = os.getenv('ALLOWED_ORIGIN', '*')
        resp.headers.add('Access-Control-Allow-Origin', allowed_origin)
        resp.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        resp.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        resp.status_code = status_code
        return resp 