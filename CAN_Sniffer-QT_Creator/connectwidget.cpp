#include "connectwidget.h"
#include "ui_connectwidget.h"
#include <QMessageBox>

ConnectWidget::ConnectWidget(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::ConnectWidget)
{
    ui->setupUi(this);

    serialPort = new QSerialPort(this);

    // Connect (Green)
    ui->btnConnect->setStyleSheet("background-color: #28A745; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");
    // Refresh (Navy Blue)
    ui->btnRefresh->setStyleSheet("background-color: #004085; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");

    // Wire up the serial port receiver
    connect(serialPort, &QSerialPort::readyRead, this, &ConnectWidget::readSerialData);

    // Scan ports on startup
    on_btnRefresh_clicked();
}

ConnectWidget::~ConnectWidget()
{
    if (serialPort->isOpen()) {
        serialPort->close();
    }
    delete ui;
}

void ConnectWidget::on_btnRefresh_clicked()
{
    ui->cmbComPort->clear();
    const auto infos = QSerialPortInfo::availablePorts();
    for (const QSerialPortInfo &info : infos) {
        // Format: "COM3 - STMicroelectronics Virtual COM Port"
        QString displayText = QString("%1 - %2").arg(info.portName(), info.description());

        // We show the pretty text, but secretly store just "COM3" in the UserData role
        ui->cmbComPort->addItem(displayText, info.portName());
    }
}

void ConnectWidget::on_btnConnect_clicked()
{
    // ==========================================
    // DISCONNECT LOGIC
    // ==========================================
    if (serialPort->isOpen()) {

        // 1. Send the disconnect command (0x31)
        char cmd = CMD_DISCONNECT;
        serialPort->write(&cmd, 1);

        // 2. Wait up to 100ms to ensure the byte actually leaves the USB buffer
        // before we close the port. This prevents the STM32 from missing the command.
        serialPort->waitForBytesWritten(100);

        // 3. Close the port
        serialPort->close();

        // 4. Wipe the device_info_t struct from memory (fill with 0s)
        memset(&currentDevice, 0, sizeof(device_info_t));

        // 5. Clear the Device Information UI Labels
        ui->label_Serialno->setText("-");
        ui->label_fwversion->setText("-");
        // ui->lblChannels->setText("-"); // Add any other labels you have here

        // 6. Reset the connection UI controls
        ui->btnConnect->setText("Connect");
        ui->btnConnect->setStyleSheet("background-color: #28A745; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");
        ui->cmbComPort->setEnabled(true);
        ui->btnRefresh->setEnabled(true);

        return; // Exit the function so we don't run the connect logic below
    }

    // ==========================================
    // CONNECT LOGIC
    // ==========================================
    if (ui->cmbComPort->currentIndex() == -1) return;

    QString portName = ui->cmbComPort->currentData().toString();
    serialPort->setPortName(portName);
    serialPort->setBaudRate(QSerialPort::Baud115200);

    if (serialPort->open(QIODevice::ReadWrite)) {
        ui->btnConnect->setText("Disconnect");
        ui->btnConnect->setStyleSheet("background-color: #DC3545; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");
        ui->cmbComPort->setEnabled(false);
        ui->btnRefresh->setEnabled(false);

        // Clear any old garbage data from the RX buffer
        rxBuffer.clear();

        // Send CMD_CONNECT (0x30)
        char cmd = CMD_CONNECT;
        serialPort->write(&cmd, 1);
    } else {
        QMessageBox::critical(this, "Error", "Could not open port. It may be in use.");
    }
}


void ConnectWidget::readSerialData()
{
    rxBuffer.append(serialPort->readAll());

    // Loop through the buffer in case multiple messages arrive at once
    while (!rxBuffer.isEmpty()) {
        uint8_t cmd = (uint8_t)rxBuffer[0];

        if (cmd == RESP_ACK) {
            int expectedSize = 1 + sizeof(device_info_t);
            if (rxBuffer.size() >= expectedSize) {
                memcpy(&currentDevice, rxBuffer.data() + 1, sizeof(device_info_t));
                ui->label_Serialno->setText(QString::fromLocal8Bit(currentDevice.serial_no));
                ui->label_fwversion->setText(QString::fromLocal8Bit(currentDevice.fw_version));

                // Remove the processed bytes from the buffer
                rxBuffer.remove(0, expectedSize);

                // Trigger the Settings tab to build its UI dynamically
                emit deviceConnected(currentDevice);
            } else {
                break; // Wait for more bytes
            }
        }
        else if (cmd == CMD_READ_BAUDRATE) {  // 0x32
            if (rxBuffer.size() >= 6) {
                emit baudReadSignal(rxBuffer.left(6)); // Send 6 bytes to Settings
                rxBuffer.remove(0, 6);
            } else {
                break;
            }
        }
        else if (cmd == CMD_SET_BAUDRATE) {   // 0x33
            if (rxBuffer.size() >= 3) {
                emit baudSetSignal(rxBuffer.left(3));  // Send 3 bytes to Settings
                rxBuffer.remove(0, 3);
            } else {
                break;
            }
        }
        // Block for CAN trace
        else if (cmd == 0xAA)
        {
            // Firmware sends exactly 16 bytes for trace: [0xAA, CH, IDx4, DLC, DATAx8, 0xBB]
            if (rxBuffer.size() >= 16) {
                // Verify the footer is 0xBB before emitting
                if ((uint8_t)rxBuffer[15] == 0xBB) {
                    emit canFrameReceived(rxBuffer.left(16));
                }
                rxBuffer.remove(0, 16);
            } else {
                break; // Wait for the rest of the packet to arrive over USB
            }
        }
        else {
            // Garbage or unknown data, remove 1 byte so we don't get stuck
            rxBuffer.remove(0, 1);
        }
    }
}
