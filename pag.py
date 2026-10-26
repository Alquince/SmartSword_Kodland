from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SMARTSWORD_SECRET", "smartsword-clave-segura-2026")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "smartsword.db"

productos = [
    {
        "id": 1,
        "nombre": "KATANA ENMA",
        "categoria": "Anime",
        "precio": 180000,
        "imagen": "enma.jpg",
        "descripcion": "Réplica decorativa inspirada en una katana legendaria del mundo del anime.",
        "material": "Resina reforzada, ABS y acabado metálico decorativo.",
        "dimensiones": "Longitud total aproximada: 103 cm.",
        "etiqueta": "Destacado"
    },
    {
        "id": 2,
        "nombre": "KATANA SANDAI KITETSU",
        "categoria": "Anime",
        "precio": 195000,
        "imagen": "sandai-kitetsu.jpg",
        "descripcion": "Pieza decorativa de estética samurái, pensada para exhibición y colección.",
        "material": "Resina reforzada, ABS y detalles de acabado lacado.",
        "dimensiones": "Longitud total aproximada: 103 cm.",
        "etiqueta": "Anime"
    },
    {
        "id": 3,
        "nombre": "HACHA LEVIATHAN",
        "categoria": "Videojuegos",
        "precio": 220000,
        "imagen": "leviathan.jpg",
        "descripcion": "Réplica decorativa de fantasía inspirada en grandes aventuras de videojuegos.",
        "material": "Resina de alta densidad y mango decorativo texturizado.",
        "dimensiones": "Longitud total aproximada: 85 cm.",
        "etiqueta": "Videojuegos"
    },
    {
        "id": 4,
        "nombre": "ESPADAS DEL CAOS",
        "categoria": "Videojuegos",
        "precio": 250000,
        "imagen": "espadas-caos.jpg",
        "descripcion": "Set decorativo de colección con estética fantástica y acabado de exhibición.",
        "material": "Resina reforzada, ABS y cadenas decorativas livianas.",
        "dimensiones": "Longitud aproximada por pieza: 54 cm.",
        "etiqueta": "Edición fan"
    }
]


def get_db():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def init_db():
    conexion = get_db()
    conexion.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            asunto TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            direccion TEXT NOT NULL,
            total INTEGER NOT NULL,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
        """
    )
    conexion.commit()
    conexion.close()


def buscar_producto(id_producto):
    return next((p for p in productos if p["id"] == id_producto), None)


def obtener_carrito():
    return session.get("carrito", {})


def detalle_carrito():
    carrito = obtener_carrito()
    items = []
    total = 0

    for id_texto, cantidad in carrito.items():
        producto = buscar_producto(int(id_texto))
        if producto:
            subtotal = producto["precio"] * cantidad
            items.append({
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": subtotal
            })
            total += subtotal

    return items, total


@app.context_processor
def datos_globales():
    carrito = obtener_carrito()
    return {
        "cantidad_carrito": sum(carrito.values()),
        "usuario_actual": session.get("usuario_nombre")
    }


@app.route("/")
def inicio():
    return render_template("index.html", destacados=productos)


@app.route("/nosotros")
def nosotros():
    return render_template("nosotros.html")


@app.route("/productos")
def mostrar_productos():
    categoria = request.args.get("categoria", "").strip()
    busqueda = request.args.get("q", "").strip()

    resultado = productos

    if categoria:
        resultado = [
            p for p in resultado
            if p["categoria"].lower() == categoria.lower()
        ]

    if busqueda:
        texto = busqueda.lower()
        resultado = [
            p for p in resultado
            if texto in p["nombre"].lower()
            or texto in p["descripcion"].lower()
            or texto in p["categoria"].lower()
        ]

    return render_template(
        "productos.html",
        productos=resultado,
        categoria_activa=categoria,
        busqueda=busqueda
    )


@app.route("/producto/<int:id_producto>")
def detalle_producto(id_producto):
    producto = buscar_producto(id_producto)
    return render_template("detalle.html", producto=producto)


@app.post("/agregar_carrito/<int:id_producto>")
def agregar_carrito(id_producto):
    if not buscar_producto(id_producto):
        flash("El producto no existe.", "error")
        return redirect(url_for("mostrar_productos"))

    carrito = obtener_carrito()
    clave = str(id_producto)
    carrito[clave] = carrito.get(clave, 0) + 1
    session["carrito"] = carrito

    flash("Producto agregado al carrito.", "success")
    return redirect(request.referrer or url_for("ver_carrito"))


@app.route("/carrito")
def ver_carrito():
    items, total = detalle_carrito()
    return render_template("carrito.html", items=items, total=total)


@app.post("/carrito/eliminar/<int:id_producto>")
def eliminar_carrito(id_producto):
    carrito = obtener_carrito()
    carrito.pop(str(id_producto), None)
    session["carrito"] = carrito
    flash("Producto eliminado del carrito.", "info")
    return redirect(url_for("ver_carrito"))


@app.post("/carrito/vaciar")
def vaciar_carrito():
    session["carrito"] = {}
    flash("Carrito vaciado.", "info")
    return redirect(url_for("ver_carrito"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")
        confirmar = request.form.get("confirmar_contrasena", "")

        if not nombre or not correo or not contrasena:
            flash("Completa todos los campos obligatorios.", "error")
            return render_template("registro.html")

        if contrasena != confirmar:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("registro.html")

        if len(contrasena) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("registro.html")

        conexion = get_db()
        existente = conexion.execute(
            "SELECT id FROM usuarios WHERE correo = ?",
            (correo,)
        ).fetchone()

        if existente:
            conexion.close()
            flash("Ya existe una cuenta con ese correo.", "error")
            return render_template("registro.html")

        cursor = conexion.execute(
            "INSERT INTO usuarios (nombre, correo, password_hash) VALUES (?, ?, ?)",
            (nombre, correo, generate_password_hash(contrasena))
        )
        conexion.commit()

        session["usuario_id"] = cursor.lastrowid
        session["usuario_nombre"] = nombre
        session["usuario_correo"] = correo
        conexion.close()

        flash("Cuenta creada correctamente. ¡Bienvenido a SmartSword!", "success")
        return redirect(url_for("inicio"))

    return render_template("registro.html")


@app.route("/iniciar-sesion", methods=["GET", "POST"])
def iniciar_sesion():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")

        conexion = get_db()
        usuario = conexion.execute(
            "SELECT * FROM usuarios WHERE correo = ?",
            (correo,)
        ).fetchone()
        conexion.close()

        if not usuario or not check_password_hash(usuario["password_hash"], contrasena):
            flash("Correo o contraseña incorrectos.", "error")
            return render_template("iniciar_sesion.html")

        session["usuario_id"] = usuario["id"]
        session["usuario_nombre"] = usuario["nombre"]
        session["usuario_correo"] = usuario["correo"]

        flash(f"Bienvenido, {usuario['nombre']}.", "success")
        return redirect(url_for("inicio"))

    return render_template("iniciar_sesion.html")


@app.route("/cerrar-sesion")
def cerrar_sesion():
    session.pop("usuario_id", None)
    session.pop("usuario_nombre", None)
    session.pop("usuario_correo", None)
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("inicio"))


@app.route("/contacto", methods=["GET", "POST"])
def contacto():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip()
        asunto = request.form.get("asunto", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        if not all([nombre, correo, asunto, mensaje]):
            flash("Completa todos los campos del formulario.", "error")
            return render_template("contacto.html")

        conexion = get_db()
        conexion.execute(
            "INSERT INTO mensajes (nombre, correo, asunto, mensaje) VALUES (?, ?, ?, ?)",
            (nombre, correo, asunto, mensaje)
        )
        conexion.commit()
        conexion.close()

        flash("Mensaje enviado. Gracias por contactarnos.", "success")
        return redirect(url_for("contacto"))

    return render_template("contacto.html")


@app.route("/pedido", methods=["GET", "POST"])
def pedido():
    items, total = detalle_carrito()

    if not items:
        flash("Tu carrito está vacío.", "info")
        return redirect(url_for("ver_carrito"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip()
        direccion = request.form.get("direccion", "").strip()

        if not all([nombre, correo, direccion]):
            flash("Completa los datos del pedido.", "error")
            return render_template(
                "pedido.html",
                items=items,
                total=total,
                nombre=nombre,
                correo=correo
            )

        conexion = get_db()
        cursor = conexion.execute(
            """
            INSERT INTO pedidos (usuario_id, nombre, correo, direccion, total)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session.get("usuario_id"),
                nombre,
                correo,
                direccion,
                total
            )
        )
        conexion.commit()
        numero_pedido = cursor.lastrowid
        conexion.close()

        session["carrito"] = {}

        return render_template(
            "confirmacion.html",
            numero_pedido=numero_pedido,
            nombre=nombre,
            correo=correo,
            direccion=direccion,
            total=total
        )

    return render_template(
        "pedido.html",
        items=items,
        total=total,
        nombre=session.get("usuario_nombre", ""),
        correo=session.get("usuario_correo", "")
    )


@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("404.html"), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True)
