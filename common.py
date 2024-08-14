import xml.etree.ElementTree as ET


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


def add_final_barline(measure):
    """
    Adds a final barline to the given measure for all staves.
    """
    # Find the number of staves in the measure (if present)
    staves = measure.findall('.//staff')

    # If there are no staff elements, assume there's only one staff
    num_staves = len(staves) if staves else 1

    for staff_number in range(1, num_staves + 1):
        # Create or find the barline element for each staff
        barline = measure.find(f'.//barline[@staff="{staff_number}"]')
        if barline is None:
            barline = ET.Element('barline')
            barline.set('staff', str(staff_number))
            measure.append(barline)

        # Set the barline's location to 'right' and type to 'final'
        barline.set('location', 'right')

        # Find or create the 'bar-style' element within the barline
        bar_style = barline.find('bar-style')
        if bar_style is None:
            bar_style = ET.Element('bar-style')
            barline.append(bar_style)

        # Set the bar-style to 'light-heavy' (typically used for final barlines)
        bar_style.text = 'light-heavy'



def copy_metadata_sections(source_root, target_root):
    """
    Copies the metadata sections from source_root to target_root.
    """
    for child in source_root:
        if child.tag in [ 'defaults', 'part-list']: #, 'credit' 'identification',
            target_root.append(child)

def copy_metadata_sections_all(source_root, target_root):
    """
    Copies the metadata sections from source_root to target_root.
    """
    for child in source_root:
        if child.tag in [ 'defaults', 'part-list', 'credit' 'identification',]: #, 'credit' 'identification',
            target_root.append(child)


def find_and_add_last_attributes(current_measure, previous_measures):
    """
    Finds the last attributes in the previous measures and adds them to the current measure.
    """
    last_tempo, last_dynamic = find_last_tempo_and_dynamics(previous_measures)
    last_key = find_last_key(previous_measures)
    last_time = find_last_time(previous_measures)
    last_clef = find_last_clef(previous_measures)
    last_divisions = find_last_divisions(previous_measures)

    add_divisions(current_measure, last_divisions)
    add_tempo_and_dynamics(current_measure, last_tempo, last_dynamic)
    add_key_signature(current_measure, last_key)
    add_time_signature(current_measure, last_time)
    add_clef(current_measure, last_clef)
    return last_tempo, last_dynamic, last_key, last_time, last_clef, last_divisions