"""
Definición del brazo robótico de 6 articulaciones y cómo se ensambla.

IDEA CLAVE (ensamble jerárquico):
Piensa en tu propio brazo. Si giras el hombro, el codo y la mano se
mueven con él sin "desarmarse". En OpenGL eso se logra así:
cada pieza se dibuja DENTRO de la transformación de la pieza anterior.

    base
     └─ J1 (gira en Z)  -> hombro
         └─ J2 (gira en Y) -> brazo
             └─ J3 (gira en Y) -> antebrazo
                 └─ J4 (gira en Z) -> muñeca
                     └─ J5 (gira en Y) -> palma
                         └─ J6 (lineal en X) -> dedos de la pinza

Como cada transformación se acumula sobre la anterior, el ensamble
nunca se rompe: eso cumple el punto 5 de la guía.

Unidades: milímetros y grados (igual que exporta SolidWorks).
"""
from dataclasses import dataclass, field
from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslatef, glRotatef


@dataclass
class Articulacion:
    nombre: str
    tipo: str            # "rot" (rotacional, grados) o "lin" (lineal, mm)
    eje: tuple           # eje de giro o de desplazamiento, ej. (0, 0, 1)
    offset: tuple        # dónde queda esta articulación respecto a la pieza anterior (mm)
    minimo: float
    maximo: float
    inicial: float       # posición HOME
    pieza: str           # nombre de la pieza que mueve esta articulación
    valor: float = field(default=None)

    def __post_init__(self):
        if self.valor is None:
            self.valor = self.inicial

    @property
    def unidad(self):
        return "°" if self.tipo == "rot" else " mm"


# Pieza fija (no se mueve con ninguna articulación)
PIEZA_BASE = "base"

# Colores de cada pieza (R, G, B) entre 0 y 1
COLORES = {
    "base":      (0.25, 0.27, 0.30),
    "hombro":    (0.95, 0.55, 0.10),
    "brazo":     (0.85, 0.85, 0.88),
    "antebrazo": (0.95, 0.55, 0.10),
    "muneca":    (0.85, 0.85, 0.88),
    "palma":     (0.30, 0.32, 0.36),
    "dedo":      (0.95, 0.55, 0.10),
}

# Archivo STL de cada pieza dentro de la carpeta piezas/
ARCHIVOS = {nombre: f"{nombre}.stl" for nombre in COLORES}


def crear_articulaciones():
    """Las 6 articulaciones del brazo, en orden desde la base."""
    return [
        Articulacion("J1 Base",       "rot", (0, 0, 1), (0, 0, 60),  -180, 180, 0,  "hombro"),
        Articulacion("J2 Hombro",     "rot", (0, 1, 0), (0, 0, 120),  -90,  90, 20, "brazo"),
        Articulacion("J3 Codo",       "rot", (0, 1, 0), (0, 0, 250), -135, 135, 50, "antebrazo"),
        Articulacion("J4 Muñeca rot", "rot", (0, 0, 1), (0, 0, 200), -180, 180, 0,  "muneca"),
        Articulacion("J5 Muñeca inc", "rot", (0, 1, 0), (0, 0, 60),  -110, 110, 40, "palma"),
        Articulacion("J6 Pinza",      "lin", (1, 0, 0), (0, 0, 45),     0,  35, 15, "dedo"),
    ]


def aplicar_movimiento(art):
    """Mueve el sistema de coordenadas según el valor de la articulación."""
    if art.tipo == "rot":
        glRotatef(art.valor, *art.eje)
    else:
        ex, ey, ez = art.eje
        glTranslatef(ex * art.valor, ey * art.valor, ez * art.valor)


def dibujar_robot(articulaciones, dibujar_pieza):
    """Dibuja el robot completo.

    `dibujar_pieza(nombre)` es una función que pinta una pieza en el
    origen actual (la pone el visor OpenGL).
    """
    glPushMatrix()
    dibujar_pieza(PIEZA_BASE)

    # J1 a J5: cadena normal, cada una se apila sobre la anterior
    for art in articulaciones[:5]:
        glTranslatef(*art.offset)   # ir a donde está la articulación
        aplicar_movimiento(art)     # girar
        dibujar_pieza(art.pieza)    # dibujar la pieza que cuelga de ella

    # J6: la pinza tiene DOS dedos que se abren en espejo
    pinza = articulaciones[5]
    glTranslatef(*pinza.offset)
    for lado in (1, -1):
        glPushMatrix()
        glTranslatef(lado * (10 + pinza.valor), 0, 0)
        if lado == -1:
            glRotatef(180, 0, 0, 1)  # el dedo izquierdo es el derecho girado 180°
        dibujar_pieza(pinza.pieza)
        glPopMatrix()

    glPopMatrix()
