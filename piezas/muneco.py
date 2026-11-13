"""
Muñeco LEGO: piezas, ensamble y articulaciones.

Todas las medidas están en milímetros y en el MISMO sistema de
coordenadas del ensamble LEGO.SLDASM de SolidWorks (allá el eje Y
es "arriba"). Así los números se pueden comparar con el CAD.

IDEA CLAVE (ensamble jerárquico):
Piensa en un muñeco de verdad. Si giras el brazo, la mano se va con
él; si giras la cadera, se van las piernas. En OpenGL eso se logra
dibujando cada pieza DENTRO de la transformación de su "padre":

    torso
     ├─ cabeza          (J1 gira en el cuello)
     ├─ brazo derecho   (J2 hombro)
     │    └─ mano derecha    (J4 muñeca)
     ├─ brazo izquierdo (J3 hombro)
     │    └─ mano izquierda  (J5 muñeca)
     └─ cadera (fija al torso)
          ├─ pierna derecha   (J6)
          └─ pierna izquierda (J7)

Como cada transformación se acumula sobre la del padre, el ensamble
nunca se rompe (punto 5 de la guía).
"""
from dataclasses import dataclass, field
from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslatef, glRotatef


@dataclass
class Pieza:
    archivo: str      # STL dentro de la carpeta piezas/
    posicion: tuple   # dónde quedó la pieza en el ensamble (mm)
    rotacion: tuple   # giros en X, Y, Z (grados) que tiene en el ensamble
    color: tuple      # (R, G, B) entre 0 y 1


ROJO = (0.80, 0.10, 0.10)
AMARILLO = (0.98, 0.80, 0.10)
AZUL = (0.10, 0.30, 0.70)

# Posición y rotación de cada pieza, tomadas del ensamble LEGO.SLDASM
PIEZAS = {
    "torso":       Pieza("TORZO.stl",            (-1.16,  -3.01, 1011.70), (0, 0, 0),                ROJO),
    "cabeza":      Pieza("Cabeza_lego.stl",      (-1.16,  32.69, 1011.70), (0, 26.10, 0),            AMARILLO),
    "brazo_der":   Pieza("BRAZO_DERECHO.stl",    (-25.05,  2.75, 1019.32), (-43.17, 5.49, -5.83),    ROJO),
    "brazo_izq":   Pieza("BRAZO_IZQUIERDO.stl",  (23.74,  -1.80, 1013.59), (-11.70, -1.41, 6.78),    ROJO),
    "mano_der":    Pieza("MANOS.stl",            (-26.08, -0.28, 1042.98), (72.05, 26.12, -173.36),  AMARILLO),
    "mano_izq":    Pieza("MANOS.stl",            (25.60, -17.33, 1033.32), (-46.69, -3.37, 4.33),    AMARILLO),
    "cadera":      Pieza("CADERA.stl",           (-1.16, -29.03, 1011.70), (0, 0, 0),                AZUL),
    "pierna_der":  Pieza("PIERNA_DERECHA.stl",   (-12.28, -50.09, 1016.36), (-20.44, 0, 0),          AZUL),
    "pierna_izq":  Pieza("PIERNA_IZQUIERDA.stl", (10.99, -50.48, 1008.24), (15.00, 0, 0),            AZUL),
}

# Quién cuelga de quién (el árbol del dibujo de arriba)
HIJOS = {
    "torso":     ["cabeza", "brazo_der", "brazo_izq", "cadera"],
    "brazo_der": ["mano_der"],
    "brazo_izq": ["mano_izq"],
    "cadera":    ["pierna_der", "pierna_izq"],
}
RAIZ = "torso"

# Para centrar el muñeco: los pies quedan en el piso y el torso en el centro
CENTRO_ENSAMBLE = (-1.16, -74.70, 1011.70)


@dataclass
class Articulacion:
    nombre: str
    pieza: str      # la pieza que mueve (y con ella, todos sus hijos)
    pivote: tuple   # punto por donde pasa el eje de giro (pin o agujero), en mm
    eje: tuple      # dirección del eje de giro
    minimo: float
    maximo: float
    inicial: float  # posición HOME (0 = la pose del ensamble de SolidWorks)
    tipo: str = "rot"
    valor: float = field(default=None)

    def __post_init__(self):
        if self.valor is None:
            self.valor = self.inicial

    @property
    def unidad(self):
        return "°" if self.tipo == "rot" else " mm"


def crear_articulaciones():
    """Las 7 articulaciones. Pivotes y ejes medidos sobre los pines de cada pieza."""
    return [
        Articulacion("J1 Cuello",      "cabeza",     (-1.16, 17.69, 1011.70),  (0, 1, 0),              -90, 90, 0),
        Articulacion("J2 Hombro der",  "brazo_der",  (-15.79, 6.12, 1011.70),  (0.990, -0.139, 0),     -180, 180, 0),
        Articulacion("J3 Hombro izq",  "brazo_izq",  (14.02, 6.14, 1011.70),   (0.993, 0.120, 0),      -180, 180, 0),
        Articulacion("J4 Muñeca der",  "mano_der",   (-25.99, -0.84, 1035.86), (0.104, -0.258, -0.961), -180, 180, 0),
        Articulacion("J5 Muñeca izq",  "mano_izq",   (25.16, -13.62, 1027.22), (-0.075, 0.681, -0.729), -180, 180, 0),
        Articulacion("J6 Pierna der",  "pierna_der", (-12.28, -37.58, 1011.70), (1, 0, 0),             -70, 90, 0),
        Articulacion("J7 Pierna izq",  "pierna_izq", (10.99, -37.58, 1011.70),  (1, 0, 0),             -90, 70, 0),
    ]


def _dibujar_nodo(nombre, articulaciones, dibujar_pieza):
    glPushMatrix()

    # 1) Si esta pieza tiene articulación, girar alrededor de su pivote.
    #    Truco: llevar el pivote al origen, girar y devolverlo
    #    (como una puerta: gira alrededor de la bisagra, no de su centro).
    art = articulaciones.get(nombre)
    if art is not None:
        glTranslatef(*art.pivote)
        glRotatef(art.valor, *art.eje)
        glTranslatef(-art.pivote[0], -art.pivote[1], -art.pivote[2])

    # 2) Poner la pieza donde estaba en el ensamble y dibujarla
    p = PIEZAS[nombre]
    glPushMatrix()
    glTranslatef(*p.posicion)
    glRotatef(p.rotacion[0], 1, 0, 0)
    glRotatef(p.rotacion[1], 0, 1, 0)
    glRotatef(p.rotacion[2], 0, 0, 1)
    dibujar_pieza(nombre)
    glPopMatrix()

    # 3) Los hijos heredan el giro de esta pieza
    for hijo in HIJOS.get(nombre, []):
        _dibujar_nodo(hijo, articulaciones, dibujar_pieza)

    glPopMatrix()


def dibujar_muneco(articulaciones, dibujar_pieza):
    """Dibuja el muñeco completo, de pie sobre el piso (eje Z hacia arriba)."""
    por_pieza = {a.pieza: a for a in articulaciones}
    glPushMatrix()
    glRotatef(90, 1, 0, 0)                 # SolidWorks usa Y arriba; aquí Z es arriba
    cx, cy, cz = CENTRO_ENSAMBLE
    glTranslatef(-cx, -cy, -cz)            # pies en el piso, muñeco centrado
    _dibujar_nodo(RAIZ, por_pieza, dibujar_pieza)
    glPopMatrix()
