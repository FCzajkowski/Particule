"""File upload handling for multipart/form-data"""

from typing import Dict, Any


class FileUpload:
    """Handle multipart file uploads"""
    
    @staticmethod
    def parse_multipart(body: bytes, content_type: str) -> Dict[str, Any]:
        """Parse multipart/form-data"""
        # Extract boundary
        boundary = None
        for part in content_type.split(';'):
            if 'boundary=' in part:
                boundary = part.split('boundary=')[1].strip()
                break
        
        if not boundary:
            return {}
        
        # Parse parts
        boundary_bytes = f'--{boundary}'.encode()
        parts = body.split(boundary_bytes)
        
        result = {}
        for part in parts:
            if not part or part == b'--\r\n' or part == b'--':
                continue
            
            # Split headers and content
            if b'\r\n\r\n' in part:
                headers_section, content = part.split(b'\r\n\r\n', 1)
                content = content.rstrip(b'\r\n')
                
                # Parse Content-Disposition
                headers_str = headers_section.decode('utf-8', errors='ignore')
                name = None
                filename = None
                
                for line in headers_str.split('\r\n'):
                    if 'Content-Disposition' in line:
                        for item in line.split(';'):
                            if 'name=' in item:
                                name = item.split('name=')[1].strip('"')
                            if 'filename=' in item:
                                filename = item.split('filename=')[1].strip('"')
                
                if name:
                    if filename:
                        result[name] = {
                            'filename': filename,
                            'content': content,
                            'size': len(content)
                        }
                    else:
                        result[name] = content.decode('utf-8', errors='ignore')
        
        return result
