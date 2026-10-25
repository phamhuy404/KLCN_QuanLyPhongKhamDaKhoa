import zipfile
import xml.etree.ElementTree as ET

doc_path = r'C:\Users\tuanq\.gemini\antigravity\brain\c5ae6137-07ba-409f-bf20-fd72925caa3f\.user_uploaded\media_1792904740706_ff6248c8.docx'
with zipfile.ZipFile(doc_path) as z:
    rels_xml = z.read('word/_rels/document.xml.rels')
    rels_tree = ET.fromstring(rels_xml)
    rel_map = {}
    for r in rels_tree:
        rel_map[r.attrib['Id']] = r.attrib.get('Target', '')
        
    xml_content = z.read('word/document.xml')
    tree = ET.fromstring(xml_content)
    
    body = tree.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
    
    with open('scratch/docx_structure.txt', 'w', encoding='utf-8') as out:
        for idx, elem in enumerate(body):
            texts = [node.text for node in elem.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            text = ''.join(texts).strip()
            
            blips = [node.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') 
                     for node in elem.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip')]
            images = [rel_map.get(b, b) for b in blips if b]
            
            if text or images:
                out.write(f'Item {idx}: TEXT="{text}" | IMAGES={images}\n')

print('Structure written to scratch/docx_structure.txt')
