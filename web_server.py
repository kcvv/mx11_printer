#!/usr/bin/env python3
"""
Simple web server for MX11 printer interface
"""

import asyncio
import json
import os
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from mx11 import Printer
from image_convert import text_to_image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class PrinterHandler(BaseHTTPRequestHandler):
    printer = None
    
    def do_GET(self):
        if self.path == '/':
            self.serve_file('web_interface.html', 'text/html')
        else:
            self.send_error(404)
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        
        if self.path == '/status':
            asyncio.run(self.handle_status())
        elif self.path == '/serial':
            asyncio.run(self.handle_serial())
        elif self.path == '/preview-image':
            asyncio.run(self.handle_preview_image())
        elif self.path == '/print-image':
            asyncio.run(self.handle_print_image())
        elif self.path == '/print-text':
            asyncio.run(self.handle_print_text())
        elif self.path == '/feed':
            asyncio.run(self.handle_feed())
        elif self.path == '/calibrate':
            asyncio.run(self.handle_calibrate())
        else:
            self.send_error(404)
    
    def serve_file(self, filename, content_type):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    async def get_printer(self):
        if not self.printer:
            # Load config
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                mac_address = config.get('mac_address', 'CA:06:26:70:8B:06')
                self.printer = Printer(mac_address, log_level=logging.WARNING)
            except:
                return None
        return self.printer
    
    async def handle_status(self):
        printer = await self.get_printer()
        if not printer:
            self.send_json({'success': False, 'message': 'Printer not configured'})
            return
        
        try:
            await printer.connect()
            status = await printer.get_status()
            await printer.disconnect()
            
            if status:
                self.send_json({'success': True, 'message': 'Printer is ready'})
            else:
                self.send_json({'success': False, 'message': 'Printer not ready or low battery'})
        except Exception as e:
            self.send_json({'success': False, 'message': f'Connection error: {str(e)}'})
    
    async def handle_serial(self):
        printer = await self.get_printer()
        if not printer:
            self.send_json({'success': False, 'message': 'Printer not configured'})
            return
        
        try:
            await printer.connect()
            serial = await printer.get_serial_number()
            await printer.disconnect()
            
            self.send_json({'success': True, 'serial': serial})
        except Exception as e:
            self.send_json({'success': False, 'message': f'Error: {str(e)}'})
    
    async def handle_preview_image(self):
        # Parse multipart form data to get image and binarization method
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            import base64
            from image_convert import preprocess_image
            
            # Extract image file and binarization method (simplified parsing)
            boundary = post_data.split(b'\r\n')[0]
            parts = post_data.split(boundary)
            
            image_data = None
            binarization = 'atkinson'  # default
            
            for part in parts:
                if b'name="binarization"' in part:
                    # Extract binarization method
                    data_start = part.find(b'\r\n\r\n') + 4
                    if data_start > 3:
                        binarization = part[data_start:].decode('utf-8').strip()
                elif b'filename=' in part and b'image' in part:
                    # Extract image data
                    data_start = part.find(b'\r\n\r\n') + 4
                    if data_start > 3:
                        image_data = part[data_start:]
                        if image_data.endswith(b'\r\n'):
                            image_data = image_data[:-2]
            
            if not image_data:
                self.send_json({'success': False, 'message': 'No image data found'})
                return
            
            # Save uploaded image to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(image_data)
                tmp_path = tmp.name
            
            # Process image with selected binarization
            processed_img = preprocess_image(tmp_path, width=384, dither=binarization)
            
            # Convert processed image to base64 for web display
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as preview_tmp:
                processed_img.save(preview_tmp.name, 'PNG')
                preview_path = preview_tmp.name
            
            with open(preview_path, 'rb') as f:
                preview_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Clean up temp files
            os.unlink(tmp_path)
            os.unlink(preview_path)
            
            self.send_json({
                'success': True, 
                'preview': f'data:image/png;base64,{preview_data}',
                'message': f'Preview generated with {binarization} dithering'
            })
            
        except Exception as e:
            self.send_json({'success': False, 'message': f'Preview error: {str(e)}'})

    async def handle_print_image(self):
        # Parse multipart form data (simplified)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Extract image file and parameters (basic implementation)
        # In production, use proper multipart parsing
        try:
            # Save uploaded image to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                # Extract image data from multipart (simplified)
                boundary = post_data.split(b'\r\n')[0]
                parts = post_data.split(boundary)
                
                for part in parts:
                    if b'filename=' in part and b'image' in part:
                        # Find image data
                        data_start = part.find(b'\r\n\r\n') + 4
                        if data_start > 3:
                            image_data = part[data_start:]
                            # Remove trailing boundary
                            if image_data.endswith(b'\r\n'):
                                image_data = image_data[:-2]
                            tmp.write(image_data)
                            break
                
                tmp_path = tmp.name
            
            # Print the image
            printer = await self.get_printer()
            await printer.connect()
            await printer.print_image(tmp_path, binarization='atkinson', extra_feed=15)
            await printer.disconnect()
            
            # Clean up
            os.unlink(tmp_path)
            
            self.send_json({'success': True, 'message': 'Image printed successfully'})
            
        except Exception as e:
            self.send_json({'success': False, 'message': f'Print error: {str(e)}'})
    
    async def handle_print_text(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data)
        
        try:
            text = data.get('text', '')
            font_size = int(data.get('fontSize', 20))  # Convert to int
            feed = int(data.get('feed', 15))
            
            # Convert text to image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                img = text_to_image(text, font_size=font_size)  # Pass as int
                img.save(tmp.name)
                tmp_path = tmp.name
            
            # Print the text image
            printer = await self.get_printer()
            await printer.connect()
            await printer.print_image(tmp_path, binarization='atkinson', extra_feed=feed)
            await printer.disconnect()
            
            # Clean up
            os.unlink(tmp_path)
            
            self.send_json({'success': True, 'message': 'Text printed successfully'})
            
        except Exception as e:
            self.send_json({'success': False, 'message': f'Print error: {str(e)}'})
    
    async def handle_feed(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data)
        
        try:
            amount = int(data.get('amount', 10))
            
            printer = await self.get_printer()
            await printer.connect()
            await printer.feed_paper(amount)
            await printer.disconnect()
            
            self.send_json({'success': True, 'message': f'Fed {amount} lines'})
            
        except Exception as e:
            self.send_json({'success': False, 'message': f'Feed error: {str(e)}'})
    
    async def handle_calibrate(self):
        try:
            printer = await self.get_printer()
            await printer.connect()
            await printer.calibrate_label()
            await printer.disconnect()
            
            self.send_json({'success': True, 'message': 'Label calibration sent'})
            
        except Exception as e:
            self.send_json({'success': False, 'message': f'Calibration error: {str(e)}'})

def run_server():
    server = HTTPServer(('localhost', 8080), PrinterHandler)
    print("MX11 Printer Web Interface running at http://localhost:8080")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == '__main__':
    run_server()
