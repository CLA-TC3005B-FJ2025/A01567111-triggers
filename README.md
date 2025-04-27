# Ejercicio de Triggers en MySQL 

## Prerequisitos

Antes de comenzar, asegúrate de tener:

- **GitHub Codespaces** habilitado.
- **Docker** ejecutándose en tu Codespace.
- **Python 3** instalado.
- **mysql-connector-python** instalado en tu entorno Python.

### Iniciar la instancia de MySQL en Docker

Para iniciar una instancia de **MySQL** en un contenedor Docker, ejecuta el siguiente comando en la terminal de tu **GitHub Codespace**:

```sh
docker run --name mysql-container -e MYSQL_ROOT_PASSWORD=contrasena -e MYSQL_DATABASE=testdb -p 3306:3306 -d mysql:latest
```

Configuremos la base de datos que usamos en el ejercicio pasado (stored-procedures):

1.  **Conéctate al servidor MySQL** usando la herramienta de línea de comandos:

    ```bash
    docker exec -it mysql-container mysql -u root -pcontrasena
    ```

2.  **Selecciona la base de datos `tienda`:**

    ```sql
    CREATE DATABASE tienda;
    USE tienda;
    ```


3.  **Crea la tabla `productos`**:

    ```sql
    CREATE TABLE IF NOT EXISTS productos (
        id_producto INT PRIMARY KEY AUTO_INCREMENT,
        nombre VARCHAR(100) NOT NULL,
        precio DECIMAL(10, 2) NOT NULL,
        stock INT NOT NULL DEFAULT 0
    );
    ```

4.  **Inserta algunos datos de prueba** en la tabla `productos`:

    ```sql
    INSERT INTO productos (nombre, precio, stock) VALUES
    ('Laptop', 1200.50, 10),
    ('Mouse', 25.99, 50),
    ('Teclado', 75.00, 30),
    ('Monitor', 300.75, 15);
    ```
    
### Escenario:

Continuando con la base de datos `tienda` y la tabla `productos`, vamos a crear un trigger que registre automáticamente cualquier cambio en el stock de los productos en una tabla de auditoría llamada `historial_stock`.

**Ejercicio:**

1.  **Conéctate al servidor MySQL** usando la herramienta de línea de comandos (si no estás conectado):

    ```bash
    docker exec -it mysql-container mysql -u root -pcontrasena
    ```

2.  **Selecciona la base de datos `tienda`:**

    ```sql
    USE tienda;
    ```

3.  **Crea la tabla `historial_stock`** para almacenar los registros de auditoría:

    ```sql
    CREATE TABLE IF NOT EXISTS historial_stock (
        id_historial INT PRIMARY KEY AUTO_INCREMENT,
        id_producto INT NOT NULL,
        nombre_producto VARCHAR(100) NOT NULL,
        fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        stock_anterior INT,
        stock_nuevo INT,
        usuario VARCHAR(100)
    );
    ```

4.  **Crea un trigger llamado `registrar_cambio_stock`** que se active **DESPUÉS** de cada **ACTUALIZACIÓN** en la tabla `productos`. Este trigger deberá insertar un nuevo registro en la tabla `historial_stock` con la siguiente información:
    * `id_producto`: El ID del producto actualizado.
    * `nombre_producto`: El nombre del producto actualizado.
    * `fecha_hora`: La fecha y hora del cambio (se generará automáticamente).
    * `stock_anterior`: El valor del stock **antes** de la actualización.
    * `stock_nuevo`: El valor del stock **después** de la actualización.
    * `usuario`: El usuario que realizó la modificación (podemos usar `USER()` function de MySQL).

    ```sql
    DELIMITER //
    CREATE TRIGGER registrar_cambio_stock
    AFTER UPDATE ON productos
    FOR EACH ROW
    BEGIN
        IF OLD.stock <> NEW.stock THEN
            INSERT INTO historial_stock (id_producto, nombre_producto, stock_anterior, stock_nuevo, usuario)
            VALUES (OLD.id_producto, OLD.nombre, OLD.stock, NEW.stock, USER());
        END IF;
    END //
    DELIMITER ;
    ```

    * `DELIMITER //` y `DELIMITER ;` cambian el delimitador, como ya lo habíamos visto previamente.
    * `CREATE TRIGGER registrar_cambio_stock` define el nombre del trigger.
    * `AFTER UPDATE ON productos` especifica que el trigger se activará después de una operación `UPDATE` en la tabla `productos`.
    * `FOR EACH ROW` indica que el trigger se ejecutará una vez por cada fila afectada por la actualización.
    * `BEGIN ... END` contiene la lógica del trigger.
    * `IF OLD.stock <> NEW.stock THEN` asegura que solo se registre un cambio si el valor del stock realmente ha cambiado.
    * `OLD.stock` y `NEW.stock` hacen referencia al valor del stock antes y después de la actualización, respectivamente.
    * La sentencia `INSERT INTO historial_stock ...` inserta un nuevo registro en la tabla de auditoría con la información relevante.
    * `USER()` devuelve el nombre del usuario de MySQL que está ejecutando la operación.

5.  **Realiza algunas actualizaciones en la tabla `productos`** para activar el trigger:

    ```sql
    UPDATE productos SET stock = stock - 2 WHERE id_producto = 1; -- Reduce el stock de 'Laptop'
    UPDATE productos SET precio = precio * 1.10 WHERE id_producto = 3; -- Aumenta el precio del 'Teclado' (no debería registrarse en historial_stock)
    UPDATE productos SET stock = stock + 10 WHERE id_producto = 2; -- Aumenta el stock del 'Mouse'
    ```

6.  **Verifica el contenido de la tabla `historial_stock`:**

    ```sql
    SELECT * FROM historial_stock;
    ```

    Deberías ver registros correspondientes a las actualizaciones que modificaron el stock de los productos ('Laptop' y 'Mouse'). La actualización del precio del 'Teclado' no debería haber generado un registro.

7.  **Crea otro trigger llamado `validar_nuevo_stock`** que se active **ANTES** de cada **INSERCIÓN** y uno `validar_actualizacion_stock` que se ejecute **ANTES** de cada **ACTUALIZACIÓN** en la tabla `productos`. Este trigger deberá verificar que el nuevo valor del `stock` no sea negativo. Si el nuevo stock es negativo, deberá impedir la inserción o actualización.

    ```sql
    DELIMITER //
    CREATE TRIGGER validar_nuevo_stock
    BEFORE INSERT ON productos
    FOR EACH ROW
    BEGIN
        IF NEW.stock < 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El stock no puede ser un valor negativo.';
        END IF;
    END //
    DELIMITER ;

    DELIMITER //
    CREATE TRIGGER validar_actualizacion_stock
    BEFORE UPDATE ON productos
    FOR EACH ROW
    BEGIN
        IF NEW.stock < 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El stock no puede ser un valor negativo.';
        END IF;
    END //
    DELIMITER ;
    ```

    * `BEFORE INSERT ON productos` y `BEFORE UPDATE ON productos` especifican cuándo se activarán los triggers.
    * `SIGNAL SQLSTATE '45000' ...` genera un error SQL personalizado *(unhandled user-defined exception)* que detiene la operación de inserción o actualización si la condición (`NEW.stock < 0`) se cumple.

8.  **Intenta insertar un nuevo producto con stock negativo:**

    ```sql
    INSERT INTO productos (nombre, precio, stock) VALUES ('Producto Error', 50.00, -5);
    ```

    Deberías recibir un error indicando que el stock no puede ser negativo.

9.  **Intenta actualizar el stock de un producto existente a un valor negativo:**

    ```sql
    UPDATE productos SET stock = -10 WHERE id_producto = 2;
    ```

    También deberías recibir el mismo error.

10. **Para ver la lista de triggers** en la base de datos actual, puedes usar el siguiente comando:

    ```sql
    SHOW TRIGGERS FROM tienda;
    ```

11. **Para ver la definición de un trigger específico** (por ejemplo, `registrar_cambio_stock`):

    ```sql
    SHOW CREATE TRIGGER registrar_cambio_stock;
    ```

12. **Para eliminar un trigger** (por ejemplo, `registrar_cambio_stock`):

    **Solo** para que sepan, no lo ejecutemos por el momento

    ```sql
    DROP TRIGGER IF EXISTS registrar_cambio_stock;
    ```

13. **Salimos de la herramienta** 

    ```sql
    quit
    ```

# Ejecución de servicios web CRUD:

### En la terminal ejecuta
```sh
cd webservices
python ws.py
```
### Abre *otra* terminal para ejecutar los siguientes servicios web
# Ejemplos de Peticiones (usando `curl`) para la API de Productos

A continuación, se muestran ejemplos de cómo interactuar con los servicios web CRUD para la tabla `productos` utilizando la herramienta de línea de comandos `curl`. Asumimos que la aplicación Flask se está ejecutando en `http://127.0.0.1:5000`.

## Obtener todos los productos (GET)

```bash
curl http://127.0.0.1:5000/productos
```
## Obtener un los producto (GET)

```bash
curl http://127.0.0.1:5000/productos/1
```

## Crear un nuevo producto (POST)

```bash
curl -X POST http://127.0.0.1:5000/productos -H "Content-Type: application/json" -d '{"nombre": "iPhone", "precio": 20000, "stock": 3}'
```
Crear un nuevo producto con stock negativo (debe generar error el webservice)
```bash
curl -X POST http://127.0.0.1:5000/productos -H "Content-Type: application/json" -d '{"nombre": "iPhone", "precio": 20000, "stock": -3}'

```

## Actualizar un producto existente (PUT)

```bash
curl -X PUT http://127.0.0.1:5000/productos/1 -H "Content-Type: application/json" -d '{"nombre": "Nuevo", "precio": 5444, "stock": 33}'
```

Actualizar un producto con stock negativo (debe generar error el webservice)

```bash
curl -X PUT http://127.0.0.1:5000/productos/1 -H "Content-Type: application/json" -d '{"nombre": "Nuevo", "precio": 5444, "stock": -33}'
```

## Obtener el historial de un producto (GET)

```bash
curl http://127.0.0.1:5000/historial_stock/1
```


# Respaldo y restauración de base de datos
Respaldo
```sh
docker exec mysql-container mysqldump -u root -pcontrasena --routines --events tienda > backup.sql
```

Restauración
```sh
docker exec -i mysql-container mysql -u root -pcontrasena tienda < backup.sql
```
