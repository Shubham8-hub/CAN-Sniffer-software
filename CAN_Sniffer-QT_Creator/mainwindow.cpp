#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QLabel>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    // // Apply Global Dark Theme Stylesheet
    // this->setStyleSheet(R"(
    //     /* Main Window and Generic Widgets */
    //     QMainWindow, QStackedWidget, QWidget {
    //         background-color: #1E1E1E;
    //         color: #E0E0E0;
    //     }

    //     /* Sidebar Container */
    //     #sidebarWidget {
    //         background-color: #141414;
    //         border-right: 1px solid #333333;
    //     }

    //     /* Sidebar Buttons */
    //     QToolButton {
    //         background-color: transparent;
    //         color: #A0A0A0;
    //         border: none;
    //         padding-top: 15px;
    //         padding-bottom: 15px;
    //         font-size: 11px;
    //         font-weight: bold;
    //     }

    //     /* Hover effect for buttons */
    //     QToolButton:hover {
    //         background-color: #2D2D30;
    //         color: #FFFFFF;
    //         border-left: 3px solid #007ACC; /* Nice blue highlight on hover */
    //     }

    //     /* Status Bar */
    //     QStatusBar {
    //         background-color: #007ACC;
    //         color: white;
    //         font-weight: bold;
    //     }
    // )");

    // 1. Instanciate the custom pages
    pageConnect = new ConnectWidget(this);
    pageSettings = new SettingsWidget(this);
    pageMessenger = new MessengerWidget(this);
    pageAbout = new AboutWidget(this);

    // 2. Add then to the Stacked Widget (Index : 0, 1, 2, 3)
    ui->mainstackedWidget->addWidget(pageConnect);
    ui->mainstackedWidget->addWidget(pageSettings);
    ui->mainstackedWidget->addWidget(pageMessenger);
    ui->mainstackedWidget->addWidget(pageAbout);

    // 3. connect the sidebar buttons to switch pages

    ui->btnConnect->setCheckable(true);
    ui->btnSettings->setCheckable(true);
    ui->btnMessenger->setCheckable(true);
    ui->btnAbout->setCheckable(true);

    ui->btnConnect->setAutoExclusive(true);
    ui->btnSettings->setAutoExclusive(true);
    ui->btnMessenger->setAutoExclusive(true);
    ui->btnAbout->setAutoExclusive(true);

    ui->btnConnect->setChecked(true); // Set default active button

    connect(ui->btnConnect, &QToolButton::clicked, [=]() {
        ui->mainstackedWidget->setCurrentIndex(0);
    });
    connect(ui->btnSettings, &QToolButton::clicked, [=]() {
        ui->mainstackedWidget->setCurrentIndex(1);
    });
    connect(ui->btnMessenger, &QToolButton::clicked, [=]() {
        ui->mainstackedWidget->setCurrentIndex(2);
    });
    connect(ui->btnAbout, &QToolButton::clicked, [=]() {
        ui->mainstackedWidget->setCurrentIndex(3);
    });

    // Share the serial port so Settings can write to it
    pageSettings->serialPort = pageConnect->serialPort;

    // Share the serial port to messenger
    pageMessenger->serialPort = pageConnect->serialPort;

    // Connect the data routing signals
    connect(pageConnect, &ConnectWidget::deviceConnected, pageSettings, &SettingsWidget::buildUiForDevice);
    connect(pageConnect, &ConnectWidget::baudReadSignal, pageSettings, &SettingsWidget::handleBaudRead);
    connect(pageConnect, &ConnectWidget::baudSetSignal, pageSettings, &SettingsWidget::handleBaudSet);

    // Route CAN frames to the Messenger tab
    connect(pageConnect, &ConnectWidget::canFrameReceived, pageMessenger, &MessengerWidget::handleIncomingCanFrame);

    connect(pageSettings, &SettingsWidget::themeToggled, this, &MainWindow::setGlobalTheme);

    connect(pageSettings, &SettingsWidget::themeToggled, pageMessenger, &MessengerWidget::applyTheme);

    // 4. Set the default page on startup
    ui->mainstackedWidget->setCurrentIndex(0);
    // ui->statusbar->showMessage("Made in India ❤️");

    // ---> NEW: Set Window Title <---
    this->setWindowTitle("BitSniff");
    this->setWindowIcon(QIcon(":/icons/icon.png"));

    // ---> NEW: Centered Status Bar <---
    QLabel *statusLabel = new QLabel("Made in India ❤️", this);
    statusLabel->setAlignment(Qt::AlignCenter);
    // The '1' tells the status bar to stretch this widget to fill the whole space
    ui->statusbar->addWidget(statusLabel, 1);

    setGlobalTheme(true);
}

MainWindow::~MainWindow()
{
    delete ui;
}

// // ==========================================
// // GLOBAL THEME SWITCHER
// // ==========================================
// void MainWindow::setGlobalTheme(bool isDark)
// {
//     if (isDark) {
//         // --- DARK MODE ---
//         this->setStyleSheet(R"(
//             /* Main Window and Generic Widgets */
//             QMainWindow, QStackedWidget, QWidget {
//                 background-color: #1E1E1E;
//                 color: #E0E0E0;
//             }

//             /* Sidebar Container */
//             #sidebarWidget {
//                 background-color: #141414;
//                 border-right: 1px solid #333333;
//             }

//             /* Sidebar Buttons */
//             QToolButton {
//                 background-color: transparent;
//                 color: #A0A0A0;
//                 border: none;
//                 padding-top: 15px;
//                 padding-bottom: 15px;
//                 font-size: 11px;
//                 font-weight: bold;
//             }

//             /* Hover effect for buttons */
//             QToolButton:hover {
//                 background-color: #2D2D30;
//                 color: #FFFFFF;
//                 border-left: 3px solid #007ACC;
//             }

//             /* Status Bar */
//             QStatusBar {
//                 background-color: #007ACC;
//                 color: white;
//                 font-weight: bold;
//             }

//             /* Table Styling */
//             QTableWidget {
//                 border: 1px solid #555555;
//                 gridline-color: #555555;
//                 background-color: #1E1E1E;
//                 color: #E0E0E0;
//             }
//             QHeaderView::section {
//                 background-color: #2D2D30;
//                 border: 1px solid #555555;
//                 font-weight: bold;
//                 color: #E0E0E0;
//             }

//             /* Group Boxes */
//             QGroupBox {
//                 border: 1px solid #555555;
//                 margin-top: 1ex;
//                 font-weight: bold;
//             }
//             QGroupBox::title {
//                 subcontrol-origin: margin;
//                 left: 10px;
//                 padding: 0 3px;
//             }

//             /* Text Inputs and Dropdowns */
//             QLineEdit, QComboBox {
//                 background-color: #2D2D30;
//                 border: 1px solid #555555;
//                 color: #FFFFFF;
//                 padding: 2px;
//             }
//         )");
//     } else {
//         // --- LIGHT MODE ---
//         this->setStyleSheet(R"(
//             /* Main Window and Generic Widgets */
//             QMainWindow, QStackedWidget, QWidget {
//                 background-color: #F5F5F5;
//                 color: #212529;
//             }

//             /* Sidebar Container */
//             #sidebarWidget {
//                 background-color: #E9ECEF;
//                 border-right: 1px solid #DEE2E6;
//             }

//             /* Sidebar Buttons */
//             QToolButton {
//                 background-color: transparent;
//                 color: #495057;
//                 border: none;
//                 padding-top: 15px;
//                 padding-bottom: 15px;
//                 font-size: 11px;
//                 font-weight: bold;
//             }

//             /* Hover effect for buttons */
//             QToolButton:hover {
//                 background-color: #CED4DA;
//                 color: #000000;
//                 border-left: 3px solid #007ACC;
//             }

//             /* Status Bar */
//             QStatusBar {
//                 background-color: #007ACC;
//                 color: white;
//                 font-weight: bold;
//             }

//             /* Table Styling */
//             QTableWidget {
//                 border: 1px solid #DEE2E6;
//                 gridline-color: #DEE2E6;
//                 background-color: #FFFFFF;
//                 color: #212529;
//             }
//             QHeaderView::section {
//                 background-color: #E9ECEF;
//                 border: 1px solid #DEE2E6;
//                 font-weight: bold;
//                 color: #212529;
//             }

//             /* Group Boxes */
//             QGroupBox {
//                 border: 1px solid #ADB5BD;
//                 margin-top: 1ex;
//                 font-weight: bold;
//             }
//             QGroupBox::title {
//                 subcontrol-origin: margin;
//                 left: 10px;
//                 padding: 0 3px;
//             }

//             /* Text Inputs and Dropdowns */
//             QLineEdit, QComboBox {
//                 background-color: #FFFFFF;
//                 border: 1px solid #CED4DA;
//                 color: #212529;
//                 padding: 2px;
//             }
//         )");
//     }
// }

// ==========================================
// GLOBAL THEME SWITCHER
// ==========================================
void MainWindow::setGlobalTheme(bool isDark)
{
    if (isDark) {
        // --- DARK MODE ---
        this->setStyleSheet(R"(
            QMainWindow, QStackedWidget, QWidget { background-color: #1E1E1E; color: #E0E0E0; }
            #sidebarWidget { background-color: #141414; border-right: 1px solid #333333; }

            /* Sidebar Buttons */
            #sidebarWidget QToolButton { background-color: transparent; color: #A0A0A0; border: none; padding-top: 15px; padding-bottom: 15px; font-size: 11px; font-weight: bold; }
            #sidebarWidget QToolButton:hover { background-color: #2D2D30; color: #FFFFFF; border-left: 3px solid #007ACC; }
            #sidebarWidget QToolButton:checked { background-color: #FFB347; color: #000000; border-left: 4px solid #CC5500; }

            QStatusBar { background-color: #007ACC; color: white; font-weight: bold; }

            /* MESSENGER TABS */
            QTabBar::tab { background-color: #2D2D30; color: #A0A0A0; padding: 8px 16px; border: 1px solid #555555; border-bottom: none; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: #FFB6C1; color: #000000; font-weight: bold; }

            /* Table Styling */
            QTableWidget { border: 1px solid #555555; gridline-color: #555555; background-color: #1E1E1E; color: #E0E0E0; }
            QHeaderView::section { background-color: #2D2D30; border: 1px solid #555555; font-weight: bold; color: #E0E0E0; }

            QGroupBox { border: 1px solid #555555; margin-top: 1ex; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QLineEdit, QComboBox { background-color: #2D2D30; border: 1px solid #555555; color: #FFFFFF; padding: 2px; }

            /* ---> NEW: RADIO BUTTON AND CHECKBOX FIX <--- */
            QCheckBox, QRadioButton { color: #E0E0E0; background-color: transparent; }

            QCheckBox::indicator { width: 14px; height: 14px; background-color: #2D2D30; border: 1px solid #555555; border-radius: 2px; }
            QCheckBox::indicator:checked { background-color: #007ACC; border: 1px solid #007ACC; }

            QRadioButton::indicator { width: 14px; height: 14px; background-color: #2D2D30; border: 1px solid #555555; border-radius: 7px; }
            QRadioButton::indicator:checked { background-color: #007ACC; border: 1px solid #007ACC; }
        )");
    } else {
        // --- LIGHT MODE ---
        this->setStyleSheet(R"(
            QMainWindow, QStackedWidget, QWidget { background-color: #F5F5F5; color: #212529; }
            #sidebarWidget { background-color: #E9ECEF; border-right: 1px solid #DEE2E6; }

            /* Sidebar Buttons */
            #sidebarWidget QToolButton { background-color: transparent; color: #495057; border: none; padding-top: 15px; padding-bottom: 15px; font-size: 11px; font-weight: bold; }
            #sidebarWidget QToolButton:hover { background-color: #CED4DA; color: #000000; border-left: 3px solid #007ACC; }
            #sidebarWidget QToolButton:checked { background-color: #FFB347; color: #000000; border-left: 4px solid #CC5500; }

            QStatusBar { background-color: #007ACC; color: white; font-weight: bold; }

            /* MESSENGER TABS */
            QTabBar::tab { background-color: #E9ECEF; color: #495057; padding: 8px 16px; border: 1px solid #DEE2E6; border-bottom: none; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: #FFB6C1; color: #000000; font-weight: bold; }

            /* ---> NEW: TABLE STYLING (BLACK BORDER) <--- */
            QTableWidget { border: 1px solid #000000; gridline-color: #ADB5BD; background-color: #FFFFFF; color: #212529; }
            QHeaderView::section { background-color: #E9ECEF; border: 1px solid #000000; font-weight: bold; color: #212529; }

            QGroupBox { border: 1px solid #ADB5BD; margin-top: 1ex; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QLineEdit, QComboBox { background-color: #FFFFFF; border: 1px solid #CED4DA; color: #212529; padding: 2px; }

            /* ---> NEW: RADIO BUTTON AND CHECKBOX FIX <--- */
            QCheckBox, QRadioButton { color: #212529; background-color: transparent; }

            QCheckBox::indicator { width: 14px; height: 14px; background-color: #FFFFFF; border: 1px solid #ADB5BD; border-radius: 2px; }
            QCheckBox::indicator:checked { background-color: #007ACC; border: 1px solid #007ACC; }

            QRadioButton::indicator { width: 14px; height: 14px; background-color: #FFFFFF; border: 1px solid #ADB5BD; border-radius: 7px; }
            QRadioButton::indicator:checked { background-color: #007ACC; border: 1px solid #007ACC; }
        )");
    }
}
