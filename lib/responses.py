"""Response helpers for JSON responses"""


class JSONResponse:
    """Helper for consistent JSON responses"""
    
    @staticmethod
    def success(data=None, message=None):
        """Return success response"""
        response = {"ok": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        return response
    
    @staticmethod
    def error(message: str, code: int = 400, details=None):
        """Return error response"""
        response = {"ok": False, "error": message, "code": code}
        if details:
            response["details"] = details
        return response
