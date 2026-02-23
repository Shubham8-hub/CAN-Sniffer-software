cmake_minimum_required(VERSION 3.19)
project(CAN_Sniffer-QT_Creator LANGUAGES CXX)

find_package(Qt6 6.5 REQUIRED COMPONENTS Core Widgets LinguistTools SerialPort)
set(CMAKE_AUTORCC ON)
qt_standard_project_setup()

qt_add_executable(CAN_Sniffer-QT_Creator
    WIN32 MACOSX_BUNDLE
    main.cpp
    mainwindow.cpp
    mainwindow.h
    mainwindow.ui
    resources.qrc
    connectwidget.h connectwidget.cpp connectwidget.ui
    settingswidget.h settingswidget.cpp settingswidget.ui
    messengerwidget.h messengerwidget.cpp messengerwidget.ui
    aboutwidget.h aboutwidget.cpp aboutwidget.ui
    can_protocol.h
)

qt_add_translations(
    TARGETS CAN_Sniffer-QT_Creator
    TS_FILES CAN_Sniffer-QT_Creator_en_IN.ts
)

target_link_libraries(CAN_Sniffer-QT_Creator
    PRIVATE
        Qt::Core
        Qt::Widgets
        Qt::SerialPort
)

include(GNUInstallDirs)

install(TARGETS CAN_Sniffer-QT_Creator
    BUNDLE  DESTINATION .
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

qt_generate_deploy_app_script(
    TARGET CAN_Sniffer-QT_Creator
    OUTPUT_SCRIPT deploy_script
    NO_UNSUPPORTED_PLATFORM_ERROR
)
install(SCRIPT ${deploy_script})
