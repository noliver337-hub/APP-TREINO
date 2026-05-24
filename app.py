import streamlit as st
import json
import os

# Nome do arquivo para persistência de dados
DATA_FILE = "treinos_data.json"

def carregar_dados():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {dia: "" for dia in ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]}

def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Inicializa os treinos carregando do arquivo
if "treinos" not in st.session_state:
    st.session_state.treinos = carregar_dados()

# Configuração da página do aplicativo
st.set_page_config(page_title="Meu Primeiro App", page_icon="🚀", layout="centered")

# Título Principal
st.title("🚀 Olá! Este é o meu novo App")
st.write("Criado no VS Code e rodando localmente com Python e Streamlit.")

# Barra lateral (Sidebar) para Controle de Acesso
st.sidebar.header("🔐 Acesso")
perfil = st.sidebar.radio("Escolha o perfil:", ["Usuário", "Administrador"])

if perfil == "Administrador":
    st.sidebar.warning("Modo Edição Ativado")

# Seção 3: Planejador de Treinos Semanal
st.markdown("---")
st.subheader("💪 Planejador de Treinos da Semana")

dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

# Inicializa o dicionário de treinos se não existir
if "treinos" not in st.session_state:
    st.session_state.treinos = {dia: "" for dia in dias_semana}
if "concluidos" not in st.session_state:
    st.session_state.concluidos = {dia: False for dia in dias_semana}
if "status_exercicios" not in st.session_state:
    st.session_state.status_exercicios = {dia: {} for dia in dias_semana}

dia_selecionado = st.selectbox("Selecione o dia:", dias_semana)

if perfil == "Administrador":
    st.info("Painel de Edição: Defina os treinos para a semana.")
    with st.form(key="form_treino"):
        detalhes = st.text_area(f"Editar exercícios para {dia_selecionado}:", 
                                value=st.session_state.treinos[dia_selecionado],
                                placeholder="Digite um exercício por linha. Ex:\nSupino Reto 3x12\nAgachamento 4x10")

        if st.form_submit_button("Salvar Treino"):
            st.session_state.treinos[dia_selecionado] = detalhes
            salvar_dados(st.session_state.treinos)
            # Atualiza a lista de exercícios para o checklist
            linhas = [linha.strip() for linha in detalhes.split('\n') if linha.strip()]
            st.session_state.status_exercicios[dia_selecionado] = {
                ex: st.session_state.status_exercicios[dia_selecionado].get(ex, False) for ex in linhas
            }
            st.success(f"Treino de {dia_selecionado} salvo com sucesso!")
else:
    # Seção de execução do treino (Apenas para Usuário)
    if st.session_state.status_exercicios.get(dia_selecionado):
        st.write(f"### Checklist de {dia_selecionado}")
        todos_feitos = True
        
        for exercicio in st.session_state.status_exercicios[dia_selecionado]:
            marcado = st.checkbox(exercicio, value=st.session_state.status_exercicios[dia_selecionado][exercicio], key=f"check_{dia_selecionado}_{exercicio}")
            st.session_state.status_exercicios[dia_selecionado][exercicio] = marcado
            if not marcado:
                todos_feitos = False
        
        st.session_state.concluidos[dia_selecionado] = todos_feitos
        if todos_feitos:
            st.success("⭐ Todos os exercícios de hoje foram concluídos!")
    else:
        st.warning("Nenhum treino cadastrado para hoje. Peça ao Administrador para configurar.")

with st.expander("Visualizar Cronograma da Semana"):
    for dia, info in st.session_state.treinos.items():
        status = "✅" if st.session_state.concluidos[dia] else "⬜"
        st.write(f"{status} **{dia}:** {info if info else 'Descanso / Não definido'}")

# Linha divisória
st.markdown("---")

# Barra lateral (Sidebar)
st.sidebar.header("Configurações do App")
opcao = st.sidebar.selectbox("Escolha uma opção de visualização:", ["Padrão", "Modo Escuro", "Modo Minimalista"])
st.sidebar.write(f"Opção selecionada: **{opcao}**") 
