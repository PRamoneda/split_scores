import xml.etree.ElementTree as ET
import os
from PyPDF2 import PdfReader, PdfWriter
from common import find_last_tempo_and_dynamics, add_tempo_and_dynamics, find_last_key, add_key_signature, \
    find_last_time, add_time_signature, find_last_clef, add_clef, find_last_divisions, add_divisions, \
    copy_metadata_sections


global_bad_pages = []
global_bad_works = []


def split_musicxml_by_page(file_path, output_dir='split_musicxml'):
    # Load the MusicXML file
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing MusicXML file: {e}")
        return

    parts = root.findall('.//part')
    print(f"Number of parts found: {len(parts)}")

    page_number = 1
    page_measures = []

    # Initialize variables to store the last known attributes
    last_tempo = None
    last_dynamic = None
    last_key = None
    last_time = None
    last_clef = None
    last_divisions = None

    for part in parts:
        part_id = part.get('id')
        print(f"Part ID: {part_id}")

        current_measures = []

        for measure in part.findall('measure'):
            measure_number = int(measure.get('number', 0))

            # Check for page breaks
            is_new_page = any(
                print_element.get('new-page') == 'yes'
                for print_element in measure.findall('print')
            )

            if is_new_page and current_measures:
                page_measures.append((page_number, part_id, current_measures.copy()))
                # Update attributes for the next page
                last_tempo, last_dynamic = find_last_tempo_and_dynamics(current_measures)
                last_key = find_last_key(current_measures)
                last_time = find_last_time(current_measures)
                last_clef = find_last_clef(current_measures)
                last_divisions = find_last_divisions(current_measures)
                current_measures.clear()
                page_number += 1

            # Adjust the measure number for continuity
            measure.set('number', str(measure_number))

            if is_new_page:
                # Add tempo, dynamics, key, time signature, clef, and divisions if needed
                add_divisions(measure, last_divisions)
                add_tempo_and_dynamics(measure, last_tempo, last_dynamic)
                add_key_signature(measure, last_key)
                add_time_signature(measure, last_time)
                add_clef(measure, last_clef)
                print()
            current_measures.append(measure)

        # Add remaining measures after the last page break
        if current_measures:
            page_measures.append((page_number, part_id, current_measures.copy()))

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write each page's measures to separate MusicXML files
    for page_number, part_id, measures in page_measures:
        new_root = ET.Element(root.tag, root.attrib)
        copy_metadata_sections(root, new_root)

        # Create a new part element with the measures for the current page
        new_part = ET.SubElement(new_root, 'part', {'id': part_id})
        for measure in measures:
            new_part.append(measure)

        # Write the new MusicXML file
        new_file_path = os.path.join(output_dir, f'page_{page_number}_part_{part_id}.xml')
        ET.ElementTree(new_root).write(new_file_path, xml_declaration=True, encoding='UTF-8', method='xml')
        print(f'Page {page_number} {part_id} saved as {new_file_path}')
        # save as audio
        #os.system(f"mscore3 {new_file_path} -o {new_file_path.replace('.xml', '.wav')}")
        # save as PDF
        # Add an empty measure at the beginning
        pdf_part = new_root.find(f".//part[@id='{part_id}']")

        empty_measure_before = create_empty_measure(last_divisions)
        # add_divisions(empty_measure_before, last_divisions)
        # add_tempo_and_dynamics(empty_measure_before, last_tempo, last_dynamic)
        # add_key_signature(empty_measure_before, last_key)
        # add_time_signature(empty_measure_before, last_time)
        # add_clef(empty_measure_before, last_clef)
        pdf_part.insert(0, empty_measure_before)
        # add  empty measures
        # for i in range(94):
        #     empty_measure = create_empty_measure(last_divisions)
        #     pdf_part.insert(1, empty_measure)

        # Add a page break after the original content
        new_page_after = ET.Element('measure', number=str(len(measures) + 1))
        new_page_element_after = ET.Element('print', {'new-page': 'yes'})
        new_page_after.append(new_page_element_after)
        pdf_part.append(new_page_after)

        # write another empty bar with an new-page at the end
        empty_measure_after = create_empty_measure(last_divisions)
        add_divisions(empty_measure_before, last_divisions)
        add_tempo_and_dynamics(empty_measure_before, last_tempo, last_dynamic)
        add_key_signature(empty_measure_before, last_key)
        add_time_signature(empty_measure_before, last_time)
        add_clef(empty_measure_before, last_clef)
        pdf_part.append(empty_measure_after)

        # Write the modified MusicXML for PDF export
        xmlpdf_file_path = os.path.join(output_dir, f'page_{page_number}_part_{part_id}_pdf.xml')
        ET.ElementTree(new_root).write(xmlpdf_file_path, xml_declaration=True, encoding='UTF-8', method='xml')
        pdf_file_path = xmlpdf_file_path.replace('.xml', '.pdf').replace("_pdf", "")
        # Save as PDF using MuseScore
        print(f"mscore3 {xmlpdf_file_path} -o {pdf_file_path}")
        os.system(f"mscore3 {xmlpdf_file_path} -o {pdf_file_path}")

        # Check the PDF page count and adjust if needed
        check_pdf_page_count_and_adjust(pdf_file_path)
        print(
            f'PDF with structure for page {page_number} for part {part_id} saved as {pdf_file_path.replace(".xml", ".pdf")}')
    return page_number


def check_pdf_page_count_and_adjust(pdf_file_path):
    # Open the PDF
    pdf_reader = PdfReader(pdf_file_path)
    total_pages = len(pdf_reader.pages)

    # Check the page count
    if total_pages != 3:
        # Raise an exception if the PDF does not have exactly three pages
        global_bad_pages.append(pdf_file_path)
        global_bad_works.append(pdf_file_path.split("/")[1])
        #raise Exception(f"The PDF does not have exactly three pages. It has {total_pages} pages.")
    else:
        # If the exception handling is desired instead of just raising an exception:
        # Remove the first and last pages to create a new PDF
        pdf_writer = PdfWriter()
        for page_number in range(1, total_pages - 1):  # Keep only the middle pages
            pdf_writer.add_page(pdf_reader.pages[page_number])

        # Write the new PDF file with the same name, replacing the original
        with open(pdf_file_path, 'wb') as new_pdf_file:
            pdf_writer.write(new_pdf_file)
        print(f"Adjusted PDF saved with middle pages only: {pdf_file_path}")


def create_empty_measure(divisions):
    """
    Creates an empty measure with the specified divisions.
    """
    measure = ET.Element('measure', number="0")
    attributes = ET.SubElement(measure, 'attributes')

    # Add divisions if specified
    if divisions is not None:
        attributes.insert(0, divisions)

    # Add an empty note for clarity
    note = ET.SubElement(measure, 'note')
    ET.SubElement(note, 'rest')
    ET.SubElement(note, 'duration').text = '4'

    return measure





if __name__ == '__main__':
    # Specify the path to your MusicXML file
    file_path = 'example/4240.musicxml'
    split_musicxml_by_page(file_path)
    # total = 0
    # total_pages = 0
    # for path in os.listdir("example"):
    #     if path.endswith(".musicxml"):
    #         page_number = split_musicxml_by_page(f"example/{path}", output_dir=f'split_musicxml/{path.replace(".musicxml", "")}')
    #         total += 1
    #         total_pages += page_number
    #
    #         print("total works:")
    #         print(total)
    #         print("total pages:")
    #         print(total_pages)
    #         print("bad pages:")
    #         print(len(global_bad_pages))
    #         print("bad works:")
    #         print(len(set(global_bad_works)))

