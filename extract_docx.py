import zipfile
import xml.etree.ElementTree as ET

docx_path = '课程设计模板.docx'
with zipfile.ZipFile(docx_path, 'r') as zip_ref:
    xml_content = zip_ref.read('word/document.xml')
    root = ET.fromstring(xml_content)
    
    # Extract all text elements
    text_elements = []
    for elem in root.iter():
        if elem.text:
            text_elements.append(elem.text)
    
    # Print all text
    for text in text_elements:
        print(text)
