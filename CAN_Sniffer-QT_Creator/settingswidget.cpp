#include "settingswidget.h"
#include "ui_settingswidget.h"
#include <QGridLayout>
#include <QMessageBox>

SettingsWidget::SettingsWidget(QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::SettingsWidget)
    ,isDarkMode(true)
{
    ui->setupUi(this);

    // Create the master layout that will hold our dynamic boxes
    mainLayout = new QVBoxLayout(this);

    // --- 1. HARDCODE THE TOGGLE BUTTON ---
    QPushButton *btnToggleTheme = new QPushButton("Toggle Light/Dark Mode", this);
    btnToggleTheme->setStyleSheet("background-color: #6C757D; color: white; font-weight: bold; border-radius: 4px; padding: 8px;");
    mainLayout->addWidget(btnToggleTheme);

    // Connect the button click to emit our signal
    connect(btnToggleTheme, &QPushButton::clicked, this, [this]() {
        isDarkMode = !isDarkMode;
        emit themeToggled(isDarkMode);
    });

    // --- 2. CREATE THE SUB-LAYOUT FOR HARDWARE BOXES ---
    // ---> THIS IS THE MISSING LINE THAT CAUSED THE CRASH <---
    dynamicLayout = new QVBoxLayout();
    mainLayout->addLayout(dynamicLayout);

    // Push everything tightly to the top
    mainLayout->addStretch();
}

SettingsWidget::~SettingsWidget()
{
    delete ui;
}

void SettingsWidget::populateBaudRates(QComboBox *cmb, uint32_t maxSpeed)
{
    // The 'currentData' hidden value maps directly to your CMD_BAUD_XXX defines
    cmb->addItem("125 Kbps", 0x71);
    cmb->addItem("250 Kbps", 0x72);
    cmb->addItem("500 Kbps", 0x73);
    cmb->addItem("1 Mbps",   0x74);

    // Only add higher speeds if the channel supports them
    if (maxSpeed >= 2000000) cmb->addItem("2 Mbps", 0x75);
    if (maxSpeed >= 2500000) cmb->addItem("2.5 Mbps", 0x76);
    if (maxSpeed >= 3000000) cmb->addItem("3 Mbps", 0x77);
    if (maxSpeed >= 4000000) cmb->addItem("4 Mbps", 0x78);
    if (maxSpeed >= 5000000) cmb->addItem("5 Mbps", 0x79);
    if (maxSpeed >= 8000000) cmb->addItem("8 Mbps", 0x82);
}

// void SettingsWidget::buildUiForDevice(device_info_t info)
// {
//     // 1. Clear any old UI if the user disconnected and reconnected
//     QLayoutItem *child;
//     while ((child = mainLayout->takeAt(0)) != nullptr) {
//         if (child->widget()) child->widget()->deleteLater();
//         delete child;
//     }
//     currentBaudLabels.clear();

//     // 2. Loop through the array and generate a QGroupBox for each CAN channel
//     for (uint32_t i = 0; i < info.no_of_CAN_Channel; ++i) {
//         QGroupBox *grp = new QGroupBox(QString("CAN Channel %1").arg(i));
//         QGridLayout *lay = new QGridLayout(grp);

//         // Type Label
//         QString typeStr = (info.CAN_type[i] == 2) ? "CAN FD" : "CAN Classic";
//         lay->addWidget(new QLabel(QString("Type: %1").arg(typeStr)), 0, 0);

//         // Max Speed Label
//         lay->addWidget(new QLabel(QString("Max Speed: %1 Mbps").arg(info.CAN_Channel_speed[i] / 1000000.0)), 0, 1);

//         // Baudrate Dropdown
//         QComboBox *cmb = new QComboBox();
//         populateBaudRates(cmb, info.CAN_Channel_speed[i]);
//         lay->addWidget(cmb, 1, 0);

//         // Set Button
//         QPushButton *btnSet = new QPushButton("Set Baudrate");
//         btnSet->setStyleSheet("background-color: #28A745; color: white; font-weight: bold; border-radius: 3px; padding: 5px;");
//         lay->addWidget(btnSet, 1, 1);

//         // Current Baudrate Label
//         QLabel *lblCurrent = new QLabel(QString("Current Baud: %1 bps").arg(info.CAN_Channel_current_baud[i]));
//         currentBaudLabels[i] = lblCurrent; // Store pointer to update it later
//         lay->addWidget(lblCurrent, 2, 0);

//         // Read Button
//         QPushButton *btnRead = new QPushButton("Read Baudrate");
//         btnRead->setStyleSheet("background-color: #004085; color: white; font-weight: bold; border-radius: 3px; padding: 5px;");
//         lay->addWidget(btnRead, 2, 1);

//         mainLayout->addWidget(grp);

//         // 3. Connect the dynamic buttons to our send functions using Lambdas
//         connect(btnSet, &QPushButton::clicked, [this, i, cmb]() {
//             int cmd = cmb->currentData().toInt();
//             this->sendSetBaudrate(i, cmd);
//         });

//         connect(btnRead, &QPushButton::clicked, [this, i]() {
//             this->sendReadBaudrate(i);
//         });
//     }

//     // Push all the boxes tightly to the top of the window
//     mainLayout->addStretch();
// }

void SettingsWidget::buildUiForDevice(device_info_t info)
{
    // 1. Clear ONLY the dynamic hardware layout (Protects the Toggle Button!)
    QLayoutItem *child;
    while ((child = dynamicLayout->takeAt(0)) != nullptr) {
        if (child->widget()) {
            child->widget()->hide();
            child->widget()->deleteLater();
        }
        delete child;
    }
    currentBaudLabels.clear();

    // 2. Generate a QGroupBox for each CAN channel
    for (uint32_t i = 0; i < info.no_of_CAN_Channel; ++i) {
        QGroupBox *grp = new QGroupBox(QString("CAN Channel %1").arg(i));
        QGridLayout *lay = new QGridLayout(grp);

        QString typeStr = (info.CAN_type[i] == 2) ? "CAN FD" : "CAN Classic";
        lay->addWidget(new QLabel(QString("Type: %1").arg(typeStr)), 0, 0);
        lay->addWidget(new QLabel(QString("Max Speed: %1 Mbps").arg(info.CAN_Channel_speed[i] / 1000000.0)), 0, 1);

        QComboBox *cmb = new QComboBox();
        populateBaudRates(cmb, info.CAN_Channel_speed[i]);
        lay->addWidget(cmb, 1, 0);

        QPushButton *btnSet = new QPushButton("Set Baudrate");
        btnSet->setStyleSheet("background-color: #28A745; color: white; font-weight: bold; border-radius: 3px; padding: 5px;");
        lay->addWidget(btnSet, 1, 1);

        QLabel *lblCurrent = new QLabel(QString("Current Baud: %1 bps").arg(info.CAN_Channel_current_baud[i]));
        currentBaudLabels[i] = lblCurrent;
        lay->addWidget(lblCurrent, 2, 0);

        QPushButton *btnRead = new QPushButton("Read Baudrate");
        btnRead->setStyleSheet("background-color: #004085; color: white; font-weight: bold; border-radius: 3px; padding: 5px;");
        lay->addWidget(btnRead, 2, 1);

        // ---> ADD TO DYNAMIC LAYOUT INSTEAD OF MAIN LAYOUT <---
        dynamicLayout->addWidget(grp);

        connect(btnSet, &QPushButton::clicked, [this, i, cmb]() {
            int cmd = cmb->currentData().toInt();
            this->sendSetBaudrate(i, cmd);
        });

        connect(btnRead, &QPushButton::clicked, [this, i]() {
            this->sendReadBaudrate(i);
        });
    }

    // (Notice we removed mainLayout->addStretch() from here because it's already in the constructor!)
}

// --- Outgoing Commands ---
void SettingsWidget::sendReadBaudrate(int channel)
{
    if (!serialPort || !serialPort->isOpen()) return;
    char payload[2] = {CMD_READ_BAUDRATE, (char)channel};
    serialPort->write(payload, 2);
}

void SettingsWidget::sendSetBaudrate(int channel, int baudCmd)
{
    if (!serialPort || !serialPort->isOpen()) return;
    char payload[3] = {CMD_SET_BAUDRATE, (char)channel, (char)baudCmd};
    serialPort->write(payload, 3);
}

// --- Incoming Responses ---
void SettingsWidget::handleBaudRead(QByteArray data)
{
    // data format: [0x32, CH, SP0, SP1, SP2, SP3]
    uint8_t ch = data[1];

    // Reconstruct the 32-bit integer (Little Endian)
    uint32_t speed = (uint8_t)data[2] |
                     ((uint8_t)data[3] << 8) |
                     ((uint8_t)data[4] << 16) |
                     ((uint8_t)data[5] << 24);

    // Update the correct label dynamically
    if (currentBaudLabels.contains(ch)) {
        currentBaudLabels[ch]->setText(QString("Current Baud: %1 bps").arg(speed));
    }
}

void SettingsWidget::handleBaudSet(QByteArray data)
{
    // data format: [0x33, CH, CMD]
    // Upon successful set, we trigger a Read to visually update the UI with the new value
    uint8_t ch = data[1];
    sendReadBaudrate(ch);
}
