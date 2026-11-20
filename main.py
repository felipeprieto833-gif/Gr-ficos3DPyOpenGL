# Laboratorio 6 - Graficos en 3D con PyOpenGL
# Muñeco LEGO con 9 articulaciones
# Programacion 3 - Ingenieria Mecatronica - UMNG

import sys
import os
import math
import numpy as np
from stl import mesh
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from OpenGL.GL import *
from OpenGL.GLU import *
import muneco

CARPETA = os.path.join(os.path.dirname(__file__), "piezas")

# camara (como si fuera una persona caminando alrededor del muñeco)
azimut = -60
elevacion = 20
distancia = 330

# posicion y rotacion de todo el modelo
mover = [0, 0, 0]
rotar = [0, 0, 0]

# aca guardo las piezas cargadas
modelos = {}


class Visor(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.ventana = None
        self.mouse_x = 0
        self.mouse_y = 0

    def initializeGL(self):
        glClearColor(0.93, 0.94, 0.96, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])

    def resizeGL(self, w, h):
        if h == 0:
            h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 1, 5000)
        glMatrixMode(GL_MODELVIEW)

    def crear_lista(self, nombre):
        # guardo los triangulos de la pieza en una display list
        # para no tener que mandarlos todos cada vez que se dibuja
        if nombre in muneco.listas:
            glDeleteLists(muneco.listas[nombre], 1)
        modelo = modelos[nombre]
        lista = glGenLists(1)
        glNewList(lista, GL_COMPILE)
        glBegin(GL_TRIANGLES)
        for i in range(len(modelo.vectors)):
            glNormal3fv(modelo.normals[i])
            for vertice in modelo.vectors[i]:
                glVertex3fv(vertice)
        glEnd()
        glEndList()
        muneco.listas[nombre] = lista

    def paintGL(self):
        # si hay piezas nuevas les creo la lista
        for nombre in modelos:
            if nombre not in muneco.listas:
                self.crear_lista(nombre)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glLightfv(GL_LIGHT0, GL_POSITION, [0.4, 0.6, 1, 0])

        # paso de azimut, elevacion y distancia a x, y, z
        az = math.radians(azimut)
        el = math.radians(elevacion)
        cx = distancia * math.cos(el) * math.cos(az)
        cy = distancia * math.cos(el) * math.sin(az)
        cz = 62 + distancia * math.sin(el)
        gluLookAt(cx, cy, cz, 0, 0, 62, 0, 0, 1)

        self.dibujar_piso()

        glPushMatrix()
        glTranslatef(mover[0], mover[1], mover[2])
        glRotatef(rotar[0], 1, 0, 0)
        glRotatef(rotar[1], 0, 1, 0)
        glRotatef(rotar[2], 0, 0, 1)
        muneco.dibujar_muneco()
        glPopMatrix()

    def dibujar_piso(self):
        glDisable(GL_LIGHTING)
        glColor3f(0.78, 0.8, 0.84)
        glBegin(GL_LINES)
        for i in range(-150, 160, 10):
            glVertex3f(i, -150, 0)
            glVertex3f(i, 150, 0)
            glVertex3f(-150, i, 0)
            glVertex3f(150, i, 0)
        glEnd()
        # ejes x rojo, y verde, z azul
        glLineWidth(3)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(40, 0, 0)
        glColor3f(0, 0.7, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 40, 0)
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 40)
        glEnd()
        glLineWidth(1)
        glEnable(GL_LIGHTING)

    # mover la camara con el mouse
    def mousePressEvent(self, evento):
        self.mouse_x = evento.x()
        self.mouse_y = evento.y()

    def mouseMoveEvent(self, evento):
        global azimut, elevacion
        dx = evento.x() - self.mouse_x
        dy = evento.y() - self.mouse_y
        self.mouse_x = evento.x()
        self.mouse_y = evento.y()
        azimut = azimut - dx * 0.5
        if azimut > 180:
            azimut = azimut - 360
        if azimut < -180:
            azimut = azimut + 360
        elevacion = elevacion + dy * 0.5
        if elevacion > 89:
            elevacion = 89
        if elevacion < -89:
            elevacion = -89
        self.ventana.actualizar_sliders_camara()

    def wheelEvent(self, evento):
        global distancia
        if evento.angleDelta().y() > 0:
            distancia = distancia * 0.9
        else:
            distancia = distancia * 1.1
        if distancia < 80:
            distancia = 80
        if distancia > 1500:
            distancia = 1500
        self.ventana.actualizar_sliders_camara()


class Ventana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lab 6 - Muñeco LEGO")
        self.resize(1350, 820)

        self.visor = Visor()
        self.visor.ventana = self

        panel = QVBoxLayout()

        # ---- articulaciones ----
        grupo1 = QGroupBox("Articulaciones")
        caja1 = QGridLayout()
        self.sliders = []
        self.etiquetas = []
        for i in range(len(muneco.articulaciones)):
            nombre = muneco.articulaciones[i][0]
            slider = QSlider(Qt.Horizontal)
            slider.setRange(muneco.articulaciones[i][3], muneco.articulaciones[i][4])
            slider.setValue(0)
            slider.valueChanged.connect(self.mover_articulaciones)
            etiqueta = QLabel("0°")
            caja1.addWidget(QLabel(nombre), i, 0)
            caja1.addWidget(slider, i, 1)
            caja1.addWidget(etiqueta, i, 2)
            self.sliders.append(slider)
            self.etiquetas.append(etiqueta)
        boton_home = QPushButton("HOME")
        boton_home.clicked.connect(self.home)
        self.boton_demo = QPushButton("Movimiento demo")
        self.boton_demo.clicked.connect(self.demo)
        caja1.addWidget(boton_home, 9, 0, 1, 2)
        caja1.addWidget(self.boton_demo, 9, 2)
        grupo1.setLayout(caja1)
        panel.addWidget(grupo1)

        # ---- camara ----
        grupo2 = QGroupBox("Camara (tambien con el mouse)")
        caja2 = QGridLayout()
        self.slider_az = QSlider(Qt.Horizontal)
        self.slider_az.setRange(-180, 180)
        self.slider_el = QSlider(Qt.Horizontal)
        self.slider_el.setRange(-89, 89)
        self.slider_dist = QSlider(Qt.Horizontal)
        self.slider_dist.setRange(80, 1500)
        self.etiqueta_az = QLabel()
        self.etiqueta_el = QLabel()
        self.etiqueta_dist = QLabel()
        caja2.addWidget(QLabel("Azimut"), 0, 0)
        caja2.addWidget(self.slider_az, 0, 1)
        caja2.addWidget(self.etiqueta_az, 0, 2)
        caja2.addWidget(QLabel("Elevacion"), 1, 0)
        caja2.addWidget(self.slider_el, 1, 1)
        caja2.addWidget(self.etiqueta_el, 1, 2)
        caja2.addWidget(QLabel("Distancia"), 2, 0)
        caja2.addWidget(self.slider_dist, 2, 1)
        caja2.addWidget(self.etiqueta_dist, 2, 2)
        self.slider_az.valueChanged.connect(self.mover_camara)
        self.slider_el.valueChanged.connect(self.mover_camara)
        self.slider_dist.valueChanged.connect(self.mover_camara)

        b_sup = QPushButton("Superior")
        b_sup.clicked.connect(self.vista_superior)
        b_iso = QPushButton("Isometrica")
        b_iso.clicked.connect(self.vista_isometrica)
        b_lat = QPushButton("Lateral")
        b_lat.clicked.connect(self.vista_lateral)
        b_fro = QPushButton("Frontal")
        b_fro.clicked.connect(self.vista_frontal)
        caja2.addWidget(b_sup, 3, 0)
        caja2.addWidget(b_iso, 3, 1)
        caja2.addWidget(b_lat, 4, 0)
        caja2.addWidget(b_fro, 4, 1)
        grupo2.setLayout(caja2)
        panel.addWidget(grupo2)

        # ---- mover y rotar el modelo ----
        grupo3 = QGroupBox("Posicion y rotacion del modelo")
        caja3 = QGridLayout()
        nombres = ["Mover X", "Mover Y", "Mover Z", "Rotar X", "Rotar Y", "Rotar Z"]
        self.sliders_modelo = []
        self.etiquetas_modelo = []
        for i in range(6):
            slider = QSlider(Qt.Horizontal)
            if i < 3:
                slider.setRange(-150, 150)
            else:
                slider.setRange(-180, 180)
            slider.valueChanged.connect(self.mover_modelo)
            etiqueta = QLabel("0")
            caja3.addWidget(QLabel(nombres[i]), i, 0)
            caja3.addWidget(slider, i, 1)
            caja3.addWidget(etiqueta, i, 2)
            self.sliders_modelo.append(slider)
            self.etiquetas_modelo.append(etiqueta)
        boton_home_cam = QPushButton("HOME CAMARA")
        boton_home_cam.clicked.connect(self.home_camara)
        caja3.addWidget(boton_home_cam, 6, 0, 1, 3)
        grupo3.setLayout(caja3)
        panel.addWidget(grupo3)

        # ---- piezas ----
        grupo4 = QGroupBox("Piezas importadas")
        caja4 = QVBoxLayout()
        self.lista_piezas = QListWidget()
        boton_cargar = QPushButton("Cambiar pieza seleccionada")
        boton_cargar.clicked.connect(self.cambiar_pieza)
        caja4.addWidget(self.lista_piezas)
        caja4.addWidget(boton_cargar)
        grupo4.setLayout(caja4)
        panel.addWidget(grupo4)

        # armar la ventana: visor a la izquierda, controles a la derecha
        widget_panel = QWidget()
        widget_panel.setLayout(panel)
        scroll = QScrollArea()
        scroll.setWidget(widget_panel)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(430)
        principal = QHBoxLayout()
        principal.addWidget(self.visor, 1)
        principal.addWidget(scroll)
        central = QWidget()
        central.setLayout(principal)
        self.setCentralWidget(central)

        # timer para la demo
        self.tiempo = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.paso_demo)

        self.cargar_piezas()
        self.actualizar_sliders_camara()

    # ---------- piezas ----------
    def cargar_piezas(self):
        # cargo las piezas una por una
        for nombre in muneco.piezas:
            archivo = muneco.piezas[nombre][0]
            try:
                modelo = mesh.Mesh.from_file(os.path.join(CARPETA, archivo))
                modelos[nombre] = modelo
                self.lista_piezas.addItem(nombre + " - " + archivo + " (" + str(len(modelo.vectors)) + " triangulos)")
            except Exception as e:
                self.lista_piezas.addItem(nombre + " - ERROR: " + str(e))

    def cambiar_pieza(self):
        fila = self.lista_piezas.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Piezas", "Primero seleccione una pieza")
            return
        nombre = list(muneco.piezas.keys())[fila]
        ruta, _ = QFileDialog.getOpenFileName(self, "Escoger STL", CARPETA, "STL (*.stl)")
        if ruta != "":
            modelos[nombre] = mesh.Mesh.from_file(ruta)
            self.visor.makeCurrent()
            self.visor.crear_lista(nombre)
            self.lista_piezas.item(fila).setText(nombre + " - " + os.path.basename(ruta) + " (" + str(len(modelos[nombre].vectors)) + " triangulos)")
            self.visor.update()

    # ---------- articulaciones ----------
    def mover_articulaciones(self):
        for i in range(len(self.sliders)):
            muneco.angulos[i] = self.sliders[i].value()
            self.etiquetas[i].setText(str(self.sliders[i].value()) + "°")
        self.visor.update()

    def home(self):
        self.timer.stop()
        for slider in self.sliders:
            slider.setValue(0)

    def demo(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(30)

    def paso_demo(self):
        # cada articulacion se mueve con un seno distinto
        self.tiempo = self.tiempo + 0.03
        t = self.tiempo
        self.sliders[0].setValue(int(45 * math.sin(t)))
        self.sliders[1].setValue(int(60 * math.sin(t * 1.5)))
        self.sliders[2].setValue(int(-60 * math.sin(t * 1.5)))
        self.sliders[3].setValue(int(90 * math.sin(t * 2)))
        self.sliders[4].setValue(int(90 * math.sin(t * 2)))
        self.sliders[5].setValue(int(30 * math.sin(t * 1.5)))
        self.sliders[6].setValue(int(-30 * math.sin(t * 1.5)))
        self.sliders[7].setValue(int(25 * math.sin(t * 0.7)))
        self.sliders[8].setValue(int(self.tiempo * 400) % 360 - 180)

    # ---------- camara ----------
    def mover_camara(self):
        global azimut, elevacion, distancia
        azimut = self.slider_az.value()
        elevacion = self.slider_el.value()
        distancia = self.slider_dist.value()
        self.etiqueta_az.setText(str(azimut) + "°")
        self.etiqueta_el.setText(str(elevacion) + "°")
        self.etiqueta_dist.setText(str(distancia) + " mm")
        self.visor.update()

    def actualizar_sliders_camara(self):
        # cuando el mouse o un boton mueve la camara, muevo tambien los sliders
        az = azimut
        el = elevacion
        dist = distancia
        self.slider_az.setValue(int(az))
        self.slider_el.setValue(int(el))
        self.slider_dist.setValue(int(dist))
        self.etiqueta_az.setText(str(int(az)) + "°")
        self.etiqueta_el.setText(str(int(el)) + "°")
        self.etiqueta_dist.setText(str(int(dist)) + " mm")
        self.visor.update()

    def poner_vista(self, az, el):
        global azimut, elevacion
        azimut = az
        elevacion = el
        self.actualizar_sliders_camara()

    def vista_superior(self):
        self.poner_vista(-90, 89)

    def vista_isometrica(self):
        self.poner_vista(45, 35)

    def vista_lateral(self):
        self.poner_vista(0, 0)

    def vista_frontal(self):
        self.poner_vista(-90, 0)

    # ---------- modelo ----------
    def mover_modelo(self):
        for i in range(3):
            mover[i] = self.sliders_modelo[i].value()
            rotar[i] = self.sliders_modelo[i + 3].value()
        for i in range(6):
            if i < 3:
                self.etiquetas_modelo[i].setText(str(self.sliders_modelo[i].value()) + " mm")
            else:
                self.etiquetas_modelo[i].setText(str(self.sliders_modelo[i].value()) + "°")
        self.visor.update()

    def home_camara(self):
        global azimut, elevacion, distancia
        azimut = -60
        elevacion = 20
        distancia = 330
        for slider in self.sliders_modelo:
            slider.setValue(0)
        self.actualizar_sliders_camara()


app = QApplication(sys.argv)
ventana = Ventana()
ventana.show()
sys.exit(app.exec_())
