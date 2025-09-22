from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import tempfile
import requests
from datetime import datetime
from wsdl_parser import WSDLParser
from swagger_generator import SwaggerGenerator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create storage directory for converted files
STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'storage')
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_wsdl():
    try:
        wsdl_content = None
        
        # Handle different input methods
        if 'wsdl_file' in request.files and request.files['wsdl_file'].filename:
            # File upload
            file = request.files['wsdl_file']
            wsdl_content = file.read().decode('utf-8')
        elif request.form.get('wsdl_text'):
            # Text input
            wsdl_content = request.form.get('wsdl_text')
        elif request.form.get('wsdl_url'):
            # URL input
            url = request.form.get('wsdl_url')
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            wsdl_content = response.text
        else:
            return jsonify({'error': 'No WSDL input provided'}), 400
        
        if not wsdl_content:
            return jsonify({'error': 'Empty WSDL content'}), 400
        
        # Parse WSDL
        parser = WSDLParser()
        wsdl_data = parser.parse(wsdl_content)
        
        # Generate Swagger
        generator = SwaggerGenerator()
        swagger_spec = generator.generate(wsdl_data)
        
        # Save the converted file
        file_id = save_converted_file(wsdl_data.get('name', 'UnknownService'), swagger_spec, wsdl_content)
        
        return jsonify({
            'success': True,
            'swagger': swagger_spec,
            'file_id': file_id
        })
        
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch WSDL from URL: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

@app.route('/manage')
def manage():
    return render_template('manage.html')

@app.route('/api/files')
def list_files():
    """Get list of all converted files"""
    files = []
    metadata_file = os.path.join(STORAGE_DIR, 'metadata.json')
    
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            files = json.load(f)
    
    return jsonify(files)

@app.route('/api/files/<file_id>')
def get_file(file_id):
    """Get specific file content"""
    metadata_file = os.path.join(STORAGE_DIR, 'metadata.json')
    
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            files = json.load(f)
        
        for file_info in files:
            if file_info['id'] == file_id:
                file_path = os.path.join(STORAGE_DIR, f"{file_id}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        swagger_content = json.load(f)
                    return jsonify({
                        'metadata': file_info,
                        'swagger': swagger_content
                    })
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a converted file"""
    metadata_file = os.path.join(STORAGE_DIR, 'metadata.json')
    
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            files = json.load(f)
        
        # Remove file from metadata
        files = [f for f in files if f['id'] != file_id]
        
        with open(metadata_file, 'w') as f:
            json.dump(files, f, indent=2)
        
        # Remove actual files
        for ext in ['.json', '.yaml', '.wsdl']:
            file_path = os.path.join(STORAGE_DIR, f"{file_id}{ext}")
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return jsonify({'success': True})
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/files/<file_id>/download/<format>')
def download_file(file_id, format):
    """Download file in specified format"""
    if format not in ['json', 'yaml']:
        return jsonify({'error': 'Invalid format'}), 400
    
    file_path = os.path.join(STORAGE_DIR, f"{file_id}.{format}")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=f"swagger_{file_id}.{format}")
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/swagger-ui/<file_id>')
def swagger_ui(file_id):
    """Display Swagger UI for a specific file"""
    return render_template('swagger_ui.html', file_id=file_id)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

def save_converted_file(service_name, swagger_spec, wsdl_content):
    """Save converted file to storage"""
    import uuid
    from swagger_generator import SwaggerGenerator
    
    file_id = str(uuid.uuid4())[:8]  # Short UUID
    timestamp = datetime.now().isoformat()
    
    # Save swagger as JSON
    json_path = os.path.join(STORAGE_DIR, f"{file_id}.json")
    with open(json_path, 'w') as f:
        json.dump(swagger_spec, f, indent=2)
    
    # Save swagger as YAML
    generator = SwaggerGenerator()
    yaml_content = generator.to_yaml(swagger_spec)
    yaml_path = os.path.join(STORAGE_DIR, f"{file_id}.yaml")
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    # Save original WSDL
    wsdl_path = os.path.join(STORAGE_DIR, f"{file_id}.wsdl")
    with open(wsdl_path, 'w') as f:
        f.write(wsdl_content)
    
    # Update metadata
    metadata_file = os.path.join(STORAGE_DIR, 'metadata.json')
    files = []
    
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            files = json.load(f)
    
    file_info = {
        'id': file_id,
        'name': service_name,
        'title': swagger_spec.get('info', {}).get('title', service_name),
        'description': swagger_spec.get('info', {}).get('description', ''),
        'version': swagger_spec.get('info', {}).get('version', '1.0.0'),
        'created_at': timestamp,
        'operations_count': len(swagger_spec.get('paths', {})),
        'schemas_count': len(swagger_spec.get('components', {}).get('schemas', {}))
    }
    
    files.append(file_info)
    
    with open(metadata_file, 'w') as f:
        json.dump(files, f, indent=2)
    
    return file_id

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
