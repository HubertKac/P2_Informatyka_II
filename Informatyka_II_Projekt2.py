import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath


# ======================================================
# Rura
# ======================================================
class Rura:
    def __init__(self, punkty, grubosc=12, kolor=Qt.gray, kolor_cieczy=None):
        self.punkty = [QPointF(p[0], p[1]) for p in punkty]
        self.grubosc = grubosc
        self.kolor_rury = kolor
        self.kolor_cieczy = kolor_cieczy or QColor(0, 180, 255)
        self.czy_plynie = False

    def ustaw_przeplyw(self, stan):
        self.czy_plynie = stan

    def rysuj(self, painter):
        if len(self.punkty) < 2:
            return

        sciezka = QPainterPath()
        sciezka.moveTo(self.punkty[0])
        for p in self.punkty[1:]:
            sciezka.lineTo(p)

        painter.setPen(QPen(self.kolor_rury, self.grubosc,
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(sciezka)

        if self.czy_plynie:
            painter.setPen(QPen(self.kolor_cieczy, self.grubosc - 4,
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawPath(sciezka)


# ======================================================
# Zbiornik
# ======================================================
class Zbiornik:
    def __init__(self, x, y, szer=100, wys=140, nazwa=""):
        self.x = x
        self.y = y
        self.szer = szer
        self.wys = wys
        self.nazwa = nazwa
        self.pojemnosc = 100.0
        self.ilosc = 0.0
        self.poziom = 0.0

    def dodaj(self, ilosc):
        dodano = min(ilosc, self.pojemnosc - self.ilosc)
        self.ilosc += dodano
        self.poziom = self.ilosc / self.pojemnosc
        return dodano

    def usun(self, ilosc):
        usunieto = min(ilosc, self.ilosc)
        self.ilosc -= usunieto
        self.poziom = self.ilosc / self.pojemnosc
        return usunieto

    def pusty(self):
        return self.ilosc <= 0.1

    def pelny(self):
        return self.ilosc >= self.pojemnosc - 0.1

    def gora(self):
        return (self.x + self.szer / 2, self.y)

    def dol(self):
        return (self.x + self.szer / 2, self.y + self.wys)

    def rysuj(self, painter):
        if self.poziom > 0:
            h = self.wys * self.poziom
            y0 = self.y + self.wys - h
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 120, 255, 200))
            painter.drawRect(self.x + 3, y0, self.szer - 6, h - 2)

        painter.setPen(QPen(Qt.white, 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.x, self.y, self.szer, self.wys)
        painter.drawText(self.x, self.y - 10, self.nazwa)


# ======================================================
# Symulacja
# ======================================================
class Symulacja(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Symulacja hydrauliczna")
        self.setFixedSize(1000, 650)
        self.setStyleSheet("background:#222;")

        # Zbiorniki
        self.z1 = Zbiornik(50, 50, nazwa="Z1")
        self.z1.ilosc = 100
        self.z1.poziom = 1.0

        self.z2 = Zbiornik(250, 150, nazwa="Z2")
        self.z3 = Zbiornik(450, 275, nazwa="Z3")
        self.z4 = Zbiornik(650, 400, nazwa="Z4")
        self.z5 = Zbiornik(850, 400, nazwa="Z5")

        self.zbiorniki = [self.z1, self.z2, self.z3, self.z4, self.z5]

        # Rury
        self.rura_12 = self.stworz_rure(self.z1, self.z2)
        self.rura_23 = self.stworz_rure(self.z2, self.z3)
        self.rura_34 = self.stworz_rure(self.z3, self.z4)
        self.rura_35 = self.stworz_rure(self.z3, self.z5)

        self.rury_graw = [self.rura_12, self.rura_23, self.rura_34, self.rura_35]

        self.rura_pompy = self.stworz_rure(
            self.z4, self.z3, Qt.darkRed, QColor(255, 80, 80)
        )

        self.pompa_wlaczona = False

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.logika)
        self.dziala = False

        # Przyciski
        QPushButton("Start / Stop", self,
                    clicked=self.przelacz).setGeometry(50, 600, 100, 30)

        self.btn_pompa = QPushButton("Pompa OFF", self)
        self.btn_pompa.setGeometry(50, 560, 100, 30)
        self.btn_pompa.clicked.connect(self.przelacz_pompe)

        self.dodaj_przyciski()

    def stworz_rure(self, z1, z2, kolor=Qt.gray, kolor_cieczy=None):
        p1 = z1.dol()
        p2 = z2.gora()
        y = (p1[1] + p2[1]) / 2
        return Rura([p1, (p1[0], y), (p2[0], y), p2],
                    kolor=kolor, kolor_cieczy=kolor_cieczy)

    def dodaj_przyciski(self):
        x, y, dx = 200, 600, 150
        for i, z in enumerate(self.zbiorniki):
            QPushButton(f"Z{i+1} [+]", self,
                        clicked=lambda _, zb=z: self.napelnij(zb)
                        ).setGeometry(x + i * dx, y, 60, 30)

            QPushButton(f"Z{i+1} [-]", self,
                        clicked=lambda _, zb=z: self.oproznij(zb)
                        ).setGeometry(x + i * dx + 65, y, 60, 30)

    def napelnij(self, z):
        z.ilosc = z.pojemnosc
        z.poziom = 1.0
        self.update()

    def oproznij(self, z):
        z.ilosc = 0.0
        z.poziom = 0.0
        self.update()

    def przelacz(self):
        self.dziala = not self.dziala
        self.timer.start(20) if self.dziala else self.timer.stop()

    def przelacz_pompe(self):
        self.pompa_wlaczona = not self.pompa_wlaczona
        self.btn_pompa.setText("Pompa ON" if self.pompa_wlaczona else "Pompa OFF")

    def logika(self):
        for r in self.rury_graw:
            r.ustaw_przeplyw(False)
        self.rura_pompy.ustaw_przeplyw(False)

        # Z1 -> Z2
        if not self.z1.pusty() and not self.z2.pelny():
            il = self.z1.usun(0.8)
            self.z2.dodaj(il)
            self.rura_12.ustaw_przeplyw(True)

        # Z2 -> Z3
        if not self.z2.pusty() and not self.z3.pelny():
            il = self.z2.usun(0.8)
            self.z3.dodaj(il)
            self.rura_23.ustaw_przeplyw(True)

        # Rozgałęzienie Z3 -> Z4 / Z5 (50/50)
        if not self.z3.pusty():
            calosc = 0.8
            polowa = calosc / 2

            wolne4 = not self.z4.pelny()
            wolne5 = not self.z5.pelny()

            if wolne4 and wolne5:
                self.z3.usun(calosc)
                self.z4.dodaj(polowa)
                self.z5.dodaj(polowa)
                self.rura_34.ustaw_przeplyw(True)
                self.rura_35.ustaw_przeplyw(True)
            elif wolne4:
                il = self.z3.usun(calosc)
                self.z4.dodaj(il)
                self.rura_34.ustaw_przeplyw(True)
            elif wolne5:
                il = self.z3.usun(calosc)
                self.z5.dodaj(il)
                self.rura_35.ustaw_przeplyw(True)

        # Pompa Z4 -> Z3
        if self.pompa_wlaczona and not self.z4.pusty() and not self.z3.pelny():
            il = self.z4.usun(1.2)
            self.z3.dodaj(il)
            self.rura_pompy.ustaw_przeplyw(True)

        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        for r in self.rury_graw:
            r.rysuj(p)
        self.rura_pompy.rysuj(p)

        for z in self.zbiorniki:
            z.rysuj(p)

        p.setPen(QPen(Qt.red, 3))
        p.drawEllipse(700, 330, 30, 30)
        p.drawText(708, 350, "P")


# ======================================================
# Start
# ======================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    okno = Symulacja()
    okno.show()
    sys.exit(app.exec_())
