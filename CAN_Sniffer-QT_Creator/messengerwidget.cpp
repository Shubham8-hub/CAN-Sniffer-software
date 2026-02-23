#include "messengerwidget.h"
#include "ui_messengerwidget.h"
#include <QDateTime>
#include <QLabel>
#include <QPushButton>
#include <QMessageBox>

MessengerWidget::MessengerWidget(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::MessengerWidget),
    isTracing(false)
{
    ui->setupUi(this);

    // 1. Setup Trace Table Columns to match exactly 7 columns from your UI file
    // ui->tableTrace->setColumnCount(8);
    // ui->tableTrace->setHorizontalHeaderLabels({"Time","Channel", "Dir", "ID", "Type", "DLC", "Data"});
    // ui->tableTrace->setHorizontalHeaderLabels({"Time", "Channel", "Dir", "ID", "Type", "DLC", "Data", "Count"});
    // Make the data column stretch to fill empty space

    // 1. Trace Table Setup
    ui->tableTrace->setColumnCount(8);
    ui->tableTrace->horizontalHeader()->setStretchLastSection(true);

    // 2. Transmit Table Setup (Added Messages List)
    ui->tableWidget_2->setColumnCount(8);

    // 3. Dynamic Data Grid Setup
    ui->tableWidget->setRowCount(1); // Make sure there is 1 row to type data into!
    ui->lineEdit_2->setText("8");    // Default DLC
    ui->lineEdit_3->setText("20");   // Default 20ms
    ui->lineEdit_3->setEnabled(false); // Disabled because 'Manual' is default

    applyTheme(true);

    // // 1. Add Borders to all Tables and Cells
    // QString tableStyle = R"(
    //     QTableWidget {
    //         border: 1px solid #555555;
    //         gridline-color: #555555;
    //         background-color: #1E1E1E;
    //     }
    //     QHeaderView::section {
    //         background-color: #2D2D30;
    //         border: 1px solid #555555;
    //         font-weight: bold;
    //     }
    // )";
    // ui->tableTrace->setStyleSheet(tableStyle);
    // ui->tableWidget->setStyleSheet(tableStyle);
    // ui->tableWidget_2->setStyleSheet(tableStyle);

    // 2. Color Static Buttons
    // Start Trace (Initial Green)
    ui->btnStartStopTrace->setStyleSheet("background-color: #28A745; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");

    // Clear Trace (Navy Blue) <--- ADD THIS LINE
    ui->btnClearTrace->setStyleSheet("background-color: #004085; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");

    // Add Message (Navy Blue)
    ui->pushButton->setStyleSheet("background-color: #004085; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");

    // Send Message (Green)
    ui->pushButton_2->setStyleSheet("background-color: #28A745; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");

    // Populate Channel Dropdown
    ui->comboBox_2->addItems({"CAN 0", "CAN 1"});

    ui->tableTrace->horizontalHeader()->setStretchLastSection(true);
}

MessengerWidget::~MessengerWidget() { delete ui; }

// --- Start / Stop Trace Logic ---
void MessengerWidget::on_btnStartStopTrace_clicked()
{
    // If the serial port isn't connected, do nothing
    if (!serialPort || !serialPort->isOpen()) return;

    if (!isTracing) {
        char cmd = CMD_START_TRACE; // 0x51
        serialPort->write(&cmd, 1);

        // Toggle text to Stop
        ui->btnStartStopTrace->setText("Stop Trace");
        // Change to RED when tracing
        ui->btnStartStopTrace->setStyleSheet("background-color: #DC3545; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");

        isTracing = true;
    } else {
        char cmd = CMD_STOP_TRACE; // 0x52
        serialPort->write(&cmd, 1);

        // Toggle text back to Start
        ui->btnStartStopTrace->setText("Start Trace");
        // Change back to GREEN when stopped
        ui->btnStartStopTrace->setStyleSheet("background-color: #28A745; color: white; font-weight: bold; border-radius: 4px; padding: 6px;");
        isTracing = false;
    }
}

// --- Clear Trace Logic ---
void MessengerWidget::on_btnClearTrace_clicked()
{
    ui->tableTrace->setRowCount(0); // Wipes the visual table

    // Wipe our tracking memories!
    traceRowMap.clear();
    messageCounterMap.clear();
    prevDataMap.clear();
}


void MessengerWidget::handleIncomingCanFrame(QByteArray packet) {
    if (packet.size() < 16) return;
    uint8_t ch = packet[1];
    uint32_t id = (uint8_t)packet[2] | ((uint8_t)packet[3] << 8) | ((uint8_t)packet[4] << 16) | ((uint8_t)packet[5] << 24);
    uint8_t dlc = packet[6];
    QByteArray payload = packet.mid(7, (dlc > 8) ? 8 : dlc);

    addMessageToTrace(ch, 0, id, dlc, payload); // dir = 0 (Rx)
}

void MessengerWidget::addMessageToTrace(uint8_t ch, uint8_t dir, uint32_t id, uint8_t dlc, QByteArray payload)
{
    const int COL_TIME = 0, COL_COUNT = 1, COL_CH = 2, COL_DIR = 3, COL_ID = 4, COL_TYPE = 5, COL_DLC = 6, COL_DATA = 7;

    QString uniqueKey = QString("%1_%2_%3").arg(dir).arg(ch).arg(id); // Added 'dir' so Rx and Tx don't merge counts!

    bool highlightEnabled = ui->chkHighLightChanges->isChecked();
    QByteArray prevData = prevDataMap.value(uniqueKey, QByteArray());
    QString dataHtml;

    for (int i = 0; i < payload.size(); i++) {
        QString byteHex = QString("%1").arg((uint8_t)payload[i], 2, 16, QChar('0')).toUpper();
        if (highlightEnabled && !prevData.isEmpty() && i < prevData.size() && payload[i] != prevData[i]) {
            dataHtml += QString("<font color='#00FF00'><b>%1</b></font> ").arg(byteHex);
        } else {
            dataHtml += byteHex + " ";
        }
    }
    prevDataMap[uniqueKey] = payload;
    QString timeStr = QDateTime::currentDateTime().toString("HH:mm:ss.zzz");

    int row;
    if (traceRowMap.contains(uniqueKey)) {
        row = traceRowMap[uniqueKey];
        messageCounterMap[uniqueKey]++;
        ui->tableTrace->item(row, COL_TIME)->setText(timeStr);
        ui->tableTrace->item(row, COL_COUNT)->setText(QString::number(messageCounterMap[uniqueKey]));
    } else {
        row = ui->tableTrace->rowCount();
        ui->tableTrace->insertRow(row);
        traceRowMap[uniqueKey] = row;
        messageCounterMap[uniqueKey] = 1;

        ui->tableTrace->setItem(row, COL_TIME,  new QTableWidgetItem(timeStr));
        ui->tableTrace->setItem(row, COL_COUNT, new QTableWidgetItem("1"));
        ui->tableTrace->setItem(row, COL_CH,    new QTableWidgetItem(QString("CAN %1").arg(ch)));
        ui->tableTrace->setItem(row, COL_DIR,   new QTableWidgetItem(dir == 0 ? "Rx" : "Tx")); // Support Tx text
        ui->tableTrace->setItem(row, COL_ID,    new QTableWidgetItem(QString::number(id, 16).toUpper()));
        ui->tableTrace->setItem(row, COL_TYPE,  new QTableWidgetItem((id > 0x7FF) ? "EXT" : "STD"));
        ui->tableTrace->setItem(row, COL_DLC,   new QTableWidgetItem(QString::number(dlc)));
    }

    QLabel *lblData = new QLabel(dataHtml);
    lblData->setTextFormat(Qt::RichText);
    lblData->setStyleSheet("background-color: transparent; padding-left: 4px;");
    ui->tableTrace->setCellWidget(row, COL_DATA, lblData);

    if (messageCounterMap[uniqueKey] == 1) ui->tableTrace->scrollToBottom();
}

// --- 1. DYNAMIC DATA GRID ---
void MessengerWidget::on_lineEdit_2_textChanged(const QString &dlcText)
{
    int dlc = dlcText.toInt();
    if (dlc < 0) dlc = 0;
    if (dlc > 64) dlc = 64; // Max FD limit

    ui->tableWidget->setColumnCount(dlc);
    QStringList headers;
    for (int i = 0; i < dlc; ++i) headers << QString("D%1").arg(i);
    ui->tableWidget->setHorizontalHeaderLabels(headers);
}

void MessengerWidget::on_radioButton_2_toggled(bool checked)
{
    ui->lineEdit_3->setEnabled(checked); // Enable 'ms' field if Periodic is checked
}

QByteArray MessengerWidget::readDataFromGrid(int dlc)
{
    QByteArray data;
    for (int i = 0; i < dlc; ++i) {
        QTableWidgetItem *item = ui->tableWidget->item(0, i);
        if (item && !item->text().isEmpty()) {
            data.append((char)item->text().toInt(nullptr, 16));
        } else {
            data.append((char)0x00); // Default pad with 00 if left empty
        }
    }
    return data;
}

// --- 2. SEND COMMAND TO HARDWARE ---
void MessengerWidget::transmitToHardware(uint8_t ch, uint32_t id, uint8_t dlc, QByteArray data)
{
    if (!serialPort || !serialPort->isOpen()) return;

    QByteArray txPacket;
    txPacket.append(CMD_CAN_TX); // 0x50 Command
    txPacket.append((char)ch);

    // Little Endian ID
    txPacket.append((char)(id & 0xFF));
    txPacket.append((char)((id >> 8) & 0xFF));
    txPacket.append((char)((id >> 16) & 0xFF));
    txPacket.append((char)((id >> 24) & 0xFF));

    txPacket.append((char)dlc);
    txPacket.append(data);
    txPacket.append((char)0xBB); // Footer

    serialPort->write(txPacket);

    // Echo the transmission into the Trace Window!
    addMessageToTrace(ch, 1, id, dlc, data); // dir = 1 (Tx)
}

// --- 3. IMMEDIATE SEND BUTTON ---
void MessengerWidget::on_pushButton_2_clicked() // "Send Message"
{
    uint32_t id = ui->lineEdit->text().toUInt(nullptr, 16);
    uint8_t dlc = ui->lineEdit_2->text().toUInt();
    uint8_t ch = ui->comboBox_2->currentIndex(); // 0 = CAN0, 1 = CAN1

    QByteArray data = readDataFromGrid(dlc);
    transmitToHardware(ch, id, dlc, data);
}



void MessengerWidget::on_pushButton_clicked() // "Add Message"
{
    // --- VALIDATION POPUP ---
    if (!ui->radioButton->isChecked() && !ui->radioButton_2->isChecked()) {
        QMessageBox::warning(this, "Selection Required", "Please select either 'Manual' or 'Periodic' before adding a message.");
        return; // Stop the function here so it doesn't add an empty row
    }

    int row = ui->tableWidget_2->rowCount();
    ui->tableWidget_2->insertRow(row);

    // --- COLUMN MAPPINGS ---
    // If your columns are: Sr no | ID | DLC | Channel | Transmission | Data | Status | Action
    const int COL_SRNO   = 0;
    const int COL_ID     = 1;
    const int COL_DLC    = 2;
    const int COL_CH     = 3;
    const int COL_TRANS  = 4;
    const int COL_DATA   = 5;
    const int COL_STATUS = 6;
    const int COL_ACTION = 7;
    // -----------------------

    QString idText = ui->lineEdit->text();
    QString dlcText = ui->lineEdit_2->text();
    QString chText = ui->comboBox_2->currentText();
    bool isPeriodic = ui->radioButton_2->isChecked();
    QString transText = isPeriodic ? QString("Periodic (%1ms)").arg(ui->lineEdit_3->text()) : "Manual";

    const QByteArray data = readDataFromGrid(dlcText.toInt());
    QString dataPreview;
    for (char b : data) dataPreview += QString("%1 ").arg((uint8_t)b, 2, 16, QChar('0')).toUpper();

    // Fill table using the correct mapped indexes
    ui->tableWidget_2->setItem(row, COL_SRNO,   new QTableWidgetItem(QString::number(row + 1))); // Auto-increments Sr no
    ui->tableWidget_2->setItem(row, COL_ID,     new QTableWidgetItem(idText));
    ui->tableWidget_2->setItem(row, COL_DLC,    new QTableWidgetItem(dlcText));
    ui->tableWidget_2->setItem(row, COL_CH,     new QTableWidgetItem(chText));
    ui->tableWidget_2->setItem(row, COL_TRANS,  new QTableWidgetItem(transText));
    ui->tableWidget_2->setItem(row, COL_DATA,   new QTableWidgetItem(dataPreview));
    ui->tableWidget_2->setItem(row, COL_STATUS, new QTableWidgetItem("Ready"));

    // Inject Action Button
    QPushButton *btnAction = new QPushButton(isPeriodic ? "Start" : "Send");
    btnAction->setStyleSheet("background-color: #28A745; color: white; font-weight: bold; border-radius: 3px;");
    ui->tableWidget_2->setCellWidget(row, COL_ACTION, btnAction);

    // Connect Action Button to handler
    connect(btnAction, &QPushButton::clicked, [this, row]() {
        handleActionClicked(row);
    });
}


void MessengerWidget::handleActionClicked(int row)
{
    const int COL_TRANS = 4;
    const int COL_ACTION = 7;
    const int COL_STATUS = 6;

    QPushButton *btn = qobject_cast<QPushButton*>(ui->tableWidget_2->cellWidget(row, COL_ACTION));
    if (!btn) return;

    QString transMode = ui->tableWidget_2->item(row, COL_TRANS)->text();

    if (transMode == "Manual") {
        sendPeriodicMessage(row);
        ui->tableWidget_2->item(row, COL_STATUS)->setText("Sent");
    }
    else { // Periodic
        if (btn->text() == "Start") {
            btn->setText("Stop");
            btn->setStyleSheet("background-color: #AA0000; color: white;");
            ui->tableWidget_2->item(row, COL_STATUS)->setText("Transmitting...");

            int ms = transMode.section('(', 1, 1).remove("ms)").toInt();

            QTimer *timer = new QTimer(this);
            connect(timer, &QTimer::timeout, [this, row]() { sendPeriodicMessage(row); });
            timer->start(ms);
            periodicTimers[row] = timer;
        }
        else {
            btn->setText("Start");
            btn->setStyleSheet("");
            ui->tableWidget_2->item(row, COL_STATUS)->setText("Stopped");

            if (periodicTimers.contains(row)) {
                periodicTimers[row]->stop();
                periodicTimers[row]->deleteLater();
                periodicTimers.remove(row);
            }
        }
    }
}

void MessengerWidget::sendPeriodicMessage(int row)
{
    // Define the exact column locations
    const int COL_ID = 1;
    const int COL_DLC = 2;
    const int COL_CH = 3;
    const int COL_DATA = 5;

    // Extract properties from the List Row using the correct columns
    uint32_t id = ui->tableWidget_2->item(row, COL_ID)->text().toUInt(nullptr, 16);
    uint8_t dlc = ui->tableWidget_2->item(row, COL_DLC)->text().toUInt();
    uint8_t ch = ui->tableWidget_2->item(row, COL_CH)->text().contains("1") ? 1 : 0;

    // Parse hex string back to bytes
    QByteArray data;
    const QStringList bytes = ui->tableWidget_2->item(row, COL_DATA)->text().simplified().split(' ');
    for (const QString &b : bytes) {
        if (!b.isEmpty()) {
            data.append((char)b.toInt(nullptr, 16));
        }
    }

    transmitToHardware(ch, id, dlc, data);
}

// --- 5. DATA ENTRY AUTO-FORMATTER ---
void MessengerWidget::on_tableWidget_cellChanged(int row, int column)
{
    QTableWidgetItem *item = ui->tableWidget->item(row, column);
    if (!item) return;

    QString text = item->text().trimmed();
    if (text.isEmpty()) return;

    // 1. Block signals so we don't trigger this function infinitely when we change the text!
    ui->tableWidget->blockSignals(true);

    bool ok;
    // 2. First, try to read it as a Hexadecimal number
    int val = text.toInt(&ok, 16);

    // 3. If it wasn't valid hex, OR if it's larger than 1 byte (e.g. user typed "255")
    if (!ok || val > 255) {
        // Fallback: Try reading it as a standard Decimal number
        val = text.toInt(&ok, 10);

        // If it's STILL invalid, or negative, or > 255, default to 0
        if (!ok || val > 255 || val < 0) {
            val = 0;
        }
    }

    // 4. Convert the final valid integer back to a 2-digit uppercase HEX string (e.g., "0A", "FF")
    QString formattedHex = QString("%1").arg(val, 2, 16, QChar('0')).toUpper();

    item->setText(formattedHex);
    item->setTextAlignment(Qt::AlignCenter); // Make it look neat in the center of the cell

    // 5. Unblock signals so the grid works normally again
    ui->tableWidget->blockSignals(false);
}

// --- THEME UPDATER FOR TABLES ---
void MessengerWidget::applyTheme(bool isDark)
{
    if (isDark) {
        // Apply your custom Dark Mode borders
        QString tableStyle = R"(
            QTableWidget {
                border: 1px solid #555555;
                gridline-color: #555555;
                background-color: #1E1E1E;
            }
            QHeaderView::section {
                background-color: #2D2D30;
                border: 1px solid #555555;
                font-weight: bold;
                color: #E0E0E0;
            }
        )";
        ui->tableTrace->setStyleSheet(tableStyle);
        ui->tableWidget->setStyleSheet(tableStyle);
        ui->tableWidget_2->setStyleSheet(tableStyle);
    } else {
        // Clear the local stylesheets so the Global Light Theme can take over!
        ui->tableTrace->setStyleSheet("");
        ui->tableWidget->setStyleSheet("");
        ui->tableWidget_2->setStyleSheet("");
    }
}
