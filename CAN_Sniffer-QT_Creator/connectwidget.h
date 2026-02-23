#ifndef CONNECTWIDGET_H
#define CONNECTWIDGET_H

#include <QWidget>

#include <QSerialPort>
#include <QSerialPortInfo>
#include <QByteArray>
#include "can_protocol.h"

namespace Ui {
class ConnectWidget;
}

class ConnectWidget : public QWidget
{
    Q_OBJECT

public:
    explicit ConnectWidget(QWidget *parent = nullptr);
    ~ConnectWidget();

    // Make this public or add a getter so other tabs can access to it
    device_info_t currentDevice;
    // Exposing this so you can pass it to other tabs
    QSerialPort *serialPort;

signals:
    // Emitted when the 0x30 Connect command succeeds and struct is parsed
    void deviceConnected(device_info_t info);

    // Emitted when a 0x32 Baud Read response arrives
    void baudReadSignal(QByteArray data);

    // Emitted when a 0x33 Baud Set response arrives
    void baudSetSignal(QByteArray data);

    // Can receive message signal
    void canFrameReceived(QByteArray packet);

private slots:
    void on_btnRefresh_clicked();
    void on_btnConnect_clicked();
    void readSerialData();

private:
    Ui::ConnectWidget *ui;
    //Buffer for assembling split USB packets
    QByteArray rxBuffer;
};

#endif // CONNECTWIDGET_H
