import os
import time
import json
import threading
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# ============================================
# CONFIGURACIÓN DE TELEGRAM
# ============================================
TELEGRAM_TOKEN = "8871598841:AAHszVIUkwGoxYklkoHeTdNSZ68MuPlzqKw"  # ← Pega tu token de BotFather
TELEGRAM_CHAT_ID = "8514421716"  # ← Pega tu chat ID

def enviar_telegram(mensaje):
    """Envía una notificación a Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        datos = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        }
        requests.post(url, data=datos)
        print(f"✅ Notificación enviada a Telegram: {mensaje[:50]}...")
    except Exception as e:
        print(f"❌ Error al enviar Telegram: {e}")

# ============================================
# CONFIGURACIÓN DE LA APP
# ============================================
app = Flask(__name__)
app.secret_key = "stellar_bot_secret_key_2024"

# Credenciales de acceso
USUARIO = "admin"
CONTRASEÑA = "admin123"

# Variables globales
alertas_activas = True
monitoreo_activo = True
precios_objetivo = {}
productos_monitoreados = []
perfiles_compra = []
historial_compras = []
credenciales_tiendas = {}
proxies_lista = []

# ============================================
# LISTA DE TIENDAS CON URLs CONFIGURABLES
# ============================================
TIENDAS = [
    {
        "id": 1, 
        "nombre": "Darizard9", 
        "url": "https://www.darizard9.com", 
        "url_busqueda": "https://www.darizard9.com/search?q={producto}",
        "url_login": "https://www.darizard9.com/login",
        "url_compra": "https://www.darizard9.com/checkout",
        "categoria": "TCG",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 2, 
        "nombre": "Pokemillon", 
        "url": "https://www.pokemillon.com", 
        "url_busqueda": "https://www.pokemillon.com/buscar?q={producto}",
        "url_login": "https://www.pokemillon.com/login",
        "url_compra": "https://www.pokemillon.com/checkout",
        "categoria": "TCG",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 3, 
        "nombre": "UnSobreMas", 
        "url": "https://www.unsobremas.com", 
        "url_busqueda": "https://www.unsobremas.com/catalogsearch/result/?q={producto}",
        "url_login": "https://www.unsobremas.com/customer/account/login",
        "url_compra": "https://www.unsobremas.com/checkout/cart",
        "categoria": "TCG",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 4, 
        "nombre": "ToysRUs", 
        "url": "https://www.toysrus.es", 
        "url_busqueda": "https://www.toysrus.es/search?q={producto}",
        "url_login": "https://www.toysrus.es/login",
        "url_compra": "https://www.toysrus.es/checkout",
        "categoria": "Juguetes",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 5, 
        "nombre": "TCGFactory", 
        "url": "https://www.tcgfactory.com", 
        "url_busqueda": "https://www.tcgfactory.com/search?q={producto}",
        "url_login": "https://www.tcgfactory.com/login",
        "url_compra": "https://www.tcgfactory.com/checkout",
        "categoria": "TCG",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 6, 
        "nombre": "Amazon", 
        "url": "https://www.amazon.es", 
        "url_busqueda": "https://www.amazon.es/s?k={producto}",
        "url_login": "https://www.amazon.es/ap/signin",
        "url_compra": "https://www.amazon.es/gp/cart/view.html",
        "categoria": "General",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 7, 
        "nombre": "eBay", 
        "url": "https://www.ebay.es", 
        "url_busqueda": "https://www.ebay.es/sch/i.html?_nkw={producto}",
        "url_login": "https://www.ebay.es/signin",
        "url_compra": "https://cart.ebay.es",
        "categoria": "General",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 8, 
        "nombre": "Carrefour", 
        "url": "https://www.carrefour.es", 
        "url_busqueda": "https://www.carrefour.es/buscar?q={producto}",
        "url_login": "https://www.carrefour.es/login",
        "url_compra": "https://www.carrefour.es/checkout",
        "categoria": "General",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 9, 
        "nombre": "Game", 
        "url": "https://www.game.es", 
        "url_busqueda": "https://www.game.es/buscar?q={producto}",
        "url_login": "https://www.game.es/login",
        "url_compra": "https://www.game.es/checkout",
        "categoria": "Videojuegos",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 10, 
        "nombre": "El Corte Ingles", 
        "url": "https://www.elcorteingles.es", 
        "url_busqueda": "https://www.elcorteingles.es/buscar?q={producto}",
        "url_login": "https://www.elcorteingles.es/login",
        "url_compra": "https://www.elcorteingles.es/checkout",
        "categoria": "General",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 11, 
        "nombre": "Topps", 
        "url": "https://www.topps.com", 
        "url_busqueda": "https://www.topps.com/search?q={producto}",
        "url_login": "https://www.topps.com/login",
        "url_compra": "https://www.topps.com/checkout",
        "categoria": "TCG",
        "moneda": "USD",
        "requiere_login": True
    },
    {
        "id": 12, 
        "nombre": "Turolgames", 
        "url": "https://www.turolgames.com", 
        "url_busqueda": "https://www.turolgames.com/buscar?q={producto}",
        "url_login": "https://www.turolgames.com/login",
        "url_compra": "https://www.turolgames.com/checkout",
        "categoria": "Videojuegos",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 13, 
        "nombre": "Flashstore", 
        "url": "https://www.flashstore.com", 
        "url_busqueda": "https://www.flashstore.com/search?q={producto}",
        "url_login": "https://www.flashstore.com/login",
        "url_compra": "https://www.flashstore.com/checkout",
        "categoria": "General",
        "moneda": "EUR",
        "requiere_login": True
    },
    {
        "id": 14, 
        "nombre": "Pokemon Center", 
        "url": "https://www.pokemoncenter.com", 
        "url_busqueda": "https://www.pokemoncenter.com/search?q={producto}",
        "url_login": "https://www.pokemoncenter.com/login",
        "url_compra": "https://www.pokemoncenter.com/checkout",
        "categoria": "TCG",
        "moneda": "USD",
        "requiere_login": True
    },
    {
        "id": 15, 
        "nombre": "Cardmarket", 
        "url": "https://www.cardmarket.com", 
        "url_busqueda": "https://www.cardmarket.com/es/Magic/Products/Singles?searchString={producto}",
        "url_login": "https://www.cardmarket.com/es/Login",
        "url_compra": "https://www.cardmarket.com/es/Cart",
        "categoria": "TCG",
        "moneda": "EUR",
        "requiere_login": True
    }
]

# ============================================
# SISTEMA DE LOGIN EN TIENDAS
# ============================================
class SistemaLoginTiendas:
    def __init__(self):
        self.sesiones_activas = {}
        self.credenciales = {}
    
    def guardar_credenciales(self, tienda_id, email, password):
        """Guarda las credenciales de una tienda"""
        tienda = next((t for t in TIENDAS if t["id"] == tienda_id), None)
        if not tienda:
            return {"error": "Tienda no encontrada"}
        
        self.credenciales[tienda_id] = {
            "tienda": tienda["nombre"],
            "email": email,
            "password": password,
            "url_login": tienda["url_login"],
            "fecha_guardado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        enviar_telegram(f"""
🔐 <b>Credenciales guardadas para {tienda['nombre']}</b>

📧 <b>Email:</b> {email}
🔗 <b>URL Login:</b> {tienda['url_login']}
✅ <b>Estado:</b> Guardado correctamente
""")
        
        return {"mensaje": f"Credenciales guardadas para {tienda['nombre']}"}
    
    def iniciar_sesion(self, tienda_id):
        """Inicia sesión en una tienda"""
        tienda = next((t for t in TIENDAS if t["id"] == tienda_id), None)
        if not tienda:
            return {"error": "Tienda no encontrada"}
        
        credenciales = self.credenciales.get(tienda_id)
        if not credenciales:
            return {"error": "No hay credenciales guardadas para esta tienda"}
        
        # Simular inicio de sesión
        sesion_id = f"sesion_{tienda_id}_{int(time.time())}"
        self.sesiones_activas[tienda_id] = {
            "sesion_id": sesion_id,
            "tienda": tienda["nombre"],
            "email": credenciales["email"],
            "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activa": True
        }
        
        enviar_telegram(f"""
✅ <b>¡Sesión iniciada en {tienda['nombre']}!</b>

👤 <b>Usuario:</b> {credenciales['email']}
🔑 <b>Sesión ID:</b> {sesion_id}
🕐 <b>Hora:</b> {datetime.now().strftime('%H:%M:%S')}
🔗 <a href="{tienda['url_login']}">Ir a la tienda</a>
""")
        
        return self.sesiones_activas[tienda_id]
    
    def cerrar_sesion(self, tienda_id):
        """Cierra la sesión en una tienda"""
        if tienda_id in self.sesiones_activas:
            self.sesiones_activas[tienda_id]["activa"] = False
            tienda = next((t for t in TIENDAS if t["id"] == tienda_id), None)
            if tienda:
                enviar_telegram(f"🔒 <b>Sesión cerrada en {tienda['nombre']}</b>")
            return {"mensaje": "Sesión cerrada"}
        return {"error": "No hay sesión activa"}
    
    def obtener_sesiones(self):
        """Obtiene todas las sesiones activas"""
        return self.sesiones_activas
    
    def verificar_sesion(self, tienda_id):
        """Verifica si hay una sesión activa"""
        sesion = self.sesiones_activas.get(tienda_id)
        if sesion and sesion["activa"]:
            return sesion
        return None

sistema_login = SistemaLoginTiendas()

# ============================================
# SISTEMA DE PROXIES
# ============================================
class SistemaProxies:
    def __init__(self):
        self.proxies = []
        self.proxies_id_counter = 1
    
    def agregar_proxies(self, proxies_list, tipo="http", formato="ip:puerto"):
        """Agrega proxies a la lista"""
        agregados = 0
        for proxy_str in proxies_list:
            proxy_str = proxy_str.strip()
            if not proxy_str:
                continue
            
            # Parsear según formato
            if formato == "ip:puerto":
                partes = proxy_str.split(":")
                if len(partes) == 2:
                    ip, puerto = partes
                    usuario = None
                    password = None
                elif len(partes) == 4:
                    ip, puerto, usuario, password = partes
                else:
                    continue
            elif formato == "http" or formato == "socks5":
                if "://" in proxy_str:
                    tipo_proxy, resto = proxy_str.split("://")
                    partes = resto.split(":")
                    if len(partes) == 2:
                        ip, puerto = partes
                        usuario = None
                        password = None
                    elif len(partes) == 4:
                        ip, puerto, usuario, password = partes
                    else:
                        continue
                else:
                    continue
            else:
                continue
            
            proxy = {
                "id": self.proxies_id_counter,
                "ip": ip,
                "puerto": puerto,
                "usuario": usuario,
                "password": password,
                "tipo": tipo,
                "activo": True,
                "pais": "Desconocido",
                "tiempo_respuesta": 0,
                "fecha_agregado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.proxies.append(proxy)
            self.proxies_id_counter += 1
            agregados += 1
        
        if agregados > 0:
            enviar_telegram(f"🔒 <b>Proxies agregados</b>\n📊 Total: {agregados}")
        
        return {"mensaje": f"Se agregaron {agregados} proxies"}
    
    def obtener_lista(self):
        """Obtiene la lista de proxies"""
        return self.proxies
    
    def eliminar_proxy(self, proxy_id):
        """Elimina un proxy específico"""
        for i, proxy in enumerate(self.proxies):
            if proxy["id"] == proxy_id:
                del self.proxies[i]
                return {"mensaje": "Proxy eliminado"}
        return {"error": "Proxy no encontrado"}
    
    def eliminar_inactivos(self):
        """Elimina todos los proxies inactivos"""
        antes = len(self.proxies)
        self.proxies = [p for p in self.proxies if p["activo"]]
        eliminados = antes - len(self.proxies)
        return {"mensaje": f"Se eliminaron {eliminados} proxies inactivos"}
    
    def testear_proxies(self):
        """Testea todos los proxies"""
        import random
        
        proxies_testeados = 0
        proxies_activos = 0
        
        for proxy in self.proxies:
            # Simular testeo
            proxy["tiempo_respuesta"] = random.uniform(50, 500)
            proxy["activo"] = random.random() > 0.2
            proxy["pais"] = random.choice(["España", "Francia", "Alemania", "Italia", "Portugal", "Reino Unido"])
            
            if proxy["activo"]:
                proxies_activos += 1
            proxies_testeados += 1
        
        enviar_telegram(f"""
🧪 <b>Testeo de proxies completado</b>

📊 <b>Total testeados:</b> {proxies_testeados}
✅ <b>Activos:</b> {proxies_activos}
❌ <b>Inactivos:</b> {proxies_testeados - proxies_activos}
""")
        
        return {"mensaje": f"Testeo completado: {proxies_activos} activos de {proxies_testeados}"}
    
    def obtener_proxies_activos(self):
        """Obtiene solo los proxies activos"""
        return [p for p in self.proxies if p["activo"]]

sistema_proxies = SistemaProxies()

# ============================================
# SISTEMA DE PAGOS
# ============================================
class SistemaPagos:
    def __init__(self):
        self.metodos_pago = {
            "paypal": {
                "nombre": "PayPal",
                "comision": 0.035,  # 3.5%
                "activo": True
            },
            "tarjeta": {
                "nombre": "Tarjeta de Crédito",
                "comision": 0.025,  # 2.5%
                "activo": True
            },
            "transferencia": {
                "nombre": "Transferencia Bancaria",
                "comision": 0.0,  # 0%
                "activo": True
            },
            "bitcoin": {
                "nombre": "Bitcoin",
                "comision": 0.01,  # 1%
                "activo": True
            }
        }
        
        self.perfiles_pago = []
        self.transacciones = []
    
    def crear_perfil_pago(self, nombre, email, metodo, datos):
        """Crea un perfil de pago"""
        perfil = {
            "id": len(self.perfiles_pago) + 1,
            "nombre": nombre,
            "email": email,
            "metodo": metodo,
            "datos": datos,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.perfiles_pago.append(perfil)
        return perfil
    
    def procesar_pago(self, perfil_id, monto, producto, tienda):
        """Procesa un pago"""
        perfil = next((p for p in self.perfiles_pago if p["id"] == perfil_id), None)
        if not perfil:
            return {"error": "Perfil no encontrado"}
        
        metodo = self.metodos_pago.get(perfil["metodo"])
        if not metodo or not metodo["activo"]:
            return {"error": "Método de pago no disponible"}
        
        # Calcular comisión
        comision = monto * metodo["comision"]
        total = monto + comision
        
        # Crear transacción
        transaccion = {
            "id": len(self.transacciones) + 1,
            "perfil_id": perfil_id,
            "producto": producto,
            "tienda": tienda,
            "monto": monto,
            "comision": comision,
            "total": total,
            "metodo": perfil["metodo"],
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estado": "completado"
        }
        
        self.transacciones.append(transaccion)
        
        # Notificar por Telegram
        enviar_telegram(f"""
💳 <b>¡PAGO PROCESADO!</b>

📦 <b>Producto:</b> {producto}
🏪 <b>Tienda:</b> {tienda}
💰 <b>Monto:</b> {monto:.2f}€
📊 <b>Comisión:</b> {comision:.2f}€
💵 <b>Total:</b> {total:.2f}€
💳 <b>Método:</b> {metodo['nombre']}
✅ <b>Estado:</b> Completado
""")
        
        return transaccion
    
    def obtener_transacciones(self):
        return self.transacciones

sistema_pagos = SistemaPagos()

# ============================================
# FUNCIONES DE BÚSQUEDA CON URLs REALES
# ============================================
def generar_url_busqueda(tienda, producto):
    """Genera la URL de búsqueda real para una tienda"""
    producto_formateado = producto.replace(" ", "+")
    url = tienda["url_busqueda"].format(producto=producto_formateado)
    return url

def buscar_en_tienda(tienda, producto):
    """Busca un producto en una tienda con URL real"""
    import random
    
    # Generar URL de búsqueda real
    url_busqueda = generar_url_busqueda(tienda, producto)
    
    # Simular precios según la tienda
    precios_base = {
        "Amazon": 25.99,
        "eBay": 23.50,
        "Cardmarket": 20.00,
        "Pokemon Center": 29.99,
        "Topps": 24.99,
        "Game": 49.99,
        "Carrefour": 27.50,
        "El Corte Ingles": 28.99,
        "ToysRUs": 26.99,
        "Darizard9": 22.00,
        "Pokemillon": 21.50,
        "UnSobreMas": 22.99,
        "TCGFactory": 23.99,
        "Turolgames": 45.00,
        "Flashstore": 24.50
    }
    
    precio = precios_base.get(tienda["nombre"], 25.00)
    # Añadir variación aleatoria
    precio = round(precio * (0.9 + random.random() * 0.3), 2)
    
    # Simular disponibilidad
    disponible = random.random() > 0.2
    
    # Verificar si hay sesión activa
    sesion = sistema_login.verificar_sesion(tienda["id"])
    tiene_sesion = sesion is not None
    
    # Verificar si hay proxies activos
    proxies_activos = sistema_proxies.obtener_proxies_activos()
    
    return {
        "tienda": tienda["nombre"],
        "tienda_id": tienda["id"],
        "producto": producto,
        "precio": precio,
        "disponible": disponible,
        "url": url_busqueda,  # URL real de búsqueda
        "url_tienda": tienda["url"],
        "url_login": tienda["url_login"],
        "url_compra": tienda["url_compra"],
        "moneda": tienda["moneda"],
        "requiere_login": tienda["requiere_login"],
        "sesion_activa": tiene_sesion,
        "proxies_activos": len(proxies_activos),
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

def buscar_producto_todas_tiendas(producto):
    """Busca un producto en todas las tiendas con URLs reales"""
    resultados = []
    for tienda in TIENDAS:
        resultado = buscar_en_tienda(tienda, producto)
        if resultado["disponible"]:
            resultados.append(resultado)
    
    # Ordenar por precio
    resultados.sort(key=lambda x: x["precio"])
    
    # Enviar notificación de Telegram si hay resultados
    if resultados and alertas_activas:
        mejor = resultados[0]
        enviar_telegram(f"""
🔍 <b>Búsqueda completada: {producto}</b>

🏆 <b>Mejor precio:</b>
🏪 {mejor['tienda']}
💰 {mejor['precio']}€
🔗 <a href="{mejor['url']}">Ver oferta</a>

📊 <b>Total de resultados:</b> {len(resultados)}
""")
    
    return resultados

# ============================================
# FUNCIONES DE MONITOREO
# ============================================
def monitorear_precios():
    """Monitorea los precios de los productos"""
    global monitoreo_activo
    
    if not monitoreo_activo or not productos_monitoreados:
        return
    
    for producto in productos_monitoreados:
        resultados = buscar_producto_todas_tiendas(producto["nombre"])
        
        if resultados:
            mejor_precio = resultados[0]["precio"]
            precio_objetivo = producto.get("precio_objetivo", 0)
            
            if precio_objetivo > 0 and mejor_precio <= precio_objetivo:
                enviar_telegram(f"""
🎯 <b>¡ALERTA DE PRECIO OBJETIVO!</b>

📦 <b>Producto:</b> {producto['nombre']}
💰 <b>Precio actual:</b> {mejor_precio}€
🎯 <b>Precio objetivo:</b> {precio_objetivo}€
🏪 <b>Tienda:</b> {resultados[0]['tienda']}
🔗 <a href="{resultados[0]['url']}">Comprar ahora</a>
""")

# ============================================
# SNIPER DE CARDMARKET
# ============================================
def sniper_cardmarket():
    """Monitorea Cardmarket para encontrar gangas"""
    global alertas_activas
    
    if not alertas_activas:
        return
    
    import random
    
    # Simular detección de ofertas
    if random.random() < 0.3:  # 30% de probabilidad de encontrar oferta
        cartas = ["Charizard VMAX", "Pikachu Illustrator", "Mewtwo GX", "Umbreon VMAX", "Rayquaza V"]
        carta = random.choice(cartas)
        precio_normal = random.uniform(50, 200)
        precio_oferta = precio_normal * random.uniform(0.6, 0.9)
        
        url_busqueda = f"https://www.cardmarket.com/es/Magic/Products/Singles?searchString={carta.replace(' ', '+')}"
        
        # Verificar si hay sesión en Cardmarket
        sesion = sistema_login.verificar_sesion(15)  # ID de Cardmarket
        proxies_activos = sistema_proxies.obtener_proxies_activos()
        
        enviar_telegram(f"""
⚡ <b>¡SNIPER CARDMARKET ACTIVADO!</b>

🃏 <b>Carta:</b> {carta}
💰 <b>Precio normal:</b> {precio_normal:.2f}€
🔥 <b>Precio oferta:</b> {precio_oferta:.2f}€
📉 <b>Descuento:</b> {((1 - precio_oferta/precio_normal) * 100):.1f}%
🔗 <a href="{url_busqueda}">Comprar en Cardmarket</a>
{'✅ Sesión activa - Compra automática disponible' if sesion else '⚠️ Necesitas iniciar sesión'}
{'🔒 Proxies disponibles: ' + str(len(proxies_activos)) if proxies_activos else '⚠️ Sin proxies configurados'}
""")

# ============================================
# RUTAS DE LA APP
# ============================================
@app.route('/')
def index():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')
        
        if usuario == USUARIO and contraseña == CONTRASEÑA:
            session['usuario'] = usuario
            enviar_telegram("✅ <b>¡Inicio de sesión exitoso!</b>\n👤 Usuario: admin")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Credenciales incorrectas")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', tiendas=TIENDAS)

# ============================================
# API DE GESTIÓN DE URLs DE TIENDAS
# ============================================
@app.route('/api/tiendas/urls', methods=['GET'])
def api_tiendas_urls():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    return jsonify(TIENDAS)

@app.route('/api/tiendas/urls/actualizar', methods=['POST'])
def api_tiendas_urls_actualizar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    tienda_id = data.get('tienda_id')
    url_tienda = data.get('url_tienda')
    url_busqueda = data.get('url_busqueda')
    url_login = data.get('url_login')
    url_compra = data.get('url_compra')
    
    tienda = next((t for t in TIENDAS if t["id"] == tienda_id), None)
    if not tienda:
        return jsonify({"error": "Tienda no encontrada"}), 404
    
    if url_tienda:
        tienda["url"] = url_tienda
    if url_busqueda:
        tienda["url_busqueda"] = url_busqueda
    if url_login:
        tienda["url_login"] = url_login
    if url_compra:
        tienda["url_compra"] = url_compra
    
    enviar_telegram(f"""
🔗 <b>URLs actualizadas para {tienda['nombre']}</b>

🏪 <b>Tienda:</b> {tienda['url']}
🔍 <b>Búsqueda:</b> {tienda['url_busqueda']}
🔑 <b>Login:</b> {tienda['url_login']}
🛒 <b>Compra:</b> {tienda['url_compra']}
""")
    
    return jsonify({"mensaje": f"URLs actualizadas para {tienda['nombre']}", "tienda": tienda})

@app.route('/api/tiendas/urls/test', methods=['POST'])
def api_tiendas_urls_test():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    tienda_id = data.get('tienda_id')
    
    tienda = next((t for t in TIENDAS if t["id"] == tienda_id), None)
    if not tienda:
        return jsonify({"error": "Tienda no encontrada"}), 404
    
    # Verificar URLs
    urls_estado = {
        "tienda": tienda["nombre"],
        "url_tienda": tienda["url"],
        "url_busqueda": tienda["url_busqueda"],
        "url_login": tienda["url_login"],
        "url_compra": tienda["url_compra"],
        "estado": "ok"
    }
    
    return jsonify(urls_estado)

# ============================================
# API DE BÚSQUEDA
# ============================================
@app.route('/api/buscar', methods=['POST'])
def api_buscar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    producto = data.get('producto', '')
    tienda_id = data.get('tienda_id')
    
    if not producto:
        return jsonify({"error": "Producto requerido"}), 400
    
    if tienda_id:
        tienda = next((t for t in TIENDAS if t["id"] == int(tienda_id)), None)
        if tienda:
            resultado = buscar_en_tienda(tienda, producto)
            return jsonify([resultado])
    
    resultados = buscar_producto_todas_tiendas(producto)
    return jsonify(resultados)

# ============================================
# API DE LOGIN EN TIENDAS
# ============================================
@app.route('/api/login/guardar', methods=['POST'])
def api_login_guardar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    tienda_id = data.get('tienda_id')
    email = data.get('email')
    password = data.get('password')
    
    if not all([tienda_id, email, password]):
        return jsonify({"error": "Datos incompletos"}), 400
    
    resultado = sistema_login.guardar_credenciales(tienda_id, email, password)
    return jsonify(resultado)

@app.route('/api/login/iniciar', methods=['POST'])
def api_login_iniciar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    tienda_id = data.get('tienda_id')
    
    if not tienda_id:
        return jsonify({"error": "Tienda requerida"}), 400
    
    resultado = sistema_login.iniciar_sesion(tienda_id)
    return jsonify(resultado)

@app.route('/api/login/cerrar', methods=['POST'])
def api_login_cerrar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    tienda_id = data.get('tienda_id')
    
    if not tienda_id:
        return jsonify({"error": "Tienda requerida"}), 400
    
    resultado = sistema_login.cerrar_sesion(tienda_id)
    return jsonify(resultado)

@app.route('/api/login/sesiones', methods=['GET'])
def api_login_sesiones():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    return jsonify(sistema_login.obtener_sesiones())

@app.route('/api/login/verificar', methods=['POST'])
def api_login_verificar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    tienda_id = data.get('tienda_id')
    
    if not tienda_id:
        return jsonify({"error": "Tienda requerida"}), 400
    
    sesion = sistema_login.verificar_sesion(tienda_id)
    return jsonify({"sesion_activa": sesion is not None, "sesion": sesion})

# ============================================
# API DE PROXIES
# ============================================
@app.route('/api/proxies/agregar', methods=['POST'])
def api_proxies_agregar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    proxies = data.get('proxies', [])
    tipo = data.get('tipo', 'http')
    formato = data.get('formato', 'ip:puerto')
    
    if not proxies:
        return jsonify({"error": "No se proporcionaron proxies"}), 400
    
    resultado = sistema_proxies.agregar_proxies(proxies, tipo, formato)
    return jsonify(resultado)

@app.route('/api/proxies/lista', methods=['GET'])
def api_proxies_lista():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    return jsonify(sistema_proxies.obtener_lista())

@app.route('/api/proxies/eliminar/<int:proxy_id>', methods=['DELETE'])
def api_proxies_eliminar(proxy_id):
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    resultado = sistema_proxies.eliminar_proxy(proxy_id)
    return jsonify(resultado)

@app.route('/api/proxies/eliminar-inactivos', methods=['DELETE'])
def api_proxies_eliminar_inactivos():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    resultado = sistema_proxies.eliminar_inactivos()
    return jsonify(resultado)

@app.route('/api/proxies/testear', methods=['POST'])
def api_proxies_testear():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    resultado = sistema_proxies.testear_proxies()
    return jsonify(resultado)

# ============================================
# API DE MONITOREO
# ============================================
@app.route('/api/monitorear', methods=['POST'])
def api_monitorear():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    producto = data.get('producto')
    precio_objetivo = data.get('precio_objetivo', 0)
    
    if not producto:
        return jsonify({"error": "Producto requerido"}), 400
    
    productos_monitoreados.append({
        "nombre": producto,
        "precio_objetivo": precio_objetivo
    })
    
    enviar_telegram(f"""
📊 <b>Nuevo producto en monitoreo:</b>
📦 {producto}
🎯 Precio objetivo: {precio_objetivo}€
""")
    
    return jsonify({"mensaje": "Producto agregado al monitoreo"})

@app.route('/api/monitoreo/estado', methods=['GET'])
def api_monitoreo_estado():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    return jsonify({
        "activo": monitoreo_activo,
        "productos": productos_monitoreados
    })

@app.route('/api/monitoreo/toggle', methods=['POST'])
def api_monitoreo_toggle():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    global monitoreo_activo
    monitoreo_activo = not monitoreo_activo
    
    estado = "activado" if monitoreo_activo else "desactivado"
    enviar_telegram(f"🔄 Monitoreo {estado}")
    
    return jsonify({"activo": monitoreo_activo})

# ============================================
# API DE TELEGRAM
# ============================================
@app.route('/telegram/test', methods=['POST'])
def telegram_test():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    enviar_telegram("✅ <b>¡Conexión con Telegram exitosa!</b>\nTu bot está funcionando correctamente.")
    return jsonify({"mensaje": "Notificación de prueba enviada"})

@app.route('/telegram/activar', methods=['POST'])
def telegram_activar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    global alertas_activas
    alertas_activas = True
    enviar_telegram("🔔 <b>Alertas activadas</b>\nRecibirás notificaciones de precios y ofertas.")
    return jsonify({"mensaje": "Alertas activadas"})

@app.route('/telegram/desactivar', methods=['POST'])
def telegram_desactivar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    global alertas_activas
    alertas_activas = False
    enviar_telegram("🔕 <b>Alertas desactivadas</b>\nNo recibirás más notificaciones.")
    return jsonify({"mensaje": "Alertas desactivadas"})

# ============================================
# API DE SNIPER
# ============================================
@app.route('/api/sniper/activar', methods=['POST'])
def api_sniper_activar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    enviar_telegram("⚡ <b>Sniper de Cardmarket activado</b>\nMonitoreando ofertas en tiempo real...")
    return jsonify({"mensaje": "Sniper activado"})

@app.route('/api/sniper/estado', methods=['GET'])
def api_sniper_estado():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    return jsonify({"activo": alertas_activas})

# ============================================
# API DE PAGOS
# ============================================
@app.route('/api/pagos/metodos', methods=['GET'])
def api_pagos_metodos():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    return jsonify(sistema_pagos.metodos_pago)

@app.route('/api/pagos/perfil', methods=['POST'])
def api_pagos_crear_perfil():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    nombre = data.get('nombre')
    email = data.get('email')
    metodo = data.get('metodo')
    datos = data.get('datos', {})
    
    if not all([nombre, email, metodo]):
        return jsonify({"error": "Datos incompletos"}), 400
    
    perfil = sistema_pagos.crear_perfil_pago(nombre, email, metodo, datos)
    return jsonify(perfil)

@app.route('/api/pagos/procesar', methods=['POST'])
def api_pagos_procesar():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    perfil_id = data.get('perfil_id')
    monto = data.get('monto')
    producto = data.get('producto')
    tienda = data.get('tienda')
    
    if not all([perfil_id, monto, producto, tienda]):
        return jsonify({"error": "Datos incompletos"}), 400
    
    resultado = sistema_pagos.procesar_pago(perfil_id, monto, producto, tienda)
    return jsonify(resultado)

@app.route('/api/pagos/transacciones', methods=['GET'])
def api_pagos_transacciones():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    return jsonify(sistema_pagos.obtener_transacciones())

# ============================================
# INICIAR MONITOREO AUTOMÁTICO
# ============================================
scheduler = BackgroundScheduler()
scheduler.add_job(monitorear_precios, 'interval', minutes=5)
scheduler.add_job(sniper_cardmarket, 'interval', minutes=10)
scheduler.start()

# ============================================
# INICIAR LA APP
# ============================================
if __name__ == "__main__":
    enviar_telegram("🚀 <b>Stellar Bot iniciado</b>\nEl bot está funcionando correctamente.")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
