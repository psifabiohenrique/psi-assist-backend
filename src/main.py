#!/usr/bin/env python
"""
Script principal para executar o PSI Assist Backend como aplicação standalone.
Cria um banco de dados SQLite local, aplica migrações e inicia o servidor Django
com uma interface gráfica simples.
"""

import os
import sys
import subprocess
import webbrowser
import time
import tkinter as tk
from tkinter import messagebox, ttk
import socket
from pathlib import Path
import threading

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Adicionar o diretório do projeto ao Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

try:
    import django
    from django.core.management import execute_from_command_line
    from django.contrib.auth import get_user_model
    from django.core.management.base import BaseCommand
    from django.db import connection
except ImportError as e:
    print(f"Erro ao importar Django: {e}")
    sys.exit(1)


class PSIAssistGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PSI Assist Backend")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Centralizar janela
        self.center_window()
        
        # Variáveis de controle
        self.server_process = None
        self.server_running = False
        self.port = 8000
        
        # Configurar interface
        self.setup_ui()
        
        # Configurar fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Configura a interface gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="PSI Assist Backend", 
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status do servidor
        self.status_label = ttk.Label(
            main_frame, 
            text="Servidor: Parado", 
            font=("Arial", 12)
        )
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Indicador visual
        self.status_indicator = tk.Canvas(main_frame, width=20, height=20)
        self.status_indicator.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        self.update_status_indicator(False)
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 20))
        
        self.start_button = ttk.Button(
            button_frame, 
            text="Iniciar Servidor", 
            command=self.start_server
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="Parar Servidor", 
            command=self.stop_server,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(10, 0))
        
        # URL do servidor
        self.url_label = ttk.Label(
            main_frame, 
            text="URL: http://localhost:8000", 
            font=("Arial", 10)
        )
        self.url_label.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        # Botão para abrir no navegador
        self.browser_button = ttk.Button(
            main_frame, 
            text="Abrir no Navegador", 
            command=self.open_browser,
            state="disabled"
        )
        self.browser_button.grid(row=5, column=0, columnspan=2, pady=(0, 20))
        
        # Log de atividades
        log_label = ttk.Label(main_frame, text="Log de Atividades:")
        log_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Frame para o log com scrollbar
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=8, width=60, state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configurar redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def update_status_indicator(self, running):
        """Atualiza o indicador visual do status"""
        self.status_indicator.delete("all")
        color = "green" if running else "red"
        self.status_indicator.create_oval(2, 2, 18, 18, fill=color, outline=color)
    
    def log_message(self, message):
        """Adiciona mensagem ao log"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
    
    def find_free_port(self):
        """Encontra uma porta livre para o servidor, priorizando 8000"""
        # Tentar primeiro a porta preferida (8000)
        preferred_port = 8000
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', preferred_port))
                self.log_message(f"Porta {preferred_port} disponível - usando porta padrão")
                return preferred_port
        except OSError:
            self.log_message(f"Porta {preferred_port} ocupada - procurando alternativa...")
        
        # Se 8000 não estiver disponível, procurar nas próximas
        for port in range(8001, 8010):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    self.log_message(f"Usando porta alternativa: {port}")
                    return port
            except OSError:
                continue
        
        # Se nenhuma porta estiver disponível, retornar 8000 mesmo assim
        # (o erro será tratado na inicialização do servidor)
        self.log_message("Nenhuma porta disponível encontrada - tentando 8000 mesmo assim")
        return 8000
    
    def setup_database(self):
        """Configura o banco de dados e cria superusuário"""
        try:
            self.log_message("Configurando banco de dados...")
            
            # Configurar Django
            django.setup()
            
            # Aplicar migrações
            self.log_message("Aplicando migrações...")
            execute_from_command_line(['manage.py', 'migrate'])
            
            # Criar superusuário se não existir
            User = get_user_model()
            if not User.objects.filter(username='admin').exists():
                self.log_message("Criando superusuário padrão...")
                User.objects.create_superuser(
                    username='admin',
                    email='admin@psiassist.local',
                    password='admin123',
                    api_key='',  # Será configurado pelo usuário
                    system_prompt='Você é um assistente especializado em psicologia.'
                )
                self.log_message("Superusuário criado: admin/admin123")
            else:
                self.log_message("Superusuário já existe")
            
            return True
            
        except Exception as e:
            self.log_message(f"Erro ao configurar banco: {str(e)}")
            return False
    
    def start_server(self):
        """Inicia o servidor Django usando subprocess"""
        if self.server_running:
            return
        
        self.log_message("Iniciando servidor...")
        
        # Configurar banco de dados
        if not self.setup_database():
            messagebox.showerror("Erro", "Falha ao configurar o banco de dados")
            return
        
        # Encontrar porta livre (priorizando 8000)
        self.port = self.find_free_port()
        
        try:
            # Preparar comando para executar o servidor
            manage_py_path = project_dir / "manage.py"
            
            # Comando para iniciar o servidor Django
            cmd = [
                sys.executable,  # Python executável atual
                str(manage_py_path),
                "runserver",
                f"localhost:{self.port}",
                "--noreload"  # Evita recarregamento automático
            ]
            
            # Configurar ambiente
            env = os.environ.copy()
            env['DJANGO_SETTINGS_MODULE'] = 'core.settings'
            env['PYTHONPATH'] = str(project_dir)
            
            # Iniciar processo do servidor
            self.server_process = subprocess.Popen(
                cmd,
                cwd=str(project_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.log_message(f"Processo do servidor iniciado (PID: {self.server_process.pid})")
            
            # Aguardar um pouco e verificar se o servidor está rodando
            self.root.after(3000, self.check_server_status)
            
        except Exception as e:
            self.log_message(f"Erro ao iniciar servidor: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao iniciar servidor: {str(e)}")
    
    def check_server_status(self):
        """Verifica se o servidor está rodando"""
        try:
            # Verificar se o processo ainda está vivo
            if self.server_process and self.server_process.poll() is None:
                # Tentar conectar na porta
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', self.port))
                    if result == 0:
                        # Servidor está respondendo
                        self.server_running = True
                        self.status_label.config(text=f"Servidor: Rodando na porta {self.port}")
                        self.update_status_indicator(True)
                        self.start_button.config(state="disabled")
                        self.stop_button.config(state="normal")
                        self.browser_button.config(state="normal")
                        self.url_label.config(text=f"URL: http://localhost:{self.port}")
                        self.log_message(f"Servidor iniciado com sucesso na porta {self.port}")
                        return
            
            # Se chegou aqui, o servidor não está respondendo ainda
            # Verificar se o processo morreu
            if self.server_process and self.server_process.poll() is not None:
                # Processo terminou com erro
                stdout, stderr = self.server_process.communicate()
                error_msg = stderr.decode('utf-8') if stderr else "Erro desconhecido"
                self.log_message(f"Servidor falhou ao iniciar: {error_msg}")
                messagebox.showerror("Erro", f"Servidor falhou ao iniciar:\n{error_msg}")
                self.server_process = None
                return
            
            # Tentar novamente em 1 segundo
            self.root.after(1000, self.check_server_status)
            
        except Exception as e:
            self.log_message(f"Erro ao verificar servidor: {str(e)}")
            self.root.after(1000, self.check_server_status)
    
    def stop_server(self):
        """Para o servidor Django"""
        if not self.server_running or not self.server_process:
            return
        
        self.log_message("Parando servidor...")
        
        try:
            # Tentar terminar o processo graciosamente
            self.server_process.terminate()
            
            # Aguardar até 5 segundos para o processo terminar
            try:
                self.server_process.wait(timeout=5)
                self.log_message("Servidor parado com sucesso")
            except subprocess.TimeoutExpired:
                # Se não terminou em 5 segundos, forçar
                self.log_message("Forçando parada do servidor...")
                self.server_process.kill()
                self.server_process.wait()
                self.log_message("Servidor forçado a parar")
            
        except Exception as e:
            self.log_message(f"Erro ao parar servidor: {str(e)}")
        
        finally:
            # Resetar estado
            self.server_process = None
            self.server_running = False
            self.status_label.config(text="Servidor: Parado")
            self.update_status_indicator(False)
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.browser_button.config(state="disabled")
    
    def open_browser(self):
        """Abre o navegador na URL do servidor"""
        if self.server_running:
            url = f"http://localhost:{self.port}"
            webbrowser.open(url)
            self.log_message(f"Abrindo navegador: {url}")
    
    def on_closing(self):
        """Manipula o fechamento da janela"""
        if self.server_running:
            if messagebox.askokcancel("Sair", "O servidor está rodando. Deseja realmente sair?"):
                self.stop_server()  # Para o servidor antes de sair
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Inicia a aplicação"""
        self.log_message("PSI Assist Backend iniciado")
        self.log_message("Clique em 'Iniciar Servidor' para começar")
        self.root.mainloop()


def main():
    """Função principal"""
    try:
        app = PSIAssistGUI()
        app.run()
    except Exception as e:
        print(f"Erro fatal: {e}")
        input("Pressione Enter para sair...")


if __name__ == "__main__":
    main()