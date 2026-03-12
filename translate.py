import threading
import customtkinter as ctk

from translator import Translator, AiTranslator

def main():
    translator = AiTranslator()

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("green")

    root = ctk.CTk()
    root.title("屏幕翻译")
    root.attributes("-topmost", True)
    root.geometry("420x220")
    root.resizable(True, True)

    text_var = ctk.StringVar(value="等待识别...")
    label = ctk.CTkLabel(
        root,
        textvariable=text_var,
        font=("微软雅黑", 15),
        wraplength=380,
        justify="center",
        padx=20,
        pady=20
    )
    label.pack(fill="both", expand=True, padx=20, pady=(30, 20))

    status_var = ctk.StringVar(value="就绪")
    status_label = ctk.CTkLabel(
        root,
        textvariable=status_var,
        font=("微软雅黑", 11),
        text_color="gray"
    )
    status_label.pack(pady=(0, 8))

    th = None

    def toggle_running():
        nonlocal th
        translator.switch()

        if translator.paused():
            status_var.set("已暂停")
            status_label.configure(text_color="salmon")
            btn.configure(text="继续", fg_color="#D32F2F", hover_color="#C62828")
        else:
            status_var.set("运行中")
            status_label.configure(text_color="#4CAF50")
            btn.configure(text="暂停", fg_color="#388E3C", hover_color="#2E7D32")

            if th is None or not th.is_alive():
                th = threading.Thread(target=translator, args=(text_var,), daemon=True)
                th.start()

    button_frame = ctk.CTkFrame(root, fg_color="transparent")
    button_frame.pack(pady=(0, 20))

    btn = ctk.CTkButton(
        button_frame,
        text="开始",
        command=toggle_running,
        width=140,
        height=38,
        corner_radius=12,
        font=("微软雅黑", 13, "bold")
    )
    btn.pack(side="left", padx=10) 

    ai_mode = True

    def mode_change():
        nonlocal ai_mode, th, translator
        ai_mode = not ai_mode

        if ai_mode:
            btn1.configure(text="AI翻译")
        else:
            btn1.configure(text="机器翻译")

        was_running = not translator.paused()

        translator.close() 
        translator = AiTranslator() if ai_mode else Translator()

        if was_running:
            translator.switch()
            th = threading.Thread(target=translator, args=(text_var,), daemon=True)
            th.start()

    btn1 = ctk.CTkButton(
        button_frame,
        text="AI模式",
        command=mode_change,
        width=140, height=38,
        corner_radius=12,
        font=("微软雅黑", 13, "bold")
    )
    btn1.pack(side="left", padx=10) 

    def on_closing():
        translator.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

if __name__ == "__main__":
    main()