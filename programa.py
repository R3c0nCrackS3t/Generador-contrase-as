import random
import os
import hashlib
import time
from flask import Flask, render_template, request, redirect, url_for
import tkinter as tk
from tkinter import messagebox
from pykeepass import PyKeePass

# Datos de configuración de KeePass
keepass_db_path = '[Localización de la Base de datos de Keepass]'  # Especifica la ruta de tu base de datos KeePass
keepass_password = '[Contraseña de la Base de datos de Keepass]'  # La contraseña de tu base de datos KeePass

# Lista de caracteres posibles para las contraseñas
caracteres = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()'

# Carpeta donde se guardarán los archivos
carpeta_archivos = 'archivos'
if not os.path.exists(carpeta_archivos):
    os.makedirs(carpeta_archivos)

# Archivos para las contraseñas usadas y su información de uso
passwords_file = os.path.join(carpeta_archivos, 'contraseñas_guardadas.txt')
uso_file = os.path.join(carpeta_archivos, 'uso_contraseñas.txt')
hash_file = os.path.join(carpeta_archivos, 'hash_registro.txt')

# Función para guardar una contraseña en el archivo de contraseñas usadas
def guardar_contraseña(password):
    with open(passwords_file, 'a') as f:
        f.write(password + '\n')

# Función para verificar si una contraseña ya ha sido usada
def password_existente(password):
    if os.path.exists(passwords_file):
        with open(passwords_file, 'r') as f:
            passwords_guardadas = f.read().splitlines()
            return password in passwords_guardadas
    return False

# Función para generar el hash de un archivo
def generar_hash(archivo):
    hash_md5 = hashlib.md5()
    with open(archivo, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Función para guardar el hash de un archivo
def guardar_hash(archivo):
    hash_valor = generar_hash(archivo)
    with open(hash_file, 'a') as f:
        f.write(f"{archivo} - {hash_valor} - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    limpiar_hashes()

# Función para mantener solo los últimos 5 hashes en el archivo
def limpiar_hashes():
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            lineas = f.readlines()
        if len(lineas) > 5:
            with open(hash_file, 'w') as f:
                f.writelines(lineas[-5:])  # Mantener solo las 5 últimas entradas

# Función para generar una nueva contraseña
def generar_password(longitud):
    while True:
        password = ''.join(random.choices(caracteres, k=longitud))
        if not password_existente(password):
            guardar_contraseña(password)
            guardar_hash(passwords_file)
            return password

# Función para guardar la contraseña en KeePass
def guardar_en_keepass(sitio, password):
    kp = PyKeePass(keepass_db_path, password=keepass_password)
    kp.add_entry(kp.root_group, sitio, sitio, password)
    kp.save()

# Crear la aplicación Flask
app = Flask(__name__)

# Ruta principal para manejar la generación de contraseñas
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            longitud = int(request.form['longitud'])
            if 8 <= longitud <= 30:
                password = generar_password(longitud)
                return render_template('index.html', password=password)
            else:
                return render_template('index.html', error="Debe ingresar un número entre 8 y 30.")
        except ValueError:
            return render_template('index.html', error="Debe ingresar un número válido.")
    return render_template('index.html')

# Ruta para copiar la contraseña y registrar su uso
@app.route('/copiar/<password>', methods=['GET', 'POST'])
def copiar_password(password):
    if request.method == 'POST':
        usar = request.form['usar'].lower()
        if usar == 'si':
            sitio = request.form['sitio']
            with open(uso_file, 'a') as f:
                f.write(f"{sitio} - {password}\n")
            guardar_hash(uso_file)
            guardar_en_keepass(sitio, password)  # Guardar en KeePass
        return redirect(url_for('index'))
    return render_template('copiar.html', password=password)

# Función para lanzar la interfaz Tkinter
def iniciar_gui():
    def generar():
        try:
            longitud = int(entry.get())
            if 8 <= longitud <= 30:
                password = generar_password(longitud)
                resultado.config(text=f"Contraseña: {password}")
            else:
                messagebox.showerror("Error", "Debe ingresar un número entre 8 y 30.")
        except ValueError:
            messagebox.showerror("Error", "Debe ingresar un número válido.")

    root = tk.Tk()
    root.title("Generador de Contraseñas")

    label = tk.Label(root, text="Introduce el número de caracteres (8-30):")
    label.pack()

    entry = tk.Entry(root)
    entry.pack()

    boton = tk.Button(root, text="Generar Contraseña", command=generar)
    boton.pack()

    resultado = tk.Label(root, text="")
    resultado.pack()

    root.mainloop()

if __name__ == '__main__':
    opcion = input("¿Deseas iniciar en modo web (Flask) o interfaz gráfica (Tkinter)? (web/gui): ").strip().lower()
    if opcion == 'web':
        app.run(debug=True)
    elif opcion == 'gui':
        iniciar_gui()
    else:
        print("Opción no válida. Elige 'web' o 'gui'.")
