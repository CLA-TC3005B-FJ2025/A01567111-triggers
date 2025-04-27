from flask import Flask, jsonify, request
import mysql.connector

app = Flask(__name__)

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'contrasena',
    'database': 'tienda'
}


def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        return None


def close_db_connection(cnx):
    if cnx and cnx.is_connected():
        cnx.close()


@app.route('/productos', methods=['GET'])
def get_productos():
    cnx = get_db_connection()
    if not cnx:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    cursor = cnx.cursor(dictionary=True)
    query = "SELECT id_producto, nombre, precio, stock FROM productos"
    cursor.execute(query)
    productos = cursor.fetchall()
    cursor.close()
    close_db_connection(cnx)
    return jsonify(productos)


@app.route('/productos/<int:id_producto>', methods=['GET'])
def get_producto(id_producto):
    cnx = get_db_connection()
    if not cnx:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    cursor = cnx.cursor(dictionary=True)
    query = "SELECT id_producto, nombre, precio, stock FROM productos WHERE id_producto = %s"
    cursor.execute(query, (id_producto,))
    producto = cursor.fetchone()
    cursor.close()
    close_db_connection(cnx)
    if producto:
        return jsonify(producto)
    return jsonify({'message': 'Producto no encontrado'}), 404


@app.route('/productos', methods=['POST'])
def create_producto():
    data = request.get_json()
    nombre = data.get('nombre')
    precio = data.get('precio')
    stock = data.get('stock')

    if not nombre or precio is None or stock is None:
        return jsonify({'error': 'Faltan campos obligatorios (nombre, precio, stock)'}), 400

    cnx = get_db_connection()
    if not cnx:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    cursor = cnx.cursor()
    query = "INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (nombre, precio, stock))
        cnx.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        close_db_connection(cnx)
        return jsonify({'id_producto': nuevo_id, 'message': 'Producto creado exitosamente'}), 201
    except mysql.connector.Error as err:
        cnx.rollback()
        cursor.close()
        close_db_connection(cnx)
        if err.errno == 1062:  # Código de error para duplicado (ejemplo)
            return jsonify({'error': f'Error al crear el producto: {err.msg}'}), 409
        elif err.sqlstate == '45000':  # Código de error para SIGNAL (triggers)
            return jsonify({'error': f'Error al crear el producto: {err.msg}'}), 400
        else:
            return jsonify({'error': f'Error al crear el producto: {err.msg}'}), 500


@app.route('/productos/<int:id_producto>', methods=['PUT'])
def update_producto(id_producto):
    data = request.get_json()
    nombre = data.get('nombre')
    precio = data.get('precio')
    stock = data.get('stock')

    if not nombre or precio is None or stock is None:
        return jsonify({'error': 'Faltan campos obligatorios (nombre, precio, stock)'}), 400

    cnx = get_db_connection()
    if not cnx:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    cursor = cnx.cursor()
    query = "UPDATE productos SET nombre = %s, precio = %s, stock = %s WHERE id_producto = %s"
    try:
        cursor.execute(query, (nombre, precio, stock, id_producto))
        cnx.commit()
        if cursor.rowcount > 0:
            cursor.close()
            close_db_connection(cnx)
            return jsonify({'message': 'Producto actualizado exitosamente'}), 200
        else:
            cursor.close()
            close_db_connection(cnx)
            return jsonify({'message': 'Producto no encontrado'}), 404
    except mysql.connector.Error as err:
        cnx.rollback()
        cursor.close()
        close_db_connection(cnx)
        if err.errno == 1062:  # Código de error para duplicado (ejemplo)
            return jsonify({'error': f'Error al actualizar el producto: {err.msg}'}), 409
        elif err.sqlstate == '45000':  # Código de error para SIGNAL (triggers)
            return jsonify({'error': f'Error al actualizar el producto: {err.msg}'}), 400
        else:
            return jsonify({'error': f'Error al actualizar el producto: {err.msg}'}), 500


@app.route('/productos/<int:id_producto>', methods=['DELETE'])
def delete_producto(id_producto):
    cnx = get_db_connection()
    if not cnx:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    cursor = cnx.cursor()
    query = "DELETE FROM productos WHERE id_producto = %s"
    try:
        cursor.execute(query, (id_producto,))
        cnx.commit()
        if cursor.rowcount > 0:
            cursor.close()
            close_db_connection(cnx)
            return jsonify({'message': 'Producto eliminado exitosamente'}), 200
        else:
            cursor.close()
            close_db_connection(cnx)
            return jsonify({'message': 'Producto no encontrado'}), 404
    except mysql.connector.Error as err:
        cnx.rollback()
        cursor.close()
        close_db_connection(cnx)
        return jsonify({'error': f'Error al eliminar el producto: {err.msg}'}), 500


@app.route('/historial_stock/<int:id_producto>', methods=['GET'])
def get_historial_stock(id_producto):
    cnx = get_db_connection()
    if not cnx:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    cursor = cnx.cursor(dictionary=True)
    query = "SELECT id_historial, fecha_hora, stock_anterior, stock_nuevo, usuario FROM historial_stock WHERE id_producto = %s ORDER BY fecha_hora DESC"
    cursor.execute(query, (id_producto,))
    historial = cursor.fetchall()
    cursor.close()
    close_db_connection(cnx)
    if historial:
        return jsonify(historial)
    return jsonify({'message': f'No se encontró historial de stock para el producto con ID {id_producto}'}), 404


if __name__ == '__main__':
    app.run(debug=True)
