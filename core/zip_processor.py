import os
import re
import io
import zipfile
import pandas as pd
import pdfplumber

def generate_zip(invoices, utility_company, location, tipo_debito):
    try:
        utility_lower = utility_company.lower()
        location_mapped = 'centros' if location == 'Centros Comunitários' else 'sedis'
        
        regex_file_path = f'data/faturas/faturas_{utility_lower}.csv'
        identifiers_file_path = f'data/identificadores/identificadores_{utility_lower}_{location_mapped}.csv'
        
        if not os.path.exists(regex_file_path) or not os.path.exists(identifiers_file_path):
            raise FileNotFoundError('Os arquivos de configuração ou de identificadores estão ausentes para a geração do ZIP.')
            
        regex_dataframe = pd.read_csv(regex_file_path)
        identifier_column = 'uc' if utility_company == 'EDP' else 'rgi'
        
        try:
            target_regex_pattern = regex_dataframe.loc[regex_dataframe['field_name'] == identifier_column, 'regex_pattern'].values[0]
            debito_regex_pattern = regex_dataframe.loc[regex_dataframe['field_name'] == 'debito', 'regex_pattern'].values[0]
        except IndexError:
            raise ValueError('Os padrões de regex obrigatórios não foram encontrados.')
            
        identifiers_dataframe = pd.read_csv(identifiers_file_path)
        identifiers_dataframe.columns = identifiers_dataframe.columns.str.strip().str.lower()
        
        identifier_to_folder_map = {}
        for _, record in identifiers_dataframe.iterrows():
            identifier_value = str(record[identifier_column]).strip().replace('.', '').replace('-', '').lstrip('0')
            folder_name = f"{record['ficha']} ({record['acao']})"
            identifier_to_folder_map[identifier_value] = folder_name
            
        memory_buffer = io.BytesIO()
        
        with zipfile.ZipFile(memory_buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            for invoice_file in invoices:
                extracted_identifier = None
                has_auto_debit = False
                invoice_text_content = ''
                invoice_file.seek(0)
                
                with pdfplumber.open(invoice_file) as pdf_document:
                    for pdf_page in pdf_document.pages:
                        extracted_text = pdf_page.extract_text()
                        if extracted_text:
                            invoice_text_content += extracted_text + '\n'
                            
                regex_match = re.search(target_regex_pattern, invoice_text_content)
                if regex_match:
                    val = regex_match.group(1).strip() if regex_match.groups() else regex_match.group(0).strip()
                    extracted_identifier = re.sub(r'[\s.-]', '', val).lstrip('0')
                        
                debito_match = re.search(debito_regex_pattern, invoice_text_content)
                if debito_match:
                    has_auto_debit = True
                    
                is_valid_debit = (tipo_debito == 'Automático' and has_auto_debit) or (tipo_debito == 'Manual' and not has_auto_debit)
                
                if is_valid_debit and extracted_identifier and extracted_identifier in identifier_to_folder_map:
                    target_folder = identifier_to_folder_map[extracted_identifier]
                    invoice_file.seek(0)
                    archive.writestr(f'{target_folder}/{invoice_file.name}', invoice_file.read())
                    
        return memory_buffer.getvalue()
        
    except Exception as application_error:
        raise Exception(f'Ocorreu um erro durante a geração do arquivo ZIP: {str(application_error)}')