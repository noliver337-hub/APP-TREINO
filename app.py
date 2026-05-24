import streamlit as st
import json
import os

# Nome do arquivo para persistência de dados
DATA_FILE = "treinos_data.json"

def carregar_dados():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    # Estrutura: { dia: { "texto": "...", "status": { "Exercicio 1": False } } }
    return {dia: {"texto": "", "status": {}} for dia in dias}

def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Inicializa o estado global carregando do arquivo
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

dia_selecionado = st.selectbox("Selecione o dia:", dias_semana)

if perfil == "Administrador":
    st.info("Painel de Edição: Defina os treinos para a semana.")
    with st.form(key="form_treino"):
        detalhes = st.text_area(f"Editar exercícios para {dia_selecionado}:", 
                                value=st.session_state.treinos[dia_selecionado]["texto"],
                                placeholder="Digite um exercício por linha...")

        if st.form_submit_button("Salvar Treino"):
            # Atualiza o texto
            st.session_state.treinos[dia_selecionado]["texto"] = detalhes
            
            # Gera novo dicionário de status baseado nas linhas
            linhas = [l.strip() for l in detalhes.split('\n') if l.strip()]
            novo_status = {ex: False for ex in linhas}
            
            # Mantém o progresso se o nome do exercício for idêntico
            for ex in linhas:
                if ex in st.session_state.treinos[dia_selecionado]["status"]:
                    novo_status[ex] = st.session_state.treinos[dia_selecionado]["status"][ex]
            
            st.session_state.treinos[dia_selecionado]["status"] = novo_status
            salvar_dados(st.session_state.treinos)
            st.success("Configuração salva!")
            st.rerun()
else:
    # Interface do Usuário: Checklist
    dados_dia = st.session_state.treinos[dia_selecionado]
    if dados_dia["status"]:
        st.write(f"### Checklist de {dia_selecionado}")
        
        progresso_alterado = False
        for exercicio in list(dados_dia["status"].keys()):
            # Checkbox para cada exercício
            marcado = st.checkbox(exercicio, value=dados_dia["status"][exercicio], key=f"cb_{dia_selecionado}_{exercicio}")
            if marcado != dados_dia["status"][exercicio]:
                st.session_state.treinos[dia_selecionado]["status"][exercicio] = marcado
                progresso_alterado = True
        
        if progresso_alterado:
            salvar_dados(st.session_state.treinos)
            st.rerun()

        # Verifica se tudo foi concluído
        if all(dados_dia["status"].values()) and dados_dia["status"]:
            st.success("⭐ Todos os exercícios de hoje foram concluídos!")
    else:
        st.warning("Nenhum exercício definido para hoje.")

with st.expander("Visualizar Cronograma da Semana"):
    for dia, dados in st.session_state.treinos.items():
        # O dia está concluído apenas se houver exercícios e todos estiverem True
        concluido = all(dados["status"].values()) if dados["status"] else False
        status_icon = "✅" if concluido else "⬜"
        st.write(f"{status_icon} **{dia}:** {dados['texto'] if dados['texto'] else 'Descanso'}")

# Barra lateral (Sidebar)
st.sidebar.header("Configurações do App")
opcao = st.sidebar.selectbox("Escolha uma opção de visualização:", ["Padrão", "Modo Escuro", "Modo Minimalista"])
st.sidebar.write(f"Opção selecionada: **{opcao}**") 
