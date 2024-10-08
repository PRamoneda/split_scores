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


def find_last_clef(measures, clef_number):
    """
    Finds the last clef in the given measures with a specific clef number.
    """
    last_clef = None

    for measure in measures:
        attributes = measure.find('attributes')
        if attributes is not None:
            clefs = attributes.findall('clef')
            for clef in clefs:
                if clef.get('number') == str(clef_number):
                    last_clef = clef
                    print(f"Clef {clef_number} found in measure {measure.get('number')}: {ET.tostring(clef)}")

    return last_clef


def add_clef(measure, last_clef):
    """
    Adds the last known clef with the specified number to the beginning of the given measure.
    """
    if last_clef is not None:
        attributes = measure.find('attributes')
        if attributes is None:
            attributes = ET.Element('attributes')
            measure.insert(0, attributes)

        # Check if the clef with the same number already exists
        existing_clef = None
        clefs = attributes.findall('clef')
        for clef in clefs:
            if clef.get('number') == last_clef.get('number'):
                existing_clef = clef
                break

        # If the clef does not exist, add the last known clef
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
    Adds a final barline to the given meaºsure for all staves.
    """
    pass




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
    last_clef_right = find_last_clef(previous_measures, 1)
    last_clef_left = find_last_clef(previous_measures, 2)
    last_divisions = find_last_divisions(previous_measures)

    add_divisions(current_measure, last_divisions)
    add_tempo_and_dynamics(current_measure, last_tempo, last_dynamic)
    add_key_signature(current_measure, last_key)
    add_time_signature(current_measure, last_time)
    add_clef(current_measure, last_clef_right)
    add_clef(current_measure, last_clef_left)
    return last_tempo, last_dynamic, last_key, last_time, last_clef_right, last_clef_left, last_divisions