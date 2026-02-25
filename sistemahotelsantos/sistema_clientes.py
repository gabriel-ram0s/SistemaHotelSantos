import sqlite3
from datetime import datetime, timedelta
import os
import shutil
import csv
import secrets
import hashlib
import sys
import socket
import subprocess
import time
try:
    import requests
except ImportError:
    requests = None

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

class SistemaCreditos:
    def __init__(self, db_name="hotel.db"):
        self.db_name = db_name
        self.versao_atual = "4.2.9"  # Versão estável (apenas EXE)
        self.empresa = {
            "nome": "HOTEL SANTOS",
            "razao": "Hotel e Restaurante Santos Ana Lucia C. dos Santos",
            "cnpj": "03.288.530/0001-75",
            "endereco": "Praca Mota Sobrinho 10, Centro, ES Pinhal - SP",
            "contato": "Tel: (19) 3651-3297 / Whats: (19) 99759-7503",
            "email": "hotelsantoss@hotmail.com"
        }
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.criar_tabelas()

    def criar_tabelas(self):
        with self.conn:
            self.cursor.execute('CREATE TABLE IF NOT EXISTS hospedes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, documento TEXT UNIQUE NOT NULL)')
            self.cursor.execute('CREATE TABLE IF NOT EXISTS categorias (nome TEXT PRIMARY KEY)')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS historico_zebra (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT, documento TEXT, tipo TEXT, 
                                    valor REAL, categoria TEXT, data_acao TEXT, data_vencimento TEXT,
                                    obs TEXT, FOREIGN KEY (documento) REFERENCES hospedes (documento))''')
            self.cursor.execute('CREATE TABLE IF NOT EXISTS configs (chave TEXT PRIMARY KEY, valor INTEGER)')
            self.cursor.execute('CREATE TABLE IF NOT EXISTS anotacoes (documento TEXT PRIMARY KEY, texto TEXT)')
            self.cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY, password TEXT, is_admin INTEGER, can_change_dates INTEGER, can_manage_products INTEGER, salt TEXT)')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS logs_auditoria (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                    data_hora TEXT, 
                                    usuario TEXT, 
                                    acao TEXT, 
                                    detalhes TEXT, 
                                    maquina TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS compras (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    data_compra TEXT,
                                    produto TEXT,
                                    quantidade REAL,
                                    valor_unitario REAL,
                                    valor_total REAL,
                                    usuario TEXT,
                                    obs TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS listas_compras (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    data_criacao TEXT,
                                    status TEXT DEFAULT 'ABERTA',
                                    usuario TEXT,
                                    obs TEXT)''')
            self.cursor.execute('CREATE TABLE IF NOT EXISTS produtos (nome TEXT PRIMARY KEY)')
            self.cursor.execute("INSERT OR IGNORE INTO configs VALUES (?, ?)", ('validade_meses', 6))
            self.cursor.execute("INSERT OR IGNORE INTO configs VALUES (?, ?)", ('alerta_dias', 30))
            self.cursor.execute("INSERT OR IGNORE INTO configs VALUES (?, ?)", ('tema', 0)) # 0=Light, 1=Dark
            # Indices para performance
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_hospedes_nome ON hospedes(nome)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_historico_doc ON historico_zebra(documento)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_compras_prod ON compras(produto)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos(nome)")
            
            # MIGRATION: Adiciona coluna usuario se não existir (para bases antigas)
            try:
                self.cursor.execute("ALTER TABLE historico_zebra ADD COLUMN usuario TEXT")
            except sqlite3.OperationalError: pass

            # MIGRATION: Adiciona coluna quarto se não existir
            try:
                self.cursor.execute("ALTER TABLE usuarios ADD COLUMN salt TEXT")
            except sqlite3.OperationalError: pass

            # MIGRATION: Adiciona permissão de produtos
            try:
                self.cursor.execute("ALTER TABLE usuarios ADD COLUMN can_manage_products INTEGER DEFAULT 0")
            except sqlite3.OperationalError: pass

            # MIGRATION: Adiciona coluna quarto se não existir
            try:
                self.cursor.execute("ALTER TABLE hospedes ADD COLUMN telefone TEXT")
            except sqlite3.OperationalError: pass
            try:
                self.cursor.execute("ALTER TABLE hospedes ADD COLUMN email TEXT")
            except sqlite3.OperationalError: pass

            # MIGRATION: Adiciona coluna quarto se não existir
            try:
                self.cursor.execute("ALTER TABLE historico_zebra ADD COLUMN quarto TEXT")
            except sqlite3.OperationalError: pass
            
            # MIGRATION: Adiciona coluna lista_id em compras
            try:
                self.cursor.execute("ALTER TABLE compras ADD COLUMN lista_id INTEGER")
            except sqlite3.OperationalError: pass

            # MIGRATION: Agrupa compras antigas (sem lista) em uma lista legado
            self.cursor.execute("SELECT 1 FROM compras WHERE lista_id IS NULL LIMIT 1")
            if self.cursor.fetchone():
                data_hj = datetime.now().strftime("%Y-%m-%d")
                self.cursor.execute("INSERT INTO listas_compras (data_criacao, status, usuario, obs) VALUES (?, ?, ?, ?)", 
                                   (data_hj, 'FECHADA', 'Sistema', 'Legado / Importado de Versão Anterior'))
                lid = self.cursor.lastrowid
                self.cursor.execute("UPDATE compras SET lista_id = ? WHERE lista_id IS NULL", (lid,))

            # Popula categorias padrão se a tabela estiver vazia
            self.cursor.execute("SELECT 1 FROM categorias")
            if not self.cursor.fetchone():
                self.cursor.executemany("INSERT INTO categorias VALUES (?)", [("Remarcacao",), ("Cancelamento",), ("Cortesia",), ("Uso",)])

            # Cria usuário padrão se não existir
            self.cursor.execute("SELECT 1 FROM usuarios WHERE username = 'gabriel'")
            if not self.cursor.fetchone():
                salt = secrets.token_hex(16)
                pass_hash = self._hash_password('132032', salt)
                self.cursor.execute("INSERT INTO usuarios (username, password, is_admin, can_change_dates, can_manage_products, salt) VALUES (?, ?, ?, ?, ?, ?)", ('gabriel', pass_hash, 1, 1, 1, salt))

    def fazer_backup(self):
        if not os.path.exists("backups"):
            os.makedirs("backups")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = f"backups/backup_{timestamp}.db"
        shutil.copy2(self.db_name, dst)
        
        # Otimização: Rotação de Backups (Mantém apenas os 20 mais recentes)
        try:
            files = sorted([os.path.join("backups", f) for f in os.listdir("backups") if f.endswith(".db")], key=os.path.getmtime)
            while len(files) > 20:
                os.remove(files.pop(0))
        except Exception: pass
        
        return dst

    def restaurar_backup(self, arquivo_backup, usuario_acao="Sistema"):
        if not os.path.exists(arquivo_backup): raise Exception("Arquivo não encontrado")
        self.conn.close() # Fecha conexão atual para permitir sobrescrita
        shutil.copy2(arquivo_backup, self.db_name)
        self.conn = sqlite3.connect(self.db_name) # Reconecta
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.criar_tabelas() # Garante que tabelas novas existam
        self.registrar_log(usuario_acao, "RESTAURAR_BACKUP", f"Restaurado de: {arquivo_backup}")

    # =========================================================================
    # 2. AUTENTICAÇÃO & USUÁRIOS
    # =========================================================================
    def _hash_password(self, password, salt=""):
        return hashlib.sha256((str(password) + str(salt)).encode()).hexdigest()

    def verificar_login(self, username, password):
        self.cursor.execute("SELECT password, salt FROM usuarios WHERE username = ?", (username,))
        user_data = self.cursor.fetchone()
        if not user_data:
            return None

        # Handle legacy users without salt
        if user_data['salt'] is None:
            legacy_hash = hashlib.sha256(str(password).encode()).hexdigest()
            if legacy_hash == user_data['password']:
                # This is a successful login with an old password.
                # We should update the password to use a salt.
                new_salt = secrets.token_hex(16)
                new_hash = self._hash_password(password, new_salt)
                with self.conn:
                    self.cursor.execute("UPDATE usuarios SET password = ?, salt = ? WHERE username = ?", (new_hash, new_salt, username))
                self.cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
                return self.cursor.fetchone()
            else:
                return None

        # Standard login with salt
        pass_hash = self._hash_password(password, user_data['salt'])
        if pass_hash == user_data['password']:
            self.cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
            return self.cursor.fetchone()
        
        return None

    def get_usuarios(self):
        self.cursor.execute("SELECT * FROM usuarios")
        return self.cursor.fetchall()

    def salvar_usuario(self, username, password, is_admin, can_change_dates, can_manage_products, usuario_acao="Sistema"):
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        with self.conn:
            self.cursor.execute("INSERT OR REPLACE INTO usuarios (username, password, is_admin, can_change_dates, can_manage_products, salt) VALUES (?, ?, ?, ?, ?, ?)", (username, password_hash, int(is_admin), int(can_change_dates), int(can_manage_products), salt))
        self.registrar_log(usuario_acao, "SALVAR_USUARIO", f"Usuario alvo: {username} | Admin: {is_admin}")

    def excluir_usuario(self, username, usuario_acao="Sistema"):
        with self.conn:
            self.cursor.execute("DELETE FROM usuarios WHERE username = ?", (username,))
        self.registrar_log(usuario_acao, "EXCLUIR_USUARIO", f"Usuario alvo: {username}")

    # =========================================================================
    # 3. MÓDULO HÓSPEDES
    # =========================================================================
    def get_hospede(self, doc):
        self.cursor.execute("SELECT * FROM hospedes WHERE documento = ?", (doc,))
        return self.cursor.fetchone()

    def cadastrar_hospede(self, nome, doc, telefone="", email="", usuario_acao="Sistema"):
        doc_limpo = str(doc).strip()
        if not self._validar_cpf_cnpj(doc_limpo):
            raise Exception("Documento inválido (CPF/CNPJ incorreto). Verifique os dígitos.")
        
        with self.conn:
            self.cursor.execute("SELECT 1 FROM hospedes WHERE documento = ?", (doc_limpo,))
            if self.cursor.fetchone():
                self.cursor.execute("UPDATE hospedes SET nome = ?, telefone = ?, email = ? WHERE documento = ?", 
                                   (nome.upper().strip(), telefone, email, doc_limpo))
                self.registrar_log(usuario_acao, "ATUALIZAR_HOSPEDE", f"Doc: {doc_limpo}")
            else:
                self.cursor.execute("INSERT INTO hospedes (nome, documento, telefone, email) VALUES (?, ?, ?, ?)", 
                                   (nome.upper().strip(), doc_limpo, telefone, email))
                self.registrar_log(usuario_acao, "CADASTRAR_HOSPEDE", f"Doc: {doc_limpo}")

    def buscar_filtrado(self, termo="", filtro="todos"):
        # Remove caracteres especiais da busca para evitar erros de SQL ou formatação
        termo_limpo = str(termo).strip()
        self.cursor.execute("SELECT nome, documento FROM hospedes WHERE nome LIKE ? OR documento LIKE ?", (f'%{termo_limpo}%', f'%{termo_limpo}%'))
        hospedes = self.cursor.fetchall()
        res = []
        for h in hospedes:
            s, v, b = self._processar_saldo(h['documento'])
            if filtro == "vencidos" and not b: continue
            if s <= 0 and filtro != "todos": continue
            res.append((h['nome'], h['documento'], s))
        return res

    def limpar_valor(self, valor):
        if isinstance(valor, (int, float)):
            return float(valor)
        if not valor or str(valor).strip() == "": return 0.0
        return float(str(valor).replace('.', '').replace(',', '.').strip())

    def _processar_saldo(self, doc):
        self.cursor.execute("SELECT tipo, valor, data_vencimento FROM historico_zebra WHERE documento = ? ORDER BY id ASC", (doc,))
        movs = self.cursor.fetchall()
        entradas = [{"valor": m['valor'], "venc": m['data_vencimento']} for m in movs if m['tipo'] == 'ENTRADA']
        saidas_total = sum(m['valor'] for m in movs if m['tipo'] == 'SAIDA')
        hoje = datetime.now().strftime("%Y-%m-%d")
        saldo, prox_venc, bloqueado = 0.0, "N/A", False
        for e in entradas:
            if saidas_total >= e['valor']:
                saidas_total -= e['valor']
                e['valor'] = 0
            else:
                e['valor'] -= saidas_total
                saidas_total = 0
            if e['valor'] > 0:
                saldo += e['valor']
                if prox_venc == "N/A":
                    prox_venc = e['venc']
                    if prox_venc < hoje: bloqueado = True
        if prox_venc != "N/A":
            prox_venc = datetime.strptime(prox_venc, "%Y-%m-%d").strftime("%d/%m/%Y")
        return round(max(0, saldo), 2), prox_venc, bloqueado

    def get_saldo_info(self, doc):
        return self._processar_saldo(doc)

    def _validar_cpf_cnpj(self, doc):
        """Valida CPF (11) ou CNPJ (14). Outros tamanhos são aceitos como RG/Passaporte se > 3 chars."""
        numeros = ''.join(filter(str.isdigit, str(doc)))
        
        if len(numeros) not in (11, 14):
            return len(str(doc).strip()) >= 3
            
        # Validação de CPF
        if len(numeros) == 11:
            if numeros == numeros[0] * 11: return False
            for i in range(9, 11):
                val = sum((int(numeros[num]) * ((i + 1) - num) for num in range(0, i)))
                digit = ((val * 10) % 11) % 10
                if digit != int(numeros[i]): return False
            return True
            
        # Validação de CNPJ
        if len(numeros) == 14:
            if numeros == numeros[0] * 14: return False
            val = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            for i in range(12, 14):
                soma = sum(int(numeros[num]) * val[num + (1 if i == 12 else 0)] for num in range(0, i))
                digit = ((soma % 11) < 2) and 0 or (11 - (soma % 11))
                if digit != int(numeros[i]): return False
            return True
        return True
    
    # =========================================================================
    # 4. MÓDULO FINANCEIRO (Movimentações, Saldo, Multas)
    # =========================================================================
    def adicionar_movimentacao(self, doc, valor, categoria, tipo, obs="", usuario="Sistema"):
        v_float = self.limpar_valor(valor)
        doc_limpo = str(doc).strip()

        self.cursor.execute("SELECT 1 FROM hospedes WHERE documento = ?", (doc_limpo,))
        if not self.cursor.fetchone():
            raise Exception(f"Hóspede com documento {doc_limpo} não encontrado. Cadastre o hóspede primeiro.")

        if tipo == "SAIDA":
            s, v, b = self._processar_saldo(doc_limpo)
            if b: raise Exception(f"BLOQUEIO: Crédito vencido em {v}!")
            if v_float > s: raise Exception("Saldo insuficiente!")
        
        with self.conn:
            venc = ""
            data_hj = datetime.now()
            if tipo == "ENTRADA":
                venc = (data_hj + timedelta(days=self.get_config('validade_meses')*30)).strftime("%Y-%m-%d")
            self.cursor.execute("INSERT INTO historico_zebra (documento, tipo, valor, categoria, data_acao, data_vencimento, obs, usuario) VALUES (?,?,?,?,?,?,?,?)",
                               (doc_limpo, tipo, v_float, categoria, data_hj.strftime("%Y-%m-%d"), venc, obs, usuario))
        self.registrar_log(usuario, f"ADD_MOV_{tipo}", f"Doc: {doc_limpo}, Valor: {v_float}")

    def adicionar_multa(self, doc, valor, motivo, obs="", usuario="Sistema"):
        v_float = self.limpar_valor(valor)
        doc_limpo = str(doc).strip()
        with self.conn:
            data_hj = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("INSERT INTO historico_zebra (documento, tipo, valor, categoria, data_acao, obs, usuario) VALUES (?,?,?,?,?,?,?)",
                               (doc_limpo, 'MULTA', v_float, motivo, data_hj, obs, usuario))
        self.registrar_log(usuario, "ADD_MULTA", f"Doc: {doc_limpo}, Valor: {v_float}, Motivo: {motivo}")

    def pagar_multa(self, doc, valor, forma_pagamento, obs="", usuario="Sistema"):
        v_float = self.limpar_valor(valor)
        doc_limpo = str(doc).strip()
        
        divida = self.get_divida_multas(doc_limpo)
        if v_float <= 0: raise Exception("Valor deve ser maior que zero.")
        if v_float > divida: raise Exception(f"Valor (R$ {v_float:.2f}) excede a dívida atual (R$ {divida:.2f})")

        with self.conn:
            data_hj = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("INSERT INTO historico_zebra (documento, tipo, valor, categoria, data_acao, obs, usuario) VALUES (?,?,?,?,?,?,?)",
                               (doc_limpo, 'PAGAMENTO_MULTA', v_float, forma_pagamento, data_hj, obs, usuario))
        self.registrar_log(usuario, "PAGAR_MULTA", f"Doc: {doc_limpo}, Valor: {v_float}")

    def get_saldo_info(self, doc):
        return self._processar_saldo(doc)

    def get_divida_multas(self, doc):
        self.cursor.execute("SELECT SUM(valor) FROM historico_zebra WHERE documento = ? AND tipo = 'MULTA'", (doc,))
        res_m = self.cursor.fetchone()
        total_m = res_m[0] if res_m and res_m[0] is not None else 0.0
        
        self.cursor.execute("SELECT SUM(valor) FROM historico_zebra WHERE documento = ? AND tipo = 'PAGAMENTO_MULTA'", (doc,))
        res_p = self.cursor.fetchone()
        total_p = res_p[0] if res_p and res_p[0] is not None else 0.0
        
        return total_m - total_p

    def get_devedores_multas(self):
        """Retorna lista de clientes que possuem dívida de multas > 0"""
        self.cursor.execute("SELECT nome, documento, telefone FROM hospedes")
        todos = self.cursor.fetchall()
        devedores = []
        for h in todos:
            divida = self.get_divida_multas(h['documento'])
            if divida > 0:
                devedores.append((h['nome'], h['documento'], h['telefone'], divida))
        return sorted(devedores, key=lambda x: x[3], reverse=True) # Ordena por maior dívida

    def get_historico_detalhado(self, doc):
        self.cursor.execute("SELECT tipo, valor, data_acao, categoria, obs, usuario FROM historico_zebra WHERE documento = ? ORDER BY id DESC", (doc,))
        return [dict(r) for r in self.cursor.fetchall()]

    def get_historico_global(self, filtro="", limite=100):
        # Retorna histórico de todos os clientes com ID para permitir exclusão
        if filtro:
            termo = f"%{filtro}%"
            query = '''
                SELECT h.id, h.data_acao, c.nome, h.documento, h.tipo, h.valor, h.categoria, h.usuario, h.obs 
                FROM historico_zebra h
                JOIN hospedes c ON h.documento = c.documento
                WHERE c.nome LIKE ? OR c.documento LIKE ?
                ORDER BY h.id DESC LIMIT ?
            '''
            self.cursor.execute(query, (termo, termo, limite))
        else:
            query = '''
                SELECT h.id, h.data_acao, c.nome, h.documento, h.tipo, h.valor, h.categoria, h.usuario, h.obs 
                FROM historico_zebra h
                JOIN hospedes c ON h.documento = c.documento
                ORDER BY h.id DESC LIMIT ?
            '''
            self.cursor.execute(query, (limite,))
        return [dict(r) for r in self.cursor.fetchall()]

    def excluir_movimentacao(self, id_mov, usuario_acao="Sistema"):
        with self.conn:
            self.cursor.execute("SELECT * FROM historico_zebra WHERE id = ?", (id_mov,))
            mov = self.cursor.fetchone()
            if not mov: raise Exception("Movimentação não encontrada.")
            self.cursor.execute("DELETE FROM historico_zebra WHERE id = ?", (id_mov,))
        self.registrar_log(usuario_acao, "EXCLUIR_MOVIMENTACAO", f"ID: {id_mov} | Doc: {mov['documento']} | Valor: {mov['valor']} | Tipo: {mov['tipo']}")

    def atualizar_data_vencimento_manual(self, doc, data_br, valor, data_mov, usuario_acao="Sistema"):
        d_iso = datetime.strptime(data_br, "%d/%m/%Y").strftime("%Y-%m-%d")
        dm_iso = datetime.strptime(data_mov, "%d/%m/%Y").strftime("%Y-%m-%d")
        with self.conn:
            self.cursor.execute("UPDATE historico_zebra SET data_vencimento = ? WHERE documento = ? AND valor = ? AND data_acao = ? AND tipo = 'ENTRADA'", 
                               (d_iso, doc, valor, dm_iso))
        self.registrar_log(usuario_acao, "ALTERAR_VENCIMENTO", f"Doc: {doc} | Valor: {valor} | Nova Data: {data_br}")

    # =========================================================================
    # 5. RELATÓRIOS & DASHBOARD
    # =========================================================================
    def gerar_pdf_voucher(self, nome_hospede, doc_hospede):
        if not FPDF: raise Exception("Biblioteca FPDF não encontrada.")
        saldo, venc, bloqueado = self._processar_saldo(doc_hospede)
        if saldo <= 0: raise Exception("Sem saldo para voucher.")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, self.empresa["nome"], ln=True, align='C')
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 5, self.empresa["razao"].encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
        pdf.cell(0, 5, f"CNPJ: {self.empresa['cnpj']} | {self.empresa['contato']}", ln=True, align='C')
        pdf.ln(10); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(10)
        pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, "VOUCHER DE CREDITO", ln=True, align='C'); pdf.ln(5)
        pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, f"HOSPEDE: {nome_hospede.upper()}", ln=True); pdf.cell(0, 8, f"DOCUMENTO: {doc_hospede}", ln=True); pdf.ln(5)
        pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 15, f" VALOR: R$ {saldo:.2f}", border=1, ln=True, fill=True)
        pdf.set_font("Arial", 'I', 11); pdf.cell(0, 10, f" VALIDADE: {venc}", border=1, ln=True); pdf.ln(10)
        pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 6, "Este documento comprova a existencia de credito para futuras hospedagens. Apresente no check-in.")
        pdf.ln(20); pdf.cell(0, 10, "________________________________________", ln=True, align='C')
        pdf.cell(0, 5, "Hotel Santos - Assinatura", ln=True, align='C')
        fname = f"Voucher_{doc_hospede}.pdf"
        try:
            pdf.output(fname)
        except PermissionError:
            raise Exception(f"O arquivo '{fname}' parece estar aberto. Feche-o e tente novamente.")
        return fname

    def gerar_pdf_extrato(self, nome_hospede, doc_hospede):
        if not FPDF: raise Exception("Biblioteca FPDF não encontrada.")
        hist = self.get_historico_detalhado(doc_hospede)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, self.empresa["nome"], ln=True, align='C')
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 5, self.empresa["razao"].encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
        pdf.cell(0, 5, f"CNPJ: {self.empresa['cnpj']} | {self.empresa['contato']}", ln=True, align='C')
        pdf.cell(0, 5, self.empresa["endereco"].encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
        pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 5, "EXTRATO DETALHADO DE MOVIMENTACOES", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, f"CLIENTE: {nome_hospede.upper()}", ln=True)
        pdf.cell(0, 8, f"DOCUMENTO: {doc_hospede}", ln=True)
        pdf.ln(5)
        
        # Header da Tabela
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(25, 8, "DATA", 1, 0, 'C', 1)
        pdf.cell(25, 8, "TIPO", 1, 0, 'C', 1)
        pdf.cell(40, 8, "CATEGORIA", 1, 0, 'C', 1)
        pdf.cell(30, 8, "VALOR", 1, 0, 'C', 1)
        pdf.cell(0, 8, "OBSERVACAO", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 9)
        for h in hist:
            data_br = datetime.strptime(h['data_acao'], "%Y-%m-%d").strftime("%d/%m/%Y")
            pdf.cell(25, 8, data_br, 1, 0, 'C')
            pdf.cell(25, 8, h['tipo'], 1, 0, 'C')
            pdf.cell(40, 8, h['categoria'][:18], 1, 0, 'C')
            pdf.cell(30, 8, f"R$ {h['valor']:.2f}", 1, 0, 'C')
            pdf.cell(0, 8, h['obs'][:40], 1, 1, 'L')
            
        pdf.ln(10)
        saldo, _, _ = self._processar_saldo(doc_hospede)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"SALDO FINAL DISPONIVEL: R$ {saldo:.2f}", ln=True, align='R')
        
        fname = f"Extrato_{doc_hospede}.pdf"
        try: pdf.output(fname)
        except PermissionError: raise Exception(f"Feche o arquivo '{fname}' antes de gerar um novo.")
        return fname

    def gerar_pdf_multas(self, nome_hospede, doc_hospede):
        if not FPDF: raise Exception("Biblioteca FPDF não encontrada.")
        
        # Busca apenas multas e pagamentos de multas
        self.cursor.execute("SELECT tipo, valor, data_acao, categoria, obs, usuario FROM historico_zebra WHERE documento = ? AND tipo IN ('MULTA', 'PAGAMENTO_MULTA') ORDER BY id DESC", (doc_hospede,))
        hist = [dict(r) for r in self.cursor.fetchall()]
        
        if not hist: raise Exception("Não há registros de multas para este cliente.")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, self.empresa["nome"], ln=True, align='C')
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 5, self.empresa["razao"].encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
        pdf.cell(0, 5, f"CNPJ: {self.empresa['cnpj']} | {self.empresa['contato']}", ln=True, align='C')
        pdf.cell(0, 5, self.empresa["endereco"].encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
        pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 5, "EXTRATO DE MULTAS E PAGAMENTOS", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, f"CLIENTE: {nome_hospede.upper()}", ln=True)
        pdf.cell(0, 8, f"DOCUMENTO: {doc_hospede}", ln=True)
        pdf.ln(5)
        
        # Header da Tabela
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(25, 8, "DATA", 1, 0, 'C', 1)
        pdf.cell(35, 8, "TIPO", 1, 0, 'C', 1)
        pdf.cell(40, 8, "MOTIVO/PGTO", 1, 0, 'C', 1)
        pdf.cell(30, 8, "VALOR", 1, 0, 'C', 1)
        pdf.cell(0, 8, "OBSERVACAO", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 9)
        for h in hist:
            data_br = datetime.strptime(h['data_acao'], "%Y-%m-%d").strftime("%d/%m/%Y")
            tipo_fmt = "MULTA" if h['tipo'] == 'MULTA' else "PAGAMENTO"
            pdf.cell(25, 8, data_br, 1, 0, 'C')
            pdf.cell(35, 8, tipo_fmt, 1, 0, 'C')
            pdf.cell(40, 8, h['categoria'][:18], 1, 0, 'C')
            pdf.cell(30, 8, f"R$ {h['valor']:.2f}", 1, 0, 'C')
            pdf.cell(0, 8, h['obs'][:40], 1, 1, 'L')
            
        pdf.ln(10)
        divida = self.get_divida_multas(doc_hospede)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"TOTAL PENDENTE (MULTAS): R$ {divida:.2f}", ln=True, align='R')
        
        fname = f"Ticket_Multas_{doc_hospede}.pdf"
        try: pdf.output(fname)
        except PermissionError: raise Exception(f"Feche o arquivo '{fname}' antes de gerar um novo.")
        return fname

    # =========================================================================
    # MÓDULO COMPRAS
    # =========================================================================
    def adicionar_compra(self, data_compra, produto, qtd, valor_unit, obs="", usuario="Sistema", lista_id=None):
        qtd_float = self.limpar_valor(qtd)
        unit_float = self.limpar_valor(valor_unit)
        total = qtd_float * unit_float
        
        # Converte data dd/mm/yyyy para yyyy-mm-dd
        try:
            data_iso = datetime.strptime(data_compra, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            data_iso = datetime.now().strftime("%Y-%m-%d")

        with self.conn:
            self.cursor.execute("INSERT INTO compras (data_compra, produto, quantidade, valor_unitario, valor_total, usuario, obs, lista_id) VALUES (?,?,?,?,?,?,?,?)",
                               (data_iso, produto.upper().strip(), qtd_float, unit_float, total, usuario, obs, lista_id))
        self.registrar_log(usuario, "ADD_COMPRA", f"Prod: {produto} | Total: {total}")

    def criar_lista_compras(self, usuario, obs=""):
        data_hj = datetime.now().strftime("%Y-%m-%d")
        with self.conn:
            self.cursor.execute("INSERT INTO listas_compras (data_criacao, status, usuario, obs) VALUES (?, ?, ?, ?)", 
                               (data_hj, 'ABERTA', usuario, obs))
            return self.cursor.lastrowid

    def fechar_lista_compras(self, lista_id):
        with self.conn:
            self.cursor.execute("UPDATE listas_compras SET status = 'FECHADA' WHERE id = ?", (lista_id,))

    def get_listas_resumo(self):
        """Retorna listas com totais calculados"""
        query = '''
            SELECT l.id, l.data_criacao, l.status, l.usuario, COUNT(c.id) as qtd_itens, SUM(c.valor_total) as total_valor
            FROM listas_compras l
            LEFT JOIN compras c ON l.id = c.lista_id
            GROUP BY l.id
            ORDER BY l.id DESC
        '''
        self.cursor.execute(query)
        return [dict(r) for r in self.cursor.fetchall()]

    def get_itens_lista(self, lista_id):
        self.cursor.execute("SELECT * FROM compras WHERE lista_id = ? ORDER BY id DESC", (lista_id,))
        itens = [dict(r) for r in self.cursor.fetchall()]
        # Calcula tendência
        for c in itens:
            self.cursor.execute("SELECT valor_unitario FROM compras WHERE produto = ? AND data_compra < ? ORDER BY data_compra DESC LIMIT 1", (c['produto'], c['data_compra']))
            res = self.cursor.fetchone()
            c['tendencia'] = "igual"
            if res:
                antigo = res['valor_unitario']
                if c['valor_unitario'] > antigo: c['tendencia'] = "subiu"
                elif c['valor_unitario'] < antigo: c['tendencia'] = "desceu"
        return itens

    def get_historico_compras(self, filtro=""):
        query = "SELECT * FROM compras"
        params = []
        if filtro:
            query += " WHERE produto LIKE ?"
            params.append(f"%{filtro}%")
        query += " ORDER BY data_compra DESC, id DESC"
        
        self.cursor.execute(query, params)
        compras = [dict(r) for r in self.cursor.fetchall()]
        
        # Lógica de Tendência (Comparar com a compra anterior do mesmo produto)
        for c in compras:
            # Busca a última compra deste produto ANTES desta data
            self.cursor.execute("SELECT valor_unitario FROM compras WHERE produto = ? AND data_compra < ? ORDER BY data_compra DESC LIMIT 1", (c['produto'], c['data_compra']))
            res = self.cursor.fetchone()
            c['tendencia'] = "igual"
            if res:
                antigo = res['valor_unitario']
                if c['valor_unitario'] > antigo: c['tendencia'] = "subiu"
                elif c['valor_unitario'] < antigo: c['tendencia'] = "desceu"
        return compras

    def adicionar_produto_predefinido(self, nome):
        if not nome: return
        with self.conn:
            self.cursor.execute("INSERT OR IGNORE INTO produtos (nome) VALUES (?)", (nome.upper().strip(),))

    def remover_produto_predefinido(self, nome):
        with self.conn:
            self.cursor.execute("DELETE FROM produtos WHERE nome = ?", (nome,))

    def get_produtos_predefinidos(self):
        self.cursor.execute("SELECT nome FROM produtos ORDER BY nome")
        return [r['nome'] for r in self.cursor.fetchall()]

    def gerar_pdf_lista(self, lista_id):
        if not FPDF: raise Exception("Biblioteca FPDF não encontrada.")
        
        self.cursor.execute("SELECT * FROM listas_compras WHERE id = ?", (lista_id,))
        lista = self.cursor.fetchone()
        if not lista: raise Exception("Lista não encontrada.")
        
        itens = self.get_itens_lista(lista_id)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, self.empresa["nome"], ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, f"ORDEM DE COMPRA #{lista['id']}", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 10)
        data_lista = datetime.strptime(lista['data_criacao'], "%Y-%m-%d").strftime("%d/%m/%Y")
        pdf.cell(0, 5, f"DATA: {data_lista} | STATUS: {lista['status']} | RESP: {lista['usuario']}", ln=True)
        pdf.ln(5)
        
        # Header Tabela
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(80, 8, "PRODUTO", 1, 0, 'C', 1)
        pdf.cell(20, 8, "QTD", 1, 0, 'C', 1)
        pdf.cell(30, 8, "UNIT (R$)", 1, 0, 'C', 1)
        pdf.cell(30, 8, "TOTAL (R$)", 1, 0, 'C', 1)
        pdf.cell(0, 8, "OBS", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 9)
        total_geral = 0
        for i in itens:
            pdf.cell(80, 8, i['produto'][:35], 1, 0, 'L')
            pdf.cell(20, 8, str(i['quantidade']), 1, 0, 'C')
            pdf.cell(30, 8, f"{i['valor_unitario']:.2f}", 1, 0, 'R')
            pdf.cell(30, 8, f"{i['valor_total']:.2f}", 1, 0, 'R')
            pdf.cell(0, 8, "", 1, 1, 'C') # Obs vazio para check manual
            total_geral += i['valor_total']
            
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"TOTAL DA LISTA: R$ {total_geral:.2f}", ln=True, align='R')
        
        fname = f"Ordem_Compra_{lista_id}.pdf"
        try: pdf.output(fname)
        except PermissionError: raise Exception(f"Feche o arquivo '{fname}' antes de gerar um novo.")
        return fname

    def gerar_pdf_compras(self):
        if not FPDF: raise Exception("Biblioteca FPDF não encontrada.")
        
        compras = self.get_historico_compras() # Pega todas as compras
        if not compras: raise Exception("Não há compras registradas para gerar o relatório.")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, self.empresa["nome"], ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, "RELATÓRIO DE COMPRAS", ln=True, align='C')
        pdf.ln(10)
        
        # Header da Tabela
        pdf.set_fill_color(220, 220, 220)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(25, 8, "DATA", 1, 0, 'C', 1)
        pdf.cell(60, 8, "PRODUTO", 1, 0, 'C', 1)
        pdf.cell(15, 8, "QTD", 1, 0, 'C', 1)
        pdf.cell(30, 8, "UNITARIO", 1, 0, 'C', 1)
        pdf.cell(30, 8, "TOTAL", 1, 0, 'C', 1)
        pdf.cell(0, 8, "VARIACAO", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 9)
        total_geral = 0
        for c in compras:
            data_br = datetime.strptime(c['data_compra'], "%Y-%m-%d").strftime("%d/%m/%Y")
            seta = "-"
            if c['tendencia'] == 'subiu': seta = "Subiu"
            elif c['tendencia'] == 'desceu': seta = "Caiu"

            pdf.cell(25, 8, data_br, 1, 0, 'C')
            pdf.cell(60, 8, c['produto'].encode('latin-1', 'replace').decode('latin-1')[:30], 1, 0, 'L')
            pdf.cell(15, 8, str(c['quantidade']), 1, 0, 'C')
            pdf.cell(30, 8, f"R$ {c['valor_unitario']:.2f}", 1, 0, 'R')
            pdf.cell(30, 8, f"R$ {c['valor_total']:.2f}", 1, 0, 'R')
            pdf.cell(0, 8, seta, 1, 1, 'C')
            total_geral += c['valor_total']
            
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"TOTAL GERAL DAS COMPRAS: R$ {total_geral:.2f}", ln=True, align='R')
        
        fname = f"Relatorio_Compras_{datetime.now().strftime('%Y%m%d')}.pdf"
        try: pdf.output(fname)
        except PermissionError: raise Exception(f"Feche o arquivo '{fname}' antes de gerar um novo.")
        return fname

    def get_dados_dash(self):
        self.cursor.execute("SELECT documento FROM hospedes")
        docs = [d['documento'] for d in self.cursor.fetchall()]
        ts, tv, tav = 0, 0, 0
        hoje = datetime.now().strftime("%Y-%m-%d")
        alerta = (datetime.now() + timedelta(days=self.get_config('alerta_dias'))).strftime("%Y-%m-%d")
        for d in docs:
            s, v, b = self._processar_saldo(d)
            if s > 0:
                ts += s
                if v != "N/A":
                    v_iso = datetime.strptime(v, "%d/%m/%Y").strftime("%Y-%m-%d")
                    if b: tv += s
                    elif hoje <= v_iso <= alerta: tav += s
        return ts, tv, tav, len(docs)

    def get_dados_grafico_categorias(self):
        self.cursor.execute("SELECT categoria, SUM(valor) as total FROM historico_zebra WHERE tipo='ENTRADA' GROUP BY categoria")
        return [(r['categoria'], r['total']) for r in self.cursor.fetchall()]

    def get_dados_grafico_mensal(self):
        # Gera lista das chaves YYYY-MM dos últimos 6 meses
        meses_alvo = []
        year, month = datetime.now().year, datetime.now().month
        for _ in range(6):
            meses_alvo.insert(0, f"{year}-{month:02d}")
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        
        start_date = meses_alvo[0] + "-01"
        query = "SELECT strftime('%Y-%m', data_acao) as mes, tipo, SUM(valor) as total FROM historico_zebra WHERE data_acao >= ? GROUP BY mes, tipo"
        self.cursor.execute(query, (start_date,))
        
        dados = {m: {'ENTRADA': 0.0, 'SAIDA': 0.0} for m in meses_alvo}
        for r in self.cursor.fetchall():
            if r['mes'] in dados: dados[r['mes']][r['tipo']] = r['total']
            
        entradas = [dados[m]['ENTRADA'] for m in meses_alvo]
        saidas = [dados[m]['SAIDA'] for m in meses_alvo]
        meses_fmt = [datetime.strptime(m, "%Y-%m").strftime("%m/%Y") for m in meses_alvo]
        return meses_fmt, entradas, saidas

    def get_hospedes_vencendo_em_breve(self):
        hoje = datetime.now().strftime("%Y-%m-%d")
        alerta = (datetime.now() + timedelta(days=self.get_config('alerta_dias'))).strftime("%Y-%m-%d")
        self.cursor.execute("SELECT nome, documento FROM hospedes")
        docs = self.cursor.fetchall()
        res = []
        for h in docs:
            s, v, b = self._processar_saldo(h['documento'])
            if v != "N/A":
                v_iso = datetime.strptime(v, "%d/%m/%Y").strftime("%Y-%m-%d")
                if not b and hoje <= v_iso <= alerta:
                    res.append((h['nome'], v, f"{s:.2f}"))
        return sorted(res, key=lambda x: x[1])

    def exportar_csv(self):
        data = self.buscar_filtrado()
        fname = f"Relatorio_Clientes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        with open(fname, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Nome', 'Documento', 'Saldo'])
            for row in data:
                # Formata numero com virgula para Excel brasileiro reconhecer
                writer.writerow([row[0], row[1], f"{row[2]:.2f}".replace('.', ',')])
        return fname

    # =========================================================================
    # 6. CONFIGURAÇÕES & UTILS
    # =========================================================================
    def get_config(self, chave):
        self.cursor.execute("SELECT valor FROM configs WHERE chave = ?", (chave,))
        res = self.cursor.fetchone()
        return res['valor'] if res else 30

    def set_config(self, chave, valor, usuario_acao="Sistema"):
        antigo = self.get_config(chave)
        with self.conn:
            self.cursor.execute("INSERT OR REPLACE INTO configs (chave, valor) VALUES (?, ?)", (chave, valor))
        self.registrar_log(usuario_acao, "ALTERAR_CONFIG", f"Chave: {chave} | De: {antigo} Para: {valor}")

    def get_categorias(self):
        self.cursor.execute("SELECT nome FROM categorias ORDER BY nome")
        return [r['nome'] for r in self.cursor.fetchall()]

    def adicionar_categoria(self, nome):
        if not nome: return
        with self.conn:
            self.cursor.execute("INSERT OR IGNORE INTO categorias VALUES (?)", (nome,))

    def remover_categoria(self, nome):
        with self.conn:
            self.cursor.execute("DELETE FROM categorias WHERE nome = ?", (nome,))

    def get_anotacao(self, doc):
        self.cursor.execute("SELECT texto FROM anotacoes WHERE documento = ?", (doc,))
        res = self.cursor.fetchone()
        return res['texto'] if res else ""

    def salvar_anotacao(self, doc, texto):
        with self.conn:
            self.cursor.execute("INSERT OR REPLACE INTO anotacoes (documento, texto) VALUES (?, ?)", (doc, texto))

    def registrar_log(self, usuario, acao, detalhes=""):
        try: maquina = socket.gethostname()
        except: maquina = "Desconhecido"
        dh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.cursor.execute("INSERT INTO logs_auditoria (data_hora, usuario, acao, detalhes, maquina) VALUES (?,?,?,?,?)", 
                               (dh, usuario, acao, detalhes, maquina))

    def get_logs(self):
        self.cursor.execute("SELECT * FROM logs_auditoria ORDER BY id DESC LIMIT 100")
        return self.cursor.fetchall()

    # =========================================================================
    # 7. AUTO-UPDATE (GITHUB)
    # =========================================================================
    def verificar_atualizacao(self, repo_usuario="gabriel-ram0s", repo_nome="sistemahotelsantos"):
        """
        Verifica se há uma nova release no GitHub.
        Retorna (bool_tem_update, nova_versao, url_download)
        """
        if not requests:
            print("Biblioteca 'requests' não instalada.")
            return False, None, None
            
        url = f"https://api.github.com/repos/{repo_usuario}/{repo_nome}/releases/latest"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                dados = response.json()
                tag_remota = dados.get("tag_name", "").replace("v", "")
                
                # Comparação simples de string (idealmente usar semantic versioning)
                if tag_remota > self.versao_atual:
                    assets = dados.get("assets", [])
                    if assets:
                        # Pega o primeiro asset (assumindo que é o .exe)
                        download_url = assets[0]["browser_download_url"]
                        return True, tag_remota, download_url
            return False, None, None
        except Exception as e:
            print(f"Erro ao verificar update: {e}")
            return False, None, None

    def aplicar_atualizacao(self, url_download, nome_executavel="SistemaHotel.exe", progress_callback=None):
        """
        Baixa o novo executável e cria um script .bat para substituir o atual.
        """
        if not requests: return
        
        try:
            # 1. Baixar o novo arquivo como 'update_temp.exe'
            r = requests.get(url_download, stream=True, timeout=15)
            r.raise_for_status()
            
            total_size = int(r.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open("update_temp.exe", 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if progress_callback and total_size > 0:
                        progress = downloaded_size / total_size
                        progress_callback(progress)
            
            # 2. Criar script BAT para fazer a troca (pois não podemos deletar o exe em execução)
            bat_script = f"""
            @echo off
            echo Atualizando o sistema... Por favor, aguarde.
            timeout /t 2 /nobreak > NUL
            del "{nome_executavel}"
            ren "update_temp.exe" "{nome_executavel}"
            start "" "{nome_executavel}"
            del "%~f0"
            """
            with open("updater.bat", "w") as bat:
                bat.write(bat_script)
            
            # 3. Executar o BAT e fechar o programa atual
            if progress_callback:
                progress_callback(1.0, "finalizando") # Sinaliza o fim para a GUI

            subprocess.Popen("updater.bat", shell=True)
            sys.exit(0)
            
        except Exception as e:
            raise Exception(f"Falha ao atualizar: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "reset_user":
        # Uso: python sistema_clientes.py reset_user <usuario> <nova_senha>
        core = SistemaCreditos()
        user = sys.argv[2]
        pwd = sys.argv[3]
        # Reseta como admin (1) e com permissão de datas (1) para garantir acesso
        # A função salvar_usuario agora lida com a criação do hash e salt
        core.salvar_usuario(user, pwd, 1, 1, 1, "reset_script")
        print(f"Senha do usuário '{user}' atualizada com sucesso.")
    else:
        print("Para resetar senha: python sistema_clientes.py reset_user <usuario> <nova_senha>")