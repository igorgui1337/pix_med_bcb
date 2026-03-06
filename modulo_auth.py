import os
import json
import re
from werkzeug.security import generate_password_hash, check_password_hash

# Caminho absoluto da pasta solicitada pelo usuário
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_DIR = os.path.join(BASE_DIR, "dados_senha_login")
USER_FILE = os.path.join(AUTH_DIR, "usuarios.json")

def init_auth():
    """Inicializa o diretório e o arquivo JSON de usuários, se não existirem."""
    if not os.path.exists(AUTH_DIR):
        os.makedirs(AUTH_DIR)
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def carregar_usuarios():
    init_auth()
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4)

def validar_email(email):
    """
    Verifica se o e-mail tem um domínio válido usando regex.
    Ex: usuario@dominio.com
    """
    padrao = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(padrao, email) is not None

def validar_senha(senha):
    """
    A senha precisa ter:
    - Pelo menos 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial (!@#$%^&*()_+{}|:"<>?~`-=\[\];',.\/)
    """
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r'[A-Z]', senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    if not re.search(r'[a-z]', senha):
        return False, "A senha deve conter pelo menos uma letra minúscula."
    if not re.search(r'\d', senha):
        return False, "A senha deve conter pelo menos um número."
    if not re.search(r'[!@#$%^&*()_+{}|:"<>?~`\-=\[\];\',./]', senha):
        return False, "A senha deve conter pelo menos um caractere especial."
    return True, ""

def registrar_usuario(email, senha):
    """Registra um novo usuário no sistema salvando no arquivo JSON com hash."""
    email = email.strip().lower()
    
    # 1. Validações
    if not validar_email(email):
        return False, "E-mail inválido. Certifique-se de usar um domínio válido."
    
    valida_senha, msg_senha = validar_senha(senha)
    if not valida_senha:
        return False, msg_senha
    
    # 2. Carrega usuários existentes e verifica duplicidade
    usuarios = carregar_usuarios()
    if email in usuarios:
        return False, "Este e-mail já está cadastrado."
    
    # 3. Hash da senha e armazenamento
    senha_hash = generate_password_hash(senha)
    usuarios[email] = {
        "senha_hash": senha_hash,
        "criado_em": __import__('datetime').datetime.now().isoformat()
    }
    salvar_usuarios(usuarios)
    
    return True, "Usuário registrado com sucesso!"

def verificar_login(email, senha):
    """Verifica as credenciais do usuário."""
    email = email.strip().lower()
    usuarios = carregar_usuarios()
    if email not in usuarios:
        return False, "E-mail não encontrado."
    
    if check_password_hash(usuarios[email]["senha_hash"], senha):
        return True, "Login realizado com sucesso."
    
    return False, "Senha incorreta."
