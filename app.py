# importar bibliotecas

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# configuraçoes iniciais do Dashboard
st.set_page_config(page_title="Dashboard - Frota de Veículos", layout="wide")

st.title("Dashboard de Desempenho da Frota")
st.markdown("Este painel permite analisar o consumo, quilometragem e custos de manutenção da frota de veículos.")

# carregar dados
@st.cache_data

def carregar_dados():
    df = pd.read_csv(r'dados_frota_veiculos.csv')
    df['Data'] = pd.to_datetime(df['Data'])
    df['Ano'] = df['Data'].dt.year
    df['Mes'] = df['Data'].dt.month
    df['Consumo Km/L'] = df['KM_Rodado'] / df['Litros_Combustivel']
    df['Custo/KM'] = df['Custo_Manutencao'] / df['KM_Rodado']

    return df

# função que gera o PDF
def gerar_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "📄 Relatório da Frota de Veículos")

    # Métricas básicas
    c.setFont("Helvetica", 12)
    c.drawString(50, altura - 100, f"Total de veículos na análise: {df['ID_Veiculo'].nunique()}")
    c.drawString(50, altura - 120, f"Total KM rodado: {df['KM_Rodado'].sum():,.0f} km")
    c.drawString(50, altura - 140, f"Média de consumo: {df['Consumo Km/L'].mean():.2f} km/L")
    c.drawString(50, altura - 160, f"Custo médio por KM: R$ {df['Custo/KM'].mean():.2f}")

     # Rodapé da página inicial
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 30, "Relatório gerado automaticamente via Streamlit")
    c.showPage()

    # Inserir gráficos (chama função que os gera)
    graficos = gerar_graficos(df)

    for graf in graficos:
        imagem = ImageReader(graf)
        c.drawImage(imagem, 50, 200, width=500, preserveAspectRatio=True, mask='auto')
        c.showPage()
        
    # Página final - Conclusão
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, altura - 50, "🔍 Conclusões e Observações")
    c.setFont("Helvetica", 12)

    # Gerar dados para conclusões automáticas

    total_km = df['KM_Rodado'].sum()
    media_consumo = df['Consumo Km/L'].mean()
    media_custo_km = df['Custo/KM'].mean()
    veiculo_mais_caro = df.groupby('ID_Veiculo')['Custo/KM'].mean().idxmax()
    custo_mais_alto = df.groupby('ID_Veiculo')['Custo/KM'].mean().max()

    veiculo_mais_economico = df.groupby('ID_Veiculo')['Consumo Km/L'].mean().idxmax()
    melhor_consumo = df.groupby('ID_Veiculo')['Consumo Km/L'].mean().max()

    conclusoes = [
    f"- A frota filtrada percorreu um total de {total_km:,.0f} km.",
    f"- O consumo médio foi de {media_consumo:.2f} km/L.",
    f"- O custo médio por km rodado foi de R$ {media_custo_km:.2f}.",
    f"- O veículo com maior custo por km foi o {veiculo_mais_caro} (R$ {custo_mais_alto:.2f}/km).",
    f"- O veículo mais econômico em consumo foi o {veiculo_mais_economico} ({melhor_consumo:.2f} km/L).",
    "- Recomenda-se atenção especial aos veículos com custos elevados e consumo abaixo da média.",
    "- O uso desses dados pode apoiar decisões estratégicas de manutenção e renovação da frota."
    ]

    # Escrever as conclusões, uma por linha
    y = altura - 80
    for linha in conclusoes:
        c.drawString(50, y, linha)
        y -= 20  # espaço entre linhas

    # Rodapé final
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 30, "Relatório gerado com dados filtrados no dashboard - Streamlit")
    c.showPage()
    
    c.save()
    buffer.seek(0)
    return buffer

# funçao que gera graficos no pdf
def gerar_graficos(df):
    
    imagens = []

    # 1. Gráfico KM rodado por mês
    km_mensal = df.groupby(['Ano', 'Mes'])['KM_Rodado'].sum().reset_index()
    km_mensal = km_mensal.rename(columns={'Ano': 'year', 'Mes': 'month'})
    km_mensal['Data'] = pd.to_datetime(km_mensal[['year', 'month']].assign(day=1))
    
    fig1, ax1 = plt.subplots()
    sns.lineplot(data=km_mensal, x='Data', y='KM_Rodado', ax=ax1)
    ax1.set_title('KM Rodado por Mês')
    fig1.tight_layout()

    buffer1 = io.BytesIO()
    fig1.savefig(buffer1, format="png")
    buffer1.seek(0)
    imagens.append(buffer1)

    # 2. Gráfico de Consumo médio por veículo
    consumo = df.groupby('ID_Veiculo')['Consumo Km/L'].mean().reset_index().sort_values(by='Consumo Km/L', ascending=False)
    fig2, ax2 = plt.subplots()
    sns.barplot(data=consumo, x='ID_Veiculo', y='Consumo Km/L', ax=ax2)
    ax2.set_title('Consumo Médio por Veículo')
    ax2.tick_params(axis='x', rotation=45)
    fig2.tight_layout()

    buffer2 = io.BytesIO()
    fig2.savefig(buffer2, format="png")
    buffer2.seek(0)
    imagens.append(buffer2)

    return imagens

df = carregar_dados()

# Criar filtros laterais
st.sidebar.header("Filtros")

# Filtro por tipo de veículo e veiculo
tipos = df['Tipo_Veiculo'].unique()
tipo_selecionado = st.sidebar.selectbox("Selecionar Tipo de Veículo", options=["Todos"] + sorted(list(tipos)))

# Filtro de veículo dependente do tipo selecionado
if tipo_selecionado == "Todos":
    veiculos_disponiveis = df['ID_Veiculo'].unique()
else:
    veiculos_disponiveis = df[df['Tipo_Veiculo'] == tipo_selecionado]['ID_Veiculo'].unique()

veiculo_selecionado = st.sidebar.selectbox("Selecionar Veículo", options=["Todos"] + sorted(list(veiculos_disponiveis)))

# Aplicar filtros no dataframe
df_filtrado = df.copy()

if tipo_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Tipo_Veiculo'] == tipo_selecionado]

if veiculo_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ID_Veiculo'] == veiculo_selecionado]

# --- Indicadores principais --- #

st.subheader('Visão Geral')

# criando 4 colunas
col1, col2, col3, col4 = st.columns(4) 

with col1:
    st.metric('Veículos na Análise', df_filtrado['ID_Veiculo'].nunique())

with col2:
    st.metric('Total KM rodado', f'{df_filtrado['KM_Rodado'].sum():,.0f} km')

with col3:
    st.metric('Média Consumo', f'{df_filtrado['Consumo Km/L'].mean():.2f} km/L')

with col4: 
    st.metric('Custo Médio por KM', f'R$ {df_filtrado['Custo/KM'].mean():.2f}')

# Graficos km/mes

st.subheader("📅 Quilometragem por Mês")

# Agrupamento por data
km_mensal = df_filtrado.groupby(['Ano', 'Mes'])['KM_Rodado'].sum().reset_index()
km_mensal = km_mensal.rename(columns={'Ano': 'year', 'Mes': 'month'})
km_mensal['Data'] = pd.to_datetime(km_mensal[['year', 'month']].assign(day=1))

# Gráfico de linha
fig1, ax1 = plt.subplots()
sns.lineplot(data=km_mensal, x='Data', y='KM_Rodado', ax=ax1)
ax1.set_title('KM Rodado ao Longo do Tempo')
ax1.set_ylabel('KM Rodado')
ax1.set_xlabel('Data')
st.pyplot(fig1)

# Botao download grafico km/mes

buffer = io.BytesIO()
fig1.savefig(buffer, format="png")
st.download_button(
    label="⬇️ Baixar gráfico - KM por Mês",
    data=buffer.getvalue(),
    file_name="grafico_km_mensal.png",
    mime="image/png"
)

# grafico Consumo Medio

st.subheader("⛽ Consumo Médio por Veículo")

# Agrupar por veículo e calcular o consumo médio
consumo_veiculos = df_filtrado.groupby('ID_Veiculo')['Consumo Km/L'].mean().reset_index()
consumo_veiculos = consumo_veiculos.sort_values(by='Consumo Km/L', ascending=False)

# Gráfico de barras
fig2, ax2 = plt.subplots()
sns.barplot(data=consumo_veiculos, x='ID_Veiculo', y='Consumo Km/L', ax=ax2)
ax2.set_title('Consumo Médio (Km/L) por Veículo')
ax2.set_xlabel('Veículo')
ax2.set_ylabel('Km/L')
plt.xticks(rotation=45)
st.pyplot(fig2)

# Botao download grafico consumo medio

buffer = io.BytesIO()
fig1.savefig(buffer, format="png")
st.download_button(
    label="⬇️ Baixar gráfico - Consumo Médio",
    data=buffer.getvalue(),
    file_name="grafico_km_mensal.png",
    mime="image/png"
)

#grafico Custo/Km

st.subheader("💰 Custo Médio por KM - Veículos")

# Agrupar por veículo e calcular custo médio por KM
custo_veiculos = df_filtrado.groupby('ID_Veiculo')['Custo/KM'].mean().reset_index()
custo_veiculos = custo_veiculos.sort_values(by='Custo/KM', ascending=False)

# Gráfico de barras
fig3, ax3 = plt.subplots()
sns.barplot(data=custo_veiculos, x='ID_Veiculo', y='Custo/KM', ax=ax3)
ax3.set_title('Custo Médio por KM por Veículo')
ax3.set_xlabel('Veículo')
ax3.set_ylabel('R$/km')
plt.xticks(rotation=45)
st.pyplot(fig3)

# Botao download grafico custo medio/km

buffer = io.BytesIO()
fig1.savefig(buffer, format="png")
st.download_button(
    label="⬇️ Baixar gráfico - Custo/Km",
    data=buffer.getvalue(),
    file_name="grafico_km_mensal.png",
    mime="image/png"
)

# Botao de Download dados filtrados
st.subheader("📥 Baixar dados filtrados")

# Converter o DataFrame filtrado em CSV (em memória)
csv = df_filtrado.to_csv(index=False).encode('utf-8')

# Botão de download

st.download_button(
    label="⬇️ Download CSV",
    data=csv,
    file_name="dados_filtrados.csv",
    mime="text/csv"
)

# Botao baixar relatorio PDF
st.subheader("📄 Baixar relatório em PDF")

pdf_bytes = gerar_pdf(df_filtrado)
st.download_button(
    label="⬇️ Baixar Relatório PDF",
    data=pdf_bytes,
    file_name="relatorio_frota.pdf",
    mime="application/pdf"
)