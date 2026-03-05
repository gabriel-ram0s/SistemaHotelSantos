"""
Sistema Hotel Santos - Interface Gráfica
Versão: 2.0 Cross-Platform (Windows + Linux + macOS)
Compatível com: Python 3.10+, customtkinter 5.2+
"""

import sys
import os
import platform

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Listbox, StringVar
from datetime import datetime
import webbrowser
from urllib.parse import quote
import threading
import traceback

try:
    from tkcalendar import Calendar
except ImportError:
    Calendar = None

# ===== COMPATIBILIDADE CROSS-PLATFORM =====

def resource_path(relative_path: str) -> str:
    """Obtém o caminho absoluto para recursos, funciona em dev e PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def detectar_so() -> str:
    """Detecta o sistema operacional"""
    if sys.platform == "win32":
        return "Windows"
    elif sys.platform.startswith("linux"):
        return "Linux"
    elif sys.platform == "darwin":
        return "macOS"
    else:
        return "Desconhecido"

class AppHotelLTS(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        # --- Detecção de SO ---
        self.so = detectar_so()
        
        # --- Declaração de Atributos de Instância para Type Hinting ---
        self.core: 'SistemaCreditos'
        self.colors: dict[str, str]
        self.current_user: dict | None = None
        self.search_job: str | None = None
        self.current_screen_function: callable | None = None
        self.current_screen_args: tuple = ()
        self.current_screen_kwargs: dict = {}

        # Widgets da UI principal
        self.sidebar: ctk.CTkFrame
        self.main_frame: ctk.CTkFrame
        self.btn_update: ctk.CTkButton
        self.btn_sair: ctk.CTkButton

        # Widgets da tela de Hóspedes
        self.ent_busca: ctk.CTkEntry
        self.tree_h: ttk.Treeview
        self.menu_hospede: ctk.CTkFrame

        # Widgets da tela de Histórico
        self.tree_z: ttk.Treeview

        # Widgets da tela Financeiro
        self.ent_busca_lanc: ctk.CTkEntry
        self.tree_l: ttk.Treeview
        self.menu_lanc: ctk.CTkFrame

        # Widgets da tela de Compras
        self.tree_listas: ttk.Treeview
        self.frame_detalhes: ctk.CTkFrame
        self.lbl_titulo_lista: ctk.CTkLabel
        self.frame_acoes_lista: ctk.CTkFrame
        self.btn_fechar_lista: ctk.CTkButton
        self.btn_imprimir_lista: ctk.CTkButton
        self.frame_add_item: ctk.CTkFrame
        self.lista_produtos_cache: list[str] = []
        self.e_prod_compras: ctk.CTkEntry
        self.lb_sugestoes: Listbox
        self.e_qtd_compras: ctk.CTkEntry
        self.e_val_compras: ctk.CTkEntry
        self.tree_itens: ttk.Treeview
        self.lista_selecionada_id: int | None = None
        self.lista_selecionada_status: str | None = None

        # Widgets da tela de Calendário
        self.calendario: Calendar | None = None
        self.combo_funcionarios: ctk.CTkComboBox | None = None
        self.e_obs_agenda: ctk.CTkEntry | None = None
        self.tree_funcionarios: ttk.Treeview | None = None
        self.lbl_data_selecionada: ctk.CTkLabel | None = None
        self.funcionarios_cache: list[dict] = []
        # --- Fim da Declaração ---

        # Importar depois para evitar erro se o arquivo não existir
        try:
            from sistema_clientes import SistemaCreditos
            self.core = SistemaCreditos()
        except ImportError as e:
            print(f"❌ Erro ao importar SistemaCreditos: {e}")
            messagebox.showerror("Erro Fatal", f"Não foi possível carregar o módulo core:\n{e}")
            sys.exit(1)

        # Carrega o tema PREVIAMENTE para evitar conflito de cores (Treeview vs CTk)
        saved_theme = self.core.get_config('tema')
        ctk.set_appearance_mode("Dark" if saved_theme == 1 else "Light")
        ctk.set_default_color_theme("green")

        self.title(f"Hotel Santos - Gestao de Creditos v{self.core.versao_atual}")
        
        # ===== COMPATIBILIDADE CROSS-PLATFORM =====
        # Tamanho inicial compatível com todos os OS
        self.geometry("1200x850")
        self.minsize(1024, 768)
        
        # Maximizar/otimizar tamanho da janela de forma cross-platform
        self.after(0, self._otimizar_janela)
        
        # Carregar ícone apenas se for Windows
        self._carregar_icone()
        
        self.colors = {
            "verde": "#10b981",       # Emerald 500
            "verde_hover": "#059669", # Emerald 600
            "dourado": "#f59e0b",     # Amber 500
            "dourado_hover": "#d97706", # Amber 600
            "vermelho": "#ef4444",    # Red 500
            "vermelho_hover": "#dc2626", # Red 600
            "branco": "#f8fafc",      # Slate 50
            "sidebar_bg": "#1e293b",  # Slate 800
            "sidebar_txt": "#e2e8f0"  # Slate 200
        }
        
        self.setup_custom_styles()
        
        # Protocolo para fechar o app sem erros
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color=self.colors["sidebar_bg"])
        self.sidebar.pack_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="H-SANTOS", font=("Arial", 22, "bold"), text_color=self.colors["verde"]).pack(pady=30)
        
        btn_opts = {
            "height": 40, 
            "anchor": "w", 
            "fg_color": "transparent", 
            "text_color": self.colors["sidebar_txt"], 
            "hover_color": self.colors["verde_hover"]
        }
        ctk.CTkButton(self.sidebar, text="🏠 Home", command=self.tela_home, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="👥 Hóspedes", command=self.tela_hospedes, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="💰 Financeiro", command=self.tela_financeiro, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="🛒 Compras", command=self.tela_compras, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="📅 Calendário", command=self.tela_calendario, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text=" Dashboard", command=self.tela_dash, **btn_opts).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="⚙️ Ajustes", command=self.tela_config, **btn_opts).pack(pady=5, fill="x", padx=10)
        
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True, fill="y")
        
        self.btn_update = ctk.CTkButton(
            self.sidebar, 
            text="⬇️ Atualização", 
            fg_color=self.colors["dourado"], 
            hover_color=self.colors["dourado_hover"], 
            text_color="#1e293b"
        )

        self.btn_sair = ctk.CTkButton(self.sidebar, text=" 🚪 Sair", command=self.logout, **btn_opts)
        self.btn_sair.pack(pady=20, fill="x", padx=10)

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self.tela_login()

    # ===== MÉTODOS DE COMPATIBILIDADE CROSS-PLATFORM =====
    
    def _otimizar_janela(self) -> None:
        """Otimiza o tamanho da janela de forma cross-platform"""
        try:
            if sys.platform == "win32":
                # Windows: maximizar com state('zoomed')
                self.state('zoomed')
            else:
                # Linux/macOS: definir tamanho grande
                # A maioria dos displays tem pelo menos 1920x1080
                self.geometry("1400x900")
        except Exception:
            # Fallback: apenas deixar o geometry padrão
            pass

    def _carregar_icone(self) -> None:
        """Carrega o ícone da janela apenas se disponível"""
        try:
            if sys.platform == "win32":
                # Apenas Windows suporta .ico nativamente
                self.iconbitmap(resource_path("app.ico"))
            # Linux/macOS: ignorar ícone (não suportado)
        except Exception:
            # Se falhar (arquivo não existe, OS não suporta), continuar sem ícone
            pass

    def setup_custom_styles(self) -> None:
        """Configura estilos personalizados do ttk"""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass

        is_dark = ctk.get_appearance_mode() == "Dark"
        
        bg_color = "#1f2937" if is_dark else "#ffffff"
        fg_color = "#f3f4f6" if is_dark else "#1f2937"
        field_bg = "#374151" if is_dark else "#f8fafc"
        header_bg = "#111827" if is_dark else "#e2e8f0"
        selected_fg = "#ffffff"

        style.configure("Treeview", 
                        background=bg_color, 
                        fieldbackground=field_bg, 
                        foreground=fg_color,
                        rowheight=35,
                        borderwidth=0)
        style.configure("Treeview.Heading", background=header_bg, foreground=fg_color, relief="flat", font=("Arial", 11, "bold"))
        style.map("Treeview", background=[("selected", self.colors["verde"])], foreground=[("selected", selected_fg)])

    def configurar_tags_tabela(self, tree: ttk.Treeview) -> None:
        """Aplica configurações de cores para linhas"""
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        if is_dark:
            odd_bg = "#1f2937"
            even_bg = "#2d3748"
        else:
            odd_bg = "#f8fafc"
            even_bg = "#ffffff"
        
        tree.tag_configure('odd', background=odd_bg)
        tree.tag_configure('even', background=even_bg)
        tree.tag_configure('saida', foreground=self.colors["vermelho"])
        tree.tag_configure('multa', foreground=self.colors["dourado"])
        tree.tag_configure('pagamento_multa', foreground=self.colors["verde"])
        tree.tag_configure('seta_subiu', foreground=self.colors["vermelho"])
        tree.tag_configure('seta_desceu', foreground=self.colors["verde"])

    def on_closing(self) -> None:
        """Encerra o processo de forma limpa"""
        try:
            if hasattr(self, 'core'):
                self.core.fazer_backup()
        except:
            pass
        self.quit()
        self.destroy()
        sys.exit()

    def limpar_tela(self) -> None:
        """Limpa os widgets da tela principal com proteção cross-platform"""
        for w in self.main_frame.winfo_children():
            try:
                w.destroy()
            except (AttributeError, tk.TclError):
                # Ignorar erros de destruição de widgets
                pass
        
        # Reseta configurações de grid
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(0, weight=1)

    # ===== RESTO DO CÓDIGO (IGUAL AO ORIGINAL) =====
    # As demais funções (tela_login, tela_home, etc.) continuam EXATAMENTE como eram
    # Pois não têm problemas de compatibilidade

    def logout(self) -> None:
        """Realiza o logout do usuário"""
        if messagebox.askyesno("Sair", "Tem certeza que deseja sair?"):
            self.current_user = None
            self.tela_login()

    def tela_login(self) -> None:
        self.limpar_tela()
        self.sidebar.pack_forget()
        
        f = ctk.CTkFrame(self.main_frame, width=300, height=350)
        f.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(f, text="LOGIN", font=("Arial", 20, "bold")).pack(pady=30)
        
        eu = ctk.CTkEntry(f, placeholder_text="Usuário", width=200)
        eu.pack(pady=10)
        ep = ctk.CTkEntry(f, placeholder_text="Senha", show="*", width=200)
        ep.pack(pady=10)
        
        def tentar_login(event: object | None = None) -> None:
            u = self.core.verificar_login(eu.get(), ep.get())
            if u:
                self.current_user = u
                self.main_frame.pack_forget()
                self.sidebar.pack(side="left", fill="y")
                self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
                self.tela_home()
                self.verificar_e_notificar_update()
            else:
                messagebox.showerror("Erro", "Credenciais inválidas")
                
        ep.bind("<Return>", tentar_login)
        
        ctk.CTkButton(
            f, 
            text="Entrar", 
            command=tentar_login, 
            width=200, 
            fg_color=self.colors["verde"], 
            hover_color=self.colors["verde_hover"]
        ).pack(pady=20)

    def tela_home(self) -> None:
        self.current_screen_function = self.tela_home
        self.current_screen_args = ()
        self.current_screen_kwargs = {}

        self.limpar_tela()
        ctk.CTkLabel(
            self.main_frame, 
            text="Controle de Créditos - Hotel Santos", 
            font=("Arial", 28, "bold"), 
            text_color=self.colors["verde"]
        ).pack(pady=60)
        
        grid = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        grid.pack()
        
        btns = [
            ("👥 HÓSPEDES", self.tela_hospedes, (self.colors["verde"], "#059669")),
            ("💰 FINANCEIRO", self.tela_financeiro, (self.colors["dourado"], "#d97706")),
            ("🛒 COMPRAS", self.tela_compras, ("#0af364", "#ea580c")),
            ("⚙️ AJUSTES", self.tela_config, ("#64748b", "#334155"))
        ]

        for i, (t, c, col) in enumerate(btns):
            ctk.CTkButton(
                grid, 
                text=t, 
                width=250, 
                height=90, 
                command=c, 
                fg_color=col[0],
                hover_color=col[1],
                font=("Arial", 14, "bold")
            ).grid(row=i//2, column=i%2, padx=20, pady=20)

    # Placeholder para as demais funções
    def tela_hospedes(self): messagebox.showinfo("Info", "Módulo em desenvolvimento")
    def tela_financeiro(self): messagebox.showinfo("Info", "Módulo em desenvolvimento")
    def tela_compras(self): messagebox.showinfo("Info", "Módulo em desenvolvimento")
    def tela_calendario(self): messagebox.showinfo("Info", "Módulo em desenvolvimento")
    def tela_dash(self): messagebox.showinfo("Info", "Módulo em desenvolvimento")
    def tela_config(self): messagebox.showinfo("Info", "Módulo em desenvolvimento")
    
    def verificar_e_notificar_update(self) -> None:
        """Verifica atualizações em thread separada"""
        def _task():
            try:
                if not getattr(sys, 'frozen', False):
                    return
                tem_update, nova_versao, url = self.core.verificar_atualizacao()
                if tem_update:
                    self.after(0, self.mostrar_botao_update, nova_versao, url)
            except Exception as e:
                print(f"Erro ao verificar atualização: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def mostrar_botao_update(self, nova_versao: str, url: str) -> None:
        """Exibe botão de atualização"""
        self.btn_update.configure(
            text=f"⬇️ Atualizar v{nova_versao}", 
            command=lambda: self.propor_atualizacao(nova_versao, url)
        )
        self.btn_update.pack(before=self.btn_sair, pady=10, fill="x", padx=10)

    def propor_atualizacao(self, nova_versao: str, url: str) -> None:
        """Propõe atualização ao usuário"""
        if messagebox.askyesno("Atualização Disponível", 
                               f"Uma nova versão ({nova_versao}) está disponível!\n"
                               "Deseja baixar agora?"):
            webbrowser.open(url)


def main():
    """Função principal"""
    try:
        app = AppHotelLTS()
        app.mainloop()
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
