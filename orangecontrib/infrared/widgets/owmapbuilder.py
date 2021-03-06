import sys
import numpy as np

import Orange.data
from Orange.widgets.widget import OWWidget, Msg
from Orange.widgets import gui, settings
from Orange.widgets.utils.annotated_data import get_next_name
from orangecontrib.infrared.widgets.gui import lineEditIntOrNone
from AnyQt.QtCore import Qt


class OWMapBuilder(OWWidget):
    # Widget's name as displayed in the canvas
    name = "Reshape Map"

    # Short widget description
    description = (
        "Builds or modifies the shape of the input dataset to create 2D maps "
        "from series data or change the dimensions of existing 2D datasets.")

    icon = ""

    # Define inputs and outputs
    inputs = [("Data", Orange.data.Table, "set_data")]
    outputs = [("Map data", Orange.data.Table)]

    autocommit = settings.Setting(True)

    want_main_area = False
    resizing_enabled = False

    xpoints = settings.Setting(None)
    ypoints = settings.Setting(None)

    class Warning(OWWidget.Warning):
        wrong_div = Msg("Wrong divisor for {} curves.")
        nodata = Msg("No useful data on input!")

    def __init__(self):
        super().__init__()

        box = gui.widgetBox(self.controlArea, "Map grid")

        self.le1 = lineEditIntOrNone(box, self, "xpoints",
            label="X dimension", labelWidth=80, orientation=Qt.Horizontal,
            callback=self.le1_changed)
        self.le3 = lineEditIntOrNone(box, self, "ypoints",
            label="Y dimension", labelWidth=80, orientation=Qt.Horizontal,
            callback=self.le3_changed)

        self.data = None
        self.set_data(self.data)  # show warning

        gui.auto_commit(self.controlArea, self, "autocommit", "Send Data")

    def set_data(self, dataset):
        self.Warning.wrong_div.clear()
        if dataset is not None:
            self.Warning.nodata.clear()
            self.data = dataset
        else:
            self.Warning.nodata()
        self.commit()

    # maybe doable with one callback...
    def le1_changed(self): # X dimension
        if self.data is not None and self.xpoints:
            self.Warning.wrong_div.clear()
            ytemp = len(self.data.X)//self.xpoints
            if len(self.data.X) % self.xpoints == 0:
                self.ypoints = ytemp
                self.commit()
            else:
                self.Warning.wrong_div(len(self.data.X))

    def le3_changed(self): # Y dimension
        if self.data is not None and self.ypoints:
            self.Warning.wrong_div.clear()
            xtemp = len(self.data.X)//self.ypoints
            if len(self.data.X) % self.ypoints == 0:
                self.xpoints = xtemp
                self.commit()
            else:
                self.Warning.wrong_div(len(self.data.X))
                # it would be nice to turn the bkg red at this point

    def commit(self):
        map_data = None
        if self.data and self.xpoints is not None and self.ypoints is not None \
                and self.xpoints * self.ypoints == len(self.data):
            used_names = [var.name for var in self.data.domain.variables + self.data.domain.metas]
            xmeta = Orange.data.ContinuousVariable.make(get_next_name(used_names, "X"))
            ymeta = Orange.data.ContinuousVariable.make(get_next_name(used_names, "Y"))
            # add new variables for X and Y dimension ot the data domain
            metas = self.data.domain.metas + (xmeta, ymeta)
            domain = Orange.data.Domain(self.data.domain.attributes, self.data.domain.class_vars, metas)
            map_data = Orange.data.Table(domain, self.data)
            map_data[:, xmeta] = np.tile(np.arange(self.xpoints), len(self.data)//self.xpoints).reshape(-1, 1)
            map_data[:, ymeta] = np.repeat(np.arange(self.ypoints), len(self.data)//self.ypoints).reshape(-1, 1)
        self.send("Map data", map_data)

    def send_report(self):
        if self.xpoints and self.ypoints is not None:
            self.report_items((
                ("Number of points in the X direction", int(self.xpoints)),
                ("Number of points in the Y direction", int(self.ypoints))
            ))
        else:
            return


def main(argv=sys.argv):
    from AnyQt.QtWidgets import QApplication
    app = QApplication(list(argv))
    ow = OWMapBuilder()
    ow.show()
    ow.raise_()
    dataset = Orange.data.Table("collagen.csv")
    ow.set_data(dataset)
    app.exec_()
    return 0

if __name__=="__main__":
    sys.exit(main())
