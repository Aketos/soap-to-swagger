import xml.etree.ElementTree as ET
from lxml import etree
import re
from urllib.parse import urlparse

class WSDLParser:
    def __init__(self):
        self.namespaces = {
            'wsdl': 'http://schemas.xmlsoap.org/wsdl/',
            'soap': 'http://schemas.xmlsoap.org/wsdl/soap/',
            'soap12': 'http://schemas.xmlsoap.org/wsdl/soap12/',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'tns': None  # Will be set dynamically
        }
        
    def parse(self, wsdl_content):
        """Parse WSDL content and extract service information"""
        try:
            # Parse XML
            root = etree.fromstring(wsdl_content.encode('utf-8'))
            
            # Update target namespace
            target_ns = root.get('targetNamespace')
            if target_ns:
                self.namespaces['tns'] = target_ns
            
            # Extract service information
            service_info = {
                'name': self._get_service_name(root),
                'description': self._get_service_description(root),
                'target_namespace': target_ns,
                'operations': self._extract_operations(root),
                'types': self._extract_types(root),
                'bindings': self._extract_bindings(root),
                'services': self._extract_services(root)
            }
            
            return service_info
            
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML syntax: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse WSDL: {str(e)}")
    
    def _get_service_name(self, root):
        """Extract service name from WSDL"""
        services = root.xpath('//wsdl:service', namespaces=self.namespaces)
        if services:
            return services[0].get('name', 'UnknownService')
        return 'UnknownService'
    
    def _get_service_description(self, root):
        """Extract service description from documentation elements"""
        docs = root.xpath('//wsdl:documentation', namespaces=self.namespaces)
        if docs:
            return docs[0].text or 'No description available'
        return 'SOAP Web Service converted from WSDL'
    
    def _extract_operations(self, root):
        """Extract operations from port types"""
        operations = []
        
        port_types = root.xpath('//wsdl:portType', namespaces=self.namespaces)
        for port_type in port_types:
            ops = port_type.xpath('.//wsdl:operation', namespaces=self.namespaces)
            for op in ops:
                operation = {
                    'name': op.get('name'),
                    'documentation': self._get_element_documentation(op),
                    'input': self._extract_message_info(root, op, 'input'),
                    'output': self._extract_message_info(root, op, 'output'),
                    'faults': self._extract_faults(root, op)
                }
                operations.append(operation)
        
        return operations
    
    def _extract_message_info(self, root, operation, msg_type):
        """Extract input/output message information"""
        msg_elements = operation.xpath(f'.//wsdl:{msg_type}', namespaces=self.namespaces)
        if not msg_elements:
            return None
            
        msg_element = msg_elements[0]
        msg_name = msg_element.get('message')
        
        if msg_name:
            # Remove namespace prefix if present
            if ':' in msg_name:
                msg_name = msg_name.split(':')[1]
            
            # Find message definition
            messages = root.xpath(f'//wsdl:message[@name="{msg_name}"]', namespaces=self.namespaces)
            if messages:
                return self._parse_message(messages[0])
        
        return None
    
    def _parse_message(self, message):
        """Parse message parts"""
        parts = []
        part_elements = message.xpath('.//wsdl:part', namespaces=self.namespaces)
        
        for part in part_elements:
            part_info = {
                'name': part.get('name'),
                'element': part.get('element'),
                'type': part.get('type')
            }
            parts.append(part_info)
        
        return {
            'name': message.get('name'),
            'parts': parts
        }
    
    def _extract_faults(self, root, operation):
        """Extract fault information"""
        faults = []
        fault_elements = operation.xpath('.//wsdl:fault', namespaces=self.namespaces)
        
        for fault in fault_elements:
            fault_info = {
                'name': fault.get('name'),
                'message': fault.get('message'),
                'documentation': self._get_element_documentation(fault)
            }
            faults.append(fault_info)
        
        return faults
    
    def _extract_types(self, root):
        """Extract type definitions from schema"""
        types = {}
        
        # Look for embedded schemas
        schemas = root.xpath('//xsd:schema', namespaces=self.namespaces)
        for schema in schemas:
            # Extract complex types
            complex_types = schema.xpath('.//xsd:complexType', namespaces=self.namespaces)
            for ct in complex_types:
                type_name = ct.get('name')
                if type_name:
                    types[type_name] = self._parse_complex_type(ct)
            
            # Extract simple types
            simple_types = schema.xpath('.//xsd:simpleType', namespaces=self.namespaces)
            for st in simple_types:
                type_name = st.get('name')
                if type_name:
                    types[type_name] = self._parse_simple_type(st)
            
            # Extract elements
            elements = schema.xpath('.//xsd:element', namespaces=self.namespaces)
            for elem in elements:
                elem_name = elem.get('name')
                if elem_name:
                    types[elem_name] = self._parse_element(elem)
        
        return types
    
    def _parse_complex_type(self, complex_type):
        """Parse complex type definition"""
        properties = {}
        
        # Look for sequence elements
        sequences = complex_type.xpath('.//xsd:sequence', namespaces=self.namespaces)
        for seq in sequences:
            elements = seq.xpath('.//xsd:element', namespaces=self.namespaces)
            for elem in elements:
                prop_name = elem.get('name')
                prop_type = elem.get('type', 'string')
                min_occurs = elem.get('minOccurs', '1')
                max_occurs = elem.get('maxOccurs', '1')
                
                properties[prop_name] = {
                    'type': self._map_xsd_type(prop_type),
                    'required': min_occurs != '0',
                    'array': max_occurs == 'unbounded' or (max_occurs.isdigit() and int(max_occurs) > 1)
                }
        
        return {
            'type': 'object',
            'properties': properties
        }
    
    def _parse_simple_type(self, simple_type):
        """Parse simple type definition"""
        restrictions = simple_type.xpath('.//xsd:restriction', namespaces=self.namespaces)
        if restrictions:
            base_type = restrictions[0].get('base', 'string')
            return {
                'type': self._map_xsd_type(base_type),
                'base': base_type
            }
        
        return {'type': 'string'}
    
    def _parse_element(self, element):
        """Parse element definition"""
        elem_type = element.get('type', 'string')
        return {
            'type': self._map_xsd_type(elem_type),
            'xml_type': elem_type
        }
    
    def _map_xsd_type(self, xsd_type):
        """Map XSD types to OpenAPI types"""
        if not xsd_type:
            return 'string'
        
        # Remove namespace prefix
        if ':' in xsd_type:
            xsd_type = xsd_type.split(':')[1]
        
        type_mapping = {
            'string': 'string',
            'int': 'integer',
            'integer': 'integer',
            'long': 'integer',
            'short': 'integer',
            'byte': 'integer',
            'double': 'number',
            'float': 'number',
            'decimal': 'number',
            'boolean': 'boolean',
            'date': 'string',
            'dateTime': 'string',
            'time': 'string',
            'base64Binary': 'string',
            'hexBinary': 'string',
            'anyURI': 'string'
        }
        
        return type_mapping.get(xsd_type.lower(), 'string')
    
    def _extract_bindings(self, root):
        """Extract binding information"""
        bindings = []
        binding_elements = root.xpath('//wsdl:binding', namespaces=self.namespaces)
        
        for binding in binding_elements:
            binding_info = {
                'name': binding.get('name'),
                'type': binding.get('type'),
                'transport': self._get_soap_transport(binding),
                'style': self._get_soap_style(binding),
                'operations': self._extract_binding_operations(binding)
            }
            bindings.append(binding_info)
        
        return bindings
    
    def _get_soap_transport(self, binding):
        """Get SOAP transport from binding"""
        soap_bindings = binding.xpath('.//soap:binding', namespaces=self.namespaces)
        if soap_bindings:
            return soap_bindings[0].get('transport', 'http://schemas.xmlsoap.org/soap/http')
        return 'http://schemas.xmlsoap.org/soap/http'
    
    def _get_soap_style(self, binding):
        """Get SOAP style from binding"""
        soap_bindings = binding.xpath('.//soap:binding', namespaces=self.namespaces)
        if soap_bindings:
            return soap_bindings[0].get('style', 'document')
        return 'document'
    
    def _extract_binding_operations(self, binding):
        """Extract operations from binding"""
        operations = []
        op_elements = binding.xpath('.//wsdl:operation', namespaces=self.namespaces)
        
        for op in op_elements:
            soap_ops = op.xpath('.//soap:operation', namespaces=self.namespaces)
            soap_action = soap_ops[0].get('soapAction', '') if soap_ops else ''
            
            operations.append({
                'name': op.get('name'),
                'soap_action': soap_action
            })
        
        return operations
    
    def _extract_services(self, root):
        """Extract service endpoint information"""
        services = []
        service_elements = root.xpath('//wsdl:service', namespaces=self.namespaces)
        
        for service in service_elements:
            ports = service.xpath('.//wsdl:port', namespaces=self.namespaces)
            service_ports = []
            
            for port in ports:
                addresses = port.xpath('.//soap:address', namespaces=self.namespaces)
                if not addresses:
                    addresses = port.xpath('.//soap12:address', namespaces=self.namespaces)
                
                location = addresses[0].get('location') if addresses else ''
                
                service_ports.append({
                    'name': port.get('name'),
                    'binding': port.get('binding'),
                    'location': location
                })
            
            services.append({
                'name': service.get('name'),
                'ports': service_ports,
                'documentation': self._get_element_documentation(service)
            })
        
        return services
    
    def _get_element_documentation(self, element):
        """Get documentation text from element"""
        docs = element.xpath('.//wsdl:documentation', namespaces=self.namespaces)
        if docs and docs[0].text:
            return docs[0].text.strip()
        return None
