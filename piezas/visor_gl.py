"""
Visor 3D: un widget de PyQt5 donde OpenGL dibuja la escena.

QOpenGLWidget nos da tres funciones que Qt llama solo:
  initializeGL() -> una vez al inicio (luces, profundidad, colores)
  resizeGL()     -> cuando cambia el tamaño de la ventana (perspectiva)
  paintGL()      -> cada vez que hay que redibujar (cámara + muñeco)
Es lo mismo que glutDisplayFunc / glutReshapeFunc de la guía,
pero dentro de una interfaz de PyQt.
"""
import math
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt

import muneco

# Valores iniciales de cámara y modelo (los usa HOME CÁMARA)
CAMARA_INICIAL = {"azimut": -60.0, "elevacion": 20.0, "distancia": 330.0}
MODELO_INICIAL = {"tx": 0.0, "ty": 0.0, "tz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}
OBJETIVO = (0.0, 0.0, 62.0)    # punto al que mira la cámara (mitad del muñeco)


class VisorGL(QOpenGLWidget):
    # Avisa a la interfaz cuando el mouse mueve la cámara, para actualizar los sliders
    camara_cambiada = pyqtSignal()

    def __init__(self, articulaciones, parent=None):
        super().__init__(parent)
        self.articulaciones = articulaciones
        self.camara = dict(CAMARA_INICIAL)
        self.modelo = dict(MODELO_INICIAL)
        self.mallas = {}        # nombre -> Malla (datos de la pieza)
        self.listas = {}        # nombre -> id de display list de OpenGL
        self.pendientes = set() # piezas que hay que (re)compilar en la GPU
        self._mouse_ant = None
        self.setFocusPolicy(Qt.StrongFocus)

    # ---------- piezas ----------
    def poner_malla(self, nombre, malla):
        """Recibe una pieza cargada. Se compila en paintGL (ahí sí hay contexto GL)."""
        self.mallas[nombre] = malla
        self.pendientes.add(nombre)
        self.update()

    def _compilar(self, nombre):
        """Convierte la malla en una display list (se dibuja mucho más rápido)."""
        if nombre in self.listas:
            glDeleteLists(self.listas[nombre], 1)
        malla = self.mallas[nombre]
        lista = glGenLists(1)
        glNewList(lista, GL_COMPILE)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, malla.vertices)
        glNormalPointer(GL_FLOAT, 0, malla.normales)
        glDrawArrays(GL_TRIANGLES, 0, len(malla.vertices))
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glEndList()
        self.listas[nombre] = lista

    def _dibujar_pieza(self, nombre):
        if nombre in self.listas:
            glColor3f(*muneco.PIEZAS[nombre].color)
            glCallList(self.listas[nombre])

    # ---------- OpenGL ----------
    def initializeGL(self):
        glClearColor(0.93, 0.94, 0.96, 1.0)
        glEnable(GL_DEPTH_TEST)            # Z-buffer: lo de adelante tapa lo de atrás
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)        # glColor3f define el color del material
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.75, 0.75, 0.75, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.25, 0.25, 0.25, 1.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.30, 0.30, 0.32, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 30.0)
        glShadeModel(GL_SMOOTH)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, max(h, 1))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / max(h, 1), 1.0, 5000.0)
        glMatrixMode(GL_MODELVIEW)

    def _posicion_camara(self):
        """Coordenadas esféricas -> posición (x, y, z) de la cámara.

        Como una persona caminando alrededor del muñeco:
        azimut = hacia qué lado está parada, elevación = qué tan alto mira,
        distancia = qué tan lejos está.
        """
        az = math.radians(self.camara["azimut"])
        el = math.radians(self.camara["elevacion"])
        d = self.camara["distancia"]
        ox, oy, oz = OBJETIVO
        return (ox + d * math.cos(el) * math.cos(az),
                oy + d * math.cos(el) * math.sin(az),
                oz + d * math.sin(el))

    def paintGL(self):
        for nombre in list(self.pendientes):
            self._compilar(nombre)
        self.pendientes.clear()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Luces fijas respecto a la cámara (se ponen antes de gluLookAt)
        glLightfv(GL_LIGHT0, GL_POSITION, [0.4, 0.6, 1.0, 0.0])
        glLightfv(GL_LIGHT1, GL_POSITION, [-0.6, -0.3, -0.5, 0.0])

        cx, cy, cz = self._posicion_camara()
        gluLookAt(cx, cy, cz, *OBJETIVO, 0, 0, 1)   # el eje Z es "arriba"

        self._dibujar_piso()

        # Transformación del modelo completo (punto 8 de la guía)
        m = self.modelo
        glPushMatrix()
        glTranslatef(m["tx"], m["ty"], m["tz"])
        glRotatef(m["rx"], 1, 0, 0)
        glRotatef(m["ry"], 0, 1, 0)
        glRotatef(m["rz"], 0, 0, 1)
        self._dibujar_ejes(40)
        muneco.dibujar_muneco(self.articulaciones, self._dibujar_pieza)
        glPopMatrix()

    def _dibujar_piso(self):
        glDisable(GL_LIGHTING)
        glLineWidth(1.0)
        glColor3f(0.78, 0.80, 0.84)
        glBegin(GL_LINES)
        paso, tam = 10, 150
        for i in range(-tam, tam + 1, paso):
            glVertex3f(i, -tam, 0); glVertex3f(i, tam, 0)
            glVertex3f(-tam, i, 0); glVertex3f(tam, i, 0)
        glEnd()
        glEnable(GL_LIGHTING)

    def _dibujar_ejes(self, largo):
        """Ejes del modelo: X rojo, Y verde, Z azul."""
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glColor3f(0.9, 0.1, 0.1); glVertex3f(0, 0, 0); glVertex3f(largo, 0, 0)
        glColor3f(0.1, 0.7, 0.1); glVertex3f(0, 0, 0); glVertex3f(0, largo, 0)
        glColor3f(0.1, 0.2, 0.9); glVertex3f(0, 0, 0); glVertex3f(0, 0, largo)
        glEnd()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    # ---------- cámara ----------
    def poner_vista(self, azimut, elevacion):
        self.camara["azimut"] = azimut
        self.camara["elevacion"] = elevacion
        self.update()
        self.camara_cambiada.emit()

    def home_camara(self):
        self.camara = dict(CAMARA_INICIAL)
        self.modelo = dict(MODELO_INICIAL)
        self.update()
        self.camara_cambiada.emit()

    # ---------- mouse ----------
    # Arrastrar con clic izquierdo: girar alrededor del muñeco
    # Rueda: acercar / alejar
    def mousePressEvent(self, e):
        self._mouse_ant = e.pos()

    def mouseMoveEvent(self, e):
        if self._mouse_ant is None:
            return
        dx = e.x() - self._mouse_ant.x()
        dy = e.y() - self._mouse_ant.y()
        self._mouse_ant = e.pos()
        if e.buttons() & Qt.LeftButton:
            self.camara["azimut"] = (self.camara["azimut"] - dx * 0.5 + 180) % 360 - 180
            self.camara["elevacion"] = max(-89.0, min(89.0, self.camara["elevacion"] + dy * 0.5))
            self.update()
            self.camara_cambiada.emit()

    def mouseReleaseEvent(self, e):
        self._mouse_ant = None

    def wheelEvent(self, e):
        factor = 0.9 if e.angleDelta().y() > 0 else 1.1
        self.camara["distancia"] = max(80.0, min(1500.0, self.camara["distancia"] * factor))
        self.update()
        self.camara_cambiada.emit()
