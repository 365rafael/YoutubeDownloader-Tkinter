import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import time
import os
from datetime import datetime
from pytubefix import YouTube
from pytubefix.exceptions import RegexMatchError, VideoUnavailable, MembersOnly, LiveStreamError
import re


class YouTubeConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor YouTube para MP4/MP3 - PytubeFix")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Variáveis de controle
        self.downloading = False
        self.current_progress = 0
        self.yt = None

        # Configurar estilo
        self.setup_styles()

        # Criar interface
        self.create_widgets()

        # Carregar ícone (se disponível)
        self.setup_icons()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Configurar cores
        bg_color = "#f0f0f0"
        accent_color = "#ff0000"  # Vermelho YouTube

        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, font=("Arial", 10))
        style.configure("Header.TLabel", background=accent_color, foreground="white",
                        font=("Arial", 14, "bold"), padding=10)
        style.configure("TButton", font=("Arial", 10))
        style.configure("Red.TButton", background=accent_color, foreground="white")
        style.configure("TEntry", font=("Arial", 10))
        style.configure("TCombobox", font=("Arial", 10))
        style.configure("Horizontal.TProgressbar", background=accent_color)

    def setup_icons(self):
        # Ícones simples usando texto
        self.icons = {
            "youtube": "🎬",
            "download": "⬇️",
            "success": "✅",
            "error": "❌"
        }

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar expansão
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Cabeçalho
        header = ttk.Frame(main_frame)
        header.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Logo do YouTube
        # youtube_logo = ttk.Label(header, text=f"{self.icons['youtube']} YouTube Converter",
        #                          font=("Arial", 20, "bold"), foreground="red")
        # youtube_logo.pack(side=tk.LEFT)

        # Entrada de URL
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(1, weight=1)

        ttk.Label(url_frame, text="URL do YouTube:", font=("Arial", 11)).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Arial", 11))
        url_entry.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Opções de conversão
        options_frame = ttk.LabelFrame(main_frame, text="Opções de Conversão", padding="10")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="Formato:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="MP3")
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_var,
                                    values=["MP3", "MP4"], state="readonly", width=10)
        format_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        format_combo.bind("<<ComboboxSelected>>", self.on_format_change)

        ttk.Label(options_frame, text="Qualidade:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.StringVar(value="alta")
        self.quality_combo = ttk.Combobox(options_frame, textvariable=self.quality_var,
                                          state="readonly", width=15)
        self.quality_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        ttk.Label(options_frame, text="Pasta de destino:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.folder_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        folder_entry = ttk.Entry(options_frame, textvariable=self.folder_var)
        folder_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Button(options_frame, text="Procurar", command=self.browse_folder).grid(
            row=2, column=2, sticky=tk.W, pady=5, padx=(5, 0))

        # Informações do vídeo
        info_frame = ttk.LabelFrame(main_frame, text="Informações do Vídeo", padding="10")
        info_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)

        # Thumbnail (placeholder)
        self.thumbnail_label = ttk.Label(info_frame, text="🖼️", font=("Arial", 40))
        self.thumbnail_label.grid(row=0, column=0, rowspan=4, padx=(0, 10))

        self.video_title = ttk.Label(info_frame, text="Nenhum vídeo selecionado",
                                     font=("Arial", 11, "bold"), wraplength=400)
        self.video_title.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))

        info_text = ttk.Frame(info_frame)
        info_text.grid(row=1, column=1, sticky=(tk.W, tk.E))

        ttk.Label(info_text, text="Duração:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.video_duration = ttk.Label(info_text, text="--:--")
        self.video_duration.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5, 0))

        ttk.Label(info_text, text="Canal:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.video_channel = ttk.Label(info_text, text="---")
        self.video_channel.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 0))

        ttk.Label(info_text, text="Visualizações:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.video_views = ttk.Label(info_text, text="---")
        self.video_views.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(5, 0))

        ttk.Label(info_text, text="Data de publicação:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.video_publish = ttk.Label(info_text, text="---")
        self.video_publish.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(5, 0))

        # Barra de progresso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                       maximum=100, style="Horizontal.TProgressbar")
        progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="Pronto para converter")
        self.progress_label.pack()

        # Botões de ação
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(0, 10))

        self.info_btn = ttk.Button(button_frame, text="Obter Informações",
                                   command=self.get_video_info)
        self.info_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.convert_btn = ttk.Button(button_frame, text="Converter", style="Red.TButton",
                                      command=self.start_conversion)
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_btn = ttk.Button(button_frame, text="Cancelar",
                                     command=self.cancel_conversion, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT)

        # Histórico de conversões
        history_frame = ttk.LabelFrame(main_frame, text="Últimas Conversões", padding="10")
        history_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        # Treeview para histórico
        columns = ("date", "title", "format", "status")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=4)

        self.history_tree.heading("date", text="Data")
        self.history_tree.heading("title", text="Título")
        self.history_tree.heading("format", text="Formato")
        self.history_tree.heading("status", text="Status")

        self.history_tree.column("date", width=120)
        self.history_tree.column("title", width=250)
        self.history_tree.column("format", width=60)
        self.history_tree.column("status", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Configurar expansão
        main_frame.rowconfigure(6, weight=1)

        # Bind events
        url_entry.bind("<Return>", lambda e: self.get_video_info())

    def on_format_change(self, event):
        """Atualiza as opções de qualidade quando o formato muda"""
        if self.format_var.get() == "MP3":
            self.quality_combo['values'] = ["alta", "média", "baixa"]
            self.quality_var.set("alta")
        else:
            self.quality_combo['values'] = ["maxima", "alta", "media", "baixa"]
            self.quality_var.set("alta")

    def is_valid_youtube_url(self, url):
        """Verifica se a URL é do YouTube"""
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')

        return re.match(youtube_regex, url) is not None

    def get_video_info(self):
        """Obtém informações reais do vídeo usando pytubefix"""
        url = self.url_var.get().strip()

        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL do YouTube.")
            return

        if not self.is_valid_youtube_url(url):
            messagebox.showerror("Erro", "URL do YouTube inválida.")
            return

        try:
            self.progress_label.config(text="Conectando ao YouTube...")
            self.progress_var.set(10)

            # Criar objeto YouTube
            self.yt = YouTube(
                url,
                on_progress_callback=self.on_progress,
                on_complete_callback=self.on_complete
            )

            # Atualizar informações na interface
            self.video_title.config(text=self.yt.title)

            # Converter duração para formato legível
            minutes, seconds = divmod(self.yt.length, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration = f"{minutes}:{seconds:02d}"

            self.video_duration.config(text=duration)
            self.video_channel.config(text=self.yt.author)
            self.video_views.config(text=f"{self.yt.views:,} visualizações")

            # Formatar data de publicação
            publish_date = self.yt.publish_date.strftime("%d/%m/%Y") if self.yt.publish_date else "Desconhecida"
            self.video_publish.config(text=publish_date)

            # Atualizar opções de qualidade baseadas no formato
            self.on_format_change(None)

            self.progress_var.set(100)
            self.progress_label.config(text="Informações obtidas com sucesso!")

        except RegexMatchError:
            messagebox.showerror("Erro", "Não foi possível processar a URL do YouTube.")
        except VideoUnavailable:
            messagebox.showerror("Erro", "O vídeo não está disponível.")
        except MembersOnly:
            messagebox.showerror("Erro", "Este vídeo é apenas para membros.")
        except LiveStreamError:
            messagebox.showerror("Erro", "Não é possível baixar transmissões ao vivo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")

    def browse_folder(self):
        """Abre diálogo para selecionar pasta de destino"""
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)

    def start_conversion(self):
        """Inicia o processo de conversão real"""
        if not self.yt:
            messagebox.showerror("Erro", "Primeiro obtenha as informações do vídeo.")
            return

        if self.downloading:
            messagebox.showwarning("Aviso", "Já existe uma conversão em andamento.")
            return

        # Iniciar conversão em thread separada
        self.downloading = True
        self.progress_var.set(0)
        self.progress_label.config(text="Preparando para converter...")

        # Atualizar estado dos botões
        self.info_btn.config(state=tk.DISABLED)
        self.convert_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)

        # Executar em thread separada para não travar a interface
        thread = threading.Thread(target=self.download_video)
        thread.daemon = True
        thread.start()

    def download_video(self):
        """Faz o download real do vídeo usando pytubefix"""
        try:
            download_folder = self.folder_var.get()
            format_type = self.format_var.get()

            if format_type == "MP3":
                # Baixar como áudio
                stream = self.yt.streams.get_audio_only()
                filename = f"{self.clean_filename(self.yt.title)}.mp3"
            else:
                # Baixar como vídeo
                quality = self.quality_var.get()
                if quality == "maxima":
                    stream = self.yt.streams.get_highest_resolution()
                else:
                    stream = self.yt.streams.filter(progressive=True, file_extension='mp4').order_by(
                        'resolution').desc().first()

                filename = f"{self.clean_filename(self.yt.title)}.mp4"

            # Criar pasta se não existir
            os.makedirs(download_folder, exist_ok=True)
            filepath = os.path.join(download_folder, filename)

            # Fazer download
            self.progress_label.config(text="Iniciando download...")
            stream.download(output_path=download_folder, filename=filename)

            # Se for MP3, precisamos converter (o pytube já baixa como MP4 mesmo para áudio)
            if format_type == "MP3" and filepath.endswith('.mp4'):
                mp3_path = filepath.replace('.mp4', '.mp3')
                os.rename(filepath, mp3_path)

            # Adicionar ao histórico
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
            title = self.yt.title[:30] + "..." if len(self.yt.title) > 30 else self.yt.title

            self.history_tree.insert("", tk.END, values=(
                current_time, title, format_type, "Concluído"
            ))

            self.progress_label.config(text="Download concluído com sucesso!")
            messagebox.showinfo("Sucesso", f"Download concluído!\nArquivo salvo em: {download_folder}")

        except Exception as e:
            self.progress_label.config(text=f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Ocorreu um erro durante o download: {str(e)}")

        finally:
            self.downloading = False
            self.progress_var.set(0)

            # Reabilitar botões
            self.root.after(100, self.enable_buttons)

    def clean_filename(self, filename):
        """Remove caracteres inválidos para nomes de arquivo"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

    def on_progress(self, stream, chunk, bytes_remaining):
        """Callback de progresso do download"""
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100

        self.progress_var.set(percentage)
        self.progress_label.config(text=f"Baixando: {int(percentage)}%")

    def on_complete(self, stream, file_path):
        """Callback de conclusão do download"""
        self.progress_var.set(100)
        self.progress_label.config(text="Download concluído!")

    def enable_buttons(self):
        """Reabilita os botões após a conversão"""
        self.info_btn.config(state=tk.NORMAL)
        self.convert_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

    def cancel_conversion(self):
        """Cancela a conversão em andamento"""
        if self.downloading:
            self.downloading = False
            self.progress_label.config(text="Conversão cancelada.")
            self.progress_var.set(0)

            # Reabilitar botões
            self.enable_buttons()


def main():
    root = tk.Tk()
    app = YouTubeConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()