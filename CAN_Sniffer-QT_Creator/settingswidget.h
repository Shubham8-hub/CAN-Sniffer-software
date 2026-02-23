#ifndef SETTINGSWIDGET_H
#define SETTINGSWIDGET_H

#include <QWidget>

#include <QVBoxLayout>
#include <QGroupBox>
#include <QLabel>
#include <QComboBox>
#include <QPushButton>
#include <QMap>
#include <QSerialPort>
#include "can_protocol.h"

namespace Ui {
class SettingsWidget;
}

class SettingsWidget : public QWidget
{
    Q_OBJECT

public:
    explicit SettingsWidget(QWidget *parent = nullptr);
    ~SettingsWidget();

    QSerialPort *serialPort;

public slots:
    void buildUiForDevice(device_info_t info);
    void handleBaudRead(QByteArray data);
    void handleBaudSet(QByteArray data);

signals:
    void themeToggled(bool isDark);

private:
    Ui::SettingsWidget *ui;

    QVBoxLayout *mainLayout;
    QVBoxLayout *dynamicLayout;
    bool isDarkMode;

    QMap<int, QLabel*> currentBaudLabels; // Keeps track of labels so we can update them later

    void populateBaudRates(QComboBox *cmb, uint32_t maxSpeed);
    void sendReadBaudrate(int channel);
    void sendSetBaudrate(int channel, int baudCmd);
};

#endif // SETTINGSWIDGET_H
