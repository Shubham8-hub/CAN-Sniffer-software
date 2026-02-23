#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

#include "connectwidget.h"
#include "settingswidget.h"
#include "messengerwidget.h"
#include "aboutwidget.h"

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);

    void setGlobalTheme(bool isDark);
    ~MainWindow();

private:
    Ui::MainWindow *ui;

    // Add Pointer to modular pages
    ConnectWidget *pageConnect;
    SettingsWidget *pageSettings;
    MessengerWidget *pageMessenger;
    AboutWidget *pageAbout;
};
#endif // MAINWINDOW_H
