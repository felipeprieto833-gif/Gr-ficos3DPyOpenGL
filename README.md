# Laboratorio 6 – Gráficos en 3D con PyOpenGL

Programación 3 · Ingeniería Mecatrónica · UMNG

Simulador de un brazo robótico de **6 articulaciones** (5 rotacionales + 1 lineal en la pinza),
con interfaz en **PyQt5** y renderizado en **PyOpenGL**.

## Instalación y ejecución

```
pip install -r requirements.txt
python generar_piezas_provisionales.py   # solo si no tienes aún las piezas de SolidWorks
python main.py
```

## Archivos

| Archivo | Qué hace |
|---|---|
| `main.py` | Ventana principal: sliders, botones, vistas, HOME, lista de piezas |
| `visor_gl.py` | Widget OpenGL: luces, cámara, mouse, dibujo de la escena |
| `robot.py` | Definición de las 6 articulaciones y ensamble jerárquico |
| `stl_loader.py` | Lectura de archivos STL (binario y ASCII) |
| `generar_piezas_provisionales.py` | Crea piezas de prueba en `piezas/` |
| `piezas/` | Archivos STL de cada pieza |

## Cumplimiento de la guía (resultados mínimos)

1. Piezas CAD: **pendiente** reemplazar las provisionales por las de SolidWorks.
2. Importación una por una en la interfaz (lista de piezas + botón para reemplazar cada una).
3. Ensamble hecho en Python (`robot.py`).
4. 6 articulaciones con sliders y valores en vivo.
5. Ensamble jerárquico con `glPushMatrix` / `glPopMatrix`: nunca se rompe.
6. Cámara con sliders y mouse, y vistas Superior, Isométrica, Lateral y Frontal.
7. Botón HOME para las articulaciones (también regresa los sliders).
8. Traslación y rotación del modelo en X, Y, Z con valores visibles y botón HOME CÁMARA.
9. Python + PyOpenGL.

Extra: botón **Movimiento demo** (movimiento predeterminado animado).

## Cómo exportar las piezas desde SolidWorks

* Cada pieza por separado, en **milímetros**, con el **origen en el eje de su articulación**.
* Guardar como → STL → Opciones: escoger el sistema de coordenadas de la articulación
  y **desactivar** "No trasladar datos de salida STL al espacio positivo".
* Usar los mismos nombres: `base.stl`, `hombro.stl`, `brazo.stl`, `antebrazo.stl`,
  `muneca.stl`, `palma.stl`, `dedo.stl`.
* Si cambian las medidas, ajustar los `offset` de cada articulación en `robot.py`.

## Controles

* Arrastrar con clic izquierdo sobre la escena: girar la cámara.
* Rueda del mouse: acercar / alejar.
