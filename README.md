# Laboratorio 6 – Gráficos en 3D con PyOpenGL

Programación 3 · Ingeniería Mecatrónica · UMNG

Simulador de un **muñeco LEGO con 9 articulaciones**. Las piezas se modelaron en
**SolidWorks**, se importan una por una como STL y se ensamblan en Python.
Interfaz en **PyQt5** y renderizado en **PyOpenGL**.

## Instalación y ejecución

```
pip install -r requirements.txt
python main.py
```

## Qué se hizo

1. **Piezas.** Se modelaron en SolidWorks (`cad/`) y se exportaron a STL (`piezas/`),
   cada una en su propio sistema de coordenadas y en milímetros.
2. **Carga.** `stl_loader.py` lee cada STL y deja los triángulos y sus normales
   listos para OpenGL.
3. **Ensamble.** `muneco.py` ubica cada pieza con la posición y rotación que tiene
   en `LEGO.SLDASM` y las organiza en un árbol: cada pieza se dibuja dentro de la
   transformación de su padre, así el ensamble nunca se rompe.
4. **Articulaciones.** Cada una gira una pieza alrededor de un pivote y un eje
   medidos sobre los pines reales. Los hijos heredan el movimiento.
5. **Cara.** Los ojos y la sonrisa no vienen del STL: se dibujan con triángulos
   de OpenGL envueltos sobre el cilindro de la cabeza.
6. **Gorra con hélice.** Se agregaron dos piezas: la gorra (fija a la cabeza) y
   la hélice (articulación J9).
7. **Interfaz.** Sliders para articulaciones, cámara y modelo, vistas
   predefinidas, botones HOME y un movimiento demo animado.

> **Pendiente:** `GORRA.stl` y `HELICE.stl` son provisionales, generadas por
> código con `herramientas/generar_gorra_helice.py`. Falta modelarlas en
> SolidWorks (las medidas están en ese archivo) y reemplazarlas.

## Árbol del ensamble

```
cadera (raíz)
 ├─ pierna derecha   (J6)
 ├─ pierna izquierda (J7)
 └─ torso            (J8 cintura)
      ├─ cabeza          (J1 cuello)
      │    └─ gorra
      │         └─ hélice     (J9)
      ├─ brazo derecho   (J2 hombro)
      │    └─ mano derecha    (J4 muñeca)
      └─ brazo izquierdo (J3 hombro)
           └─ mano izquierda  (J5 muñeca)
```

## Articulaciones

| | Articulación | Pieza que mueve | Rango | Hijos que arrastra |
|---|---|---|---|---|
| J1 | Cuello | cabeza | ±90° | gorra y hélice |
| J2 | Hombro derecho | brazo derecho | ±180° | mano derecha |
| J3 | Hombro izquierdo | brazo izquierdo | ±180° | mano izquierda |
| J4 | Muñeca derecha | mano derecha | ±180° | – |
| J5 | Muñeca izquierda | mano izquierda | ±180° | – |
| J6 | Pierna derecha | pierna derecha | −70° a 90° | – |
| J7 | Pierna izquierda | pierna izquierda | −90° a 70° | – |
| J8 | Cintura (el torso gira sobre la cadera) | torso | ±50° | cabeza, gorra, hélice, brazos y manos |
| J9 | Hélice (gira sobre el botón de la gorra) | hélice | ±180° | – |

El valor 0 de cada articulación es la pose del ensamble `LEGO.SLDASM`.

## Archivos y métodos

### `main.py` — la ventana y los controles

**Clase `FilaSlider`**: una fila con nombre, slider y valor actual.

| Método | Qué hace |
|---|---|
| `valor` | Devuelve el valor actual del slider. |
| `_mostrar(v)` | Escribe el valor con su unidad (coma decimal). |
| `_al_mover(entero)` | Se llama al mover el slider: actualiza el texto y avisa con la señal `valor_cambiado`. |
| `poner_valor(v, emitir)` | Mueve el slider desde el código (HOME, mouse, demo). |

**Clase `VentanaPrincipal`**: arma la ventana y conecta todo.

| Método | Qué hace |
|---|---|
| `_grupo_articulaciones()` | Crea un slider por articulación y los botones HOME y Movimiento demo. |
| `_mover_articulacion(art, valor)` | Guarda el nuevo ángulo y redibuja. |
| `home_articulaciones()` | Regresa todas las articulaciones y sus sliders a la posición inicial. |
| `_activar_demo(activo)` | Enciende o apaga el temporizador de la animación. |
| `_paso_demo()` | Un cuadro de la animación: cada articulación oscila con una onda seno distinta. |
| `_grupo_camara()` | Sliders de azimut, elevación y distancia, y botones de vistas. |
| `_mover_camara(clave, valor)` | Cambia un parámetro de la cámara y redibuja. |
| `_sincronizar_camara()` | Pone los sliders al día cuando la cámara se mueve con el mouse o un botón. |
| `_grupo_modelo()` | Sliders para trasladar y rotar el muñeco completo, y botón HOME CÁMARA. |
| `_mover_modelo(clave, valor)` | Cambia la posición o rotación del muñeco y redibuja. |
| `_grupo_piezas()` | Lista de piezas importadas y botón para reemplazar una. |
| `cargar_todas_las_piezas()` | Importa los STL uno por uno al abrir la ventana. |
| `_cargar_pieza(nombre, ruta, fila)` | Carga un STL, lo manda al visor y anota el resultado en la lista. |
| `_reemplazar_pieza()` | Abre un diálogo para cambiar el STL de la pieza seleccionada. |

`main()` crea la aplicación y muestra la ventana.

### `visor_gl.py` — el widget donde OpenGL dibuja

**Clase `VisorGL`**

| Método | Qué hace |
|---|---|
| `poner_malla(nombre, malla)` | Recibe una pieza cargada y la deja pendiente de compilar. |
| `_compilar(nombre)` | Convierte la malla en una display list para dibujarla rápido. |
| `_dibujar_pieza(nombre)` | Pone el color de la pieza y dibuja su display list. |
| `initializeGL()` | Configuración inicial: fondo, profundidad, luces y material. |
| `resizeGL(w, h)` | Ajusta la perspectiva al tamaño de la ventana. |
| `_posicion_camara()` | Convierte azimut, elevación y distancia en la posición (x, y, z) de la cámara. |
| `paintGL()` | Dibuja un cuadro: cámara, piso, ejes y muñeco. |
| `_dibujar_piso()` | Dibuja la cuadrícula del piso. |
| `_dibujar_ejes(largo)` | Dibuja los ejes del modelo (X rojo, Y verde, Z azul). |
| `poner_vista(azimut, elevacion)` | Aplica una vista predefinida (Superior, Frontal, etc.). |
| `home_camara()` | Regresa la cámara y el modelo a sus valores iniciales. |
| `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent` | Arrastrar con clic izquierdo gira la cámara. |
| `wheelEvent(e)` | La rueda acerca o aleja la cámara. |

### `muneco.py` — piezas, ensamble y articulaciones

| Elemento | Qué hace |
|---|---|
| `Pieza` | Datos de una pieza: archivo STL, posición, rotación y color. |
| `PIEZAS` | Todas las piezas con su ubicación en el ensamble. |
| `HIJOS`, `RAIZ` | El árbol del ensamble: quién cuelga de quién. |
| `Articulacion` | Datos de una articulación: pieza, pivote, eje, límites y valor actual. `tipo` puede ser `"rot"` (gira) o `"tras"` (se desliza). |
| `crear_articulaciones()` | Devuelve la lista de las 9 articulaciones. |
| `_punto_cara(s, y, separacion)` | Coloca un punto de la cara sobre el cilindro de la cabeza. |
| `_ovalo(...)` | Dibuja un óvalo sobre la cabeza (ojos, brillos, puntas de la sonrisa). |
| `_arco(...)` | Dibuja una banda curva sobre la cabeza (la sonrisa). |
| `dibujar_cara()` | Dibuja la cara completa. |
| `_dibujar_nodo(nombre, ...)` | Aplica las articulaciones de una pieza, la dibuja y sigue con sus hijos (recursivo). |
| `dibujar_muneco(articulaciones, dibujar_pieza)` | Dibuja el muñeco completo, de pie sobre el piso. |

### `stl_loader.py` — lectura y escritura de STL

| Elemento | Qué hace |
|---|---|
| `Malla` | Guarda los vértices y normales de una pieza. `num_triangulos` da la cantidad de triángulos y `caja` la caja envolvente. |
| `_calcular_normales(tris)` | Calcula la normal de cada triángulo con el producto cruz. |
| `_leer_binario(datos)` | Lee un STL binario. |
| `_leer_ascii(texto)` | Lee un STL de texto. |
| `cargar_stl(ruta, escala)` | Detecta el formato, lee el archivo y devuelve una `Malla`. |
| `guardar_stl(ruta, tris, nombre)` | Guarda triángulos como STL binario. |

### `herramientas/generar_gorra_helice.py` — piezas provisionales

Las medidas de ambas piezas están al inicio del archivo, como constantes.

| Función | Qué hace |
|---|---|
| `cilindro(radio, y0, y1)` | Triángulos de un cilindro cerrado de eje Y. |
| `revolucion(perfil)` | Gira un perfil alrededor de Y (como "Revolución" en SolidWorks). |
| `gorra()` | Arma la gorra: cáscara de media elipse, botón y visera. |
| `visera()` | La medialuna de la visera que sobresale al frente. |
| `aspa(altura, giro_y)` | Un aspa ovalada, inclinada y girada alrededor de Y. |
| `helice()` | Arma la hélice: eje, cubo central, remate y dos aspas. |
| `main()` | Genera y guarda `GORRA.stl` y `HELICE.stl`. |

### Otros

| Archivo | Qué hace |
|---|---|
| `herramientas/sldprt_a_stl.py` | Convierte las `.SLDPRT` de `cad/` a STL sin abrir SolidWorks. |
| `herramientas/swcont.py` | Lee el contenedor interno de los archivos de SolidWorks (lo usa el convertidor). |
| `piezas/` | STL de cada pieza. |
| `cad/` | Archivos originales de SolidWorks (piezas, ensamble y plano). |
| `requirements.txt` | Dependencias: PyQt5, PyOpenGL y numpy. |

## Cumplimiento de la guía (resultados mínimos)

1. Piezas modeladas en SolidWorks (`cad/`), sin cubos, esferas ni prismas (gorra y hélice pendientes, ver arriba).
2. Importación una por una en la interfaz (lista de piezas + botón para reemplazar cada una).
3. Ensamble hecho en Python (`muneco.py`): cada pieza se ubica con la posición y rotación del ensamble.
4. 9 articulaciones con sliders y valores en vivo.
5. Ensamble jerárquico con `glPushMatrix` / `glPopMatrix`: nunca se rompe.
6. Cámara con sliders y mouse, y vistas Superior, Isométrica, Lateral y Frontal.
7. Botón HOME para las articulaciones (también regresa los sliders).
8. Traslación y rotación del muñeco en X, Y, Z con valores visibles y botón HOME CÁMARA.
9. Python + PyOpenGL.

Extra: botón **Movimiento demo** (movimiento predeterminado animado).

## Si cambias una pieza en SolidWorks

* Guardar como → STL, en milímetros, con el mismo nombre que está en `piezas/`.
* O usar el convertidor: `python herramientas/sldprt_a_stl.py cad piezas`
* Si cambias el ensamble, actualizar las posiciones y rotaciones en `muneco.py`.

## Controles

* Arrastrar con clic izquierdo sobre la escena: girar la cámara.
* Rueda del mouse: acercar / alejar.
