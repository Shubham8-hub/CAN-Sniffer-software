#ifndef MESSENGERWIDGET_H
#define MESSENGERWIDGET_H

#include <QWidget>

#include <QSerialPort>
#include <QByteArray>
#include <QMap>
#include <QTimer>
#include "can_protocol.h"

namespace Ui {
class MessengerWidget;
}

class MessengerWidget : public QWidget
{
    Q_OBJECT

public:
    explicit MessengerWidget(QWidget *parent = nullptr);
    ~MessengerWidget();

    QSerialPort *serialPort; // Passed from Connection Widget

public slots:
    void handleIncomingCanFrame(QByteArray packet);
    void applyTheme(bool isDark);

private slots:
    void on_btnStartStopTrace_clicked();
    void on_btnClearTrace_clicked();

    // Transmit slots
    void on_lineEdit_2_textChanged(const QString &dlcText); // Detect DLC changes
    void on_radioButton_2_toggled(bool checked);            // Toggle Periodic ms field
    void on_pushButton_2_clicked();                         // "Send Message" (Immediate)
    void on_pushButton_clicked();                           // "Add Message" to list
    void handleActionClicked(int row);                      // Handles Start/Stop in the list
    void sendPeriodicMessage(int row);                      // Triggered by timers
    void on_tableWidget_cellChanged(int row, int column);
private:
    Ui::MessengerWidget *ui;
    bool isTracing; //keep track of the start/stop state

    // Tracking for the Trace table
    QMap<QString, int>  traceRowMap;               // Maps CAN ID -> Table Row Index
    QMap<QString, uint32_t> messageCounterMap;     // Maps CAN ID -> Message Count
    QMap<QString, QByteArray> prevDataMap;         // Maps CAN ID -> Previous Payload

    // Tracks Periodic Timers based on the row index in tableWidget_2
    QMap<int, QTimer*> periodicTimers;

    // Helper functions
    void addMessageToTrace(uint8_t ch, uint8_t dir, uint32_t id, uint8_t dlc, QByteArray data);
    void transmitToHardware(uint8_t ch, uint32_t id, uint8_t dlc, QByteArray data);
    QByteArray readDataFromGrid(int dlc);

};

#endif // MESSENGERWIDGET_H
