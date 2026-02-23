#include "aboutwidget.h"
#include "ui_aboutwidget.h"

#include <QVBoxLayout>
#include <QLabel>
#include <QPixmap>
#include <QDate>


AboutWidget::AboutWidget(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::AboutWidget)
{
    ui->setupUi(this);

    // 1. Create a Master Layout to perfectly center everything
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    mainLayout->setAlignment(Qt::AlignCenter);
    mainLayout->setSpacing(10); // Add nice breathing room between elements

    // 2. Add the Logo
    QLabel *lblLogo = new QLabel(this);
    QPixmap logo(":/icons/icon.png"); // Uses your existing Qt Resource!
    // Scale the logo to look sharp and crisp
    lblLogo->setPixmap(logo.scaled(120, 120, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    lblLogo->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(lblLogo);

    // 3. Add the Application Title
    QLabel *lblTitle = new QLabel("<h1>BitSniff</h1>", this);
    lblTitle->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(lblTitle);

    // 4. Add the Subtitle / Description
    QLabel *lblDesc = new QLabel("High-Performance USB to CAN Bus Analyzer<br>"
                                 "Optimized for Hardware Diagnostics.", this);
    lblDesc->setAlignment(Qt::AlignCenter);

    // Make sure text wraps if the window is resized
    lblDesc->setWordWrap(true);
    mainLayout->addWidget(lblDesc);

    // 5. Add Version and Dynamic Build Date
    // __DATE__ is a special C++ macro that automatically inserts today's date when you hit "Build"!
    QString buildInfo = QString("<b>Version:</b> 1.0.0<br>"
                                "<span style='color: gray; font-size: 10px;'>Compiled on: %1</span>").arg(__DATE__);
    QLabel *lblVersion = new QLabel(buildInfo, this);
    lblVersion->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(lblVersion);

    // ---> 6. Clickable Contact Email <---
    // Replace 'your.email@example.com' with your actual email!
    QLabel *lblContact = new QLabel("<br><span style='font-size: 12px;'>For support and custom software development:</span><br>"
                                    "<a href='mailto:bitstobytesdiy@gmail.com' style='color: #007ACC; font-weight: bold; text-decoration: none;'>bitstobytesdiy@gmail.com</a>", this);
    lblContact->setAlignment(Qt::AlignCenter);
    lblContact->setOpenExternalLinks(true); // This makes the email link actually clickable!
    mainLayout->addWidget(lblContact);

    // ---> 7. Auto-updating Copyright <---
    int currentYear = QDate::currentDate().year();
    QString copyrightText = QString("<br><span style='color: gray; font-size: 11px;'>"
                                    "&copy; %1 BitSniff. All rights reserved.</span>").arg(currentYear);
    QLabel *lblCopyright = new QLabel(copyrightText, this);
    lblCopyright->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(lblCopyright);

    // 8. Add the Footer
    QLabel *lblFooter = new QLabel("<b>Made in India ❤️</b>", this);
    lblFooter->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(lblFooter);}

AboutWidget::~AboutWidget()
{
    delete ui;
}

// AboutWidget::AboutWidget(QWidget *parent)
//     : QWidget(parent)
//     , ui(new Ui::AboutWidget)
// {
//     ui->setupUi(this);
// }

// AboutWidget::~AboutWidget()
// {
//     delete ui;
// }
