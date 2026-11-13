"""
Laboratorio 6 - Gráficos en 3D con PyOpenGL
Programación 3 - Ingeniería Mecatrónica - UMNG

Simulador de un muñeco LEGO de 9 articulaciones (piezas hechas en SolidWorks).
Ejecutar:  python main.py
"""
import math
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QGridLayout, QGroupBox, QLabel, QSlider,
                             QPushButton, QListWidget, QFileDialog, QScrollArea,
                             QMessageBox)

import muneco
from stl_loader import cargar_stl
from visor_gl import VisorGL, CAMARA_INICIAL, MODELO_INICIAL

CARPETA_PIEZAS = Path(__file__).parent / "piezas"


class FilaSlider(QWidget):
    """Una fila con: nombre | slider | valor actual.

    El slider de Qt solo maneja enteros, así que guardamos el valor
    multiplicado por `escala` (ej. escala 10 -> resolución de 0,1).
    """
    valor_cambiado = pyqtSignal(float)

    def __init__(self, nombre, minimo, maximo, inicial, unidad="", escala=1):
        super().__init__()
        self.unidad = unidad
        self.escala = escala
        self.inicial = inicial

        self.etiqueta = QLabel(nombre)
        self.etiqueta.setMinimumWidth(95)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(minimo * escala), int(maximo * escala))
        self.slider.setValue(int(inicial * escala))
        self.lectura = QLabel()
        self.lectura.setMinimumWidth(70)
        self.lectura.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        fila = QHBoxLayout(self)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.addWidget(self.etiqueta)
        fila.addWidget(self.slider, 1)
        fila.addWidget(self.lectura)

        self.slider.valueChanged.connect(self._al_mover)
        self._mostrar(inicial)

    @property
    def valor(self):
        return self.slider.value() / self.escala

    def _mostrar(self, v):
        # coma decimal, como en Colombia
        texto = f"{v:.1f}".replace(".", ",") if self.escala > 1 else f"{v:.0f}"
        self.lectura.setText(f"{texto}{self.unidad}")

    def _al_mover(self, entero):
        v = entero / self.escala
        self._mostrar(v)
        self.valor_cambiado.emit(v)

    def poner_valor(self, v, emitir=True):
        """Mueve el slider desde el código (HOME, mouse, demo)."""
        self.slider.blockSignals(not emitir)
        self.slider.setValue(int(round(v * self.escala)))
        self.slider.blockSignals(False)
        self._mostrar(v)


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lab 6 - Muñeco LEGO articulado (PyOpenGL)")
        self.resize(1350, 820)

        self.articulaciones = muneco.crear_articulaciones()
        self.visor = VisorGL(self.articulaciones)
        self.visor.camara_cambiada.connect(self._sincronizar_camara)

        panel = QWidget()
        col = QVBoxLayout(panel)
        col.addWidget(self._grupo_articulaciones())
        col.addWidget(self._grupo_camara())
        col.addWidget(self._grupo_modelo())
        col.addWidget(self._grupo_piezas())
        col.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(panel)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(430)

        central = QWidget()
        fila = QHBoxLayout(central)
        fila.addWidget(self.visor, 1)
        fila.addWidget(scroll)
        self.setCentralWidget(central)

        # Movimiento predeterminado (demo)
        self.tiempo_demo = 0.0
        self.timer_demo = QTimer(self)
        self.timer_demo.timeout.connect(self._paso_demo)

        # Cargar las piezas una por una apenas abra la ventana
        QTimer.singleShot(100, self.cargar_todas_las_piezas)

    # ---------------- Articulaciones ----------------
    def _grupo_articulaciones(self):
        grupo = QGroupBox("Articulaciones")
        caja = QVBoxLayout(grupo)
        self.filas_art = []
        for art in self.articulaciones:
            f = FilaSlider(art.nombre, art.minimo, art.maximo, art.inicial, art.unidad)
            f.valor_cambiado.connect(lambda v, a=art: self._mover_articulacion(a, v))
            caja.addWidget(f)
            self.filas_art.append(f)

        botones = QHBoxLayout()
        b_home = QPushButton("HOME")
        b_home.clicked.connect(self.home_articulaciones)
        self.b_demo = QPushButton("Movimiento demo")
        self.b_demo.setCheckable(True)
        self.b_demo.toggled.connect(self._activar_demo)
        botones.addWidget(b_home)
        botones.addWidget(self.b_demo)
        caja.addLayout(botones)
        return grupo

    def _mover_articulacion(self, art, valor):
        art.valor = valor
        self.visor.update()

    def home_articulaciones(self):
        self.b_demo.setChecked(False)
        for art, fila in zip(self.articulaciones, self.filas_art):
            art.valor = art.inicial
            fila.poner_valor(art.inicial, emitir=False)
        self.visor.update()

    def _activar_demo(self, activo):
        if activo:
            self.timer_demo.start(16)   # ~60 cuadros por segundo
        else:
            self.timer_demo.stop()

    def _paso_demo(self):
        """Cada articulación oscila con una onda seno distinta."""
        self.tiempo_demo += 0.016
        t = self.tiempo_demo
        for i, (art, fila) in enumerate(zip(self.articulaciones, self.filas_art)):
            centro = (art.maximo + art.minimo) / 2
            amplitud = (art.maximo - art.minimo) * 0.3
            if art.tipo == "rot" and art.maximo - art.minimo >= 360:
                centro, amplitud = 0, 90
            v = centro + amplitud * math.sin(t * (0.6 + 0.25 * i))
            art.valor = v
            fila.poner_valor(v, emitir=False)   # los sliders se mueven en vivo
        self.visor.update()

    # ---------------- Cámara ----------------
    def _grupo_camara(self):
        grupo = QGroupBox("Cámara (también con el mouse: arrastrar y rueda)")
        caja = QVBoxLayout(grupo)
        c = CAMARA_INICIAL
        self.f_az = FilaSlider("Azimut", -180, 180, c["azimut"], "°")
        self.f_el = FilaSlider("Elevación", -89, 89, c["elevacion"], "°")
        self.f_dist = FilaSlider("Distancia", 80, 1500, c["distancia"], " mm")
        for fila, clave in ((self.f_az, "azimut"), (self.f_el, "elevacion"),
                            (self.f_dist, "distancia")):
            fila.valor_cambiado.connect(lambda v, k=clave: self._mover_camara(k, v))
            caja.addWidget(fila)

        vistas = QGridLayout()
        for i, (texto, az, el) in enumerate((("Superior", -90, 89),
                                             ("Isométrica", 45, 35.26),
                                             ("Lateral", 0, 0),
                                             ("Frontal", -90, 0))):
            b = QPushButton(texto)
            b.clicked.connect(lambda _, a=az, e=el: self.visor.poner_vista(a, e))
            vistas.addWidget(b, i // 2, i % 2)
        caja.addLayout(vistas)
        return grupo

    def _mover_camara(self, clave, valor):
        self.visor.camara[clave] = valor
        self.visor.update()

    def _sincronizar_camara(self):
        """Cuando el mouse o un botón mueven la cámara, los sliders lo reflejan."""
        c = self.visor.camara
        self.f_az.poner_valor(c["azimut"], emitir=False)
        self.f_el.poner_valor(c["elevacion"], emitir=False)
        self.f_dist.poner_valor(c["distancia"], emitir=False)
        for clave, fila in self.filas_modelo.items():
            fila.poner_valor(self.visor.modelo[clave], emitir=False)

    # ---------------- Modelo completo ----------------
    def _grupo_modelo(self):
        grupo = QGroupBox("Posición y rotación del modelo")
        caja = QVBoxLayout(grupo)
        self.filas_modelo = {}
        for clave, nombre, mn, mx, u in (("tx", "Mover X", -150, 150, " mm"),
                                         ("ty", "Mover Y", -150, 150, " mm"),
                                         ("tz", "Mover Z", -100, 100, " mm"),
                                         ("rx", "Rotar X", -180, 180, "°"),
                                         ("ry", "Rotar Y", -180, 180, "°"),
                                         ("rz", "Rotar Z", -180, 180, "°")):
            f = FilaSlider(nombre, mn, mx, MODELO_INICIAL[clave], u)
            f.valor_cambiado.connect(lambda v, k=clave: self._mover_modelo(k, v))
            caja.addWidget(f)
            self.filas_modelo[clave] = f

        b = QPushButton("HOME CÁMARA")
        b.clicked.connect(self.visor.home_camara)
        caja.addWidget(b)
        return grupo

    def _mover_modelo(self, clave, valor):
        self.visor.modelo[clave] = valor
        self.visor.update()

    # ---------------- Piezas ----------------
    def _grupo_piezas(self):
        grupo = QGroupBox("Piezas importadas (STL)")
        caja = QVBoxLayout(grupo)
        self.lista_piezas = QListWidget()
        self.lista_piezas.setFixedHeight(150)
        b = QPushButton("Reemplazar pieza seleccionada...")
        b.clicked.connect(self._reemplazar_pieza)
        caja.addWidget(self.lista_piezas)
        caja.addWidget(b)
        return grupo

    def cargar_todas_las_piezas(self):
        """Importa las piezas una por una (punto 2 de la guía)."""
        self.lista_piezas.clear()
        for nombre, pieza in muneco.PIEZAS.items():
            self._cargar_pieza(nombre, CARPETA_PIEZAS / pieza.archivo)

    def _cargar_pieza(self, nombre, ruta, fila=None):
        try:
            malla = cargar_stl(ruta)
            self.visor.poner_malla(nombre, malla)
            texto = f"✔ {nombre}  ({Path(ruta).name}, {malla.num_triangulos} triángulos)"
        except Exception as error:
            texto = f"✘ {nombre}  ({Path(ruta).name}: {error})"
        if fila is None:
            self.lista_piezas.addItem(texto)
        else:
            self.lista_piezas.item(fila).setText(texto)
        QApplication.processEvents()   # para que se vea cómo carga cada una

    def _reemplazar_pieza(self):
        fila = self.lista_piezas.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Piezas", "Selecciona primero una pieza de la lista.")
            return
        nombre = list(muneco.PIEZAS)[fila]
        ruta, _ = QFileDialog.getOpenFileName(self, f"STL para '{nombre}'",
                                              str(CARPETA_PIEZAS), "STL (*.stl)")
        if ruta:
            self._cargar_pieza(nombre, ruta, fila)


def main():
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
