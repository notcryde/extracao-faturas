import os
import io
import pandas as pd

def generate_report(processed_dataframe, utility_company, location, mes_competencia, tipo_debito, conta):
    try:
        utility_lower = utility_company.lower()
        location_mapped = 'centros' if location == 'Centros Comunitários' else 'sedis'
        
        fichas_path = f'data/fichas/fichas_{utility_lower}_{location_mapped}.csv'
        identificadores_path = f'data/identificadores/identificadores_{utility_lower}_{location_mapped}.csv'
        dotacoes_path = 'data/dotacoes/dotacoes.csv'
        
        if not os.path.exists(fichas_path):
            raise FileNotFoundError(f'O arquivo de fichas não foi encontrado no caminho: {fichas_path}')
        if not os.path.exists(identificadores_path):
            raise FileNotFoundError(f'O arquivo de identificadores não foi encontrado no caminho: {identificadores_path}')
        if not os.path.exists(dotacoes_path):
            raise FileNotFoundError(f'O arquivo de dotações não foi encontrado no caminho: {dotacoes_path}')
            
        fichas_dataframe = pd.read_csv(fichas_path)
        identificadores_dataframe = pd.read_csv(identificadores_path)
        dotacoes_dataframe = pd.read_csv(dotacoes_path)
        
        fichas_dataframe.columns = fichas_dataframe.columns.str.strip().str.lower()
        identificadores_dataframe.columns = identificadores_dataframe.columns.str.strip().str.lower()
        dotacoes_dataframe.columns = dotacoes_dataframe.columns.str.strip().str.lower()
        
        identifier_column = 'uc' if utility_company == 'EDP' else 'rgi'
        
        processed_dataframe[identifier_column] = processed_dataframe[identifier_column].astype(str).str.strip()
        identificadores_dataframe[identifier_column] = identificadores_dataframe[identifier_column].astype(str).str.strip()
        
        merged_dataframe = pd.merge(processed_dataframe, identificadores_dataframe, on=identifier_column, how='inner')
        final_dataframe = pd.merge(merged_dataframe, fichas_dataframe, on=['ficha', 'acao'], how='inner')
        final_dataframe = pd.merge(final_dataframe, dotacoes_dataframe, on='ficha', how='inner')
        
        def clean_currency(value):
            if pd.isna(value) or str(value).strip() == '':
                return 0.0
            cleaned_string = str(value).replace('.', '').replace(',', '.')
            try:
                return float(cleaned_string)
            except ValueError:
                return 0.0
                
        final_dataframe['valor_liquido_float'] = final_dataframe['valor'].apply(clean_currency)
        
        retencao_key = None
        for col in final_dataframe.columns:
            if col.lower().strip() in ['retencao', 'retencao_ir', 'retenção']:
                retencao_key = col
                break
                
        if retencao_key:
            final_dataframe['ir_float'] = final_dataframe[retencao_key].apply(clean_currency)
        else:
            final_dataframe['ir_float'] = 0.0
            
        grouped_dataframe = final_dataframe.groupby(['dotacao', 'acao', 'secretaria', 'empenho', 'af']).agg(
            valor_liquido=('valor_liquido_float', 'sum'),
            ir=('ir_float', 'sum')
        ).reset_index()
        
        grouped_dataframe['valor_bruto'] = grouped_dataframe['valor_liquido'] + grouped_dataframe['ir']
        
        vencimento_value = final_dataframe['vencimento'].iloc[0] if 'vencimento' in final_dataframe.columns and not final_dataframe.empty else 'N/D'
        
        memory_buffer = io.BytesIO()
        with pd.ExcelWriter(memory_buffer, engine='xlsxwriter') as excel_writer:
            workbook = excel_writer.book
            worksheet = workbook.add_worksheet('Relatório')
            
            title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 20, 'font_color': '#ffffff', 'bg_color': '#2f5597', 'font_name': 'Arial', 'border': 1})
            header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_color': '#000000', 'bg_color': '#dae3f3', 'font_name': 'Arial', 'border': 1})
            data_format = workbook.add_format({'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'border': 1})
            currency_format = workbook.add_format({'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'num_format': '"R$" #,##0.00', 'border': 1})
            
            worksheet.set_column('A:H', 22)
            
            image_one_path = 'data/images/logo_prefeitura.png'
            image_two_path = 'data/images/texto_prefeitura.png'
            
            if os.path.exists(image_one_path):
                worksheet.insert_image('A1', image_one_path, {
                    'x_scale': 0.10, 
                    'y_scale': 0.10,
                    'x_offset': 5,
                    'y_offset': 5,
                    'object_position': 1
                })
            if os.path.exists(image_two_path):
                worksheet.insert_image('C1', image_two_path, {
                    'x_offset': 5,
                    'y_offset': 5,
                    'object_position': 1
            })
                
            worksheet.set_row(0, 70)
            
            worksheet.merge_range('A2:H2', f'Relatório das faturas {utility_company} referentes a {mes_competencia}', title_format)
            worksheet.merge_range('A3:H3', f'Débito {tipo_debito} - {conta} - Vencimento {vencimento_value} - {location}', title_format)
            worksheet.set_row(1, 35)
            worksheet.set_row(2, 35)
            
            headers_list = ['DOTAÇÃO', 'AÇÃO', 'SECRETARIA RESPONSAVEL', 'EMPENHO', 'AF', 'VALOR LIQUIDO', 'IR', 'VALOR BRUTO']
            for col_index, header_text in enumerate(headers_list):
                worksheet.write(3, col_index, header_text, header_format)
                
            worksheet.set_row(3, 20)
                
            current_row = 4
            sum_liquido = 0
            sum_ir = 0
            sum_bruto = 0
            
            for _, record in grouped_dataframe.iterrows():
                worksheet.write(current_row, 0, record['dotacao'], data_format)
                worksheet.write(current_row, 1, record['acao'], data_format)
                worksheet.write(current_row, 2, record['secretaria'], data_format)
                worksheet.write(current_row, 3, record['empenho'], data_format)
                worksheet.write(current_row, 4, record['af'], data_format)
                worksheet.write_number(current_row, 5, record['valor_liquido'], currency_format)
                worksheet.write_number(current_row, 6, record['ir'], currency_format)
                worksheet.write_number(current_row, 7, record['valor_bruto'], currency_format)
                
                sum_liquido += record['valor_liquido']
                sum_ir += record['ir']
                sum_bruto += record['valor_bruto']
                current_row += 1
                
            worksheet.merge_range(f'A{current_row + 1}:E{current_row + 1}', 'Total Geral', header_format)
            worksheet.write_number(current_row, 5, sum_liquido, header_format)
            worksheet.write_number(current_row, 6, sum_ir, header_format)
            worksheet.write_number(current_row, 7, sum_bruto, header_format)
            worksheet.set_row(current_row, 25)
            
        return memory_buffer.getvalue()
        
    except Exception as application_error:
        raise Exception(f'Ocorreu um erro durante a geração do relatório: {str(application_error)}')