"""
Cargador de archivos STL (binarios y ASCII) usando solo numpy.

Un STL no es más que una lista de triángulos. Cada triángulo tiene
3 vértices (x, y, z) y una normal (hacia dónde "mira" la cara).
Aquí leemos esos triángulos y los dejamos listos para OpenGL.
"""
import struct
import numpy as np


class Malla:
    """Guarda los triángulos de una pieza ya listos para dibujar."""

    def __init__(self, vertices, normales, nombre=""):
        # vertices: arreglo (N*3, 3)  -> un vértice por fila
        # normales: arreglo (N*3, 3)  -> la normal repetida para cada vértice
        self.vertices = np.ascontiguousarray(vertices, dtype=np.float32)
        self.normales = np.ascontiguousarray(normales, dtype=np.float32)
        self.nombre = nombre

    @property
    def num_triangulos(self):
        return len(self.vertices) // 3

    @property
    def caja(self):
        """Caja envolvente: (mínimos, máximos) en x, y, z."""
        return self.vertices.min(axis=0), self.vertices.max(axis=0)


def _calcular_normales(tris):
    """Normal de cada triángulo con el producto cruz (regla de la mano derecha).

    SolidWorks a veces guarda normales en cero, por eso las recalculamos
    siempre a partir del orden de los vértices.
    """
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    n = np.cross(b - a, c - a)
    largo = np.linalg.norm(n, axis=1, keepdims=True)
    largo[largo == 0] = 1.0
    return n / largo


def _leer_binario(datos):
    num = struct.unpack("<I", datos[80:84])[0]
    formato = np.dtype([("normal", "<f4", (3,)),
                        ("v", "<f4", (3, 3)),
                        ("attr", "<u2")])
    registros = np.frombuffer(datos, dtype=formato, count=num, offset=84)
    return registros["v"].astype(np.float32)


def _leer_ascii(texto):
    vertices = []
    for linea in texto.splitlines():
        partes = linea.strip().split()
        if partes and partes[0] == "vertex":
            vertices.append([float(p) for p in partes[1:4]])
    return np.array(vertices, dtype=np.float32).reshape(-1, 3, 3)


def cargar_stl(ruta, escala=1.0):
    """Lee un STL y devuelve una Malla. `escala` sirve si el CAD exportó en metros."""
    with open(ruta, "rb") as f:
        datos = f.read()

    # Un STL binario mide exactamente 84 + 50 * (número de triángulos) bytes.
    # Si no cumple eso y empieza por "solid", es ASCII.
    es_binario = True
    if len(datos) >= 84:
        num = struct.unpack("<I", datos[80:84])[0]
        es_binario = (84 + 50 * num == len(datos))
    if not es_binario and datos[:5].lower() == b"solid":
        tris = _leer_ascii(datos.decode("utf-8", errors="ignore"))
    else:
        tris = _leer_binario(datos)

    if len(tris) == 0:
        raise ValueError(f"El archivo {ruta} no tiene triángulos")

    tris = tris * escala
    normales = np.repeat(_calcular_normales(tris), 3, axis=0)
    return Malla(tris.reshape(-1, 3), normales, nombre=str(ruta))


def guardar_stl(ruta, tris, nombre=b"pieza"):
    """Guarda triángulos (N, 3, 3) como STL binario."""
    tris = np.asarray(tris, dtype=np.float32)
    normales = _calcular_normales(tris).astype(np.float32)
    with open(ruta, "wb") as f:
        f.write(nombre.ljust(80, b" ")[:80])
        f.write(struct.pack("<I", len(tris)))
        for n, t in zip(normales, tris):
            f.write(struct.pack("<12fH", *n, *t.ravel(), 0))
