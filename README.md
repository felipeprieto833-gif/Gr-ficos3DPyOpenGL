# Laboratorio 6 - Graficos en 3D con PyOpenGL

Muñeco LEGO hecho en SolidWorks, importado a Python y animado con PyOpenGL.
La interfaz esta hecha con PyQt5.

## Como correrlo

    pip install -r requirements.txt
    python main.py

## Archivos

- main.py: la ventana, los sliders, la camara y el dibujo con OpenGL
- muneco.py: las piezas, las articulaciones y la funcion que dibuja el muñeco
- piezas/: los STL de cada pieza y los archivos de SolidWorks

## Articulaciones

J1 cuello, J2 y J3 hombros, J4 y J5 muñecas, J6 y J7 piernas, J8 cintura y J9 helice de la gorra.

## Controles

- Sliders para mover cada articulacion, la camara y el modelo
- Arrastrar con el mouse para girar la camara y la rueda para acercar
- Botones de vista superior, isometrica, lateral y frontal
- HOME para volver las articulaciones a 0 y HOME CAMARA para la camara y el modelo
- Movimiento demo para que se mueva solo
