import os
import re
import pandas as pd
import pdfplumber

def process_csv(invoices, utility_company, location):
    try:
        utility_lower = utility_company.lower()
        regex_file_path = f'data/faturas/faturas_{utility_lower}.csv'
        
        if not os.path.exists(regex_file_path):
            raise FileNotFoundError(f'O arquivo de expressões regulares não foi encontrado no caminho: {regex_file_path}')
            
        regex_dataframe = pd.read_csv(regex_file_path)
        regex_patterns = dict(zip(regex_dataframe['field_name'], regex_dataframe['regex_pattern']))
        
        location_mapped = 'centros' if location == 'Centros Comunitários' else 'sedis'
        identifiers_file_path = f'data/identificadores/identificadores_{utility_lower}_{location_mapped}.csv'
        
        if not os.path.exists(identifiers_file_path):
            raise FileNotFoundError(f'O arquivo de identificadores não foi encontrado no caminho: {identifiers_file_path}')
            
        identifiers_dataframe = pd.read_csv(identifiers_file_path)
        identifiers_dataframe.columns = identifiers_dataframe.columns.str.strip().str.lower()
        
        identifier_column = 'uc' if utility_company == 'EDP' else 'rgi'
        
        if identifier_column not in identifiers_dataframe.columns:
            available_columns = ', '.join(identifiers_dataframe.columns)
            raise ValueError(f'A coluna "{identifier_column}" não foi encontrada. Colunas presentes: {available_columns}')
            
        identifiers_dataframe[identifier_column] = identifiers_dataframe[identifier_column].astype(str).str.strip().str.replace(r'[\s.-]', '', regex=True).str.lstrip('0')
        ordered_identifiers = identifiers_dataframe[identifier_column].tolist()
        
        extracted_invoices_data = []
        
        for invoice_file in invoices:
            invoice_text_content = ''
            invoice_file.seek(0)
            with pdfplumber.open(invoice_file) as pdf_document:
                for pdf_page in pdf_document.pages:
                    extracted_page_text = pdf_page.extract_text()
                    if extracted_page_text:
                        invoice_text_content += extracted_page_text + '\n'
            
            parsed_invoice_data = {}
            for field_name, regex_pattern in regex_patterns.items():
                regex_match = re.search(regex_pattern, invoice_text_content)
                if regex_match:
                    val = regex_match.group(1).strip() if regex_match.groups() else regex_match.group(0).strip()
                    if field_name == identifier_column:
                        val = re.sub(r'[\s.-]', '', val).lstrip('0')
                    parsed_invoice_data[field_name] = val
                else:
                    parsed_invoice_data[field_name] = ''
                    
            extracted_invoices_data.append(parsed_invoice_data)
            
        results_dataframe = pd.DataFrame(extracted_invoices_data)
        
        if identifier_column in results_dataframe.columns:
            results_dataframe[identifier_column] = results_dataframe[identifier_column].astype(str).str.strip()
            
            results_dataframe = results_dataframe[results_dataframe[identifier_column].isin(ordered_identifiers)].copy()
            
            if not results_dataframe.empty:
                results_dataframe['sorter_column'] = results_dataframe[identifier_column].apply(lambda x: ordered_identifiers.index(x))
                results_dataframe = results_dataframe.sort_values('sorter_column').drop(columns=['sorter_column']).reset_index(drop=True)
        else:
            raise ValueError(f'O sistema não conseguiu extrair a coluna de identificador {identifier_column} das faturas.')
            
        return results_dataframe
        
    except Exception as application_error:
        raise Exception(f'Ocorreu um erro durante o processamento das faturas: {str(application_error)}')