import sys
import os

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, Listbox
from sistema_clientes import SistemaCreditos
from datetime import datetime
import webbrowser
from urllib.parse import quote
import threading
from difflib import get_close_matches

class AppHotelLTS(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.core = SistemaCreditos()
        self.title("Hotel Santos - Gestao de Creditos v4.2.8")
        self.geometry("1200x850")
        self.minsize(1024, 768) # Garante um tamanho mínimo para não quebrar o layout
        self.after(0, lambda: self.state('zoomed')) # Inicia maximizado no Windows
        
        # Carrega tema salvo (0=Light, 1=Dark)
        ctk.set_appearance_mode("Dark" if self.core.get_config('tema') == 1 else "Light")
        
        # Paleta de Cores (Baseada no style.css do Site)
        self.colors = {
            "verde": "#004d31",
            "verde_hover": "#003622",
            "dourado": "#b08d21",
            "dourado_hover": "#8e7018",
            "vermelho": "#c0392b",
            "branco": "#fdfdfd"
        }
        self.setup_custom_styles()
        self.current_user = None
        self.search_job = None # Variável para controlar o timer da busca (Debounce)
        self.current_screen_function = None
        self.current_screen_args = ()
        self.current_screen_kwargs = {}
        
        # Protocolo para fechar o app sem erros de terminal
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color=self.colors["verde"])
        # Sidebar começa oculta até o login
        self.sidebar.pack_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="H-SANTOS", font=("Times New Roman", 24, "bold"), text_color=self.colors["dourado"]).pack(pady=30)
        
        btn_opts = {"height": 40, "anchor": "w", "fg_color": "transparent", "text_color": "white", "hover_color": self.colors["dourado"]}
        ctk.CTkButton(self.sidebar, text="🏠 Home", command=self.tela_home, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="👥 Hóspedes", command=self.tela_hospedes, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="💰 Financeiro", command=self.tela_financeiro, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="🛒 Compras", command=self.tela_compras, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text=" Dashboard", command=self.tela_dash, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="⚙️ Ajustes", command=self.tela_config, **btn_opts).pack(pady=5, fill="x", padx=10)
        
        # Botão de Logout no final da sidebar
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True, fill="y")
        ctk.CTkButton(self.sidebar, text=" 🚪 Sair", command=self.logout, **btn_opts).pack(pady=20, fill="x", padx=10)

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        self.tela_login()

    # =========================================================================
    # 1. SETUP & CORE (Estilos, Configurações Globais)
    # =========================================================================
    def setup_custom_styles(self):
        style = ttk.Style()
        # Tenta usar o tema 'clam', que é mais moderno e customizável
        try:
            style.theme_use("clam")
        except:
            pass # Usa o tema padrão se 'clam' não estiver disponível

        is_dark = ctk.get_appearance_mode() == "Dark"
        
        # Cores para tema claro e escuro
        bg_color = "#2b2b2b" if is_dark else "#ffffff"
        fg_color = "#dce4ee" if is_dark else "#333333"
        field_bg = "#343638" if is_dark else "#ffffff"
        header_bg = "#3c3f41" if is_dark else "#e5e5e5"
        selected_fg = "#ffffff"

        style.configure("Treeview", 
                        background=bg_color, 
                        fieldbackground=field_bg, 
                        foreground=fg_color,
                        rowheight=35,
                        borderwidth=0)
        style.configure("Treeview.Heading", background=header_bg, foreground=fg_color, relief="flat", font=("Arial", 11, "bold"))
        style.map("Treeview", background=[("selected", self.colors["verde"])], foreground=[("selected", selected_fg)])

    def configurar_tags_tabela(self, tree):
        """Aplica configurações de cores para linhas pares, ímpares e saídas, adaptando-se ao tema."""
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        # Cores para tema claro e escuro
        if is_dark:
            # Acessa a cor do tema (índice 1 para Dark Mode)
            odd_bg = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1]
            even_bg = ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"][1]
        else:
            odd_bg = "#f2f2f2"
            even_bg = "#ffffff"
        
        tree.tag_configure('odd', background=odd_bg)
        tree.tag_configure('even', background=even_bg)
        tree.tag_configure('saida', foreground='#e74c3c')
        tree.tag_configure('multa', foreground='#f1c40f')
        tree.tag_configure('pagamento_multa', foreground='#2ecc71')
        tree.tag_configure('seta_subiu', foreground='#e74c3c') # Vermelho
        tree.tag_configure('seta_desceu', foreground='#2ecc71') # Verde

    def on_closing(self):
        """Encerra o processo de forma limpa"""
        try:
            # Tenta realizar um backup automático silencioso ao fechar
            self.core.fazer_backup()
        except:
            pass # Não impede o fechamento se o backup falhar
        self.quit()
        self.destroy()
        sys.exit()

    def limpar_tela(self):
        for w in self.main_frame.winfo_children(): w.destroy()
        # Reseta configurações de grid (importante pois a tela de histórico altera isso)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(0, weight=1)

    # =========================================================================
    # 2. AUTENTICAÇÃO
    # =========================================================================
    def logout(self):
        """Realiza o logout do usuário"""
        if messagebox.askyesno("Sair", "Tem certeza que deseja sair?"):
            self.current_user = None
            self.tela_login()

    def tela_login(self):
        self.limpar_tela()
        self.sidebar.pack_forget() # Garante que a sidebar esteja oculta
        
        f = ctk.CTkFrame(self.main_frame, width=300, height=350)
        f.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(f, text="LOGIN", font=("Arial", 20, "bold")).pack(pady=30)
        
        eu = ctk.CTkEntry(f, placeholder_text="Usuário", width=200); eu.pack(pady=10)
        ep = ctk.CTkEntry(f, placeholder_text="Senha", show="*", width=200); ep.pack(pady=10)
        
        def tentar_login(event=None):
            u = self.core.verificar_login(eu.get(), ep.get())
            if u:
                self.current_user = u
                # Repack para garantir que a sidebar fique à esquerda e o main preencha o resto
                self.main_frame.pack_forget()
                self.sidebar.pack(side="left", fill="y")
                self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
                self.tela_home()
            else:
                messagebox.showerror("Erro", "Credenciais inválidas")
                
        ep.bind("<Return>", tentar_login)
        
        ctk.CTkButton(f, text="Entrar", command=tentar_login, width=200, fg_color=self.colors["verde"], hover_color=self.colors["verde_hover"]).pack(pady=20)

    # =========================================================================
    # 3. NAVEGAÇÃO PRINCIPAL
    # =========================================================================
    def tela_home(self):
        self.current_screen_function = self.tela_home
        self.current_screen_args = ()
        self.current_screen_kwargs = {}

        self.limpar_tela()
        ctk.CTkLabel(self.main_frame, text="Controle de Créditos - Hotel Santos", font=("Times New Roman", 28, "bold"), text_color=self.colors["verde"]).pack(pady=60)
        grid = ctk.CTkFrame(self.main_frame, fg_color="transparent"); grid.pack()
        btns = [("📊 DASHBOARD", self.tela_dash, self.colors["verde"]), ("👥 HÓSPEDES", self.tela_hospedes, self.colors["verde"]),
                ("💰 FINANCEIRO", self.tela_financeiro, self.colors["dourado"]), ("🛒 COMPRAS", self.tela_compras, "#e67e22"), ("⚙️ AJUSTES", self.tela_config, "#7f8c8d")]
        for i, (t, c, col) in enumerate(btns):
            ctk.CTkButton(grid, text=t, width=250, height=90, command=c, fg_color=col, font=("Arial", 14, "bold")).grid(row=i//2, column=i%2, padx=20, pady=20)

    # =========================================================================
    # 4. MÓDULO HÓSPEDES (Listagem e Busca)
    # =========================================================================
    def tela_hospedes(self, filtro="todos"):
        self.current_screen_function = self.tela_hospedes
        self.current_screen_args = ()
        self.current_screen_kwargs = {'filtro': filtro}

        self.limpar_tela()
        nav = ctk.CTkFrame(self.main_frame, fg_color="transparent"); nav.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(nav, text="← Início", width=80, command=self.tela_home).pack(side="left")
        ctk.CTkLabel(nav, text="LISTAGEM DE HÓSPEDES", font=("Arial", 18, "bold"), text_color=self.colors["verde"]).pack(side="left", padx=20)
        ctk.CTkButton(nav, text="+ Novo Hóspede", width=120, fg_color=self.colors["dourado"], hover_color=self.colors["dourado_hover"], command=self.janela_cadastro_hospede).pack(side="right")

        self.ent_busca = ctk.CTkEntry(self.main_frame, placeholder_text="Pesquisar por nome ou documento...", width=500)
        self.ent_busca.pack(pady=10)
        self.ent_busca.bind("<KeyRelease>", lambda e: self.atualizar_lista_hospedes(filtro))
        self.ent_busca.bind("<KeyRelease>", lambda e: self.agendar_busca(filtro))

        self.tree_h = ttk.Treeview(self.main_frame, columns=("N", "D", "S"), show='headings')
        for c, t in [("N", "Nome Completo"), ("D", "CPF ou CNPJ"), ("S", "Saldo Disponível (R$)")]: 
            self.tree_h.heading(c, text=t); self.tree_h.column(c, anchor="center")
        self.configurar_tags_tabela(self.tree_h)
        self.tree_h.pack(expand=True, fill="both", padx=15, pady=10)
        self.tree_h.bind("<Double-1>", self.preparar_historico)

        # Menu de contexto (clique direito)
        self.menu_hospede = ctk.CTkFrame(self, width=150, height=100, border_width=1)
        ctk.CTkButton(self.menu_hospede, text="Ver Histórico Financeiro", command=self.preparar_historico, fg_color="transparent", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"], anchor="w").pack(fill="x")
        ctk.CTkButton(self.menu_hospede, text="Editar Cadastro", command=self.preparar_edicao_hospede, fg_color="transparent", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"], anchor="w").pack(fill="x")

        def show_menu(event):
            selection = self.tree_h.identify_row(event.y)
            if selection:
                self.tree_h.selection_set(selection)
                self.menu_hospede.place(x=event.x_root - self.winfo_x(), y=event.y_root - self.winfo_y())
                self.menu_hospede.lift()

        self.tree_h.bind("<Button-3>", show_menu)
        self.bind("<Button-1>", lambda e: self.menu_hospede.place_forget())
        self.atualizar_lista_hospedes(filtro)

    def agendar_busca(self, filtro):
        """Aguarda 500ms após a última tecla antes de buscar (Debounce)"""
        if self.search_job:
            self.after_cancel(self.search_job)
        self.search_job = self.after(500, lambda: self.atualizar_lista_hospedes(filtro))

    def atualizar_lista_hospedes(self, filtro):
        self.tree_h.delete(*self.tree_h.get_children())
        for i, h in enumerate(self.core.buscar_filtrado(self.ent_busca.get(), filtro)):
            # Usamos o documento como iid para garantir que o valor exato (string) seja preservado
            tag = 'odd' if i % 2 != 0 else 'even'
            self.tree_h.insert("", "end", iid=h[1], values=(h[0], h[1], f"{h[2]:.2f}"), tags=(tag,))

    def preparar_historico(self, event=None):
        self.menu_hospede.place_forget()
        sel = self.tree_h.selection()
        if sel:
            doc = sel[0]  # O iid agora é o documento exato, sem risco de conversão numérica
            n = self.tree_h.item(doc)['values'][0]
            self.tela_historico(n, str(doc))

    def preparar_edicao_hospede(self, event=None):
        self.menu_hospede.place_forget()
        sel = self.tree_h.selection()
        if sel:
            doc = sel[0]
            self.janela_cadastro_hospede(doc_to_edit=str(doc))

    # =========================================================================
    # 5. MÓDULO HISTÓRICO & FINANCEIRO (Detalhes do Cliente)
    # =========================================================================
    def tela_historico(self, nome, doc):
        self.current_screen_function = self.tela_historico
        self.current_screen_args = (nome, doc)
        self.current_screen_kwargs = {}

        self.limpar_tela()
        self.main_frame.columnconfigure(0, weight=3); self.main_frame.columnconfigure(1, weight=1)
        f_esq = ctk.CTkFrame(self.main_frame, fg_color="transparent"); f_esq.grid(row=0, column=0, sticky="nsew", padx=10)
        top = ctk.CTkFrame(f_esq, fg_color="transparent"); top.pack(fill="x", pady=5)
        ctk.CTkButton(top, text="← Voltar", width=80, command=self.tela_hospedes).pack(side="left")
        ctk.CTkButton(top, text="💬 WhatsApp", fg_color="#25D366", width=100, command=lambda: self.enviar_whatsapp(nome, doc)).pack(side="right", padx=5)
        ctk.CTkButton(top, text="📄 Extrato", fg_color="#2c3e50", width=80, command=lambda: self.emitir_extrato(nome, doc)).pack(side="right", padx=5)
        ctk.CTkButton(top, text="📄 Ticket Multas", fg_color="#c0392b", width=80, command=lambda: self.emitir_extrato_multas(nome, doc)).pack(side="right", padx=5)
        ctk.CTkButton(top, text="📄 PDF Voucher", fg_color=self.colors["verde"], width=100, command=lambda: self.emitir_voucher(nome, doc)).pack(side="right", padx=5)
        ctk.CTkLabel(f_esq, text=f"Histórico Financeiro: {nome}", font=("Arial", 20, "bold")).pack(pady=10)

        form = ctk.CTkFrame(f_esq, fg_color="transparent"); form.pack(fill="x", pady=5)
        ctk.CTkButton(form, text="Adicionar Crédito", fg_color=self.colors["verde"], command=lambda: self.janela_add_credito(doc, nome)).pack(side="left", padx=5)
        ctk.CTkButton(form, text="Utilizar Crédito", fg_color=self.colors["vermelho"], command=lambda: self.janela_usar_credito(doc, nome)).pack(side="left", padx=5)
        ctk.CTkButton(form, text="Lançar Multa", fg_color=self.colors["dourado"], command=lambda: self.janela_add_multa(doc, nome)).pack(side="left", padx=5)
        ctk.CTkButton(form, text="Pagar Multa", fg_color="#27ae60", command=lambda: self.janela_pagar_multa(doc, nome)).pack(side="left", padx=5)

        self.tree_z = ttk.Treeview(f_esq, columns=("T", "V", "D", "C", "U"), show='headings', height=10)
        for c, t in [("T","Tipo"),("V","Valor"),("D","Data"),("C","Categoria"), ("U", "Resp.")]: self.tree_z.heading(c, text=t); self.tree_z.column(c, anchor="center")
        self.tree_z.pack(expand=True, fill="both")
        self.configurar_tags_tabela(self.tree_z)
        
        # RESTAURADO: Clique direito para editar data
        self.tree_z.bind("<Button-3>", lambda e: self.janela_calendario_vencimento(e, doc, nome))
        
        hist = self.core.get_historico_detalhado(doc)
        for i, m in enumerate(hist):
            data_br = datetime.strptime(m['data_acao'], "%Y-%m-%d").strftime("%d/%m/%Y")
            user_resp = m['usuario'] if m['usuario'] else "Sistema"
            
            tags = ['odd' if i % 2 != 0 else 'even']
            if m['tipo'] == 'SAIDA': tags.append('saida')
            if m['tipo'] == 'MULTA': tags.append('multa')
            if m['tipo'] == 'PAGAMENTO_MULTA': tags.append('pagamento_multa')

            self.tree_z.insert("", "end", values=(m['tipo'], f"{m['valor']:.2f}", data_br, m['categoria'], user_resp), tags=tags)

        f_dir = ctk.CTkFrame(self.main_frame, fg_color="transparent"); f_dir.grid(row=0, column=1, sticky="nsew", padx=10)
        s, v, b = self.core.get_saldo_info(doc)
        divida = self.core.get_divida_multas(doc)
        
        info_cards = [("Saldo de Crédito", f"R$ {s:.2f}", self.colors["verde"]), 
                      ("Vencimento Próximo", v, self.colors["vermelho"] if b else "#f39c12"),
                      ("Dívida (Multas)", f"R$ {divida:.2f}", self.colors["dourado"] if divida > 0 else "gray")]

        for t, val, col in info_cards:
            c = ctk.CTkFrame(f_dir, border_width=1); c.pack(fill="x", pady=5, ipady=10)
            ctk.CTkLabel(c, text=t, font=("Arial", 11)).pack()
            ctk.CTkLabel(c, text=val, font=("Arial", 16, "bold"), text_color=col).pack()

        p = ctk.CTkFrame(f_dir, fg_color="#fef9c3", border_width=1, border_color="#facc15")
        p.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(p, text="📌 NOTAS GERAIS", text_color="#854d0e", font=("Arial", 12, "bold")).pack(pady=5)
        txt = ctk.CTkTextbox(p, fg_color="transparent", text_color="black"); txt.pack(fill="both", expand=True, padx=5)
        txt.insert("1.0", self.core.get_anotacao(doc))
        ctk.CTkButton(p, text="Salvar Notas", width=100, fg_color=self.colors["dourado"], text_color="white", command=lambda: self.core.salvar_anotacao(doc, txt.get("1.0","end-1c"))).pack(pady=5)

    def enviar_whatsapp(self, nome, doc):
        s, v, b = self.core.get_saldo_info(doc)
        if s <= 0:
            messagebox.showwarning("Aviso", "Cliente sem saldo para enviar.")
            return

        hospede = self.core.get_hospede(doc)
        fone = hospede['telefone'] if hospede and hospede['telefone'] else None

        if not fone:
            if messagebox.askyesno("Telefone não encontrado", "Este cliente não possui um telefone cadastrado. Deseja cadastrar/editar agora?"):
                self.janela_cadastro_hospede(doc_to_edit=doc)
            return

        # Limpa o número para conter apenas dígitos
        fone_limpo = "".join(filter(str.isdigit, fone))
        if not fone_limpo:
            messagebox.showerror("Erro", f"O número de telefone cadastrado ('{fone}') é inválido.")
            return

        msg = f"*HOTEL SANTOS - VOUCHER DE CRÉDITO*\n\nOlá {nome},\nSegue seu saldo atualizado:\n\n💰 *Valor:* R$ {s:.2f}\n📅 *Validade:* {v}\n\nUtilize este crédito em sua próxima hospedagem!"
        link = f"https://web.whatsapp.com/send?phone=55{fone_limpo}&text={quote(msg)}"
        webbrowser.open(link)

    def emitir_voucher(self, nome, doc):
        """Gera o voucher em uma thread separada para não travar a interface"""
        self.configure(cursor="watch") # Muda cursor para 'carregando'
        def _task():
            try:
                f = self.core.gerar_pdf_voucher(nome, doc)
                # UI updates devem ser agendados na main thread
                self.after(0, lambda: messagebox.showinfo("Sucesso", f"Voucher gerado: {f}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            finally:
                self.after(0, lambda: self.configure(cursor="arrow")) # Restaura cursor
        threading.Thread(target=_task, daemon=True).start()

    def emitir_extrato(self, nome, doc):
        self.configure(cursor="watch")
        def _task():
            try:
                f = self.core.gerar_pdf_extrato(nome, doc)
                self.after(0, lambda: messagebox.showinfo("Sucesso", f"Extrato gerado: {f}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            finally:
                self.after(0, lambda: self.configure(cursor="arrow"))
        threading.Thread(target=_task, daemon=True).start()

    def emitir_extrato_multas(self, nome, doc):
        self.configure(cursor="watch")
        def _task():
            try:
                f = self.core.gerar_pdf_multas(nome, doc)
                self.after(0, lambda: messagebox.showinfo("Sucesso", f"Ticket de Multas gerado: {f}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            finally:
                self.after(0, lambda: self.configure(cursor="arrow"))
        threading.Thread(target=_task, daemon=True).start()

    # =========================================================================
    # 6. MÓDULO DASHBOARD & RELATÓRIOS
    # =========================================================================
    def tela_dash(self):
        # Importação tardia (Lazy Import) para acelerar a abertura do App
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        # Aplica o tema do CustomTkinter ao Matplotlib para consistência visual
        if ctk.get_appearance_mode() == "Dark":
            plt.style.use('dark_background')
            plt.rcParams.update({
                "figure.facecolor": "#2b2b2b",
                "axes.facecolor": "#2b2b2b",
                "text.color": "white",
                "axes.labelcolor": "white",
                "xtick.color": "white",
                "ytick.color": "white",
                "axes.edgecolor": "white",
                "legend.facecolor": "#343638",
            })
        else:
            # Reseta para o padrão do Matplotlib para o tema claro
            plt.style.use('default')
            plt.rcParams.update(plt.rcParamsDefault)

        self.current_screen_function = self.tela_dash
        self.current_screen_args = ()
        self.current_screen_kwargs = {}
        self.limpar_tela()
        t, v, av, q = self.core.get_dados_dash()
        dias_config = self.core.get_config('alerta_dias')
        nav = ctk.CTkFrame(self.main_frame, fg_color="transparent"); nav.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(nav, text="← Início", width=80, command=self.tela_home).pack(side="left")
        ctk.CTkButton(nav, text="📥 Exportar Relatório CSV", fg_color=self.colors["verde"], width=180, command=lambda: [
            messagebox.showinfo("Exportado", f"Relatório salvo em:\n{self.core.exportar_csv()}")
        ]).pack(side="right")
        
        # Conteúdo em Frame Rolável para telas pequenas
        scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        cards = ctk.CTkFrame(scroll, fg_color="transparent"); cards.pack(fill="x", pady=10)
        lista_cards = [
            ("Saldo Total Geral", f"R$ {t:.2f}", self.colors["verde"]), 
            ("Total Vencidos", f"R$ {v:.2f}", self.colors["vermelho"]), 
            (f"A Vencer ({dias_config} dias)", f"R$ {av:.2f}", "#f39c12"),
            ("Base de Clientes", str(q), self.colors["verde"])
        ]
        for tit, val, col in lista_cards:
            c = ctk.CTkFrame(cards, border_width=1); c.pack(side="left", expand=True, padx=5, fill="both", ipady=10)
            ctk.CTkLabel(c, text=tit, font=("Arial", 11)).pack()
            ctk.CTkLabel(c, text=val, font=("Arial", 18, "bold"), text_color=col).pack()

        # Gráfico de Barras (Entradas vs Saídas)
        meses, entradas, saidas = self.core.get_dados_grafico_mensal()
        if meses:
            f_bar = ctk.CTkFrame(scroll, fg_color="transparent")
            f_bar.pack(fill="x", padx=10, pady=5)
            
            fig_bar, ax_bar = plt.subplots(figsize=(8, 2.5), dpi=80)
            x = range(len(meses))
            width = 0.35
            
            ax_bar.bar([i - width/2 for i in x], entradas, width, label='Entradas', color=self.colors["verde"])
            ax_bar.bar([i + width/2 for i in x], saidas, width, label='Saídas', color=self.colors["vermelho"])
            
            ax_bar.set_xticks(x); ax_bar.set_xticklabels(meses)
            ax_bar.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False, fontsize='small')
            ax_bar.spines['top'].set_visible(False); ax_bar.spines['right'].set_visible(False)
            FigureCanvasTkAgg(fig_bar, master=f_bar).get_tk_widget().pack(fill="both", expand=True)

        inf = ctk.CTkFrame(scroll, fg_color="transparent"); inf.pack(fill="both", expand=True)
        gr = ctk.CTkFrame(inf); gr.pack(side="left", fill="both", expand=True, padx=5)
        dados_g = self.core.get_dados_grafico_categorias()
        if dados_g:
            fig, ax = plt.subplots(figsize=(4,3), dpi=85)
            ax.pie([x[1] for x in dados_g], labels=[x[0] for x in dados_g], autopct='%1.1f%%')
            FigureCanvasTkAgg(fig, master=gr).get_tk_widget().pack(pady=10)
        
        tab = ctk.CTkFrame(inf); tab.pack(side="right", fill="both", expand=True, padx=5)
        ctk.CTkLabel(tab, text=f"Detalhamento Alerta ({dias_config} dias)", font=("Arial", 12, "bold")).pack(pady=5)
        tv = ttk.Treeview(tab, columns=("H", "D", "V"), show='headings')
        for c, t_ in [("H","Hóspede"),("D","Vencimento"),("V","Saldo")]: tv.heading(c, text=t_); tv.column(c, anchor="center", width=100)
        tv.pack(fill="both", expand=True); [tv.insert("", "end", values=h) for h in self.core.get_hospedes_vencendo_em_breve()]

    # =========================================================================
    # MÓDULO COMPRAS
    # =========================================================================
    def tela_compras(self):
        self.current_screen_function = self.tela_compras
        self.current_screen_args = ()
        self.current_screen_kwargs = {}
        self.limpar_tela()

        nav = ctk.CTkFrame(self.main_frame, fg_color="transparent"); nav.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(nav, text="← Início", width=80, command=self.tela_home).pack(side="left")
        ctk.CTkLabel(nav, text="REGISTRO DE COMPRAS", font=("Arial", 18, "bold"), text_color="#e67e22").pack(side="left", padx=20)
        ctk.CTkButton(nav, text="💬 Enviar WhatsApp", fg_color="#25D366", width=140, command=self.enviar_whatsapp_compras).pack(side="right", padx=5)
        ctk.CTkButton(nav, text="📄 Exportar PDF", fg_color="#2c3e50", width=120, command=self.exportar_pdf_compras).pack(side="right", padx=5)

        # Formulário de Entrada
        form = ctk.CTkFrame(self.main_frame); form.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(form, text="Data (dd/mm/aaaa):").grid(row=0, column=0, padx=5, pady=5)
        self.e_data_compras = ctk.CTkEntry(form, width=100); self.e_data_compras.grid(row=1, column=0, padx=5, pady=5)
        self.e_data_compras.insert(0, datetime.now().strftime("%d/%m/%Y"))

        ctk.CTkLabel(form, text="Produto:").grid(row=0, column=1, padx=5, pady=5)
        
        # Configuração da Busca Estilo Google (Entry + Listbox)
        self.lista_produtos_cache = self.core.get_produtos_predefinidos()
        self.e_prod_compras = ctk.CTkEntry(form, width=250, placeholder_text="Digite para buscar...")
        self.e_prod_compras.grid(row=1, column=1, padx=5, pady=5)
        
        # Listbox para sugestões (inicialmente oculta)
        # Cores adaptadas para o tema (simples)
        bg_list = "#333333" if ctk.get_appearance_mode() == "Dark" else "#ffffff"
        fg_list = "#ffffff" if ctk.get_appearance_mode() == "Dark" else "#000000"
        
        self.lb_sugestoes = Listbox(self.main_frame, width=40, height=5, bg=bg_list, fg=fg_list, selectbackground=self.colors["verde"], selectforeground="white", borderwidth=1, relief="solid")
        
        def autocomplete_prod(event):
            # Teclas de navegação não devem acionar o filtro
            if event.keysym in ['Down', 'Up', 'Return', 'Tab']: return
            
            typed = self.e_prod_compras.get()
            if not typed:
                self.lb_sugestoes.place_forget()
                return
            
            filtered = [p for p in self.lista_produtos_cache if typed.lower() in p.lower()]
            
            if filtered:
                self.lb_sugestoes.delete(0, 'end')
                for item in filtered:
                    self.lb_sugestoes.insert('end', item)
                # Posiciona a lista logo abaixo do Entry
                self.lb_sugestoes.place(in_=self.e_prod_compras, x=0, rely=1.0, relwidth=1.0)
                self.lb_sugestoes.lift()
            else:
                self.lb_sugestoes.place_forget()

        def selecionar_sugestao(event=None):
            if self.lb_sugestoes.curselection():
                item = self.lb_sugestoes.get(self.lb_sugestoes.curselection())
                self.e_prod_compras.delete(0, 'end')
                self.e_prod_compras.insert(0, item)
                self.lb_sugestoes.place_forget()
                self.e_prod_compras.focus_set()
                # Opcional: Pular para o próximo campo (Qtd)
                e_qtd.focus_set()

        def navegar_lista(event):
            if self.lb_sugestoes.winfo_ismapped():
                self.lb_sugestoes.focus_set()
                self.lb_sugestoes.selection_set(0)

        self.e_prod_compras.bind("<KeyRelease>", autocomplete_prod)
        self.e_prod_compras.bind("<Down>", navegar_lista)
        self.lb_sugestoes.bind("<Return>", selecionar_sugestao)
        self.lb_sugestoes.bind("<Button-1>", selecionar_sugestao)
        # Fecha a lista se clicar fora (simplificado: fecha ao sair do campo)
        # self.e_prod_compras.bind("<FocusOut>", lambda e: self.after(200, self.lb_sugestoes.place_forget)) 

        ctk.CTkLabel(form, text="Qtd:").grid(row=0, column=2, padx=5, pady=5)
        e_qtd = ctk.CTkEntry(form, width=80); e_qtd.grid(row=1, column=2, padx=5, pady=5)

        ctk.CTkLabel(form, text="Valor Unit. (R$):").grid(row=0, column=3, padx=5, pady=5)
        e_val = ctk.CTkEntry(form, width=100); e_val.grid(row=1, column=3, padx=5, pady=5)

        def add_compra():
            try:
                raw_prod = self.e_prod_compras.get()
                if not raw_prod or not e_qtd.get() or not e_val.get():
                    raise Exception("Preencha todos os campos.")
                
                prod_digitado = raw_prod.upper().strip()

                # Verifica se o produto existe na lista de produtos cadastrados
                produtos_existentes = [p.upper() for p in self.lista_produtos_cache]
                if prod_digitado not in produtos_existentes:
                    raise Exception("Produto não cadastrado! Cadastre-o primeiro no menu Ajustes > Produtos.")

                self.core.adicionar_compra(self.e_data_compras.get(), prod_digitado, e_qtd.get(), e_val.get(), usuario=self.current_user['username'])
                
                atualizar_tabela()
                self.e_prod_compras.delete(0, 'end'); e_qtd.delete(0, 'end'); e_val.delete(0, 'end'); self.e_prod_compras.focus()
                self.lb_sugestoes.place_forget()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        # Bind do Enter para adicionar
        def on_enter_prod(event):
            # Se a lista estiver visível e algo selecionado, o Enter seleciona a sugestão
            # Caso contrário, tenta adicionar a compra
            if self.lb_sugestoes.winfo_ismapped() and self.lb_sugestoes.curselection():
                selecionar_sugestao()
            else:
                add_compra()

        self.e_prod_compras.bind("<Return>", on_enter_prod)
        e_qtd.bind("<Return>", lambda e: add_compra())
        e_val.bind("<Return>", lambda e: add_compra())

        ctk.CTkButton(form, text="Adicionar", fg_color=self.colors["verde"], command=add_compra).grid(row=1, column=4, padx=10, pady=5)

        # Tabela de Histórico
        ctk.CTkLabel(self.main_frame, text="Histórico de Compras", font=("Arial", 12, "bold")).pack(pady=(15,5))
        
        cols = ("Data", "Produto", "Qtd", "Unitário", "Total", "Tendência")
        tree = ttk.Treeview(self.main_frame, columns=cols, show='headings')
        
        tree.heading("Data", text="Data"); tree.column("Data", width=100, anchor="center")
        tree.heading("Produto", text="Produto"); tree.column("Produto", width=300)
        tree.heading("Qtd", text="Qtd"); tree.column("Qtd", width=80, anchor="center")
        tree.heading("Unitário", text="Unitário (R$)"); tree.column("Unitário", width=100, anchor="center")
        tree.heading("Total", text="Total (R$)"); tree.column("Total", width=100, anchor="center")
        tree.heading("Tendência", text="Variação"); tree.column("Tendência", width=80, anchor="center")
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.configurar_tags_tabela(tree)

        def atualizar_tabela():
            tree.delete(*tree.get_children())
            for i, c in enumerate(self.core.get_historico_compras()):
                data_br = datetime.strptime(c['data_compra'], "%Y-%m-%d").strftime("%d/%m/%Y")
                seta = "➖"
                tag_seta = "even"
                if c['tendencia'] == 'subiu': seta = "▲ Subiu"; tag_seta = "seta_subiu"
                elif c['tendencia'] == 'desceu': seta = "▼ Caiu"; tag_seta = "seta_desceu"
                
                tree.insert("", "end", values=(data_br, c['produto'], f"{c['quantidade']}", f"{c['valor_unitario']:.2f}", f"{c['valor_total']:.2f}", seta), tags=(tag_seta,))
        
        atualizar_tabela()

    def exportar_pdf_compras(self):
        self.configure(cursor="watch")
        def _task():
            try:
                f = self.core.gerar_pdf_compras()
                self.after(0, lambda: messagebox.showinfo("Sucesso", f"Relatório de Compras gerado: {f}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            finally:
                self.after(0, lambda: self.configure(cursor="arrow"))
        threading.Thread(target=_task, daemon=True).start()

    def enviar_whatsapp_compras(self):
        # Filtra compras pela data selecionada no campo de data
        data_str = self.e_data_compras.get()
        try:
            data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            data_iso = datetime.now().strftime("%Y-%m-%d")
            
        todas_compras = self.core.get_historico_compras()
        compras_dia = [c for c in todas_compras if c['data_compra'] == data_iso]

        if not compras_dia:
            messagebox.showwarning("Aviso", f"Não há compras registradas para {data_str}.")
            return

        msg_parts = [f"*RELATÓRIO DE COMPRAS - {data_str}*"]
        for c in compras_dia:
            seta = ""
            if c['tendencia'] == 'subiu': seta = "🔺"
            elif c['tendencia'] == 'desceu': seta = "🔻"

            parte = f"\n\n*Produto:* {c['produto']}\n*Qtd:* {c['quantidade']} | *Unit:* R$ {c['valor_unitario']:.2f} {seta}"
            msg_parts.append(parte)
        
        msg = "".join(msg_parts)
        fone_fixo = "19997597503"
        link = f"https://web.whatsapp.com/send?phone=55{fone_fixo}&text={quote(msg)}"
        webbrowser.open(link)

    # =========================================================================
    # 7. MÓDULO LANÇAMENTOS (Central)
    # =========================================================================
    def tela_financeiro(self):
        self.current_screen_function = self.tela_financeiro
        self.current_screen_args = ()
        self.current_screen_kwargs = {}

        self.limpar_tela()
        nav = ctk.CTkFrame(self.main_frame, fg_color="transparent"); nav.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(nav, text="← Início", width=80, command=self.tela_home).pack(side="left")
        ctk.CTkLabel(nav, text="CENTRAL FINANCEIRA", font=("Arial", 18, "bold"), text_color=self.colors["verde"]).pack(side="left", padx=20)
        ctk.CTkButton(nav, text="+ Novo Lançamento", width=160, fg_color=self.colors["dourado"], hover_color=self.colors["dourado_hover"], command=self.janela_novo_lancamento_central).pack(side="right")

        # Sistema de Abas
        tabview = ctk.CTkTabview(self.main_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=5)
        tabview.add("Extrato Global")
        tabview.add("Controle de Inadimplência (Multas)")

        # --- ABA 1: EXTRATO GLOBAL ---
        tab_extrato = tabview.tab("Extrato Global")
        self.ent_busca_lanc = ctk.CTkEntry(tab_extrato, placeholder_text="Filtrar por nome ou documento...", width=500)
        self.ent_busca_lanc.pack(pady=10)
        
        # Treeview
        self.tree_l = ttk.Treeview(tab_extrato, columns=("ID", "Data", "Nome", "Tipo", "Valor", "Categoria", "Usuario"), show='headings')
        self.tree_l.heading("ID", text="ID"); self.tree_l.column("ID", width=50, anchor="center")
        self.tree_l.heading("Data", text="Data"); self.tree_l.column("Data", width=100, anchor="center")
        self.tree_l.heading("Nome", text="Cliente"); self.tree_l.column("Nome", width=250)
        self.tree_l.heading("Tipo", text="Tipo"); self.tree_l.column("Tipo", width=100, anchor="center")
        self.tree_l.heading("Valor", text="Valor"); self.tree_l.column("Valor", width=100, anchor="center")
        self.tree_l.heading("Categoria", text="Cat/Motivo"); self.tree_l.column("Categoria", width=150)
        self.tree_l.heading("Usuario", text="Resp."); self.tree_l.column("Usuario", width=100, anchor="center")
        
        self.tree_l.pack(expand=True, fill="both", padx=15, pady=10)
        self.configurar_tags_tabela(self.tree_l)

        # Context Menu for Deletion
        self.menu_lanc = ctk.CTkFrame(self, width=150, height=50, border_width=1)
        ctk.CTkButton(self.menu_lanc, text="Excluir Lançamento", command=self.excluir_lancamento_selecionado, fg_color="transparent", text_color="red", anchor="w").pack(fill="x")
        
        def show_menu(event):
            selection = self.tree_l.identify_row(event.y)
            if selection:
                self.tree_l.selection_set(selection)
                self.menu_lanc.place(x=event.x_root - self.winfo_x(), y=event.y_root - self.winfo_y())
                self.menu_lanc.lift()
        
        self.tree_l.bind("<Button-3>", show_menu)
        self.bind("<Button-1>", lambda e: self.menu_lanc.place_forget())

        self.ent_busca_lanc.bind("<KeyRelease>", lambda e: self.atualizar_lista_lancamentos())
        self.atualizar_lista_lancamentos()

        # --- ABA 2: CONTROLE DE INADIMPLÊNCIA ---
        tab_multas = tabview.tab("Controle de Inadimplência (Multas)")
        ctk.CTkLabel(tab_multas, text="Clientes com multas pendentes de pagamento", text_color="gray").pack(pady=5)
        
        tv_m = ttk.Treeview(tab_multas, columns=("N", "D", "T", "V"), show="headings")
        tv_m.heading("N", text="Nome"); tv_m.column("N", width=300)
        tv_m.heading("D", text="Documento"); tv_m.column("D", width=150, anchor="center")
        tv_m.heading("T", text="Telefone"); tv_m.column("T", width=150, anchor="center")
        tv_m.heading("V", text="Dívida Total"); tv_m.column("V", width=100, anchor="center")
        tv_m.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Carrega dados
        devedores = self.core.get_devedores_multas()
        for d in devedores:
            tv_m.insert("", "end", values=(d[0], d[1], d[2], f"R$ {d[3]:.2f}"))
        
        # Duplo clique para ir ao histórico pagar
        tv_m.bind("<Double-1>", lambda e: self.tela_historico(tv_m.item(tv_m.selection()[0])['values'][0], str(tv_m.item(tv_m.selection()[0])['values'][1])))

    def atualizar_lista_lancamentos(self):
        self.tree_l.delete(*self.tree_l.get_children())
        filtro = self.ent_busca_lanc.get()
        dados = self.core.get_historico_global(filtro)
        for i, d in enumerate(dados):
            data_br = datetime.strptime(d['data_acao'], "%Y-%m-%d").strftime("%d/%m/%Y")
            tags = ['odd' if i % 2 != 0 else 'even']
            if d['tipo'] == 'SAIDA': tags.append('saida')
            if d['tipo'] == 'MULTA': tags.append('multa')
            if d['tipo'] == 'PAGAMENTO_MULTA': tags.append('pagamento_multa')
            
            self.tree_l.insert("", "end", values=(d['id'], data_br, d['nome'], d['tipo'], f"{d['valor']:.2f}", d['categoria'], d['usuario']), tags=tags)

    def excluir_lancamento_selecionado(self):
        self.menu_lanc.place_forget()
        if not self.current_user['is_admin']:
            messagebox.showerror("Acesso Negado", "Apenas administradores podem excluir lançamentos.")
            return
        
        sel = self.tree_l.selection()
        if not sel: return
        item = self.tree_l.item(sel[0])
        id_mov = item['values'][0]
        
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o lançamento ID {id_mov}?"):
            try:
                self.core.excluir_movimentacao(id_mov, self.current_user['username'])
                self.atualizar_lista_lancamentos()
                messagebox.showinfo("Sucesso", "Lançamento excluído.")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    # =========================================================================
    # 8. MÓDULO CONFIGURAÇÕES & ADMIN
    # =========================================================================
    def tela_config(self):
        self.current_screen_function = self.tela_config
        self.current_screen_args = ()
        self.current_screen_kwargs = {}

        self.limpar_tela()
        nav = ctk.CTkFrame(self.main_frame, fg_color="transparent"); nav.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(nav, text="← Início", width=80, command=self.tela_home).pack(side="left")
        
        def toggle_theme():
            new_mode = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"
            ctk.set_appearance_mode(new_mode)
            self.setup_custom_styles()
            self.core.set_config('tema', 1 if new_mode == "Dark" else 0, self.current_user['username'])
            
            # Força o redesenho completo da tela atual para aplicar todas as mudanças de estilo
            if self.current_screen_function:
                self.current_screen_function(*self.current_screen_args, **self.current_screen_kwargs)

        icon = "🌙" if ctk.get_appearance_mode() == "Light" else "☀️"
        btn_tema = ctk.CTkButton(nav, text=f"{icon} Tema", width=100, fg_color="#555", command=toggle_theme)
        btn_tema.pack(side="right")
        
        if self.current_user['is_admin'] or self.current_user.get('can_manage_products'):
            self.config_admin_view()
        else:
            self.config_user_view()

    def config_admin_view(self):
        # --- Sistema de Abas para melhor organização ---
        tabview = ctk.CTkTabview(self.main_frame, segmented_button_selected_color=self.colors["verde"])
        tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Adiciona abas conforme permissão
        if self.current_user['is_admin']:
            tab_sistema = tabview.add("Sistema")
            tab_usuarios = tabview.add("Usuários")
            tab_categorias = tabview.add("Categorias")
            tab_auditoria = tabview.add("Auditoria")
        
        if self.current_user['is_admin'] or self.current_user.get('can_manage_products'):
            tab_produtos = tabview.add("Produtos")

        # --- ABA 1: SISTEMA (Configs, Backup) ---
        if self.current_user['is_admin']:
            f_grid = ctk.CTkFrame(tab_sistema, fg_color="transparent"); f_grid.pack(pady=10, padx=20, anchor="w")
            ctk.CTkLabel(f_grid, text="Validade (Meses):").grid(row=0, column=0, padx=5)
            ev = ctk.CTkEntry(f_grid, width=50); ev.insert(0, str(self.core.get_config('validade_meses'))); ev.grid(row=0, column=1, padx=5)
            
            ctk.CTkLabel(f_grid, text="Alerta (Dias):").grid(row=0, column=2, padx=5)
            ea = ctk.CTkComboBox(f_grid, values=["15", "30", "60", "90"], width=60)
            ea.set(str(self.core.get_config('alerta_dias'))); ea.grid(row=0, column=3, padx=5)
            
            ctk.CTkButton(tab_sistema, text="Salvar Configurações", height=30, fg_color=self.colors["verde"], command=lambda: [
                self.core.set_config('validade_meses', int(ev.get()), self.current_user['username']), 
                self.core.set_config('alerta_dias', int(ea.get()), self.current_user['username']), 
                messagebox.showinfo("Sucesso", "Configurações salvas!"),
                self.tela_dash()
            ]).pack(pady=10, padx=20, anchor="w")

            f_backup = ctk.CTkFrame(tab_sistema, fg_color="transparent"); f_backup.pack(pady=20, padx=20, anchor="w")
            ctk.CTkButton(f_backup, text="Fazer Backup do Banco", height=30, fg_color=self.colors["dourado"], command=lambda: [
                self.core.fazer_backup(),
                messagebox.showinfo("Backup", "Backup realizado com sucesso na pasta 'backups'!")
            ]).pack(side="left", padx=5)

            def restaurar():
                path = filedialog.askopenfilename(filetypes=[("Banco de Dados", "*.db")])
                if path:
                    if messagebox.askyesno("Confirmar", "Isso substituirá os dados atuais pelos do backup. Continuar?"):
                        try: self.core.restaurar_backup(path, self.current_user['username']); messagebox.showinfo("Sucesso", "Backup restaurado! Reinicie o sistema.")
                        except Exception as e: messagebox.showerror("Erro", str(e))
            ctk.CTkButton(f_backup, text="Restaurar Backup", height=30, fg_color=self.colors["vermelho"], command=restaurar).pack(side="left", padx=5)

        # --- ABA 2: USUÁRIOS ---
        f_form = ctk.CTkFrame(tab_usuarios, fg_color="transparent"); f_form.pack(pady=10, fill="x", padx=10)
        eu_user = ctk.CTkEntry(f_form, placeholder_text="Usuário"); eu_user.pack(side="left", padx=5)
        eu_pass = ctk.CTkEntry(f_form, placeholder_text="Senha"); eu_pass.pack(side="left", padx=5)
        chk_admin = ctk.CTkCheckBox(f_form, text="Admin"); chk_admin.pack(side="left", padx=5)
        chk_dates = ctk.CTkCheckBox(f_form, text="Alterar Datas"); chk_dates.pack(side="left", padx=5)
        chk_products = ctk.CTkCheckBox(f_form, text="Gerir Produtos"); chk_products.pack(side="left", padx=5)
        
        tv_u = ttk.Treeview(tab_usuarios, columns=("U", "A", "D"), show='headings', height=8)
        tv_u.heading("U", text="Usuário"); tv_u.heading("A", text="Admin"); tv_u.heading("D", text="Pode Alterar Datas")
        tv_u.column("U", anchor="center"); tv_u.column("A", anchor="center"); tv_u.column("D", anchor="center")
        tv_u.pack(fill="both", expand=True, padx=10, pady=5)
        self.configurar_tags_tabela(tv_u)
        
        def refresh_users():
            tv_u.delete(*tv_u.get_children())
            for i, u in enumerate(self.core.get_usuarios()):
                tag = 'odd' if i % 2 != 0 else 'even'
                tv_u.insert("", "end", values=(u['username'], "Sim" if u['is_admin'] else "Não", "Sim" if u['can_change_dates'] else "Não"), tags=(tag,))
        
        def save_user(event=None):
            if not eu_user.get() or not eu_pass.get(): return
            self.core.salvar_usuario(eu_user.get(), eu_pass.get(), chk_admin.get(), chk_dates.get(), chk_products.get(), self.current_user['username'])
            refresh_users(); eu_user.delete(0, 'end'); eu_pass.delete(0, 'end')
            
        eu_pass.bind("<Return>", save_user)
        ctk.CTkButton(f_form, text="Salvar/Atualizar", command=save_user, fg_color=self.colors["verde"]).pack(side="left", padx=5)
        
        refresh_users()
        
        def del_user():
            sel = tv_u.selection()
            if not sel: return
            u = tv_u.item(sel[0])['values'][0]
            if u == 'gabriel': messagebox.showerror("Erro", "Não é possível excluir o superadmin."); return
            if messagebox.askyesno("Confirmar", f"Excluir {u}?"): self.core.excluir_usuario(u, self.current_user['username']); refresh_users()
        ctk.CTkButton(tab_usuarios, text="Excluir Selecionado", fg_color=self.colors["vermelho"], command=del_user).pack(pady=10, anchor="e", padx=10)

        # --- ABA 3: CATEGORIAS ---
        if self.current_user['is_admin']:
            fc_top = ctk.CTkFrame(tab_categorias, fg_color="transparent"); fc_top.pack(fill="x", padx=10, pady=10)
            ec_cat = ctk.CTkEntry(fc_top, placeholder_text="Nova Categoria"); ec_cat.pack(side="left", padx=5, expand=True, fill="x")
            
            def add_c(event=None):
                self.core.adicionar_categoria(ec_cat.get()); ec_cat.delete(0, 'end'); refresh_c()
            ec_cat.bind("<Return>", add_c)
            ctk.CTkButton(fc_top, text="+", width=40, command=add_c, fg_color=self.colors["verde"]).pack(side="left")
            
            tv_c = ttk.Treeview(tab_categorias, columns=("C",), show="headings")
            tv_c.heading("C", text="Nome"); tv_c.pack(fill="x", padx=10, pady=5)
            self.configurar_tags_tabela(tv_c)

            def refresh_c():
                tv_c.delete(*tv_c.get_children())
                for i, c in enumerate(self.core.get_categorias()):
                    tag = 'odd' if i % 2 != 0 else 'even'
                    tv_c.insert("", "end", values=(c,), tags=(tag,))
            refresh_c()

            def del_c():
                if tv_c.selection(): self.core.remover_categoria(tv_c.item(tv_c.selection()[0])['values'][0]); refresh_c()
            ctk.CTkButton(tab_categorias, text="Remover Selecionada", height=25, fg_color=self.colors["vermelho"], command=del_c).pack(pady=5, anchor="e", padx=10)

        # --- ABA PRODUTOS (NOVA) ---
        if self.current_user['is_admin'] or self.current_user.get('can_manage_products'):
            fp_top = ctk.CTkFrame(tab_produtos, fg_color="transparent"); fp_top.pack(fill="x", padx=10, pady=10)
            ep_prod = ctk.CTkEntry(fp_top, placeholder_text="Nome do Produto (Ex: Detergente 5L)"); ep_prod.pack(side="left", padx=5, expand=True, fill="x")
            
            def add_p(event=None):
                self.core.adicionar_produto_predefinido(ep_prod.get()); ep_prod.delete(0, 'end'); refresh_p()
            ep_prod.bind("<Return>", add_p)
            ctk.CTkButton(fp_top, text="+ Adicionar", width=100, command=add_p, fg_color=self.colors["verde"]).pack(side="left")
            
            tv_p = ttk.Treeview(tab_produtos, columns=("P",), show="headings")
            tv_p.heading("P", text="Produto"); tv_p.pack(fill="both", expand=True, padx=10, pady=5)
            self.configurar_tags_tabela(tv_p)

            def refresh_p():
                tv_p.delete(*tv_p.get_children())
                for i, p in enumerate(self.core.get_produtos_predefinidos()):
                    tag = 'odd' if i % 2 != 0 else 'even'
                    tv_p.insert("", "end", values=(p,), tags=(tag,))
            refresh_p()

            def del_p():
                if tv_p.selection(): self.core.remover_produto_predefinido(tv_p.item(tv_p.selection()[0])['values'][0]); refresh_p()
            ctk.CTkButton(tab_produtos, text="Remover Selecionado", height=25, fg_color=self.colors["vermelho"], command=del_p).pack(pady=5, anchor="e", padx=10)

        # --- ABA 4: AUDITORIA ---
        if self.current_user['is_admin']:
            tv_log = ttk.Treeview(tab_auditoria, columns=("DH", "U", "A", "D", "M"), show='headings')
            tv_log.heading("DH", text="Data/Hora"); tv_log.column("DH", width=140)
            tv_log.heading("U", text="Usuário"); tv_log.column("U", width=100)
            tv_log.heading("A", text="Ação"); tv_log.column("A", width=150)
            tv_log.heading("D", text="Detalhes"); tv_log.column("D", width=350)
            tv_log.heading("M", text="Máquina"); tv_log.column("M", width=100)
            tv_log.pack(fill="both", expand=True, padx=10, pady=10)
            self.configurar_tags_tabela(tv_log)

            for i, log in enumerate(self.core.get_logs()):
                tag = 'odd' if i % 2 != 0 else 'even'
                tv_log.insert("", "end", values=(log['data_hora'], log['usuario'], log['acao'], log['detalhes'], log['maquina']), tags=(tag,))

    def config_user_view(self):
        f = ctk.CTkFrame(self.main_frame, width=400); f.pack(pady=50, ipady=20)
        ctk.CTkLabel(f, text="Alterar Minha Senha", font=("Arial", 16, "bold")).pack(pady=15)
        
        ep = ctk.CTkEntry(f, placeholder_text="Nova Senha", show="*", width=250); ep.pack(pady=10)
        epc = ctk.CTkEntry(f, placeholder_text="Confirmar Nova Senha", show="*", width=250); epc.pack(pady=10)
        
        def save_pass(event=None):
            p1 = ep.get()
            p2 = epc.get()
            if not p1: return
            if p1 != p2:
                messagebox.showerror("Erro", "As senhas não coincidem.")
                return
            
            u = self.current_user
            self.core.salvar_usuario(u['username'], p1, u['is_admin'], u['can_change_dates'], u.get('can_manage_products', 0), u['username'])
            messagebox.showinfo("Sucesso", "Senha alterada com sucesso!")
            ep.delete(0, 'end'); epc.delete(0, 'end')
            
        epc.bind("<Return>", save_pass)
        ctk.CTkButton(f, text="Atualizar Senha", command=save_pass, fg_color=self.colors["verde"]).pack(pady=20)

    # =========================================================================
    # 9. JANELAS DE DIÁLOGO (POPUPS & TOPLEVELS)
    # =========================================================================
    def janela_novo_lancamento_central(self):
        jan = ctk.CTkToplevel(self); jan.title("Novo Lançamento"); jan.geometry("500x650")
        jan.transient(self); jan.lift(); jan.focus_force()
        jan.after(100, lambda: [jan.grab_set(), jan.focus_force()])
        
        ctk.CTkLabel(jan, text="1. Selecione o Cliente", font=("Arial", 14, "bold")).pack(pady=5)
        
        f_busca = ctk.CTkFrame(jan, fg_color="transparent"); f_busca.pack(fill="x", padx=10)
        e_busca = ctk.CTkEntry(f_busca, placeholder_text="Nome ou CPF/CNPJ"); e_busca.pack(side="left", fill="x", expand=True, padx=5)
        
        # Treeview pequena para resultados
        tv_res = ttk.Treeview(jan, columns=("N", "D"), show="headings", height=5)
        tv_res.heading("N", text="Nome"); tv_res.column("N", width=250)
        tv_res.heading("D", text="Documento"); tv_res.column("D", width=150)
        tv_res.pack(fill="x", padx=10, pady=5)
        
        def buscar(e=None):
            tv_res.delete(*tv_res.get_children())
            for h in self.core.buscar_filtrado(e_busca.get()):
                tv_res.insert("", "end", values=(h[0], h[1]))
        
        ctk.CTkButton(f_busca, text="🔍", width=40, command=buscar).pack(side="left")
        e_busca.bind("<Return>", buscar)
        
        # Frame de Detalhes
        f_detalhes = ctk.CTkFrame(jan); f_detalhes.pack(fill="both", expand=True, padx=10, pady=10)
        
        lbl_cliente = ctk.CTkLabel(f_detalhes, text="Nenhum cliente selecionado", font=("Arial", 12))
        lbl_cliente.pack(pady=5)
        
        selected_doc = ctk.StringVar(value="")
        
        def selecionar_cliente(e):
            sel = tv_res.selection()
            if not sel: return
            vals = tv_res.item(sel[0])['values']
            selected_doc.set(str(vals[1]))
            s, v, b = self.core.get_saldo_info(selected_doc.get())
            div = self.core.get_divida_multas(selected_doc.get())
            lbl_cliente.configure(text=f"Cliente: {vals[0]}\nSaldo: R$ {s:.2f} | Dívida: R$ {div:.2f}")
            
        tv_res.bind("<ButtonRelease-1>", selecionar_cliente)
        
        ctk.CTkLabel(f_detalhes, text="2. Dados do Lançamento", font=("Arial", 14, "bold")).pack(pady=5)
        
        tipo_var = ctk.StringVar(value="ENTRADA")
        f_tipo = ctk.CTkFrame(f_detalhes, fg_color="transparent"); f_tipo.pack(pady=5)
        ctk.CTkRadioButton(f_tipo, text="Crédito", variable=tipo_var, value="ENTRADA", fg_color=self.colors["verde"]).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkRadioButton(f_tipo, text="Uso (Baixa)", variable=tipo_var, value="SAIDA", fg_color=self.colors["vermelho"]).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkRadioButton(f_tipo, text="Multa", variable=tipo_var, value="MULTA", fg_color=self.colors["dourado"]).grid(row=1, column=0, padx=5, pady=5)
        ctk.CTkRadioButton(f_tipo, text="Pgto Multa", variable=tipo_var, value="PAGAMENTO_MULTA", fg_color="#27ae60").grid(row=1, column=1, padx=5, pady=5)
        
        e_valor = ctk.CTkEntry(f_detalhes, placeholder_text="Valor (R$)"); e_valor.pack(pady=5)
        e_cat = ctk.CTkComboBox(f_detalhes, values=self.core.get_categorias()); e_cat.pack(pady=5)
        e_obs = ctk.CTkTextbox(f_detalhes, height=60); e_obs.pack(pady=5, fill="x", padx=20); e_obs.insert("1.0", "Observação...")
        
        def confirmar(event=None):
            if not selected_doc.get(): messagebox.showwarning("Atenção", "Selecione um cliente primeiro."); return
            t, v, c, o, u = tipo_var.get(), e_valor.get(), e_cat.get(), e_obs.get("1.0", "end-1c"), self.current_user['username']
            try:
                if t == "ENTRADA": self.core.adicionar_movimentacao(selected_doc.get(), v, c, "ENTRADA", o, u)
                elif t == "SAIDA": self.core.adicionar_movimentacao(selected_doc.get(), v, "Uso", "SAIDA", o, u)
                elif t == "MULTA": self.core.adicionar_multa(selected_doc.get(), v, c, o, u)
                elif t == "PAGAMENTO_MULTA": self.core.pagar_multa(selected_doc.get(), v, c, o, u)
                messagebox.showinfo("Sucesso", "Lançamento realizado!"); jan.destroy(); self.tela_financeiro()
            except Exception as e: messagebox.showerror("Erro", str(e))
        
        e_valor.bind("<Return>", confirmar)
        ctk.CTkButton(f_detalhes, text="CONFIRMAR LANÇAMENTO", fg_color=self.colors["verde"], height=40, command=confirmar).pack(pady=10, fill="x", padx=20)

    def janela_calendario_vencimento(self, event, doc, nome):
        # Verificação de permissão melhorada: permite se for admin ou tiver a permissão específica
        if not self.current_user.get('is_admin') and not self.current_user.get('can_change_dates'):
            messagebox.showerror("Acesso Negado", "Você não tem permissão para alterar datas.")
            return

        from tkcalendar import DateEntry  # Importação tardia para acelerar inicialização
        item = self.tree_z.identify_row(event.y)
        if not item: return
        self.tree_z.selection_set(item)
        tp, val, dt_mov, *_ = self.tree_z.item(item)['values']
        if tp != "ENTRADA": return
        jan = ctk.CTkToplevel(self); jan.title("Ajustar Data"); jan.geometry("300x320")
        jan.transient(self); jan.lift(); jan.focus_force()
        # Garante foco e modalidade após renderização completa
        jan.after(100, lambda: [jan.grab_set(), jan.focus_force()])
        
        cal = DateEntry(jan, width=12, background='darkblue', date_pattern='dd/mm/yyyy'); cal.pack(pady=20)
        def ok(): 
            self.core.atualizar_data_vencimento_manual(str(doc), cal.get(), val, dt_mov, self.current_user['username'])
            jan.destroy(); self.tela_historico(nome, doc)
        ctk.CTkButton(jan, text="Atualizar Vencimento", command=ok).pack(pady=10)

    def janela_logs(self):
        jan = ctk.CTkToplevel(self); jan.title("Logs de Auditoria"); jan.geometry("900x500")
        jan.transient(self); jan.lift(); jan.focus_force()
        jan.after(100, lambda: [jan.grab_set(), jan.focus_force()])
        tv = ttk.Treeview(jan, columns=("DH", "U", "A", "D", "M"), show='headings')
        tv.heading("DH", text="Data/Hora"); tv.column("DH", width=140)
        tv.heading("U", text="Usuário"); tv.column("U", width=100)
        tv.heading("A", text="Ação"); tv.column("A", width=150)
        tv.heading("D", text="Detalhes"); tv.column("D", width=350)
        tv.heading("M", text="Máquina"); tv.column("M", width=100)
        tv.pack(fill="both", expand=True)
        
        for log in self.core.get_logs():
            tv.insert("", "end", values=(log['data_hora'], log['usuario'], log['acao'], log['detalhes'], log['maquina']))

    def janela_cadastro_hospede(self, doc_to_edit=None):
        jan = ctk.CTkToplevel(self); jan.geometry("400x400")
        jan.transient(self); jan.lift(); jan.focus_force()
        jan.after(100, lambda: [jan.grab_set(), jan.focus_force()])

        title = "Editar Hóspede" if doc_to_edit else "Novo Hóspede"
        jan.title(title)
        ctk.CTkLabel(jan, text=title, font=("Arial", 16, "bold")).pack(pady=15)

        en = ctk.CTkEntry(jan, placeholder_text="Nome Completo", width=350); en.pack(pady=10)
        ed = ctk.CTkEntry(jan, placeholder_text="CPF ou CNPJ", width=300); ed.pack(pady=10)
        etel = ctk.CTkEntry(jan, placeholder_text="Telefone (WhatsApp)", width=300); etel.pack(pady=10)
        eemail = ctk.CTkEntry(jan, placeholder_text="E-mail", width=300); eemail.pack(pady=10)

        if doc_to_edit:
            hospede = self.core.get_hospede(doc_to_edit)
            if hospede:
                en.insert(0, hospede['nome'])
                ed.insert(0, hospede['documento'])
                ed.configure(state="disabled") # Não permite editar o documento
                etel.insert(0, hospede['telefone'] or "")
                eemail.insert(0, hospede['email'] or "")

        def salvar(event=None):
            user = self.current_user['username'] if self.current_user else "Sistema"
            try:
                self.core.cadastrar_hospede(en.get(), ed.get(), etel.get(), eemail.get(), usuario_acao=user)
                jan.destroy()
                # Atualiza a tela atual para refletir a mudança (seja a lista de hóspedes ou o histórico)
                if self.current_screen_function:
                    self.current_screen_function(*self.current_screen_args, **self.current_screen_kwargs)
            except Exception as e: messagebox.showerror("Erro", str(e))
        
        en.bind("<Return>", salvar)
        ed.bind("<Return>", salvar)
        etel.bind("<Return>", salvar)
        eemail.bind("<Return>", salvar)
        ctk.CTkButton(jan, text="Salvar", fg_color=self.colors["verde"], width=300, command=salvar).pack(pady=20)

    def _janela_movimentacao(self, title, doc, nome, tipo_mov, callback):
        jan = ctk.CTkToplevel(self); jan.title(title); jan.geometry("350x350")
        jan.transient(self); jan.lift(); jan.focus_force()
        jan.after(100, lambda: [jan.grab_set(), jan.focus_force()])
        ctk.CTkLabel(jan, text=title, font=("Arial", 16, "bold")).pack(pady=15)
        
        ev = ctk.CTkEntry(jan, placeholder_text="Valor (R$)", width=250); ev.pack(pady=10)
        
        label_cat = "Categoria"
        if tipo_mov == "MULTA": label_cat = "Motivo"
        elif tipo_mov == "PAGAMENTO_MULTA": label_cat = "Forma de Pagamento"
        
        ec = ctk.CTkComboBox(jan, values=self.core.get_categorias(), width=250) if tipo_mov == "ENTRADA" else ctk.CTkEntry(jan, placeholder_text=label_cat, width=250)
        ec.pack(pady=10)
        
        eo = ctk.CTkTextbox(jan, width=250, height=60); eo.pack(pady=10)
        
        def salvar(event=None):
            user = self.current_user['username']
            try:
                callback(doc, ev.get(), ec.get(), eo.get("1.0", "end-1c"), user)
                jan.destroy()
                self.tela_historico(nome, doc)
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=jan)

        ev.bind("<Return>", salvar)
        ctk.CTkButton(jan, text="Confirmar", command=salvar, fg_color=self.colors["verde"]).pack(pady=10)

    def janela_add_credito(self, doc, nome):
        def cb(d, v, c, o, u): self.core.adicionar_movimentacao(d, v, c, "ENTRADA", o, u)
        self._janela_movimentacao("Adicionar Crédito", doc, nome, "ENTRADA", cb)

    def janela_usar_credito(self, doc, nome):
        def cb(d, v, c, o, u): self.core.adicionar_movimentacao(d, v, "Uso", "SAIDA", o, u)
        self._janela_movimentacao("Utilizar Crédito", doc, nome, "SAIDA", cb)

    def janela_add_multa(self, doc, nome):
        def cb(d, v, m, o, u): self.core.adicionar_multa(d, v, m, o, u)
        self._janela_movimentacao("Adicionar Multa", doc, nome, "MULTA", cb)

    def janela_pagar_multa(self, doc, nome):
        def cb(d, v, m, o, u): self.core.pagar_multa(d, v, m, o, u)
        self._janela_movimentacao("Pagar Multa", doc, nome, "PAGAMENTO_MULTA", cb)

if __name__ == "__main__":
    AppHotelLTS().mainloop()