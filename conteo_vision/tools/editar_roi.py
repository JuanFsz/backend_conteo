import os
import django
import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk

# Inicializar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_conteo.settings')
django.setup()

from conteo_api.models import Camara, Poligono, Coordenada, Estado

# --- CONFIGURACIÓN DE TKINTER ---
root = tk.Tk()
root.title("Editor de Áreas ROI")

# Pedir ID de cámara
root.withdraw()
camara_id = simpledialog.askinteger("Seleccionar Cámara", "Ingrese el ID de la cámara:")
root.deiconify()

try:
    camara = Camara.objects.get(id=camara_id)
except Camara.DoesNotExist:
    messagebox.showerror("Error", f"Cámara con ID {camara_id} no existe.")
    exit()

VIDEO_SOURCE = camara.streaming_path
cap = cv2.VideoCapture(VIDEO_SOURCE)
paused = False
frame = None
photo = None
canvas_img = None

rois = {1: [], 2: []}
current_roi = 1

# --- FUNCIONES DE DIBUJO ---
def draw_canvas(img):
    global photo, canvas_img
    display = img.copy()
    for idx in (1, 2):
        pts = np.array(rois[idx], np.int32)
        if len(pts) > 1:
            cv2.polylines(display, [pts], True, (255, 0, 0), 2)
        for pt in rois[idx]:
            cv2.circle(display, pt, 4, (0, 255, 0), -1)
        if rois[idx]:
            cv2.putText(display, f"ROI{idx}", rois[idx][-1], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    img_rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
    photo = ImageTk.PhotoImage(Image.fromarray(img_rgb))
    canvas.create_image(0, 0, image=photo, anchor=tk.NW)
    actualizar_contador()

def on_click(event):
    global paused
    if paused:
        x, y = event.x, event.y
        rois[current_roi].append((x, y))
        draw_canvas(frame)

def deshacer_punto():
    if rois[current_roi]:
        rois[current_roi].pop()
        draw_canvas(frame)

def set_roi(n):
    global current_roi
    current_roi = n
    draw_canvas(frame)

def reset_roi():
    rois[current_roi].clear()
    draw_canvas(frame)

def actualizar_contador():
    puntos = len(rois[current_roi])
    contador_label.config(text=f"Puntos en ROI {current_roi}: {puntos}")

def guardar():
    estado, _ = Estado.objects.get_or_create(estado='activado')
    Poligono.objects.filter(camara=camara).delete()

    for idx in (1, 2):
        poligono = Poligono.objects.create(
            nombre_poligono=f"ROI{idx}_cam{camara.id}",
            camara=camara,
            estado=estado
        )
        Coordenada.objects.bulk_create([
            Coordenada(poligono=poligono, x=x, y=y) for x, y in rois[idx]
        ])

    messagebox.showinfo("Guardado", "ROIs guardados correctamente.")
    root.quit()

def salir():
    if messagebox.askyesno("Salir", "¿Salir sin guardar?"):
        root.quit()

def congelar_frame():
    global paused
    paused = not paused
    if paused:
        btn_pausa.config(text="▶️ Continuar")
    else:
        btn_pausa.config(text="⏸️ Pausar")

# --- INTERFAZ ---
canvas = tk.Canvas(root, width=1020, height=500)
canvas.pack()
canvas.bind("<Button-1>", on_click)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="ROI 1", command=lambda: set_roi(1)).grid(row=0, column=0, padx=4)
tk.Button(btn_frame, text="ROI 2", command=lambda: set_roi(2)).grid(row=0, column=1, padx=4)
tk.Button(btn_frame, text="Reset ROI", command=reset_roi).grid(row=0, column=2, padx=4)
tk.Button(btn_frame, text="Deshacer punto", command=deshacer_punto).grid(row=0, column=3, padx=4)
btn_pausa = tk.Button(btn_frame, text="⏸️ Pausar", command=congelar_frame)
btn_pausa.grid(row=0, column=4, padx=4)
tk.Button(btn_frame, text="💾 Guardar", command=guardar).grid(row=0, column=5, padx=4)
tk.Button(btn_frame, text="❌ Salir", command=salir).grid(row=0, column=6, padx=4)

contador_label = tk.Label(root, text="")
contador_label.pack()

# --- LOOP PRINCIPAL ---
def mostrar_video():
    global frame
    if not paused:
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (1020, 500))
            draw_canvas(frame)
    root.after(33, mostrar_video)

mostrar_video()
root.mainloop()
cap.release()
