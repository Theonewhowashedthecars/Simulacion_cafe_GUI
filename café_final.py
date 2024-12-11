from tkinter import Tk, Canvas, Label, Button, Entry, ttk, Text, Scrollbar, Frame, filedialog
import ipaddress
import random
import time
import math
import csv

# Inicializar red y rango DHCP
network = ipaddress.ip_network("192.168.1.0/24")
dhcp_range_start = ipaddress.IPv4Address("192.168.1.100")
dhcp_range_end = ipaddress.IPv4Address("192.168.1.200")
all_ips = list(network.hosts())
dhcp_range = [ip for ip in all_ips if dhcp_range_start <= ip <= dhcp_range_end]

# Diccionario para dispositivos
assigned_ips = {}  # {device_name: (ip, expiration_time)}

# Lista de dispositivos predefinidos
available_devices = [f"Device_{i}" for i in range(1, 21)]

# Función para registrar logs visuales
def log_event(message):
    log_text.insert("end", f"{time.ctime()}: {message}\n")
    log_text.see("end")  # Desplazar el texto hacia abajo automáticamente
    write_log(message)

# Función para escribir logs en archivo
def write_log(message):
    with open("C:/Users/bamba/OneDrive/Escritorio/dhcp_logs.txt", "a") as log_file:
        log_file.write(f"{time.ctime()}: {message}\n")

# Función para asignar IP
def assign_ip(device_name):
    if len(dhcp_range) > 0 and device_name not in assigned_ips:
        ip = random.choice(dhcp_range)
        dhcp_range.remove(ip)
        assigned_ips[device_name] = (ip, time.time() + 600)
        log_event(f"IP {ip} asignada a {device_name}.")
        update_topology()
        return ip
    return "No hay más IPs disponibles o el dispositivo ya tiene una IP."

# Función para liberar IP
def release_ip(device_name):
    if device_name in assigned_ips:
        ip, _ = assigned_ips.pop(device_name)
        dhcp_range.append(ip)
        log_event(f"IP {ip} liberada por {device_name}.")
        update_topology()
        return True
    return False

# Función para asignar un dispositivo manualmente
def assign_manual():
    device_name = manual_entry.get()
    if device_name:
        result = assign_ip(device_name)
        if result != "No hay más IPs disponibles o el dispositivo ya tiene una IP.":
            log_event(f"Dispositivo '{device_name}' asignado manualmente.")

# Función para asignar un dispositivo desde la lista
def assign_from_list():
    device_name = device_list.get()
    if device_name:
        result = assign_ip(device_name)
        if result != "No hay más IPs disponibles o el dispositivo ya tiene una IP.":
            log_event(f"Dispositivo '{device_name}' asignado desde lista.")

# Función para liberar un dispositivo manualmente
def release_manual():
    device_name = release_entry.get()
    if device_name:
        if release_ip(device_name):
            table.delete(device_name)
            log_event(f"Dispositivo '{device_name}' liberado manualmente.")

# Actualizar GUI de la tabla
def update_gui():
    for device, (ip, expiration) in assigned_ips.items():
        remaining_time = max(0, int(expiration - time.time()))
        if table.exists(device):
            table.item(device, values=(device, str(ip), f"{remaining_time}s"))
        else:
            table.insert("", "end", iid=device, values=(device, str(ip), f"{remaining_time}s"))
    root.after(1000, update_gui)

# Mostrar información al pasar el cursor
def show_device_info(event):
    for device_name, (ip, expiration) in assigned_ips.items():
        x, y = device_positions.get(device_name, (None, None))
        if x is not None and y is not None:
            # Verificar si el cursor está cerca del dispositivo
            if abs(event.x - x) < 25 and abs(event.y - y) < 25:
                remaining_time = max(0, int(expiration - time.time()))
                info_label.config(text=f"{device_name}\nIP: {ip}\nTiempo Restante: {remaining_time}s")
                info_label.place(x=event.x + 10, y=event.y + 10)
                return
    info_label.place_forget()  # Oculta la etiqueta si no está sobre un dispositivo

# Actualizar topología de red
device_positions = {}  # Posiciones de los dispositivos
def update_topology():
    canvas.delete("all")  # Limpia el canvas
    # Dibujar el switch central
    canvas.create_oval(250, 150, 350, 250, fill="lightblue", outline="black", tags="switch")
    canvas.create_text(300, 200, text="Switch", font=("Helvetica", 12), tags="switch")

    # Dibujar dispositivos conectados
    angle_step = 360 // max(1, len(assigned_ips))  # Evita dividir entre 0
    for i, (device_name, (ip, _)) in enumerate(assigned_ips.items()):
        angle = i * angle_step
        x = 300 + 150 * math.cos(math.radians(angle))
        y = 200 + 150 * math.sin(math.radians(angle))
        device_positions[device_name] = (x, y)
        
        # Verifica el estado del dispositivo para definir el color
        remaining_time = max(0, int(assigned_ips[device_name][1] - time.time()))
        if remaining_time <= 0:
            color = "red"  # Desconectado
        elif remaining_time <= 120:
            color = "yellow"  # Tiempo bajo
        else:
            color = "green"  # Conectado

        canvas.create_rectangle(x - 25, y - 25, x + 25, y + 25, fill=color, outline="black", tags=device_name)
        canvas.create_text(x, y, text=device_name, font=("Helvetica", 10), tags=device_name)
        canvas.create_line(300, 200, x, y, fill="gray", tags="line")

# Actualizar el reloj
def update_clock():
    current_time = time.strftime("%H:%M:%S")
    clock_label.config(text=f"Hora Actual: {current_time}")
    root.after(1000, update_clock)

# Generar reporte en CSV
def generate_csv_report():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not file_path:
        return  # El usuario canceló la selección

    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Dispositivo", "Dirección IP", "Tiempo Restante"])
        for device, (ip, expiration) in assigned_ips.items():
            remaining_time = max(0, int(expiration - time.time()))
            writer.writerow([device, ip, f"{remaining_time}s"])

    log_event(f"Reporte CSV generado en: {file_path}")

# Simular fallos de red
def simulate_network_failure():
    if assigned_ips:
        failed_device = random.choice(list(assigned_ips.keys()))
        release_ip(failed_device)
        table.delete(failed_device)
        log_event(f"Fallo de red: {failed_device} desconectado.")

# GUI Principal
root = Tk()
root.title("Simulación DHCP con Topología de Red")

# Reloj en tiempo real
clock_label = Label(root, text="Hora Actual: --:--:--", font=("Helvetica", 14))
clock_label.pack()

# Tabla principal
columns = ("Device", "IP", "Time Remaining")
table = ttk.Treeview(root, columns=columns, show="headings")
table.heading("Device", text="Dispositivo")
table.heading("IP", text="Dirección IP")
table.heading("Time Remaining", text="Tiempo Restante")
table.pack(fill="both", expand=True)

# Canvas para la topología
canvas = Canvas(root, width=600, height=400, bg="white")
canvas.pack()

# Etiqueta para mostrar información
info_label = Label(canvas, text="", bg="yellow", font=("Helvetica", 10), relief="solid")

# Área de logs visuales
Label(root, text="Logs de Actividad:").pack()
log_frame = ttk.Frame(root)
log_frame.pack(fill="both", expand=True)
log_scrollbar = Scrollbar(log_frame)
log_scrollbar.pack(side="right", fill="y")
log_text = Text(log_frame, height=10, wrap="word", yscrollcommand=log_scrollbar.set)
log_text.pack(fill="both", expand=True)
log_scrollbar.config(command=log_text.yview)

# Botones organizados horizontalmente
button_frame = Frame(root)
button_frame.pack(fill="x")

Label(button_frame, text="Dispositivo:").pack(side="left", padx=5)
manual_entry = Entry(button_frame)
manual_entry.pack(side="left", padx=5)
assign_button_manual = Button(button_frame, text="Asignar Manual", command=assign_manual)
assign_button_manual.pack(side="left", padx=5)

Label(button_frame, text="Desde Lista:").pack(side="left", padx=5)
device_list = ttk.Combobox(button_frame, values=available_devices)
device_list.pack(side="left", padx=5)
assign_button_list = Button(button_frame, text="Asignar Lista", command=assign_from_list)
assign_button_list.pack(side="left", padx=5)

Label(button_frame, text="Liberar:").pack(side="left", padx=5)
release_entry = Entry(button_frame)
release_entry.pack(side="left", padx=5)
release_button = Button(button_frame, text="Liberar", command=release_manual)
release_button.pack(side="left", padx=5)

# Botones adicionales
csv_button = Button(button_frame, text="Generar Reporte CSV", command=generate_csv_report)
csv_button.pack(side="left", padx=5)
failure_button = Button(button_frame, text="Simular Falla de Red", command=simulate_network_failure)
failure_button.pack(side="left", padx=5)

# Vincular evento para mostrar información
canvas.bind("<Motion>", show_device_info)

# Iniciar actualizaciones
update_gui()
update_clock()
update_topology()

root.mainloop()