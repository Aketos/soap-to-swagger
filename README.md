# WSDL to Swagger Converter

A comprehensive web application that converts WSDL (Web Services Description Language) files to Swagger/OpenAPI format with management interface and interactive documentation.

## Features

### 🔄 Conversion
- **Multiple Input Methods**: Upload WSDL files, paste WSDL text directly, or provide a URL to a WSDL file
- **Clean Swagger Output**: Generates readable OpenAPI 3.0 specifications
- **Modern Web Interface**: Responsive, user-friendly design
- **Real-time Conversion**: Instant processing with progress feedback

### 📁 File Management
- **Persistent Storage**: Automatically saves converted files
- **Management Dashboard**: View, organize, and manage all converted files
- **File Operations**: Preview, download, and delete converted files
- **Metadata Tracking**: Track creation dates, operation counts, and schemas

### 📚 Interactive Documentation
- **Swagger UI Integration**: Full interactive API documentation
- **Try It Out**: Test API endpoints directly from the documentation
- **Multiple Formats**: Download as JSON or YAML
- **Professional Display**: Clean, organized API documentation

## Installation

### Quick Start
```bash
# Clone or download the project
cd soap-swagger

# Run the startup script (recommended)
./start.sh
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## Usage

### 1. Convert WSDL Files
1. Navigate to `http://localhost:5000`
2. Choose your input method:
   - **File Upload**: Select a WSDL file from your computer
   - **Text Input**: Copy and paste WSDL content directly
   - **URL Input**: Provide a URL to a WSDL file
3. Click "Convert to Swagger" to process the WSDL
4. View the generated Swagger documentation

### 2. Manage Converted Files
1. Navigate to `http://localhost:5000/manage`
2. View all your converted files in an organized dashboard
3. Use file operations:
   - **View Swagger UI**: Interactive API documentation
   - **Preview**: Quick view of the Swagger content
   - **Download**: Get JSON or YAML files
   - **Delete**: Remove unwanted files

### 3. Interactive Documentation
1. Click "View Swagger UI" from any converted file
2. Explore the interactive API documentation
3. Use "Try it out" to test endpoints
4. Download the specification in your preferred format

## Technical Details

- **Backend**: Python Flask with REST API
- **Frontend**: HTML/CSS/JavaScript with responsive design
- **XML Processing**: lxml for robust WSDL parsing
- **Documentation**: Swagger UI for interactive API docs
- **Storage**: File-based storage with JSON metadata
- **Standards**: OpenAPI 3.0 compliant specifications

## Project Structure

```
soap-swagger/
├── app.py                 # Main Flask application
├── wsdl_parser.py         # WSDL parsing logic
├── swagger_generator.py   # OpenAPI generation
├── templates/
│   ├── index.html        # Main converter interface
│   ├── manage.html       # File management interface
│   └── swagger_ui.html   # Interactive Swagger UI
├── requirements.txt      # Python dependencies
├── start.sh             # Startup script
└── .gitignore           # Git ignore rules
```

## API Endpoints

- `GET /` - Main converter interface
- `POST /convert` - Convert WSDL to Swagger
- `GET /manage` - File management interface
- `GET /api/files` - List all converted files
- `GET /api/files/<id>` - Get specific file content
- `DELETE /api/files/<id>` - Delete a file
- `GET /api/files/<id>/download/<format>` - Download file
- `GET /swagger-ui/<id>` - Interactive Swagger UI

## License

MIT License
