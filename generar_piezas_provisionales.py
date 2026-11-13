"""
Genera piezas STL PROVISIONALES para poder probar el programa
mientras se modelan las piezas reales en SolidWorks.

OJO: la guía NO acepta estas piezas para la entrega. Hay que
reemplazarlas por las de SolidWorks con el MISMO nombre de archivo
y con el origen en el eje de cada articulación.

Ejecutar una sola vez:  python generar_piezas_provisionales.py
"""
from pathlib import Path
import numpy as np
from stl_loader import guardar_stl

CARPETA = Path(__file__).parent / "piezas"


def rect_redondeado(ancho, alto, radio, n=6):
    """Perfil 2D (convexo) de un rectángulo con esquinas redondeadas."""
    puntos = []
    cx, cy = ancho / 2 - radio, alto / 2 - radio
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        for k in range(n + 1):
            a = np.radians(a0 + 90 * k / n)
            puntos.append((sx * cx + radio * np.cos(a), sy * cy + radio * np.sin(a)))
    return np.array(puntos)


def poligono(radio, lados):
    a = np.linspace(0, 2 * np.pi, lados, endpoint=False) + np.pi / lados
    return np.column_stack((radio * np.cos(a), radio * np.sin(a)))


def extruir(perfil, z0, z1, dx=0.0, dy=0.0):
    """Extruye un perfil convexo (en XY, sentido antihorario) entre z0 y z1."""
    p = perfil + (dx, dy)
    n = len(p)
    c = p.mean(axis=0)
    tris = []
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        tris.append([(*c, z0), (*b, z0), (*a, z0)])               # tapa de abajo
        tris.append([(*c, z1), (*a, z1), (*b, z1)])               # tapa de arriba
        tris.append([(*a, z0), (*b, z0), (*b, z1)])               # costado
        tris.append([(*a, z0), (*b, z1), (*a, z1)])
    return np.array(tris, dtype=np.float32)


def a_plano_xz(tris):
    """Pasa una extrusión hecha en XY a una placa en el plano XZ (extruida en Y)."""
    t = tris[:, :, [0, 2, 1]].copy()   # (x, y, z) -> (x, z, y)
    return t[:, [0, 2, 1], :]          # voltear el orden para que las normales queden afuera


def orejas(ancho_x, z0, z1, y_in, y_out, radio=15):
    """Dos placas laterales (como una horquilla) para sostener una articulación en Y."""
    perfil = rect_redondeado(ancho_x, z1 - z0, radio) + (0, (z0 + z1) / 2)
    return np.vstack([a_plano_xz(extruir(perfil, y_in, y_out)),
                      a_plano_xz(extruir(perfil, -y_out, -y_in))])


def generar():
    CARPETA.mkdir(exist_ok=True)
    piezas = {
        "base": np.vstack([extruir(rect_redondeado(240, 240, 30), 0, 20),
                           extruir(poligono(70, 10), 20, 60)]),
        "hombro": np.vstack([extruir(poligono(60, 10), 0, 60),
                             orejas(90, 30, 150, 42, 62)]),
        "brazo": extruir(rect_redondeado(60, 80, 18), -35, 285),
        "antebrazo": extruir(rect_redondeado(50, 56, 15), -30, 200),
        "muneca": np.vstack([extruir(poligono(32, 10), 0, 35),
                             orejas(50, 25, 80, 26, 36, radio=12)]),
        "palma": np.vstack([extruir(rect_redondeado(40, 50, 10), -22, 30),
                            extruir(rect_redondeado(110, 44, 8), 30, 45)]),
        "dedo": np.vstack([extruir(rect_redondeado(14, 22, 4), 0, 70, dx=7),
                           extruir(rect_redondeado(8, 22, 3), 55, 85, dx=4)]),
    }
    for nombre, tris in piezas.items():
        guardar_stl(CARPETA / f"{nombre}.stl", tris, nombre.encode())
        print(f"{nombre}.stl: {len(tris)} triángulos")


if __name__ == "__main__":
    generar()
