import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,\
    QTableWidgetItem, QLabel, QMessageBox, \
    QFileDialog
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import pyqtSlot

class MainApp(QWidget):
    """
    Coordinate transform program for relocating samples in different coordinate systems

    Developer:  Reto Trappitsch, trappitsch1@llnl.gov
    Version:    0.9
    Date:       September 10, 2018

    Todo:
    - Implement Copy and Paste with Ctrl+C, Ctrl+V
    """

    def __init__(self):
        # run in debug mode?
        self.rundebug = False
        # round digits
        self.rounddig = 3
        # initialize the thing
        super().__init__()
        self.title = 'Coordinate Transformation'
        self.left = 10
        self.top = 30
        self.width = 760
        # this is used for geometry but then also for tableheight. tableheight dominates!
        self.height = 400

        # my clipboard
        self.clipboard = QApplication.clipboard()

        # initialize the UI
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # define outermost v layout
        outervlayout = QVBoxLayout()

        # some top row buttons and layout
        toprowbutthlayout = QHBoxLayout()
        # open buttons
        opencsv_butt = QPushButton('Open csv')
        opencsv_butt.clicked.connect(lambda: self.openfile('csv'))
        toprowbutthlayout.addWidget(opencsv_butt)
        opentxt_butt = QPushButton('Open txt')
        opentxt_butt.clicked.connect(lambda: self.openfile('txt'))
        toprowbutthlayout.addWidget(opentxt_butt)
        # save buttons
        toprowbutthlayout.addStretch()
        savecsv_butt = QPushButton('Save csv')
        savecsv_butt.clicked.connect(lambda: self.savefile('csv'))
        toprowbutthlayout.addWidget(savecsv_butt)
        savetxt_butt = QPushButton('Save txt')
        savetxt_butt.clicked.connect(lambda: self.savefile('txt'))
        toprowbutthlayout.addWidget(savetxt_butt)
        # add test, help, quit
        toprowbutthlayout.addStretch()
        if self.rundebug:
            test_butt = QPushButton('Test')
            test_butt.clicked.connect(self.test)
            toprowbutthlayout.addWidget(test_butt)
        help_butt = QPushButton('Help')
        help_butt.clicked.connect(self.help)
        toprowbutthlayout.addWidget(help_butt)
        quit_butt = QPushButton('Quit')
        quit_butt.clicked.connect(self.close)
        toprowbutthlayout.addWidget(quit_butt)
        # add buttons to layout
        outervlayout.addLayout(toprowbutthlayout)
        outervlayout.addStretch()

        # make the table
        self.datatable = QTableWidget()
        self.datatable.setRowCount(13)
        self.datatable.setColumnCount(7)
        # set headers
        headers = [QTableWidgetItem('Name'), QTableWidgetItem('x'), QTableWidgetItem('y'),
                   QTableWidgetItem('x_ref'), QTableWidgetItem('y_ref'),
                   QTableWidgetItem('x_calc'), QTableWidgetItem('y_calc')]
        for it in range(len(headers)):
            self.datatable.setHorizontalHeaderItem(it, headers[it])
        # set the height of the table widget
        self.datatable.setFixedHeight(self.height)
        # set up clipboard for table
        self.clip = QGuiApplication.clipboard()
        # add table to widget
        outervlayout.addWidget(self.datatable)


        # bottom button row
        bottrowbutthlayout = QHBoxLayout()
        # add Row
        addrow_butt = QPushButton('+ Row')
        addrow_butt.clicked.connect(self.addrow)
        bottrowbutthlayout.addWidget(addrow_butt)
        # clear table
        clear_butt = QPushButton('Clear all')
        clear_butt.clicked.connect(self.cleartable)
        bottrowbutthlayout.addWidget(clear_butt)
        # copy and paste buttons
        copybutt = QPushButton('Copy')
        copybutt.clicked.connect(self.copy)
        bottrowbutthlayout.addWidget(copybutt)
        pastebutt = QPushButton('Paste')
        pastebutt.clicked.connect(self.paste)
        bottrowbutthlayout.addWidget(pastebutt)
        bottrowbutthlayout.addStretch()
        # information on Fit
        self.infolbl = QLabel('')
        bottrowbutthlayout.addWidget(self.infolbl)
        bottrowbutthlayout.addStretch()
        # calculate button
        calc_butt = QPushButton('Calculate')
        calc_butt.clicked.connect(self.calculate)
        bottrowbutthlayout.addWidget(calc_butt)
        # add to outer layout
        outervlayout.addStretch()
        outervlayout.addLayout(bottrowbutthlayout)

        # set layout to app
        self.setLayout(outervlayout)

        # show the UI
        self.show()

    @pyqtSlot()
    # Buttons
    def openfile(self, sep):
        if self.rundebug:
            if sep == 'txt':
                filename = 'testinput.txt'
            else:
                filename = 'testinput.csv'
        else:
            # file dialog
            options = QFileDialog.Options()
            # options |= QFileDialog.DontUseNativeDialog
            if sep == 'csv':
                filename, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                          'Comma Separated Files (*.csv);;All Files (*)',
                                                          options=options)
            else:
                filename, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                          'Text Files (*.txt);;All Files (*)', options=options)

            # check for empty string, in case cancel was pressed
        if filename == '':
            return

        # read the file
        f = open(filename, 'r')
        datain = []
        for line in f:
            datain.append(line)
        f.close()

        # # now split according to separator
        if len(datain) < 1:
            return
        data = []
        for it in datain:
            # strip newline characters
            it.strip()
            it.rstrip()
            it.replace('\n', '')
            it.replace('\r', '')
            # separate
            if sep == 'csv':
                itsep = it.split(',')
            else:
                itsep = it.split()
            # now move on with itsep
            if len(itsep) > 0:
                data.append(itsep)

        # let's check if there is a location description, i.e., 3 or 5 columns
        if len(data[0]) == 3 or len(data[0]) == 5 or len(data[0]) == 7:
            namecolumn = True
        elif len(data[0]) == 2 or len(data[0]) == 4 or len(data[0]) == 6:
            namecolumn = False
        else:
            QMessageBox.warning(self, 'Wrong input format', 'Your input does not have a valid format.')
            print(data)
            return

        # now make floats, and if not skip the column
        dataflt = []
        headercolumn = False
        for it in range(len(data)):
            tmp = []
            if namecolumn:
                tmp.append(data[it][0])
                for jt in range(1, len(data[it])):
                    try:
                        float(data[it][jt])
                        tmp.append(data[it][jt])
                    except ValueError:
                        if jt == 1:
                            headercolumn = True
                        else:
                            tmp.append('')
                if headercolumn:
                    headercolumn = False
                    continue
                else:
                    dataflt.append(tmp)

            else:
                for jt in range(len(data[it])):
                    try:
                        tmp.append(float(data[it][jt]))
                    except ValueError:
                        if jt == 1:
                            headercolumn = True
                        else:
                            tmp.append('')
                if headercolumn:
                    headercolumn = False
                    continue
                else:
                    dataflt.append(tmp)

        # first set the length of the table to be the length of the data
        self.datatable.setRowCount(len(dataflt))

        # now fill the table with the values that were just read in
        for it in range(len(dataflt)):
            for jt in range(len(dataflt[it])):
                self.datatable.setItem(it, jt, QTableWidgetItem(dataflt[it][jt]))

        # adjust table size
        self.datatable.resizeColumnsToContents()

    def savefile(self, sep):
        # get file name from dialog
        if sep == 'txt':
            filename, _ = QFileDialog.getSaveFileName(self, 'Save File As', '',
                                                   'Text Files (*.txt);;All Files (*)')
        else:
            filename, _ = QFileDialog.getSaveFileName(self, 'Save File As', '',
                                                   'Comma Separated Files (*.csv);;All Files (*)')

        # if filename is empty
        if filename is '':
            return

        # open the file
        f = open(filename, 'w')

        # separator
        if sep == 'csv':
            ss = ','
        else:
            ss = '\t'

        # write header
        f.writelines('Name' + ss + 'x_old' + ss + 'y_old' + ss + 'x_ref' + ss + 'y_ref' + ss + 'x_calc' + ss +
                     'y_calc'  + '\n')
        # write the data out
        for it in range(self.datatable.rowCount()):
            for jt in range(7):
                if self.datatable.item(it, jt) is not None:
                    f.writelines(self.datatable.item(it, jt).text())
                # separator if not last
                if jt < 6:
                    f.writelines(ss)
            f.writelines('\n')

        # flush and close
        f.flush()
        f.close()

    def test(self):
        self.clipboard.clear()
        print(self.clipboard.text())
        print(type(self.clipboard.text()))

        self.datatable.setCurrentItem(None)

    def help(self):
        # todo add a help file and maybe add tooltips like for LION software
        QMessageBox.information(self, 'Help', 'Help is not yet implemented. Ask Reto. There\'s tons of other things '
                                              'still to do in this code. You should take it with a grain of salt. '
                                              'Or two...')
        print('Help...')

    def calculate(self):
        # stop editing
        self.datatable.setCurrentItem(None)

        # initialize data input array as nan
        tabold = np.full((self.datatable.rowCount(), 2), np.nan)
        tabref = np.full((self.datatable.rowCount(), 2), np.nan)
        for it in range(self.datatable.rowCount()):
            # append data
            if self.datatable.item(it, 1) is not None and self.datatable.item(it, 2) is not None:
                try:
                    if self.datatable.item(it, 1).text() is not '' and self.datatable.item(it, 2).text() is not '':
                        tabold[it][0] = float(self.datatable.item(it, 1).text())
                        tabold[it][1] = float(self.datatable.item(it, 2).text())
                except ValueError:
                    QMessageBox.warning(self, 'Table error', 'There is an error in your data table. Please make sure all '
                                                             'numbers are floats.')
                    return
                except AttributeError:
                    QMessageBox.warning(self, 'Table error', 'There is an error in the data table. Did you finish all '
                                                         'editing?')

            # append reference
            if self.datatable.item(it, 3) is not None and self.datatable.item(it, 4) is not None:
                try:
                    if self.datatable.item(it, 3).text() is not '' and self.datatable.item(it, 4).text() is not '':
                        tabref[it][0] = float(self.datatable.item(it, 3).text())
                        tabref[it][1] = float(self.datatable.item(it, 4).text())
                except ValueError:
                    QMessageBox.warning(self, 'Table error', 'There is an error in your data table. Please fix.')
                    return
                except AttributeError:
                    QMessageBox.warning(self, 'Table error', 'There is an error in the data table. Did you finish all '
                                                             'editing?')

        # make sure at least two reference points are given
        # now find crefold and crefnew for calculation of parameters
        crefold = []
        crefnew = []
        for it in range(len(tabold)):
            if not np.isnan(tabold[it][0]) and not np.isnan(tabref[it][0]):
                crefold.append([tabold[it][0], tabold[it][1]])
                crefnew.append([tabref[it][0], tabref[it][1]])

        if len(crefnew) < 2:
            QMessageBox.warning(self, 'Reference error', 'Need at least two reference points to transform into the '
                                                         'new coordinates.')
            return

        # transform to np.arrays
        crefold = np.array(crefold)
        crefnew = np.array(crefnew)

        # now calculate what i need to calculate with all the reference values, all variables start with var
        vara = 0.
        varb = 0.
        varc = 0.
        vard = float(len(crefold))
        vare = 0.
        varf = 0.
        varg = 0.
        varh = 0.
        # run the sums
        for it in range(len(crefold)):
            vara += (crefold[it][0]**2. + crefold[it][1]**2.)
            varb += crefold[it][0]
            varc += crefold[it][1]
            vare += (crefold[it][0] * crefnew[it][0] + crefold[it][1] * crefnew[it][1])
            varf += (crefold[it][1] * crefnew[it][0] - crefold[it][0] * crefnew[it][1])
            varg += crefnew[it][0]
            varh += crefnew[it][1]
        # calculate parameters
        params = (1. / (varb**2. + varc**2 - vara * vard)) * np.array([-vard * vare + varb * varg + varc * varh,
                                                                       -vard * varf + varc * varg - varb * varh,
                                                                       varb * vare + varc * varf - vara * varg,
                                                                       varc * vare - varb * varf - vara * varh])

        tabnew = np.zeros((len(tabold), 2))
        for it in range(len(tabnew)):
            if not np.isnan(tabold[it][0]):
                tabnew[it][0] = np.round(tabold[it][0] * params[0] + tabold[it][1] * params[1] + params[2],
                                         self.rounddig)
                tabnew[it][1] = np.round(-tabold[it][0] * params[1] + tabold[it][1] * params[0] + params[3],
                                         self.rounddig)

        # calculate the reference
        crefcalc = []
        for it in range(len(crefold)):
            crefcalc.append([crefold[it][0] * params[0] + crefold[it][1] * params[1] + params[2],
                            -crefold[it][0] * params[1] + crefold[it][1] * params[0] + params[3]])

        # calculate shortest distance
        dsane = 0.
        for it in range(len(crefnew)):
            # add the delta between the points in the actual points
            dsane += np.sqrt((crefcalc[it][0] - crefnew[it][0])**2. + (crefcalc[it][1] - crefnew[it][1])**2.)
            # now divide by total number of points to get average deviation
        dsane /= len(crefnew)

        # set text in info label
        self.infolbl.setText('Average distance error: ' + str(np.round(dsane, self.rounddig)))

        # write the calc and the new into the table
        for it in range(len(tabold)):
            self.datatable.setItem(it, 5, QTableWidgetItem(str(tabnew[it][0])))
            self.datatable.setItem(it, 6, QTableWidgetItem(str(tabnew[it][1])))

        # resize columns to contents
        self.datatable.resizeColumnsToContents()

    def addrow(self):
        self.datatable.insertRow(self.datatable.rowCount())

    def copy(self):
        inds = []
        for idx in self.datatable.selectedIndexes():
            inds.append([idx.row(), idx.column()])
        # now start string to copy
        str2cpy = ''
        try:
            oldrow = inds[0][0]
        except IndexError:   # nothing selected
            QMessageBox.warning(self, 'Selection error', 'Select cells to copy!')
            return
        for it in range(len(inds)):
            # easier handling
            row = inds[it][0]
            col = inds[it][1]
            datfield = self.datatable.item(row, col)
            # check if the first
            if it == 0:
                if datfield is None:
                    str2cpy += ''
                else:
                    str2cpy += datfield.text()
            else:
                # add separator
                if oldrow == row:
                    str2cpy += '\t'
                else:
                    str2cpy += '\n'
                # now add the entry
                if datfield is None:
                    str2cpy += ''
                else:
                    str2cpy += datfield.text()
            # set new row
            oldrow = row
        # now copy the string to the clipboard
        self.clipboard.clear()
        self.clipboard.setText(str2cpy)

    def paste(self):
        # get the current index
        try:
            tmp = self.datatable.selectedIndexes()[0]
        except IndexError:   # nothing selected
            QMessageBox.warning(self, 'Selection error', 'Select a cell where to paste into')
            return
        currind = [tmp.row(), tmp.column()]
        # read in clipboard
        datain = self.clipboard.text().split('\n')

        # check for empty input
        if datain is '':
            QMessageBox.warning(self, 'Paste error', 'Nothing in clipboard to paste.')
            return

        data = []
        for line in datain:
            data.append(line.replace('\r','').split())

        # check if outside of range in horizontal
        if currind[1] + len(data[0]) > 7:
            QMessageBox.warning(self, 'Paste error', 'Too many columns in clipboard to fit. Wrong selection where to '
                                                     'paste into?')
            return

        # add rows in the end until we have enough to paste into
        while currind[0] + len(data) > self.datatable.rowCount():
            self.datatable.insertRow(self.datatable.rowCount())

        # now fill the cells with the pasted stuff
        for row in range(len(data)):
            for col in range(len(data[row])):
                self.datatable.setItem(row + currind[0], col+currind[1], QTableWidgetItem(data[row][col]))

    def cleartable(self):
        # clear the table
        msgbox = QMessageBox.question(self, 'Clear table?', 'Are you sure you want to clear the table?',
                                      QMessageBox.Yes, QMessageBox.No)

        if msgbox == QMessageBox.Yes:
            self.datatable.clearContents()
            self.datatable.setRowCount(13)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    sys.exit(app.exec_())
