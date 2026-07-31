import streamlit as st
from core.csv_processor import process_csv
from core.report_processor import generate_report
from core.zip_processor import generate_zip

def home():
    if 'report_data' not in st.session_state:
        st.session_state.report_data = None

    if 'zip_data' not in st.session_state:
        st.session_state.zip_data = None
        
    st.title('Sistema de Extração de Faturas')

    st.subheader('1. Upload de Faturas')
    
    left_column, right_column = st.columns(2)

    with left_column:
        concessionaria = st.selectbox(label='Selecione uma concessionária', options=['EDP', 'Sabesp'])
    with right_column:
        mes_competencia = st.text_input(label='Digite o mês de competência (ex. Jan/2026):')

    faturas = st.file_uploader('Faça o upload de suas faturas aqui:', type=['pdf'], accept_multiple_files=True)

    if faturas:
        st.subheader('2. Opções de Processamento')
        
        option = st.selectbox(label='Selecione uma opção de processamento:', options=['Planilha', 'Relatório'])
        
        if option == 'Planilha':
            local = st.selectbox(label='Selecione o local:', options=['SEDIS', 'Centros Comunitários'])
        elif option == 'Relatório':
            local = st.selectbox(label='Selecione o local:', options=['SEDIS', 'Centros Comunitários'])
            
            left_column, right_column = st.columns(2)

            with left_column:
                tipo_debito = st.selectbox(label='Selecione o tipo de débito:', options=['Manual', 'Automático'])
            with right_column:
                conta = st.text_input(label='Digite a conta bancária:')
                
            gerar_zip = st.selectbox(label='Gerar arquivo ZIP?', options=['Sim', 'Não'])

        process_button = st.button(label='Processar', width='stretch', type='primary', key='process_button')

        if process_button:
            if not mes_competencia:
                st.warning('Preencha o mês de competência antes de prosseguir.')
            else:
                if option == 'Planilha':
                    with st.spinner('O sistema está processando as faturas...'):
                        try:
                            processed_dataframe = process_csv(invoices=faturas, utility_company=concessionaria, location=local)
                            
                            if processed_dataframe.empty:
                                st.warning('O sistema não encontrou faturas correspondentes aos identificadores do local selecionado.')
                            else:
                                st.success('O sistema processou as faturas com sucesso.')
                                st.dataframe(data=processed_dataframe)
                                
                                csv_file_bytes = processed_dataframe.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    label='Baixar Planilha',
                                    data=csv_file_bytes,
                                    file_name=f'Faturas_{concessionaria}_{mes_competencia.replace("/", "_")}.csv',
                                    mime='text/csv'
                                )
                        except Exception as error_message:
                            st.error(str(error_message))
                elif option == 'Relatório':
                    with st.spinner('O sistema está processando o relatório e agrupando os arquivos...'):
                        try:
                            processed_dataframe = process_csv(invoices=faturas, utility_company=concessionaria, location=local)
                            
                            if processed_dataframe.empty:
                                st.warning('O sistema não encontrou faturas correspondentes aos identificadores do local selecionado.')
                            else:
                                st.session_state.report_data = generate_report(
                                    processed_dataframe=processed_dataframe,
                                    utility_company=concessionaria,
                                    location=local,
                                    mes_competencia=mes_competencia,
                                    tipo_debito=tipo_debito,
                                    conta=conta
                                )
                                
                                if gerar_zip == 'Sim':
                                    st.session_state.zip_data = generate_zip(
                                        invoices=faturas,
                                        utility_company=concessionaria,
                                        location=local,
                                        tipo_debito=tipo_debito
                                    )
                                else:
                                    st.session_state.zip_data = None
                                    
                                st.success('O sistema concluiu o processamento com sucesso.')
                        except Exception as error_message:
                            st.error(str(error_message))

        if option == 'Relatório' and st.session_state.get('report_data') is not None:
            st.download_button(
                label='Baixar Relatório',
                data=st.session_state.report_data,
                file_name=f'Relatorio_{mes_competencia.replace("/", "_")}_{local.replace(" ", "_")}_{concessionaria}_Debito_{tipo_debito.replace("á", "a")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            if st.session_state.get('zip_data') is not None:
                st.download_button(
                    label='Baixar Arquivos ZIP',
                    data=st.session_state.zip_data,
                    file_name=f'ZIP_{mes_competencia.replace("/", "_")}_{local.replace(" ", "_")}_{concessionaria}_Debito_{tipo_debito.replace("á", "a")}.zip',
                    mime='application/zip'
                )