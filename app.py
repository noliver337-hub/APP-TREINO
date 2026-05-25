import streamlit as st
import json
import os

# Nome do arquivo para persistência de dados
DATA_FILE = "treinos_data.json"

def carregar_dados():
    dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    treinos_vazio = {dia: {"texto": "", "status": {}} for dia in dias}
    dados_padrao = {
        "centrais": [],
        "usuarios": {
            "admin": {"senha": "admin", "role": "admin", "central": "Sistema", "treinos": treinos_vazio}
        }
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                
                if "usuarios" not in dados:
                    # MIGRACAO: Se encontrar treinos no formato antigo, move para o admin
                    migrados = {}
                    for dia in dias:
                        # Tenta pegar os dados existentes ou cria vazio
                        val = dados.get(dia, {"texto": "", "status": {}})
                        if isinstance(val, str): # Formato texto puro
                            migrados[dia] = {"texto": val, "status": {}}
                        else: # Formato texto + status
                            migrados[dia] = val
                    
                    dados = dados_padrao
                    dados["usuarios"]["admin"]["treinos"] = migrados
                    salvar_dados(dados)
                
                return dados
        except Exception:
            return dados_padrao
    return dados_padrao

def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Inicializa o estado global carregando do arquivo
if "db" not in st.session_state:
    st.session_state.db = carregar_dados()
if "auth" not in st.session_state:
    st.session_state.auth = None

# Configuração da página do aplicativo
st.set_page_config(page_title="Sistema de Treino Pro", page_icon="💪", layout="centered")

dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

# --- SISTEMA DE LOGIN ---
if st.session_state.auth is None:
    st.title("🔐 Login do Sistema")
    with st.form("login_form"):
        user_input = st.text_input("Usuário")
        pass_input = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if user_input in st.session_state.db["usuarios"] and st.session_state.db["usuarios"][user_input]["senha"] == pass_input:
                st.session_state.auth = user_input
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
    st.stop()

# --- INTERFACE LOGADA ---
user_logado = st.session_state.auth
dados_user = st.session_state.db["usuarios"][user_logado]
role = dados_user.get("role", "user")

st.sidebar.title(f"Olá, {user_logado}!")
st.sidebar.write(f"Central: {dados_user.get('central', 'N/A')}")
if st.sidebar.button("Sair"):
    st.session_state.auth = None
    st.rerun()

if role == "admin":
    st.title("🎮 Painel de Controle ADM")
    
    tab1, tab2, tab3 = st.tabs(["Centrais", "Usuários", "Montar Treinos"])
    
    with tab1:
        st.subheader("Cadastrar Nova Central")
        nova_central = st.text_input("Nome da Central")
        if st.button("Adicionar Central"):
            if nova_central and nova_central not in st.session_state.db["centrais"]:
                st.session_state.db["centrais"].append(nova_central)
                salvar_dados(st.session_state.db)
                st.success("Central cadastrada!")
                st.rerun()

    with tab2:
        st.subheader("Cadastrar Novo Usuário")
        with st.form("cad_user"):
            new_login = st.text_input("Login")
            new_pass = st.text_input("Senha")
            central_user = st.selectbox("Vincular à Central", st.session_state.db["centrais"])
            if st.form_submit_button("Salvar Usuário"):
                if new_login and new_pass:
                    st.session_state.db["usuarios"][new_login] = {
                        "senha": new_pass,
                        "role": "user",
                        "central": central_user,
                        "treinos": {dia: {"texto": "", "status": {}} for dia in dias_semana}
                    }
                    salvar_dados(st.session_state.db)
                    st.success(f"Usuário {new_login} criado!")

    with tab3:
        st.subheader("Montar Treino por Usuário")
        lista_users = [u for u, d in st.session_state.db["usuarios"].items() if d["role"] == "user"]
        if lista_users:
            user_alvo = st.selectbox("Selecionar Aluno", lista_users)
            dia_alvo = st.selectbox("Dia da Semana", dias_semana, key="admin_dia")
            
            texto_atual = st.session_state.db["usuarios"][user_alvo]["treinos"][dia_alvo]["texto"]
            detalhes = st.text_area("Exercícios (um por linha)", value=texto_atual)
            
            if st.button("Salvar Treino do Aluno"):
                st.session_state.db["usuarios"][user_alvo]["treinos"][dia_alvo]["texto"] = detalhes
                # Sincroniza Checklist
                linhas = [l.strip() for l in detalhes.split('\n') if l.strip()]
                old_status = st.session_state.db["usuarios"][user_alvo]["treinos"][dia_alvo]["status"]
                st.session_state.db["usuarios"][user_alvo]["treinos"][dia_alvo]["status"] = {
                    ex: old_status.get(ex, False) for ex in linhas
                }
                salvar_dados(st.session_state.db)
                st.success("Treino atualizado!")
        else:
            st.info("Cadastre um usuário primeiro.")

st.markdown("---")
# --- INTERFACE DE TREINOS (Disponível para todos os perfis) ---
st.title("💪 Meus Treinos")
dia_selecionado = st.selectbox("Selecione o dia para treinar:", dias_semana)

if "treinos" not in dados_user:
    st.warning("Seu plano de treinos ainda não foi montado.")
else:
    treino_dia = dados_user["treinos"][dia_selecionado]
    if treino_dia["status"]:
        st.write(f"### Checklist de {dia_selecionado}")
        progresso_alterado = False
        for exercicio in list(treino_dia["status"].keys()):
            # Key única baseada no usuário, dia e exercício
            key = f"check_{user_logado}_{dia_selecionado}_{exercicio}"
            marcado = st.checkbox(exercicio, value=treino_dia["status"][exercicio], key=key)
            if marcado != treino_dia["status"][exercicio]:
                st.session_state.db["usuarios"][user_logado]["treinos"][dia_selecionado]["status"][exercicio] = marcado
                progresso_alterado = True
        
        if progresso_alterado:
            salvar_dados(st.session_state.db)
            st.rerun()
        
        if all(treino_dia["status"].values()) and treino_dia["status"]:
            st.success("⭐ Treino de hoje concluído!")
    else:
        st.info("Nenhum exercício cadastrado para hoje.")

with st.expander("Visualizar Resumo da Semana"):
    if "treinos" in dados_user:
        for dia, info in dados_user["treinos"].items():
            concluido = all(info["status"].values()) if info["status"] else False
            st.write(f"{'✅' if concluido else '⬜'} **{dia}:** {info['texto'][:50]}...")
