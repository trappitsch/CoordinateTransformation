"""
Copyright (C) 2020 Reto Trappitsch

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import sys
import pandas as pd
import numpy as np
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,\
    QTableWidgetItem, QLabel, QMessageBox, QFileDialog, QRadioButton, QSpinBox, QShortcut, QMenu
from PyQt5.QtGui import QGuiApplication, QKeySequence, QMouseEvent
from PyQt5.QtCore import Qt


class MainApp(QWidget):
    """
    Coordinate transform program for relocating samples in different coordinate systems

    Developer:  Reto Trappitsch
    Version:    2.1.1
    Date:       May 29, 2020
    """

    def __init__(self):
        # version number:
        self.version = '2.1.1'
        self.version_date = 'May 29, 2020'

        # run in debug mode?
        self.rundebug = False
        # round digits
        self.rounddig = 3
        # which calculation mode to start in (Nittler or Admon - labels of radiobuttons)
        self.calcmode = 'Nittler'
        # initialize the thing
        super().__init__()
        self.title = 'Coordinate Transformation'
        self.left = 50
        self.top = 80
        self.width = 900
        # this is used for geometry but then also for tableheight. tableheight dominates!
        self.height = 845

        # default for header, columns
        self.default_header_rows = 1
        self.default_name_column = 1
        self.default_x_column = 2
        self.default_y_column = 3

        # my clipboard
        self.clipboard = QApplication.clipboard()

        self.setup_keyboard_shortcuts()

        # initialize the UI
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # define outermost v layout
        outervlayout = QVBoxLayout()

        # some top row buttons and layout
        toprowbutthlayout = QHBoxLayout()
        # open buttons
        openfile_butt = QPushButton('Open file')
        openfile_butt.clicked.connect(self.openfile)
        openfile_butt.setToolTip('Load coordinates from a file. Please make sure you specify\n'
                                'how many header rows the file has and where your x, y, and\n'
                                'fiducial data is.'
                                'Files that can be read are: comma separated (*.csv), tab\n'
                                'separated (*.txt), or excel files.')
        toprowbutthlayout.addWidget(openfile_butt)
        # save button
        toprowbutthlayout.addStretch()
        savecsv_butt = QPushButton('Save csv')
        savecsv_butt.clicked.connect(lambda: self.savefile('csv'))
        savecsv_butt.setToolTip('Save the current table, as is displayed, into a csv file. This file can also be\n'
                                'imported later with the \'Open csv\' button.')
        toprowbutthlayout.addWidget(savecsv_butt)
        savetxt_butt = QPushButton('Save txt')
        savetxt_butt.clicked.connect(lambda: self.savefile('txt'))
        savecsv_butt.setToolTip('Save the current table, as is displayed, into a txt file. This file can also be\n'
                                'imported later with the \'Open txt\' button.')
        toprowbutthlayout.addWidget(savetxt_butt)
        # add radiobuttons for method
        toprowbutthlayout.addStretch()
        mnit_radio = QRadioButton('Nittler')
        mnit_radio.setToolTip('Method from Larry Nittler\' PhD thesis, App. E. Only shift and rotation are \n'
                              'considered. Strech not possible. Linear regression through all reference points\n'
                              'is calculated, so mechanical slack, etc., is regressed out over time.')
        madm_radio = QRadioButton('Admon')
        madm_radio.setToolTip('Method from Admon et al. (2015). See \'Help\' for full reference. Only three\n'
                              'fiducial marks are considered for coordinate transformation, however, the stretch\n'
                              'of coordinate systems is included as well.')
        if self.calcmode == 'Nittler':
            mnit_radio.setChecked(True)
        else:
            madm_radio.setChecked(True)
        # connect buttons to the subroutine
        mnit_radio.toggled.connect(lambda: self.set_calcmode(mnit_radio))
        mnit_radio.toggled.connect(lambda: self.set_calcmode(madm_radio))
        # add to layout
        toprowbutthlayout.addWidget(mnit_radio)
        toprowbutthlayout.addWidget(madm_radio)
        # add test, help, quit
        toprowbutthlayout.addStretch()
        if self.rundebug:
            test_butt = QPushButton('Test')
            test_butt.clicked.connect(self.test)
            toprowbutthlayout.addWidget(test_butt)
        help_butt = QPushButton('Help')
        help_butt.clicked.connect(self.help)
        help_butt.setToolTip('Display a brief help message.')
        toprowbutthlayout.addWidget(help_butt)
        quit_butt = QPushButton('Quit')
        quit_butt.clicked.connect(self.close)
        quit_butt.setToolTip('Close the program')
        toprowbutthlayout.addWidget(quit_butt)
        # add buttons to layout
        outervlayout.addLayout(toprowbutthlayout)
        # outervlayout.addStretch()

        # set a second row with options, QSpinBoxes mostly
        secondrow = QHBoxLayout()
        header_label = QLabel('header rows:')
        self.header_spinbox = QSpinBox(self, minimum=0, maximum=1000)
        self.header_spinbox.setAlignment(Qt.AlignRight)
        self.header_spinbox.setValue(self.default_header_rows)
        self.header_spinbox.setToolTip('Select how many rows should be skipped\n'
                                       'at the beginning of file. These are the\n'
                                       'header rows.')

        namecol_label = QLabel('name col:')
        self.namecol_spinbox = QSpinBox(self, minimum=0, maximum=1000)
        self.namecol_spinbox.setAlignment(Qt.AlignRight)
        self.namecol_spinbox.setValue(self.default_name_column)
        self.namecol_spinbox.setToolTip('Which column contains the name\n'
                                        'of the location? Select 0 for None.')

        xcol_label = QLabel('x col:')
        self.xcol_spinbox = QSpinBox(self, minimum=0, maximum=1000)
        self.xcol_spinbox.setAlignment(Qt.AlignRight)
        self.xcol_spinbox.setValue(self.default_x_column)
        self.xcol_spinbox.setToolTip('Which column contains the x coordinate\n'
                                     'of the location? Select 0 for None.')

        ycol_label = QLabel('y col:')
        self.ycol_spinbox = QSpinBox(self, minimum=0, maximum=1000)
        self.ycol_spinbox.setAlignment(Qt.AlignRight)
        self.ycol_spinbox.setValue(self.default_y_column)
        self.ycol_spinbox.setToolTip('Which column contains the y coordinate\n'
                                     'of the location? Select 0 for None.')

        fid_xcol_label = QLabel('ref x col:')
        self.fid_xcol_spinbox = QSpinBox(self, minimum=0, maximum=1000)
        self.fid_xcol_spinbox.setAlignment(Qt.AlignRight)
        self.fid_xcol_spinbox.setValue(self.default_x_column + 2)
        self.fid_xcol_spinbox.setToolTip('Which column contains the x reference coordinate\n'
                                         'of the location? Select 0 for None.')

        fid_ycol_label = QLabel('ref y col:')
        self.fid_ycol_spinbox = QSpinBox(self, minimum=0, maximum=1000)
        self.fid_ycol_spinbox.setAlignment(Qt.AlignRight)
        self.fid_ycol_spinbox.setValue(self.default_y_column + 2)
        self.fid_xcol_spinbox.setToolTip('Which column contains the y reference coordinate\n'
                                         'of the location? Select 0 for None.')

        secondrow.addWidget(header_label)
        secondrow.addWidget(self.header_spinbox)
        secondrow.addStretch()
        secondrow.addWidget(namecol_label)
        secondrow.addWidget(self.namecol_spinbox)
        secondrow.addStretch()
        secondrow.addWidget(xcol_label)
        secondrow.addWidget(self.xcol_spinbox)
        secondrow.addStretch()
        secondrow.addWidget(ycol_label)
        secondrow.addWidget(self.ycol_spinbox)
        secondrow.addStretch()
        secondrow.addWidget(fid_xcol_label)
        secondrow.addWidget(self.fid_xcol_spinbox)
        secondrow.addStretch()
        secondrow.addWidget(fid_ycol_label)
        secondrow.addWidget(self.fid_ycol_spinbox)
        secondrow.addStretch()

        # add to outer layout
        outervlayout.addLayout(secondrow)

        # make the table
        self.datatable = QTableWidget()
        self.datatable.setRowCount(23)
        self.datatable.setColumnCount(7)
        # implement mouse button
        self.datatable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.datatable.customContextMenuRequested.connect(self.context_menu)
        # set headers
        headers = [QTableWidgetItem('Name'), QTableWidgetItem('x'), QTableWidgetItem('y'),
                   QTableWidgetItem('x_ref'), QTableWidgetItem('y_ref'),
                   QTableWidgetItem('x_calc'), QTableWidgetItem('y_calc')]
        for it in range(len(headers)):
            self.datatable.setHorizontalHeaderItem(it, headers[it])
        # set up clipboard for table
        self.clip = QGuiApplication.clipboard()
        # add table to widget
        outervlayout.addWidget(self.datatable)
        # bottom button row
        bottrowbutthlayout = QHBoxLayout()
        # add Row
        addrow_butt = QPushButton('+ Row')
        addrow_butt.clicked.connect(self.addrow)
        addrow_butt.setToolTip('Add an empty row to the data table. You can then manually enter new values into this\n'
                               'empty row.')
        bottrowbutthlayout.addWidget(addrow_butt)
        # clear table
        clear_butt = QPushButton('Clear all')
        clear_butt.clicked.connect(self.cleartable)
        clear_butt.setToolTip('Clear all data in the table. A confirmation will be required, but after that, there\n'
                              'is no undoing this action. Make sure you have the data, assuming you need it, saved.')
        bottrowbutthlayout.addWidget(clear_butt)

        bottrowbutthlayout.addStretch()
        # information on Fit
        self.infolbl = QLabel('')
        bottrowbutthlayout.addWidget(self.infolbl)
        bottrowbutthlayout.addStretch()
        # calculate button
        calc_butt = QPushButton('Calculate')
        calc_butt.clicked.connect(self.calculate)
        calc_butt.setToolTip('Calculate the regression. An \'Average distance error\' will be provided. This is a\n'
                             'number that is good to compare from fit to fit. If weird, non-numeric values show up\n'
                             'make sure that you have entered proper numbers.')
        bottrowbutthlayout.addWidget(calc_butt)
        # add to outer layout
        # outervlayout.addStretch()
        outervlayout.addLayout(bottrowbutthlayout)

        # set layout to app
        self.setLayout(outervlayout)

        # show the UI
        self.show()

    def setup_keyboard_shortcuts(self):
        # Keyboard shortcuts
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy)
        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        paste_shortcut.activated.connect(self.paste)
        open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_shortcut.activated.connect(self.openfile)
        del_shortcut = QShortcut(QKeySequence("Del"), self)
        del_shortcut.activated.connect(self.delete)

    def context_menu(self, position):
        menu = QMenu()
        copyAction = menu.addAction("Copy")
        pasteAction = menu.addAction("Paste")
        delAction = menu.addAction("Delete")
        action = menu.exec_(self.datatable.mapToGlobal(position))
        if action == copyAction:
            self.copy()
        elif action == pasteAction:
            self.paste()
        elif action == delAction:
            self.delete()

    def set_calcmode(self, rb):
        if rb.isChecked():
            self.calcmode = rb.text()
            if self.rundebug:
                print(self.calcmode)

    def openfile(self):
        # file dialog
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                  'Supported Files (*.csv *.txt *.xls *.xlsx);;All Files (*)',
                                                  options=options)

        if filename == '':
            return

        sep = filename[-4:len(filename)]

        headerrows = int(self.header_spinbox.value())
        namecol = int(self.namecol_spinbox.value())
        xdatcol = int(self.xcol_spinbox.value())
        ydatcol = int(self.ycol_spinbox.value())
        xfidcol = int(self.fid_xcol_spinbox.value())
        yfidcol = int(self.fid_ycol_spinbox.value())

        # columns to use
        usecol = []
        if namecol > 0:
            usecol.append(namecol-1)
        usecol.append(xdatcol-1)
        usecol.append(ydatcol-1)
        usecol.append(xfidcol-1)
        usecol.append(yfidcol-1)

        datain = None
        # csv and txt read in:
        try:
            if sep == '.csv':
                datain = pd.read_csv(filename, header=None, skiprows=headerrows, usecols=usecol)[usecol]
            # separator:
            elif sep == '.txt':
                datain = pd.read_csv(filename, delimiter='\t', header=None, skiprows=headerrows, usecols=usecol)[usecol]
            elif sep == '.xls' or sep == 'xlsx':
                datain = pd.read_excel(filename, header=None, skiprows=headerrows, usecols=usecol)[usecol]
        except KeyError or ValueError:
            self.show_data_error()
            return

        # first set the length of the table to be the length of the data
        self.datatable.setRowCount(0)
        # name column present
        namecolpresent = False
        if namecol > 0:
            namecolpresent = True

        # now add data rows
        for it in range(datain.shape[0]):
            row = []
            if not namecolpresent:
                row.append('')
            for jt in range(datain.shape[1]):
                row.append(datain.iloc[it, jt])
            # add the row to the table
            self.addTableRow(row)

        # adjust table size
        self.datatable.resizeColumnsToContents()

    def show_data_error(self):
        QMessageBox.warning(self, 'Requested data not found', 'Could not find the data you requested. Please ensure'
                                                              'that the data exists in the respective columns.')

    def addTableRow(self, row_data):
        row = self.datatable.rowCount()
        self.datatable.setRowCount(row+1)
        col = 0
        for item in row_data:
            itemstr = str(item)
            if itemstr == 'nan':
                itemstr = ''
            cell = QTableWidgetItem(itemstr)
            self.datatable.setItem(row, col, cell)
            col += 1

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
                     'y_calc' + '\n')
        # write the data out

        for it in range(self.datatable.rowCount()):
            for jt in range(7):
                if self.datatable.item(it, jt) is not None:
                    savestring = self.datatable.item(it, jt).text().strip().rstrip().replace('\n', '').replace('\r', '')
                    f.writelines(savestring)
                # separator if not last
                if jt < 6:
                    f.writelines(ss)
            f.writelines('\n')

        # flush and close
        f.flush()
        f.close()

    def test(self):
        print(self.calcmode)

    def help(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setWindowTitle('Help')
        msgBox.setInformativeText('Help is implemented with tooltips, hover over the buttons in question\n'
                                  'and you should receive some information.\n\n'
                                  'Routines:\n'
                                  'Nittler: (PhD Thesis Larry Nittler, Appendix F)\n'
                                  'Linear regression to as many reference points that are given. Only \n'
                                  'Rotation and shift are included in this method. No stretch of the data.\n'
                                  'Make sure that the reference systems are in the same unit system!\n\n'
                                  'Admon: (Admon et al. (2005) Microsc. Microanal. 11, 354–362)\n'
                                  'Only three fiducial marks can be selected, however, stretch of the\n'
                                  'coordinate system is also calculated. Ideal when switching between\n'
                                  'different units from one coordinate system to the next.\n\n'
                                  'Author: Reto Trappitsch\n'
                                  'Version: ' + self.version + '\n'
                                  'Date: ' + self.version_date + '\n\n')
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec()

    def calculate(self):
        # admon or nittler
        if self.calcmode == 'Nittler':
            self.calculate_nittler()
        else:
            self.calculate_admon()

    def calculate_admon(self):
        # stop editing
        self.datatable.setCurrentItem(None)

        # fake z coordinate
        zcoord = 1.

        # initialize data input array as nan
        tabold = np.full((self.datatable.rowCount(), 3), np.nan)
        tabref = np.full((self.datatable.rowCount(), 2), np.nan)
        for it in range(self.datatable.rowCount()):
            # append data
            if self.datatable.item(it, 1) is not None and self.datatable.item(it, 2) is not None:
                try:
                    if self.datatable.item(it, 1).text() is not '' and self.datatable.item(it, 2).text() is not '':
                        tabold[it][0] = float(self.datatable.item(it, 1).text())
                        tabold[it][1] = float(self.datatable.item(it, 2).text())
                        tabold[it][2] = zcoord
                except ValueError:
                    QMessageBox.warning(self, 'Table error', 'There is an error in your data table. Please make sure '
                                                             'all numbers are floats.')
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
                crefold.append([tabold[it][0], tabold[it][1], zcoord])   # artificially add a z coordinate
                crefnew.append([tabref[it][0], tabref[it][1], zcoord])   # artificially add a z coordinate

        if len(crefnew) < 3:
            QMessageBox.warning(self, 'Reference error', 'Need three reference points to transform into the '
                                                         'new coordinates.')
            return
        if len(crefnew) > 3:
            QMessageBox.information(self, 'Too many reference points', 'Only the first three reference values are '
                                                                       'taken for the transformation.')

        # transform to np.arrays, only take the first three entries
        crefold = np.array(crefold[0:3])
        crefnew = np.array(crefnew[0:3])
        crefoldt = np.array(crefold).transpose()
        crefnewt = np.array(crefnew).transpose()

        tabnew = np.zeros((len(tabold), 2))
        for it in range(len(tabold)):
            tmpnew = np.matmul(crefnewt, np.matmul(np.linalg.inv(crefoldt), tabold[it]))
            tabnew[it][0] = np.round(tmpnew[0], self.rounddig)
            tabnew[it][1] = np.round(tmpnew[1], self.rounddig)

        # write the calc and the new into the table
        for it in range(len(tabold)):
            self.datatable.setItem(it, 5, QTableWidgetItem(str(tabnew[it][0])))
            self.datatable.setItem(it, 6, QTableWidgetItem(str(tabnew[it][1])))

        # resize columns to contents
        self.datatable.resizeColumnsToContents()

    def calculate_nittler(self):
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

    # def keyPressEvent(self, event):
    #     """
    #     Implement copy, paste
    #     """
    #     if type(event) == QKeyEvent:
    #         if event.key() == Qt.Key_Space:
    #             print('spacer')
    #
    def copy(self):
        inds = []
        for idx in self.datatable.selectedIndexes():
            inds.append([idx.row(), idx.column()])
        # now start string to copy
        str2cpy = ''
        try:
            oldrow = inds[0][0]
        except IndexError:   # nothing selected, then just do nothing
            return
        for it in range(len(inds)):
            # easier handling
            row = inds[it][0]
            col = inds[it][1]
            datfield = self.datatable.item(row, col)
            # check if the first
            if it == 0:
                if datfield is None:
                    str2cpy = ''
                else:
                    str2cpy = datfield.text()
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

    def delete(self):
        # get the current index
        inds = []
        try:
            for idx in self.datatable.selectedIndexes():
                inds.append([idx.row(), idx.column()])
        except IndexError:   # nothing selected
            return

        # selected indeces
        print(inds)

        # now fill the cells with the pasted stuff
        for row, col in inds:
            self.datatable.setItem(row, col, QTableWidgetItem(''))

    def cleartable(self):
        # clear the table
        msgbox = QMessageBox.question(self, 'Clear table?', 'Are you sure you want to clear the table?',
                                      QMessageBox.Yes, QMessageBox.No)

        if msgbox == QMessageBox.Yes:
            self.datatable.clearContents()
            self.datatable.setRowCount(23)
            # set geometry


if __name__ == '__main__':
    appctxt = ApplicationContext()
    ex = MainApp()
    exit_code = appctxt.app.exec_()  # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)