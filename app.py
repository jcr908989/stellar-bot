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
TELEGRAM_TOKEN = "PON_AQUI_TU_TOKEN"  # ← Pega tu token de BotFather
TELEGRAM_CHAT_ID = "PON_AQUI_TU_CHAT_ID"  # ← Pega tu chat ID

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

# ============================================
# LISTA DE TIENDAS (15 tiendas)
# ============================================
TIENDAS = [
    {"id": 1, "nombre": "Darizard9", "url": "https://www.darizard9.com", "categoria": "TCG"},
    {"id": 2, "nombre": "Pokemillon", "url": "https://www.pokemillon.com", "categoria": "TCG"},
    {"id": 3, "nombre": "UnSobreMas", "url": "https://www.unsobremas.com", "categoria": "TCG"},
    {"id": 4, "nombre": "ToysRUs", "url": "https://www.toysrus.es", "categoria": "Juguetes"},
    {"id": 5, "nombre": "TCGFactory", "url": "https://www.tcgfactory.com", "categoria": "TCG"},
    {"id": 6, "nombre": "Amazon", "url": "https://www.amazon.es", "categoria": "General"},
    {"id": 7, "nombre": "eBay", "url": "https://www.ebay.es", "categoria": "General"},
    {"id": 8, "nombre": "Carrefour", "url": "https://www.carrefour.es", "categoria": "General"},
    {"id": 9, "nombre": "Game", "url": "https://www.game.es", "categoria": "Videojuegos"},
    {"id": 10, "nombre": "El Corte Ingles", "url": "https://www.elcorteingles.es", "categoria": "General"},
    {"id": 11, "nombre": "Topps", "url": "https://www.topps.com", "categoria": "TCG"},
    {"id": 12, "nombre": "Turolgames", "url": "https://www.turolgames.com", "categoria": "Videojuegos"},
    {"id": 13, "nombre": "Flashstore", "url": "https://www.flashstore.com", "categoria": "General"},
    {"id": 14, "nombre": "Pokemon Center", "url": "https://www.pokemoncenter.com", "categoria": "TCG"},
    {"id": 15, "nombre": "Cardmarket", "url": "https://www.cardmarket.com", "categoria": "TCG"}
]

# ============================================
# FUNCIONES DE BÚSQUEDA
# ============================================
def buscar_en_tienda(tienda, producto):
    """Simula la búsqueda de un producto en una tienda"""
    import random
    
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
    
    return {
        "tienda": tienda["nombre"],
        "producto": producto,
        "precio": precio,
        "disponible": disponible,
        "url": tienda["url"],
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

def buscar_producto_todas_tiendas(producto):
    """Busca un producto en todas las tiendas"""
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
        
        enviar_telegram(f"""
⚡ <b>¡SNIPER CARDMARKET ACTIVADO!</b>

🃏 <b>Carta:</b> {carta}
💰 <b>Precio normal:</b> {precio_normal:.2f}€
🔥 <b>Precio oferta:</b> {precio_oferta:.2f}€
📉 <b>Descuento:</b> {((1 - precio_oferta/precio_normal) * 100):.1f}%
🔗 <a href="https://www.cardmarket.com">Ver en Cardmarket</a>
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
