# Laboratorio 6 – Gráficos en 3D con PyOpenGL

Programación 3 · Ingeniería Mecatrónica · UMNG

Simulador de un **muñeco LEGO con 7 articulaciones**. Las piezas se modelaron en
**SolidWorks**, se importan una por una como STL y se ensamblan en Python.
Interfaz en **PyQt5** y renderizado en **PyOpenGL**.

## Instalación y ejecución

```
pip install -r requirements.txt
python main.py
```

## Archivos

| Archivo | Qué hace |
|---|---|
| `main.py` | Ventana principal: sliders, botones, vistas, HOME, lista de piezas |
| `visor_gl.py` | Widget OpenGL: luces, cámara, mouse, dibujo de la escena |
| `muneco.py` | Piezas, ensamble jerárquico y las 7 articulaciones |
| `stl_loader.py` | Lectura de archivos STL (binario y ASCII) |
| `piezas/` | STL de cada pieza (en mm, cada una en su propio sistema de coordenadas) |
| `cad/` | Archivos originales de SolidWorks (piezas, ensamble y plano) |
| `herramientas/sldprt_a_stl.py` | Convierte las `.SLDPRT` de `cad/` a STL sin abrir SolidWorks |

## Articulaciones

| | Articulación | Pieza que mueve | Hijos que arrastra |
|---|---|---|---|
| J1 | Cuello | cabeza | – |
| J2 | Hombro derecho | brazo derecho | mano derecha |
| J3 | Hombro izquierdo | brazo izquierdo | mano izquierda |
| J4 | Muñeca derecha | mano derecha | – |
| J5 | Muñeca izquierda | mano izquierda | – |
| J6 | Pierna derecha | pierna derecha | – |
| J7 | Pierna izquierda | pierna izquierda | – |

El valor 0 de cada articulación es la pose del ensamble `LEGO.SLDASM`.
Los pivotes y ejes se midieron sobre los pines y agujeros reales de las piezas
(pin de la cadera, agujeros de las piernas, pines de hombros, manos y cuello).

## Cumplimiento de la guía (resultados mínimos)

1. Piezas modeladas en SolidWorks (`cad/`), sin cubos, esferas ni prismas.
2. Importación una por una en la interfaz (lista de piezas + botón para reemplazar cada una).
3. Ensamble hecho en Python (`muneco.py`): cada pieza se ubica con la posición y rotación del ensamble.
4. 7 articulaciones con sliders y valores en vivo.
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
