# muneco.py
# Aca estan los datos del muñeco LEGO y la funcion que lo dibuja.
# Las medidas estan en mm y son las del ensamble LEGO.SLDASM de SolidWorks.

import math
from OpenGL.GL import *

# colores (R, G, B)
ROJO = (0.8, 0.1, 0.1)
AMARILLO = (0.98, 0.8, 0.1)
AZUL = (0.1, 0.3, 0.7)
VERDE = (0.1, 0.6, 0.25)

# cada pieza: [archivo stl, posicion en el ensamble, rotacion (x, y, z), color]
piezas = {
    "cadera":     ["CADERA.stl",           (-1.16, -29.03, 1011.70),  (0, 0, 0),               AZUL],
    "pierna_der": ["PIERNA_DERECHA.stl",   (-12.28, -50.09, 1016.36), (-20.44, 0, 0),          AZUL],
    "pierna_izq": ["PIERNA_IZQUIERDA.stl", (10.99, -50.48, 1008.24),  (15.00, 0, 0),           AZUL],
    "torso":      ["TORZO.stl",            (-1.16, -3.01, 1011.70),   (0, 0, 0),               ROJO],
    "cabeza":     ["Cabeza_lego.stl",      (-1.16, 32.69, 1011.70),   (0, 26.10, 0),           AMARILLO],
    "gorra":      ["GORRA.stl",            (-1.16, 39.69, 1011.70),   (0, 0, 0),               AZUL],
    "helice":     ["HELICE.stl",           (-1.16, 54.19, 1011.70),   (0, 0, 0),               VERDE],
    "brazo_der":  ["BRAZO_DERECHO.stl",    (-25.05, 2.75, 1019.32),   (-43.17, 5.49, -5.83),   ROJO],
    "brazo_izq":  ["BRAZO_IZQUIERDO.stl",  (23.74, -1.80, 1013.59),   (-11.70, -1.41, 6.78),   ROJO],
    "mano_der":   ["MANOS.stl",            (-26.08, -0.28, 1042.98),  (72.05, 26.12, -173.36), AMARILLO],
    "mano_izq":   ["MANOS.stl",            (25.60, -17.33, 1033.32),  (-46.69, -3.37, 4.33),   AMARILLO],
}

# articulaciones: [nombre, pivote (punto por donde gira), eje de giro, minimo, maximo]
# el pivote lo saque de los pines y agujeros de cada pieza
articulaciones = [
    ["J1 Cuello",     (-1.16, 17.69, 1011.70),   (0, 1, 0),                -90, 90],
    ["J2 Hombro der", (-15.79, 6.12, 1011.70),   (0.990, -0.139, 0),       -180, 180],
    ["J3 Hombro izq", (14.02, 6.14, 1011.70),    (0.993, 0.120, 0),        -180, 180],
    ["J4 Muñeca der", (-25.99, -0.84, 1035.86),  (0.104, -0.258, -0.961),  -180, 180],
    ["J5 Muñeca izq", (25.16, -13.62, 1027.22),  (-0.075, 0.681, -0.729),  -180, 180],
    ["J6 Pierna der", (-12.28, -37.58, 1011.70), (1, 0, 0),                -70, 90],
    ["J7 Pierna izq", (10.99, -37.58, 1011.70),  (1, 0, 0),                -90, 70],
    ["J8 Cintura",    (-1.16, -21.91, 1011.70),  (0, 1, 0),                -50, 50],
    ["J9 Helice",     (-1.16, 54.19, 1011.70),   (0, 1, 0),                -180, 180],
]

# angulo actual de cada articulacion (en HOME todos son 0)
angulos = [0, 0, 0, 0, 0, 0, 0, 0, 0]

# aca main.py guarda las display lists de cada pieza
listas = {}


def girar(i):
    # para que gire en el pivote y no en el origen:
    # muevo el pivote al origen, giro y lo devuelvo
    pivote = articulaciones[i][1]
    eje = articulaciones[i][2]
    glTranslatef(pivote[0], pivote[1], pivote[2])
    glRotatef(angulos[i], eje[0], eje[1], eje[2])
    glTranslatef(-pivote[0], -pivote[1], -pivote[2])


def poner_pieza(nombre):
    # pone la pieza en su sitio del ensamble y la dibuja
    archivo, pos, rot, color = piezas[nombre]
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rot[0], 1, 0, 0)
    glRotatef(rot[1], 0, 1, 0)
    glRotatef(rot[2], 0, 0, 1)
    glColor3f(color[0], color[1], color[2])
    if nombre in listas:
        glCallList(listas[nombre])
    glPopMatrix()


# ----- cara -----
# la cabeza es un cilindro de radio 15.22, entonces cada punto de la cara
# lo pongo encima de la superficie del cilindro
RADIO = 15.22

def punto_cara(x, y):
    z = math.sqrt(RADIO * RADIO - x * x) + 0.15
    glNormal3f(x / RADIO, 0, z / RADIO)
    glVertex3f(x, y, z)


def dibujar_cara():
    glColor3f(0, 0, 0)
    # ojos
    for x0 in [-4.6, 4.6]:
        glBegin(GL_POLYGON)
        for i in range(20):
            a = 2 * math.pi * i / 20
            punto_cara(x0 + 1.5 * math.cos(a), 2.2 + 1.9 * math.sin(a))
        glEnd()
    # sonrisa (un pedazo de circulo grueso)
    glBegin(GL_QUAD_STRIP)
    for i in range(21):
        a = math.radians(215 + 110 * i / 20)
        punto_cara(5.55 * math.cos(a), 1.0 + 5.55 * math.sin(a))
        punto_cara(6.45 * math.cos(a), 1.0 + 6.45 * math.sin(a))
    glEnd()


def dibujar_muneco():
    glPushMatrix()
    # en SolidWorks Y es arriba, aca Z es arriba, por eso giro 90 en X
    glRotatef(90, 1, 0, 0)
    # muevo el muñeco para que quede parado en el piso y centrado
    glTranslatef(1.16, 74.70, -1011.70)

    poner_pieza("cadera")

    # pierna derecha
    glPushMatrix()
    girar(5)
    poner_pieza("pierna_der")
    glPopMatrix()

    # pierna izquierda
    glPushMatrix()
    girar(6)
    poner_pieza("pierna_izq")
    glPopMatrix()

    # torso (todo lo de arriba se mueve con la cintura)
    glPushMatrix()
    girar(7)
    poner_pieza("torso")

    # cabeza con la cara, la gorra y la helice
    glPushMatrix()
    girar(0)
    poner_pieza("cabeza")
    glPushMatrix()
    pos = piezas["cabeza"][1]
    glTranslatef(pos[0], pos[1], pos[2])
    dibujar_cara()
    glPopMatrix()
    poner_pieza("gorra")
    glPushMatrix()
    girar(8)
    poner_pieza("helice")
    glPopMatrix()
    glPopMatrix()

    # brazo derecho y su mano
    glPushMatrix()
    girar(1)
    poner_pieza("brazo_der")
    glPushMatrix()
    girar(3)
    poner_pieza("mano_der")
    glPopMatrix()
    glPopMatrix()

    # brazo izquierdo y su mano
    glPushMatrix()
    girar(2)
    poner_pieza("brazo_izq")
    glPushMatrix()
    girar(4)
    poner_pieza("mano_izq")
    glPopMatrix()
    glPopMatrix()

    glPopMatrix()  # fin del torso
    glPopMatrix()
