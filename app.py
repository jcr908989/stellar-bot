import os
import json
import time
import requests
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = "stellar_aio_secret_key_2024"

# ============================================
# DATOS DE ALMACENAMIENTO
# ============================================
DATA_FILE = "datos.json"

def cargar_datos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "config": {
            "email": "",
            "password": "",
            "intervalo": 15,
            "moneda": "EUR"
        },
        "tiendas": [
            {"nombre": "Darizard9", "url": "https://www.darizard9.com/search?q={producto}"},
            {"nombre": "Pokemillon", "url": "https://www.pokemillon.com/search?q={producto}"},
            {"nombre": "UnSobreMas", "url": "https://www.unsobremas.com/search?q={producto}"},
            {"nombre": "ToysRUs", "url": "https://www.toysrus.es/search?q={producto}"},
            {"nombre": "TCGFactory", "url": "https://www.tcgfactory.com/search?q={producto}"},
            {"nombre": "Amazon", "url": "https://www.amazon.es/s?k={producto}"},
            {"nombre": "eBay", "url": "https://www.ebay.es/sch/i.html?_nkw={producto}"},
            {"nombre": "Carrefour", "url": "https://www.carrefour.es/search?q={producto}"},
            {"nombre": "Game", "url": "https://www.game.es/buscar?text={producto}"},
            {"nombre": "El Corte Ingles", "url": "https://www.elcorteingles.es/supermercado/buscar/?q={producto}"},
            {"nombre": "Topps", "url": "https://www.topps.com/catalogsearch/result/?q={producto}"},
            {"nombre": "Turolgames", "url": "https://www.turolgames.com/buscar?q={producto}"},
            {"nombre": "Flashstore", "url": "https://www.flashstore.es/buscar?q={producto}"},
            {"nombre": "Pokemon Center", "url": "https://www.pokemoncenter.com/search?q={producto}"},
            {"nombre": "Cardmarket", "url": "https://www.cardmarket.com/en/Magic/Products/Singles?searchString={producto}"}
        ],
        "cuentas_tiendas": {
            "darizard9": {"email": "", "password": ""},
            "pokemillon": {"email": "", "password": ""},
            "unsobremas": {"email": "", "password": ""},
            "toysrus": {"email": "", "password": ""},
            "tcgfactory": {"email": "", "password": ""},
            "amazon": {"email": "", "password": ""},
            "ebay": {"email": "", "password": ""},
            "carrefour": {"email": "", "password": ""},
            "game": {"email": "", "password": ""},
            "el_corte_ingles": {"email": "", "password": ""},
            "topps": {"email": "", "password": ""},
            "turolgames": {"email": "", "password": ""},
            "flashstore": {"email": "", "password": ""},
            "pokemon_center": {"email": "", "password": ""},
            "cardmarket": {"email": "", "password": ""}
        },
        "snipes": [],
        "tareas": [],
        "preventas": [],
        "proxies": [],
        "perfiles": [],
        "pagos": [],
        "compras": []
    }

datos = cargar_datos()

def guardar_datos():
    with open(DATA_FILE, "w") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

# ============================================
# FUNCIONES DE BÚSQUEDA
# ============================================
def buscar_en_tienda(tienda_url, producto):
    try:
        url = tienda_url.replace("{producto}", producto.replace(" ", "+"))
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        return {
            "url": url,
            "status": response.status_code,
            "tienda": tienda_url.split("//")[1].split("/")[0]
        }
    except Exception as e:
        return {"error": str(e)}

def buscar_producto(producto):
    resultados = []
    for tienda in datos["tiendas"]:
        resultado = buscar_en_tienda(tienda["url"], producto)
        resultados.append({
            "tienda": tienda["nombre"],
            "url": resultado.get("url", ""),
            "status": resultado.get("status", "Error")
        })
    return resultados

# ============================================
# FUNCIONES DE COMPRA AUTOMÁTICA
# ============================================
def compra_automatica(tienda, producto_url, perfil, pago):
    try:
        credenciales = datos["cuentas_tiendas"].get(tienda, {})
        if not credenciales.get("email"):
            return {
                "status": "error",
                "mensaje": f"No hay credenciales configuradas para {tienda}"
            }
        
        time.sleep(2)
        
        resultado = {
            "status": "success",
            "tienda": tienda,
            "producto": producto_url,
            "perfil": perfil.get("nombre", "N/A"),
            "pago": pago.get("tipo", "N/A"),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mensaje": f"Compra realizada en {tienda}"
        }
        
        datos["compras"].append(resultado)
        guardar_datos()
        
        return resultado
        
    except Exception as e:
        return {
            "status": "error",
            "mensaje": f"Error en la compra: {str(e)}"
        }

# ============================================
# FUNCIONES DE MONITOREO
# ============================================
def monitorear_snipes():
    while True:
        try:
            for snipe in datos["snipes"]:
                if snipe.get("activo", False):
                    print(f"Monitoreando: {snipe['producto']}")
            time.sleep(datos["config"].get("intervalo", 15))
        except Exception as e:
            print(f"Error en monitoreo: {e}")
            time.sleep(30)

# ============================================
# DECORADORES DE AUTENTICACIÓN
# ============================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# RUTAS PRINCIPALES
# ============================================
@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")
        
        if usuario == "admin" and password == "admin123":
            session["logged_in"] = True
            session["usuario"] = usuario
            flash("Bienvenido al sistema", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales incorrectas", "danger")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", datos=datos)

@app.route("/buscar", methods=["POST"])
@login_required
def buscar():
    producto = request.form.get("producto")
    if not producto:
        flash("Introduce un producto para buscar", "warning")
        return redirect(url_for("dashboard"))
    
    resultados = buscar_producto(producto)
    return render_template("dashboard.html", datos=datos, resultados=resultados, busqueda=producto)

@app.route("/comprar", methods=["POST"])
@login_required
def comprar():
    tienda = request.form.get("tienda")
    producto_url = request.form.get("producto_url")
    perfil_nombre = request.form.get("perfil")
    
    perfil = next((p for p in datos["perfiles"] if p["nombre"] == perfil_nombre), None)
    pago = datos["pagos"][0] if datos["pagos"] else None
    
    if not perfil:
        flash("Configura un perfil de compra primero", "danger")
        return redirect(url_for("dashboard"))
    
    if not pago:
        flash("Configura un método de pago primero", "danger")
        return redirect(url_for("dashboard"))
    
    resultado = compra_automatica(tienda, producto_url, perfil, pago)
    
    if resultado["status"] == "success":
        flash(f"Compra realizada: {resultado['mensaje']}", "success")
    else:
        flash(f"Error: {resultado['mensaje']}", "danger")
    
    return redirect(url_for("dashboard"))

# ============================================
# RUTAS DE CONFIGURACIÓN
# ============================================
@app.route("/guardar_config", methods=["POST"])
@login_required
def guardar_config():
    datos["config"]["email"] = request.form.get("email", "")
    datos["config"]["password"] = request.form.get("password", "")
    datos["config"]["intervalo"] = int(request.form.get("intervalo", 15))
    guardar_datos()
    flash("Configuración guardada", "success")
    return redirect(url_for("dashboard"))

@app.route("/agregar_tienda", methods=["POST"])
@login_required
def agregar_tienda():
    nombre = request.form.get("nombre")
    url = request.form.get("url")
    
    if nombre and url:
        datos["tiendas"].append({"nombre": nombre, "url": url})
        guardar_datos()
        flash("Tienda agregada correctamente", "success")
    else:
        flash("Nombre y URL son obligatorios", "danger")
    
    return redirect(url_for("dashboard"))

@app.route("/guardar_cuenta_tienda", methods=["POST"])
@login_required
def guardar_cuenta_tienda():
    tienda = request.form.get("tienda")
    email = request.form.get("email")
    password = request.form.get("password")
    
    if tienda in datos["cuentas_tiendas"]:
        datos["cuentas_tiendas"][tienda]["email"] = email
        datos["cuentas_tiendas"][tienda]["password"] = password
        guardar_datos()
        flash(f"Credenciales de {tienda} guardadas", "success")
    else:
        flash("Tienda no encontrada", "danger")
    
    return redirect(url_for("dashboard"))

@app.route("/agregar_perfil", methods=["POST"])
@login_required
def agregar_perfil():
    perfil = {
        "nombre": request.form.get("nombre"),
        "nombre_completo": request.form.get("nombre_completo"),
        "direccion": request.form.get("direccion"),
        "ciudad": request.form.get("ciudad"),
        "codigo_postal": request.form.get("codigo_postal"),
        "pais": request.form.get("pais"),
        "telefono": request.form.get("telefono")
    }
    
    datos["perfiles"].append(perfil)
    guardar_datos()
    flash("Perfil agregado correctamente", "success")
    return redirect(url_for("dashboard"))

@app.route("/agregar_pago", methods=["POST"])
@login_required
def agregar_pago():
    tipo = request.form.get("tipo")
    
    if tipo == "tarjeta":
        pago = {
            "tipo": "tarjeta",
            "numero": request.form.get("numero"),
            "titular": request.form.get("titular"),
            "caducidad": request.form.get("caducidad"),
            "cvv": request.form.get("cvv"),
            "marca": request.form.get("marca")
        }
    else:
        pago = {
            "tipo": "paypal",
            "email": request.form.get("email_paypal"),
            "password": request.form.get("password_paypal"),
            "titular": request.form.get("titular_paypal")
        }
    
    datos["pagos"].append(pago)
    guardar_datos()
    flash("Método de pago agregado", "success")
    return redirect(url_for("dashboard"))

@app.route("/agregar_snipe", methods=["POST"])
@login_required
def agregar_snipe():
    snipe = {
        "producto": request.form.get("producto"),
        "tienda": request.form.get("tienda"),
        "precio_max": float(request.form.get("precio_max", 0)),
        "activo": True,
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    datos["snipes"].append(snipe)
    guardar_datos()
    flash("Sniper configurado correctamente", "success")
    return redirect(url_for("dashboard"))

@app.route("/agregar_tarea", methods=["POST"])
@login_required
def agregar_tarea():
    tarea = {
        "nombre": request.form.get("nombre"),
        "tienda": request.form.get("tienda"),
        "producto": request.form.get("producto"),
        "estado": "pendiente",
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    datos["tareas"].append(tarea)
    guardar_datos()
    flash("Tarea agregada correctamente", "success")
    return redirect(url_for("dashboard"))

@app.route("/agregar_preventa", methods=["POST"])
@login_required
def agregar_preventa():
    preventa = {
        "producto": request.form.get("producto"),
        "tienda": request.form.get("tienda"),
        "fecha_lanzamiento": request.form.get("fecha_lanzamiento"),
        "precio": float(request.form.get("precio", 0)),
        "activo": True
    }
    
    datos["preventas"].append(preventa)
    guardar_datos()
    flash("Preventa configurada", "success")
    return redirect(url_for("dashboard"))

@app.route("/agregar_proxy", methods=["POST"])
@login_required
def agregar_proxy():
    proxy = {
        "ip": request.form.get("ip"),
        "puerto": request.form.get("puerto"),
        "usuario": request.form.get("usuario"),
        "password": request.form.get("password"),
        "pais": request.form.get("pais")
    }
    
    datos["proxies"].append(proxy)
    guardar_datos()
    flash("Proxy agregado", "success")
    return redirect(url_for("dashboard"))

# ============================================
# INICIAR MONITOREO EN SEGUNDO PLANO
# ============================================
def iniciar_monitoreo():
    thread = threading.Thread(target=monitorear_snipes, daemon=True)
    thread.start()

# ============================================
# INICIAR APLICACIÓN
# ============================================
if __name__ == "__main__":
    iniciar_monitoreo()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
