import json
import yaml
from urllib.parse import urlparse

class SwaggerGenerator:
    def __init__(self):
        self.swagger_version = "3.0.0"
    
    def generate(self, wsdl_data):
        """Generate OpenAPI 3.0 specification from WSDL data"""
        
        # Extract base URL from service endpoints
        base_url = self._extract_base_url(wsdl_data.get('services', []))
        
        swagger_spec = {
            "openapi": self.swagger_version,
            "info": {
                "title": wsdl_data.get('name', 'SOAP Web Service'),
                "description": wsdl_data.get('description', 'SOAP Web Service converted from WSDL'),
                "version": "1.0.0",
                "contact": {
                    "name": "API Support"
                }
            },
            "servers": [
                {
                    "url": base_url,
                    "description": "SOAP Service Endpoint"
                }
            ] if base_url else [],
            "paths": {},
            "components": {
                "schemas": self._generate_schemas(wsdl_data.get('types', {})),
                "securitySchemes": {}
            },
            "tags": [
                {
                    "name": "SOAP Operations",
                    "description": "SOAP web service operations"
                }
            ]
        }
        
        # Generate paths from operations
        operations = wsdl_data.get('operations', [])
        for operation in operations:
            path = f"/{operation['name']}"
            swagger_spec["paths"][path] = self._generate_operation_spec(operation, wsdl_data)
        
        return swagger_spec
    
    def _extract_base_url(self, services):
        """Extract base URL from service endpoints"""
        for service in services:
            for port in service.get('ports', []):
                location = port.get('location', '')
                if location:
                    parsed = urlparse(location)
                    if parsed.scheme and parsed.netloc:
                        # Return base URL without path
                        return f"{parsed.scheme}://{parsed.netloc}"
        return "https://example.com"
    
    def _generate_operation_spec(self, operation, wsdl_data):
        """Generate OpenAPI operation specification"""
        
        operation_spec = {
            "post": {
                "tags": ["SOAP Operations"],
                "summary": operation.get('name', 'SOAP Operation'),
                "description": operation.get('documentation') or f"SOAP operation: {operation.get('name')}",
                "operationId": operation.get('name'),
                "requestBody": {
                    "description": "SOAP request body",
                    "required": True,
                    "content": {
                        "text/xml": {
                            "schema": {
                                "type": "string",
                                "example": self._generate_soap_example(operation, 'request')
                            }
                        },
                        "application/soap+xml": {
                            "schema": {
                                "type": "string",
                                "example": self._generate_soap_example(operation, 'request')
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful SOAP response",
                        "content": {
                            "text/xml": {
                                "schema": {
                                    "type": "string",
                                    "example": self._generate_soap_example(operation, 'response')
                                }
                            }
                        }
                    },
                    "500": {
                        "description": "SOAP Fault",
                        "content": {
                            "text/xml": {
                                "schema": {
                                    "type": "string",
                                    "example": self._generate_soap_fault_example()
                                }
                            }
                        }
                    }
                },
                "parameters": [
                    {
                        "name": "SOAPAction",
                        "in": "header",
                        "description": "SOAP Action header",
                        "required": False,
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "Content-Type",
                        "in": "header",
                        "description": "Content type",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "enum": ["text/xml", "application/soap+xml"],
                            "default": "text/xml"
                        }
                    }
                ]
            }
        }
        
        # Add input/output schema references if available
        if operation.get('input'):
            operation_spec["post"]["requestBody"]["content"]["application/json"] = {
                "schema": self._generate_input_schema(operation['input'], wsdl_data)
            }
        
        if operation.get('output'):
            operation_spec["post"]["responses"]["200"]["content"]["application/json"] = {
                "schema": self._generate_output_schema(operation['output'], wsdl_data)
            }
        
        return operation_spec
    
    def _generate_input_schema(self, input_msg, wsdl_data):
        """Generate input schema from message definition"""
        if not input_msg or not input_msg.get('parts'):
            return {"type": "object"}
        
        properties = {}
        required = []
        
        for part in input_msg['parts']:
            part_name = part.get('name', 'parameter')
            part_type = part.get('type') or part.get('element', 'string')
            
            # Map to OpenAPI type
            openapi_type = self._map_type_to_openapi(part_type)
            properties[part_name] = openapi_type
            required.append(part_name)
        
        schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            schema["required"] = required
        
        return schema
    
    def _generate_output_schema(self, output_msg, wsdl_data):
        """Generate output schema from message definition"""
        if not output_msg or not output_msg.get('parts'):
            return {"type": "object"}
        
        properties = {}
        
        for part in output_msg['parts']:
            part_name = part.get('name', 'result')
            part_type = part.get('type') or part.get('element', 'string')
            
            # Map to OpenAPI type
            openapi_type = self._map_type_to_openapi(part_type)
            properties[part_name] = openapi_type
        
        return {
            "type": "object",
            "properties": properties
        }
    
    def _map_type_to_openapi(self, wsdl_type):
        """Map WSDL/XSD types to OpenAPI schema"""
        if not wsdl_type:
            return {"type": "string"}
        
        # Remove namespace prefix
        if ':' in wsdl_type:
            wsdl_type = wsdl_type.split(':')[1]
        
        type_mapping = {
            'string': {"type": "string"},
            'int': {"type": "integer", "format": "int32"},
            'integer': {"type": "integer"},
            'long': {"type": "integer", "format": "int64"},
            'short': {"type": "integer", "format": "int32"},
            'byte': {"type": "integer", "format": "int32"},
            'double': {"type": "number", "format": "double"},
            'float': {"type": "number", "format": "float"},
            'decimal': {"type": "number"},
            'boolean': {"type": "boolean"},
            'date': {"type": "string", "format": "date"},
            'dateTime': {"type": "string", "format": "date-time"},
            'time': {"type": "string", "format": "time"},
            'base64Binary': {"type": "string", "format": "byte"},
            'hexBinary': {"type": "string", "format": "binary"},
            'anyURI': {"type": "string", "format": "uri"}
        }
        
        return type_mapping.get(wsdl_type.lower(), {"type": "string"})
    
    def _generate_schemas(self, types):
        """Generate component schemas from WSDL types"""
        schemas = {}
        
        for type_name, type_def in types.items():
            if type_def.get('type') == 'object':
                schema = {
                    "type": "object",
                    "properties": {}
                }
                
                properties = type_def.get('properties', {})
                required = []
                
                for prop_name, prop_def in properties.items():
                    prop_schema = {"type": prop_def.get('type', 'string')}
                    
                    if prop_def.get('array'):
                        prop_schema = {
                            "type": "array",
                            "items": prop_schema
                        }
                    
                    schema["properties"][prop_name] = prop_schema
                    
                    if prop_def.get('required'):
                        required.append(prop_name)
                
                if required:
                    schema["required"] = required
                
                schemas[type_name] = schema
            else:
                # Simple type
                schemas[type_name] = self._map_type_to_openapi(type_def.get('type', 'string'))
        
        return schemas
    
    def _generate_soap_example(self, operation, msg_type):
        """Generate SOAP envelope example"""
        op_name = operation.get('name', 'Operation')
        
        if msg_type == 'request':
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header>
        <!-- Optional SOAP headers -->
    </soap:Header>
    <soap:Body>
        <{op_name} xmlns="http://example.com/service">
            <!-- Request parameters -->
        </{op_name}>
    </soap:Body>
</soap:Envelope>'''
        else:
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <{op_name}Response xmlns="http://example.com/service">
            <!-- Response data -->
        </{op_name}Response>
    </soap:Body>
</soap:Envelope>'''
    
    def _generate_soap_fault_example(self):
        """Generate SOAP fault example"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>soap:Server</faultcode>
            <faultstring>Server Error</faultstring>
            <detail>
                <!-- Fault details -->
            </detail>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>'''
    
    def to_json(self, swagger_spec, indent=2):
        """Convert swagger spec to JSON string"""
        return json.dumps(swagger_spec, indent=indent, ensure_ascii=False)
    
    def to_yaml(self, swagger_spec):
        """Convert swagger spec to YAML string"""
        return yaml.dump(swagger_spec, default_flow_style=False, allow_unicode=True)
