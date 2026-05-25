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
def contar_concluidos(user_data):
    count = 0
    if "treinos" in user_data:
        for dia in user_data["treinos"]:
            status = user_data["treinos"][dia].get("status", {})
            if status and all(status.values()):
                count += 1
    return count

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
    
    tab1, tab2, tab3, tab4 = st.tabs(["Centrais", "Usuários", "Meus Templates", "Montar Treinos Alunos"])
    
    with tab1:
        st.subheader("Cadastrar Nova Central")
        nova_central = st.text_input("Nome da Central")
        if st.button("Adicionar Central"):
            if nova_central and nova_central not in st.session_state.db["centrais"]:
                st.session_state.db["centrais"].append(nova_central)
                salvar_dados(st.session_state.db)
                st.success("Central cadastrada!")
                st.rerun()

        st.markdown("---")
        st.subheader("Visualização por Central")
        if not st.session_state.db["centrais"]:
            st.info("Nenhuma central cadastrada ainda.")
        else:
            for central in st.session_state.db["centrais"]:
                # Filtra os usuários que pertencem a esta central
                usuarios_vinculados = [u for u, d in st.session_state.db["usuarios"].items() if d.get("central") == central]
                
                with st.expander(f"🏢 Central: {central} ({len(usuarios_vinculados)} usuários)"):
                    if usuarios_vinculados:
                        for user in usuarios_vinculados:
                            st.write(f"👤 **{user}**")
                    else:
                        st.write("Nenhum usuário vinculado a esta central.")

    with tab2:
        st.subheader("Cadastrar Novo Usuário")
        with st.form("cad_user"):
            new_login = st.text_input("Login")
            new_pass = st.text_input("Senha")
            central_user = st.selectbox("Vincular à Central", st.session_state.db["centrais"])
            if st.form_submit_button("Salvar Usuário"):
                if new_login and new_pass:
                    treinos_vazio = {dia: {"texto": "", "status": {}} for dia in dias_semana}
                    st.session_state.db["usuarios"][new_login] = {
                        "senha": new_pass,
                        "role": "user",
                        "central": central_user,
                        "treinos": treinos_vazio
                    }
                    salvar_dados(st.session_state.db)
                    st.success(f"Usuário {new_login} criado!")
                    st.rerun()

        st.markdown("---")
        st.subheader("📊 Estatísticas de Treino (Semana)")
        lista_user_stats = [u for u, d in st.session_state.db["usuarios"].items() if d.get("role") == "user"]
        for u in lista_user_stats:
            concluidos = contar_concluidos(st.session_state.db["usuarios"][u])
            st.write(f"👤 **{u}**: {concluidos} / 7 treinos concluídos")

    with tab3:
        st.subheader("⚙️ Biblioteca de Templates (Admin)")
        templates_admin = st.session_state.db["usuarios"]["admin"]["treinos"]

        # Listagem Simples
        if templates_admin:
            with st.expander("Ver lista de templates cadastrados"):
                for t_name in templates_admin.keys():
                    st.write(f"• {t_name}")

        st.markdown("---")
        # Interface para Criar ou Editar
        acao_template = st.radio("O que deseja fazer?", ["Editar/Excluir Template", "Criar Novo Template"], horizontal=True)

        if acao_template == "Editar/Excluir Template" and templates_admin:
            temp_selecionado = st.selectbox("Selecione o template:", list(templates_admin.keys()))
            texto_atual = templates_admin[temp_selecionado]["texto"]
            
            with st.form(key=f"edit_temp_{temp_selecionado}"):
                novo_nome = st.text_input("Nome do Template", value=temp_selecionado)
                novo_texto = st.text_area("Exercícios (um por linha)", value=texto_atual, height=200)
                col1, col2 = st.columns(2)
                
                if col1.form_submit_button("💾 Salvar Alterações"):
                    if novo_nome != temp_selecionado:
                        del st.session_state.db["usuarios"]["admin"]["treinos"][temp_selecionado]
                    
                    linhas = [l.strip() for l in novo_texto.split('\n') if l.strip()]
                    st.session_state.db["usuarios"]["admin"]["treinos"][novo_nome] = {
                        "texto": novo_texto,
                        "status": {ex: False for ex in linhas}
                    }
                    salvar_dados(st.session_state.db)
                    st.success("Template atualizado!")
                    st.rerun()
                
                if col2.form_submit_button("🗑️ Excluir Template"):
                    del st.session_state.db["usuarios"]["admin"]["treinos"][temp_selecionado]
                    salvar_dados(st.session_state.db)
                    st.warning("Template removido.")
                    st.rerun()
        
        elif acao_template == "Criar Novo Template":
            with st.form(key="novo_template"):
                nome_n = st.text_input("Nome do Template (ex: Treino A - Superior)")
                texto_n = st.text_area("Exercícios (um por linha)", height=200)
                if st.form_submit_button("➕ Criar"):
                    if nome_n:
                        linhas = [l.strip() for l in texto_n.split('\n') if l.strip()]
                        st.session_state.db["usuarios"]["admin"]["treinos"][nome_n] = {
                            "texto": texto_n,
                            "status": {ex: False for ex in linhas}
                        }
                        salvar_dados(st.session_state.db)
                        st.success(f"Template '{nome_n}' criado!")
                        st.rerun()

    with tab4:
        st.subheader("📋 Montar Treino por Usuário")
        lista_users = [u for u, d in st.session_state.db["usuarios"].items() if d["role"] == "user"]
        if lista_users:
            user_alvo = st.selectbox("Selecionar Aluno", lista_users)
            dia_alvo = st.selectbox("Dia da Semana", dias_semana, key="admin_dia")
            
            texto_atual = st.session_state.db["usuarios"][user_alvo]["treinos"][dia_alvo]["texto"]
            
            # Seção de Importação
            templates_admin = st.session_state.db["usuarios"]["admin"]["treinos"]
            if templates_admin:
                st.write("---")
                st.write("#### 📥 Importar da Biblioteca")
                temp_para_importar = st.selectbox("Escolha um template disponível:", list(templates_admin.keys()))
                if st.button("Confirmar Importação para este dia"):
                    admin_data = templates_admin[temp_para_importar]
                    st.session_state.db["usuarios"][user_alvo]["treinos"][dia_alvo] = {
                        "texto": admin_data["texto"],
                        "status": {ex: False for ex in admin_data["status"].keys()}
                    }
                    salvar_dados(st.session_state.db)
                    st.success(f"Template '{temp_para_importar}' aplicado a {user_alvo} na {dia_alvo}!")
                    st.rerun()
                st.write("---")

            # Usamos um formulário com chave única para garantir que o texto mude ao trocar o aluno/dia
            with st.form(key=f"form_treino_{user_alvo}_{dia_alvo}"):
                detalhes = st.text_area("Editar exercícios manualmente (um por linha)", value=texto_atual, height=200)
                if st.form_submit_button("Salvar Treino do Aluno"):
                    st.session_state.db["usuarios"][user_alvo]["treinos"][dia_alvo]["texto"] = detalhes
                    linhas = [l.strip() for l in detalhes.split('\n') if l.strip()]
                    st.session_state.db["usuarios"][user_alvo]["treinos"][dia_alvo]["status"] = {ex: False for ex in linhas}
                    salvar_dados(st.session_state.db)
                    st.success("Treino salvo!")
                    st.rerun()
        else:
            st.info("Cadastre um usuário primeiro.")

if role == "user":
    st.markdown("---")
    # --- INTERFACE DE TREINOS (Apenas para Alunos) ---
    st.title("💪 Meus Treinos")
    dia_selecionado = st.selectbox("Selecione o dia para treinar:", dias_semana)

    if "treinos" not in dados_user:
        st.warning("Seu plano de treinos ainda não foi montado.")
    else:
        treino_dia = dados_user["treinos"][dia_selecionado]
        if treino_dia["status"]:
            st.write(f"### Checklist de {dia_selecionado}")

            # Barra de progresso
            total_ex = len(treino_dia["status"])
            concluidos = sum(1 for v in treino_dia["status"].values() if v)
            percentual = concluidos / total_ex if total_ex > 0 else 0.0
            st.progress(percentual)
            st.write(f"Progresso: **{int(percentual * 100)}%**")

            progresso_alterado = False
            for exercicio in list(treino_dia["status"].keys()):
                key = f"check_{user_logado}_{dia_selecionado}_{exercicio}"
                marcado = st.checkbox(exercicio, value=treino_dia["status"][exercicio], key=key)
                if marcado != treino_dia["status"][exercicio]:
                    st.session_state.db["usuarios"][user_logado]["treinos"][dia_selecionado]["status"][exercicio] = marcado
                    progresso_alterado = True
            
            if progresso_alterado:
                salvar_dados(st.session_state.db)
                # Se acabou de completar o último
                novo_concluidos = sum(1 for v in st.session_state.db["usuarios"][user_logado]["treinos"][dia_selecionado]["status"].values() if v)
                if novo_concluidos == total_ex:
                    st.toast("⭐ Treino concluído com sucesso!", icon="🎉")
                st.rerun()
        else:
            st.info("Nenhum exercício cadastrado para hoje.")

    with st.expander("Visualizar Resumo da Semana"):
        if "treinos" in dados_user:
            for dia, info in dados_user["treinos"].items():
                concluido_dia = all(info["status"].values()) if info["status"] else False
                st.write(f"{'✅' if concluido_dia else '⬜'} **{dia}:** {info['texto'][:50]}...")
