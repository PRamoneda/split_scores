import xml.etree.ElementTree as ET
import os

def split_musicxml_by_page(file_path):
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

    for part in parts:
        part_id = part.get('id')
        print(f"Part ID: {part_id}")

        current_measures = []
        measure_offset = 0  # This will help to correctly number measures on new pages

        for measure in part.findall('measure'):
            measure_number = int(measure.get('number', 0)) + measure_offset

            # Check for page breaks
            is_new_page = any(
                print_element.get('new-page') == 'yes'
                for print_element in measure.findall('print')
            )

            if is_new_page and current_measures:
                # Add single barline to the last measure of the current section
                add_single_barline(current_measures[-1])
                page_measures.append((page_number, part_id, current_measures.copy()))
                current_measures.clear()
                page_number += 1
                measure_offset = measure_number - 1  # Adjust measure numbers for split

            # Adjust the measure number for continuity
            measure.set('number', str(measure_number))
            current_measures.append(measure)

        # Add remaining measures after the last page break
        if current_measures:
            add_single_barline(current_measures[-1])
            page_measures.append((page_number, part_id, current_measures.copy()))

    # Create output directory if it doesn't exist
    output_dir = 'split_musicxml'
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
        print(f'Page {page_number} for part {part_id} saved as {new_file_path}')


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


def add_single_barline(measure):
    """
    Adds a single regular barline to the given measure if none exists.
    """
    measure_number = measure.get('number', 'Unknown')
    print(f"Adding single barline to measure number: {measure_number}")

    existing_barline = measure.find('barline')
    if existing_barline is None:
        barline = ET.Element('barline')
        bar_style = ET.SubElement(barline, 'bar-style')
        bar_style.text = 'regular'
        measure.append(barline)
    else:
        bar_style = existing_barline.find('bar-style')
        if bar_style is not None:
            bar_style.text = 'regular'


def copy_metadata_sections(source_root, target_root):
    """
    Copies the metadata sections from source_root to target_root.
    """
    for child in source_root:
        if child.tag in ['identification', 'defaults', 'credit', 'part-list']:
            target_root.append(child)


if __name__ == '__main__':
    # Specify the path to your MusicXML file
    file_path = 'example/4240.musicxml'
    split_musicxml_by_page(file_path)
