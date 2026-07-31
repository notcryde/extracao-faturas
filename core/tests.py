import csv
import os
import re
import pdfplumber


def get_absolute_path(relative_path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, relative_path))

def extract_pdf_text(file_path: str) -> str:
    absolute_path = get_absolute_path(file_path)
    with pdfplumber.open(absolute_path) as pdf:
        return '\n'.join(page.extract_text() or '' for page in pdf.pages)

def load_regex_patterns(csv_path: str) -> dict:
    absolute_path = get_absolute_path(csv_path)
    patterns = {}
    with open(absolute_path, mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            patterns[row['field_name']] = row['regex_pattern']
    return patterns

def extract_fields_from_text(text: str, patterns: dict) -> dict:
    extracted_data = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            extracted_data[field] = (
                match.group(1) if match.groups() else match.group(0)
            )
        else:
            extracted_data[field] = None
    return extracted_data

def process_pdf(file_path: str, option: int) -> None:
    if option == 1:
        text = extract_pdf_text(file_path)
        print(text)

    elif option == 2:
        text = extract_pdf_text(file_path)
        patterns = load_regex_patterns('../data/faturas/faturas_edp.csv')
        extracted_data = extract_fields_from_text(text, patterns)
        for key, value in extracted_data.items():
            print(f'{key}: {value}')

files = []

process_pdf(files[...], 2)