import shutil
import xml.etree.ElementTree as ET
import os
from PyPDF2 import PdfReader, PdfWriter
import xml.dom.minidom as minidom

def write_pretty_xml(element, file_path):
    """
    Writes an ElementTree to an XML file with pretty printing and correct indentation.

    Parameters:
    element (ET.Element): The root element of the XML tree.
    file_path (str): The path to the file where the XML should be written.
    """
    # Convert the ElementTree element to a string
    xml_string = ET.tostring(element, encoding='UTF-8', method='xml')

    # Parse the string using minidom for pretty printing
    dom = minidom.parseString(xml_string)
    pretty_xml_as_string = dom.toprettyxml(indent="  ")

    # Write the pretty-printed XML to a file
    with open(file_path, 'w', encoding='UTF-8') as f:
        f.write(pretty_xml_as_string)


# Recursive function to print elements
def counter(element, level=0, search="new-page", count=0):
    text = f"Tag: {element.tag}, Attributes: {element.attrib}, Text: {element.text.strip() if element.text else 'None'}"
    if search in text:
        count += 1
        print(text)
    for child in element:
        count += counter(child, level + 1, search, count)
    return count


def remove_page_and_system_breaks(root):
    """Remove all new-system and new-page breaks from the original MusicXML."""
    for print_element in root.findall('.//print'):
        if 'new-system' in print_element.attrib:
            del print_element.attrib['new-system']
        if 'new-page' in print_element.attrib:
            del print_element.attrib['new-page']

import xml.etree.ElementTree as ET
import os
import shutil

def split_musicxml_by_page(file_path, output_dir='split_musicxml'):
    # Load the MusicXML file
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing MusicXML file: {e}")
        return

    # Remove all new-system and new-page breaks
    remove_page_and_system_breaks(root)

    parts = root.findall('.//part')
    page_number = 1

    for part in parts:
        part_id = part.get('id')
        print(f"Part ID: {part_id}")

        current_measures = list(part.findall('measure'))
        measure_index = 0
        total_measures = len(current_measures)

        while measure_index < total_measures:
            # Create the first page (mostly blank)
            empty_measure = create_empty_measure()

            # Implement binary search to find the maximum number of measures that can fit on a page
            low = 0
            high = total_measures - measure_index
            best_fit = 0
            first_page = False

            while low <= high:
                mid = (low + high) // 2
                measures_for_second_page = current_measures[measure_index:measure_index + mid]
                add_new_page_break(measures_for_second_page[0])
                # Create a temporary MusicXML structure to test the layout
                temp_root = ET.Element(root.tag, root.attrib)
                copy_metadata_sections(root, temp_root)

                temp_part = ET.SubElement(temp_root, 'part', {'id': part_id})
                temp_part.append(empty_measure)
                temp_part.extend(measures_for_second_page)

                # Create the third page with a new page break at the start
                last_measure = create_empty_measure()
                add_new_page_break(last_measure)
                temp_part.append(last_measure)

                temp_file_path = os.path.join(output_dir, 'temp.xml')
                temp_file_path_1 = os.path.join(output_dir, 'temp-1.xml')
                if os.path.exists(temp_file_path):
                    shutil.copy(temp_file_path, temp_file_path_1)
                write_pretty_xml(temp_root, temp_file_path)

                temp_pdf_path = temp_file_path.replace('.xml', '.pdf')
                temp_pdf_path_1 = temp_file_path_1.replace('.xml', '.pdf')
                if os.path.exists(temp_pdf_path):
                    shutil.copy(temp_pdf_path, temp_pdf_path_1)
                os.system(f"mscore3 {temp_file_path} -o {temp_pdf_path}")

                # Check the PDF page count
                if check_pdf_page_count(temp_pdf_path) <= 3:
                    best_fit = mid
                    low = mid + 1
                else:
                    high = mid - 1

                # Clean up temporary files
                os.remove(temp_file_path)
                os.remove(temp_pdf_path)

            # Add the best fitting measures to the page
            measure_index += best_fit

            # Save the section to an output file
            if best_fit > 0:
                measures_for_second_page = current_measures[measure_index - best_fit:measure_index]

                temp_root = ET.Element(root.tag, root.attrib)
                copy_metadata_sections(root, temp_root)

                temp_part = ET.SubElement(temp_root, 'part', {'id': part_id})
                temp_part.append(empty_measure)
                temp_part.extend(measures_for_second_page)

                last_measure = create_empty_measure()
                add_new_page_break(last_measure)
                temp_part.append(last_measure)

                final_file_path = os.path.join(output_dir, f"section_{page_number}_part_{part_id}.xml")
                write_pretty_xml(temp_root, final_file_path)

                final_pdf_path = final_file_path.replace('.xml', '.pdf')
                os.system(f"mscore3 {final_file_path} -o {final_pdf_path}")

            page_number += 1

    return page_number


def create_empty_measure():
    """Creates an empty measure."""
    measure = ET.Element('measure', number="0")
    attributes = ET.SubElement(measure, 'attributes')
    note = ET.SubElement(measure, 'note')
    ET.SubElement(note, 'rest')
    ET.SubElement(note, 'duration').text = '4'
    return measure

def add_line_break(measure):
    """Adds a line break to the given measure."""
    print_element = ET.Element('print', {'new-system': 'yes'})
    measure.append(print_element)

def add_new_page_break(measure):
    """Adds a new page break to the given measure."""
    print_element = ET.Element('print', {'new-page': 'yes'})
    measure.append(print_element)

def copy_metadata_sections(source_root, target_root):
    """Copies the metadata sections from source_root to target_root."""
    for child in source_root:
        if child.tag in ['defaults', 'part-list']:
            target_root.append(child)

def check_pdf_page_count(pdf_file_path):
    """Check the number of pages in a PDF."""
    pdf_reader = PdfReader(pdf_file_path)
    return len(pdf_reader.pages)

if __name__ == '__main__':
    # Specify the path to your MusicXML file
    file_path = 'example/4240.musicxml'
    split_musicxml_by_page(file_path)
