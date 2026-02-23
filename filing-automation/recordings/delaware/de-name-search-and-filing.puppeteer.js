const puppeteer = require('puppeteer'); // v23.0.0 or later

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    const timeout = 5000;
    page.setDefaultTimeout(timeout);

    {
        const targetPage = page;
        await targetPage.setViewport({
            width: 995,
            height: 889
        })
    }
    {
        const targetPage = page;
        await targetPage.goto('https://corp.delaware.gov/');
    }
    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('#corpServices3 > div:nth-of-type(1) strong'),
            targetPage.locator('::-p-xpath(//*[@id=\\"corpServices3\\"]/div[1]/p/a/strong)'),
            targetPage.locator(':scope >>> #corpServices3 > div:nth-of-type(1) strong')
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click({
              offset: {
                x: 114.33984375,
                y: 12.169921875,
              },
            });
        await Promise.all(promises);
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(  I have read and understand the disclaimer.)'),
            targetPage.locator('tr:nth-of-type(5) > td'),
            targetPage.locator('::-p-xpath(//*[@id=\\"TableBody\\"]/tbody/tr[2]/td[2]/table[3]/tbody/tr[5]/td)'),
            targetPage.locator(':scope >>> tr:nth-of-type(5) > td'),
            targetPage.locator('::-p-text(I have read and)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 164.5,
                y: 7.060546875,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(  I have read and understand the disclaimer.) >>>> ::-p-aria([role=\\"checkbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmDisclaimerChkBox'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmDisclaimerChkBox\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmDisclaimerChkBox')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 3.1875,
                y: 8.06640625,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(-- Select One -- If you would like information about what kind of entity you should form, please click here.) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityType'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityType\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityType')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 21.451171875,
                y: 7.076171875,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(CORPORATION If you would like information about what kind of entity you should form, please click here.) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityType'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityType\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityType')
        ])
            .setTimeout(timeout)
            .fill('C');
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(-- Select One -- If you would like information about what kind of entity you should form, please click here.) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityType'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityType\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityType')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 49.451171875,
                y: 4.076171875,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(CORPORATION If you would like information about what kind of entity you should form, please click here.) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityType'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityType\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityType')
        ])
            .setTimeout(timeout)
            .fill('Y');
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(-- Select One --) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityEnding'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityEnding\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityEnding'),
            targetPage.locator('::-p-text(-1)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 156.611328125,
                y: 10.837890625,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(L.L.C.) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityEnding'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityEnding\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityEnding'),
            targetPage.locator('::-p-text(-1)')
        ])
            .setTimeout(timeout)
            .fill('L.L.C.');
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(LIMITED LIABILITY COMPANY \\(LLC\\) If you would like information about what kind of entity you should form, please click here.) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityType'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityType\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityType')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 130.451171875,
                y: 11.076171875,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(CORPORATION If you would like information about what kind of entity you should form, please click here.) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityType'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityType\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityType')
        ])
            .setTimeout(timeout)
            .fill('C');
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(-- Select One --) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityEnding'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityEnding\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityEnding'),
            targetPage.locator('::-p-text(-1)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 101.986328125,
                y: 2.837890625,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(INC.) >>>> ::-p-aria([role=\\"combobox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityEnding'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityEnding\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityEnding'),
            targetPage.locator('::-p-text(-1)')
        ])
            .setTimeout(timeout)
            .fill('INC.');
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria( This field is not case sensitive.) >>>> ::-p-aria([role=\\"textbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityName'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityName\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityName')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 29.451171875,
                y: 7.599609375,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria( This field is not case sensitive.) >>>> ::-p-aria([role=\\"textbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityName'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityName\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityName')
        ])
            .setTimeout(timeout)
            .fill('ffff');
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(CAPTCHA ↻ 🔊 Type code from the image:   ) >>>> ::-p-aria([role=\\"textbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 46.87109375,
                y: 18.40234375,
              },
            });
    }
    {
        const targetPage = page;
        await targetPage.keyboard.down('Shift');
    }
    {
        const targetPage = page;
        await targetPage.keyboard.up('Shift');
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Frequently Asked Questions Every entity that is to be formed or incorporated in Delaware must be represented by a Registered Agent located in the State of Delaware. If you would like assistance in reserving a name we encourage you to contact a Delaware online agent or contact us. Name Availability Search CAPTCHA ↻ 🔊 Type code from the image:   The intent of this tool is to provide real-time entity name availability. The Division of Corporations strictly prohibits mining data. Excessive and repeated searches that may have a negative impact on our systems and customer experience are also prohibited. Use of automated tools in any form may result in the suspension of your access to utilize this service. Search)'),
            targetPage.locator('tr:nth-of-type(2) > td:nth-of-type(2)'),
            targetPage.locator('::-p-xpath(//*[@id=\\"TableBody\\"]/tbody/tr[2]/td[2])'),
            targetPage.locator(':scope >>> tr:nth-of-type(2) > td:nth-of-type(2)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 304.375,
                y: 397.888671875,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('#ctl00_ContentPlaceHolder1_pnlCaptcha > div > div:nth-of-type(1) > div'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_pnlCaptcha\\"]/div/div[1]/div)'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_pnlCaptcha > div > div:nth-of-type(1) > div')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 396.50390625,
                y: 5.40234375,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(🔊)'),
            targetPage.locator('#playCaptchaButton'),
            targetPage.locator('::-p-xpath(//*[@id=\\"playCaptchaButton\\"])'),
            targetPage.locator(':scope >>> #playCaptchaButton'),
            targetPage.locator('::-p-text(🔊)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 19.380859375,
                y: 8.158203125,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(↻)'),
            targetPage.locator('#btnRefresh'),
            targetPage.locator('::-p-xpath(//*[@id=\\"btnRefresh\\"])'),
            targetPage.locator(':scope >>> #btnRefresh'),
            targetPage.locator('::-p-text(↻)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 14.380859375,
                y: 15.142578125,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(🔊)'),
            targetPage.locator('#playCaptchaButton'),
            targetPage.locator('::-p-xpath(//*[@id=\\"playCaptchaButton\\"])'),
            targetPage.locator(':scope >>> #playCaptchaButton'),
            targetPage.locator('::-p-text(🔊)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 15.380859375,
                y: 13.158203125,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(CAPTCHA ↻ 🔊 Type code from the image:   ) >>>> ::-p-aria([role=\\"textbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 86.87109375,
                y: 17.40234375,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(CAPTCHA ↻ 🔊 Type code from the image:   ) >>>> ::-p-aria([role=\\"textbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha')
        ])
            .setTimeout(timeout)
            .fill('HDLUD');
    }
    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Search)'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_btnSubmit'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_btnSubmit\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_btnSubmit')
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click({
              offset: {
                x: 28.1484375,
                y: 2.056640625,
              },
            });
        await Promise.all(promises);
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('tr:nth-of-type(8)'),
            targetPage.locator('::-p-xpath(//*[@id=\\"TableBody\\"]/tbody/tr[2]/td[2]/table[3]/tbody/tr[8])'),
            targetPage.locator(':scope >>> tr:nth-of-type(8)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 129.5,
                y: 14.595703125,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(ffff This field is not case sensitive.) >>>> ::-p-aria([role=\\"textbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_frmEntityName'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_frmEntityName\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_frmEntityName'),
            targetPage.locator('::-p-text(ffff)')
        ])
            .setTimeout(timeout)
            .fill('this corpor');
    }
    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Search)'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_btnSubmit'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_btnSubmit\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_btnSubmit')
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click({
              offset: {
                x: 51.1484375,
                y: 8.056640625,
              },
            });
        await Promise.all(promises);
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(CAPTCHA ↻ 🔊 Type code from the image:   ) >>>> ::-p-aria([role=\\"textbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 54.87109375,
                y: 1.40234375,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(CAPTCHA ↻ 🔊 Type code from the image:   ) >>>> ::-p-aria([role=\\"textbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 51.87109375,
                y: 16.40234375,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(CAPTCHA ↻ 🔊 Type code from the image:   ) >>>> ::-p-aria([role=\\"textbox\\"])'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha')
        ])
            .setTimeout(timeout)
            .fill('IYGS7');
    }
    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await targetPage.keyboard.down('Enter');
        await Promise.all(promises);
    }
    {
        const targetPage = page;
        await targetPage.keyboard.up('Enter');
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(No, Perform New search)'),
            targetPage.locator('#ctl00_ContentPlaceHolder1_btnNo'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ctl00_ContentPlaceHolder1_btnNo\\"])'),
            targetPage.locator(':scope >>> #ctl00_ContentPlaceHolder1_btnNo'),
            targetPage.locator('::-p-text(No, Perform New)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 53.400390625,
                y: 11.056640625,
              },
            });
    }
    {
        const targetPage = page;
        await targetPage.goto('https://icis.corp.delaware.gov/Ecorp/NameReserv/NameReservation.aspx');
    }
    {
        const targetPage = page;
        await targetPage.goto('https://icis.corp.delaware.gov/Ecorp/NameReserv/NameReservation.aspx');
    }
    {
        const targetPage = page;
        await targetPage.goto('https://icis.corp.delaware.gov/Ecorp/NameReserv/NameReservation.aspx');
    }
    {
        const targetPage = page;
        await targetPage.goto('https://icis.corp.delaware.gov/Ecorp/NameReserv/NameReservation.aspx');
    }
    {
        const targetPage = page;
        await targetPage.goto('https://corp.delaware.gov/');
    }
    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('#corpServices5 > div:nth-of-type(1) strong'),
            targetPage.locator('::-p-xpath(//*[@id=\\"corpServices5\\"]/div[1]/p/a/strong)'),
            targetPage.locator(':scope >>> #corpServices5 > div:nth-of-type(1) strong')
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click({
              offset: {
                x: 170.5,
                y: 12.447265625,
              },
            });
        await Promise.all(promises);
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('html'),
            targetPage.locator('::-p-xpath(/html)'),
            targetPage.locator(':scope >>> html')
        ])
            .setTimeout(timeout)
            .click({
              delay: 529.7000000476837,
              offset: {
                x: 672,
                y: 2349.75,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('#readSpeak_test li:nth-of-type(8)'),
            targetPage.locator('::-p-xpath(//*[@id=\\"main_content\\"]/div/ol/li[8])'),
            targetPage.locator(':scope >>> #readSpeak_test li:nth-of-type(8)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 405.5,
                y: 197.345703125,
              },
            });
    }
    {
        const targetPage = page;
        await targetPage.goto('https://corp.delaware.gov/');
    }
    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Division of Corporations Navigation) >>>> ::-p-aria(Document Filing and Certificate Request Service)'),
            targetPage.locator('#menu-item-7456 > a'),
            targetPage.locator('::-p-xpath(//*[@id=\\"menu-item-7456\\"]/a)'),
            targetPage.locator(':scope >>> #menu-item-7456 > a')
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click({
              offset: {
                x: 94.5,
                y: 29.8671875,
              },
            });
        await Promise.all(promises);
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(click here)'),
            targetPage.locator('p:nth-of-type(8) a'),
            targetPage.locator('::-p-xpath(//*[@id=\\"main_content\\"]/div/p[8]/span/strong/a)'),
            targetPage.locator(':scope >>> p:nth-of-type(8) a'),
            targetPage.locator('::-p-text(click here)')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 47.03515625,
                y: 13.16796875,
              },
            });
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Document Filing and Certificate Request)'),
            targetPage.locator('div:nth-of-type(4) div > div > div:nth-of-type(1) h3'),
            targetPage.locator('::-p-xpath(//*[@id=\\"service\\"]/div/div/div[1]/a/div[2]/h3)'),
            targetPage.locator(':scope >>> div:nth-of-type(4) div > div > div:nth-of-type(1) h3')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 134.5,
                y: 100.740234375,
              },
            });
    }
    {
        const targetPage = page;
        await targetPage.goto('https://icis.corp.delaware.gov/ecorp2/');
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Document Filing and Certificate Request)'),
            targetPage.locator('div:nth-of-type(4) div > div > div:nth-of-type(1) h3'),
            targetPage.locator('::-p-xpath(//*[@id=\\"service\\"]/div/div/div[1]/a/div[2]/h3)'),
            targetPage.locator(':scope >>> div:nth-of-type(4) div > div > div:nth-of-type(1) h3')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 121.5,
                y: 66.740234375,
              },
            });
    }
    {
        const targetPage = page;
        await targetPage.goto('https://icis.corp.delaware.gov/ecorp2/');
    }

    await browser.close();

})().catch(err => {
    console.error(err);
    process.exit(1);
});
