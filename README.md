# WSDL to Swagger Converter

A web application that converts WSDL (Web Services Description Language) files to Swagger/OpenAPI format for better documentation and API management.

## Features

- **Multiple Input Methods**: Upload WSDL files, paste WSDL text directly, or provide a URL to a WSDL file
- **Clean Swagger Output**: Generates readable OpenAPI 3.0 specifications
- **Web Interface**: Modern, user-friendly web interface
- **Download Support**: Download generated Swagger files as JSON or YAML

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Choose your input method:
   - **File Upload**: Select a WSDL file from your computer
   - **Text Input**: Copy and paste WSDL content directly
   - **URL Input**: Provide a URL to a WSDL file

2. Click "Convert to Swagger" to process the WSDL

3. View the generated Swagger documentation in the output panel

4. Download the result as JSON or YAML format

## Technical Details

- Built with Flask (Python backend)
- Uses lxml for XML parsing
- Generates OpenAPI 3.0 compliant specifications
- Responsive web design with modern UI/UX

## License

MIT License
