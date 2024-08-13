import xml.etree.ElementTree as ET
import os
from PyPDF2 import PdfReader, PdfWriter


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


def find_last_tempo_and_dynamics(measures):
    """
    Finds the last tempo and dynamic markings within a list of measures.
    """
    last_tempo = None
    last_dynamic = None

    for measure in measures:
        # Find the tempo in the measure
        for direction in measure.findall('direction'):
            sound = direction.find('sound')
            if sound is not None and 'tempo' in sound.attrib:
                last_tempo = float(sound.get('tempo'))
                print(f"Tempo found in measure {measure.get('number')}: {last_tempo}")

        # Find the dynamic markings in the measure
        for direction in measure.findall('direction'):
            dynamics = direction.find('direction-type/dynamics')
            if dynamics is not None and len(dynamics) > 0:
                last_dynamic = dynamics[0].tag
                print(f"Dynamic found in measure {measure.get('number')}: {last_dynamic}")

    return last_tempo, last_dynamic


def add_tempo_and_dynamics(measure, last_tempo, last_dynamic):
    """
    Adds the last known tempo and dynamics to the beginning of the given measure.
    """
    if last_tempo is not None:
        direction = ET.Element('direction')
        direction_type = ET.SubElement(direction, 'direction-type')
        metronome = ET.SubElement(direction_type, 'metronome')
        beat_unit = ET.SubElement(metronome, 'beat-unit')
        beat_unit.text = 'quarter'
        per_minute = ET.SubElement(metronome, 'per-minute')
        per_minute.text = str(last_tempo)
        measure.insert(0, direction)  # Insert at the start of the measure

    if last_dynamic is not None:
        direction = ET.Element('direction')
        direction_type = ET.SubElement(direction, 'direction-type')
        dynamics = ET.SubElement(direction_type, 'dynamics')
        dynamic = ET.SubElement(dynamics, last_dynamic)
        dynamic.text = ''  # Text is not usually used, but ensure node exists
        measure.insert(0, direction)  # Insert at the start of the measure


def find_last_key(measures):
    """
    Finds the last key signature in the given measures.
    """
    last_key = None

    for measure in measures:
        attributes = measure.find('attributes')
        if attributes is not None:
            key = attributes.find('key')
            if key is not None:
                last_key = key
                print(f"Key signature found in measure {measure.get('number')}: {ET.tostring(key)}")

    return last_key


def add_key_signature(measure, last_key):
    """
    Adds the last known key signature to the beginning of the given measure.
    """
    if last_key is not None:
        attributes = measure.find('attributes')
        if attributes is None:
            attributes = ET.Element('attributes')
            measure.append(attributes)

        existing_key = attributes.find('key')
        # if there is not key signature Add the last known key signature
        if existing_key is None:
            attributes.append(last_key)


def find_last_time(measures):
    """
    Finds the last time signature in the given measures.
    """
    last_time = None

    for measure in measures:
        attributes = measure.find('attributes')
        if attributes is not None:
            time = attributes.find('time')
            if time is not None:
                last_time = time
                print(f"Time signature found in measure {measure.get('number')}: {ET.tostring(time)}")

    return last_time


def add_time_signature(measure, last_time):
    """
    Adds the last known time signature to the beginning of the given measure.
    """
    if last_time is not None:
        attributes = measure.find('attributes')
        if attributes is None:
            attributes = ET.Element('attributes')
            measure.insert(0, attributes)

        # if there is not time signature Add the last known time signature
        existing_time = attributes.find('time')
        if existing_time is None:
            attributes.append(last_time)


def find_last_clef(measures):
    """
    Finds the last clef in the given measures.
    """
    last_clef = None

    for measure in measures:
        attributes = measure.find('attributes')
        if attributes is not None:
            clef = attributes.find('clef')
            if clef is not None:
                last_clef = clef
                print(f"Clef found in measure {measure.get('number')}: {ET.tostring(clef)}")

    return last_clef


def add_clef(measure, last_clef):
    """
    Adds the last known clef to the beginning of the given measure.
    """
    if last_clef is not None:
        attributes = measure.find('attributes')
        if attributes is None:
            attributes = ET.Element('attributes')
            measure.insert(0, attributes)

        # if there is not clef Add the last known clef
        existing_clef = attributes.find('clef')
        if existing_clef is None:
            attributes.append(last_clef)


def find_last_divisions(measures):
    """
    Finds the last divisions in the given measures.
    """
    last_divisions = None

    for measure in measures:
        attributes = measure.find('attributes')
        if attributes is not None:
            divisions = attributes.find('divisions')
            if divisions is not None:
                last_divisions = divisions
                print(f"Divisions found in measure {measure.get('number')}: {ET.tostring(divisions)}")

    return last_divisions


def add_divisions(measure, last_divisions):
    """
    Adds the last known divisions to the beginning of the given measure.
    """
    if last_divisions is not None:
        attributes = measure.find('attributes')
        if attributes is None:
            attributes = ET.Element('attributes')
            measure.insert(0, attributes)

        # if there is not divisions Add the last known divisions
        existing_divisions = attributes.find('divisions')
        if existing_divisions is None:
            attributes.insert(0, last_divisions)



def copy_metadata_sections(source_root, target_root):
    """
    Copies the metadata sections from source_root to target_root.
    """
    for child in source_root:
        if child.tag in [ 'defaults', 'part-list']: #, 'credit' 'identification',
            target_root.append(child)


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

