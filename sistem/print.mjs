#!/usr/bin/env node
/**
 * print_linux.mjs — HTML -> PDF (Linux, puppeteer-core + system Chrome)
 * FAZ 3 / Görev A2 — Claude-Sonnet #2
 *
 * Windows'taki build\print.mjs'in Linux karşılığı: Chrome CLI
 * (--print-to-pdf) header/footer template desteklemediği için CDP
 * (Page.printToPDF) üzerinden puppeteer-core ile basıyoruz.
 *
 * Kullanım:
 *   node print_linux.mjs <girdi.html> <cikti.pdf>
 *
 * Header: SADECE logo (sol üst köşe, ~52px yükseklik, hafif yuvarlak köşe),
 * YAZI YOK. Footer: ortada sayfa numarası (X / Y biçiminde).
 * Marginler: üst 1.15in, alt 0.5in, sol/sağ 0.4in.
 *
 * ÖNEMLİ (proje tuzağı): girdi HTML'in linklediği CSS'te
 * `@page { margin: 0 }` OLMAMALI — bu, buradaki margin.top/bottom/left/right
 * parametrelerini ezer. flow_linux.css bu satırı BİLEREK içermiyor.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import puppeteer from "puppeteer-core";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const CHROME_PATH = "/usr/bin/google-chrome-stable";
const LOGO_PATH = path.join(__dirname, "logo_es.jpg");

function usageAndExit() {
  console.error("Kullanim: node print.mjs <girdi.html> <cikti.pdf>");
  process.exit(1);
}

async function main() {
  const [, , inputArg, outputArg] = process.argv;
  if (!inputArg || !outputArg) usageAndExit();

  const inputPath = path.resolve(inputArg);
  const outputPath = path.resolve(outputArg);

  if (!fs.existsSync(inputPath)) {
    console.error("Girdi HTML bulunamadi:", inputPath);
    process.exit(1);
  }
  if (!fs.existsSync(LOGO_PATH)) {
    console.error("Logo bulunamadi:", LOGO_PATH);
    process.exit(1);
  }

  // Logo'yu base64 data-URI'ye göm — CDP header/footer template'leri
  // file:// kaynaklarini yukleyemiyor, data URI sart (proje notu).
  const logoB64 = fs.readFileSync(LOGO_PATH).toString("base64");
  const logoDataUri = `data:image/jpeg;base64,${logoB64}`;

  const headerTemplate = `
    <div style="width:100%; font-size:0px; margin:0; padding:0;">
      <img src="${logoDataUri}"
           style="height:52px; width:auto; margin-left:10.5mm; margin-top:2mm;
                  border-radius:3px; display:block;" />
    </div>`;

  const footerTemplate = `
    <div style="width:100%; font-size:9px; font-family:sans-serif; color:#666;
                text-align:center; margin:0 auto;">
      <span class="pageNumber"></span> / <span class="totalPages"></span>
    </div>`;

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--allow-file-access-from-files"],
  });

  try {
    const page = await browser.newPage();
    const fileUrl = pathToFileURL(inputPath).href;
    await page.goto(fileUrl, { waitUntil: "networkidle0" });

    // Gömülü @font-face fontlarının (Comic Sans MS Embedded vb.) tamamen
    // yüklenmesini bekle — yoksa ilk baskıda fallback fontla basılabilir.
    await page.evaluate(async () => {
      if (document.fonts && document.fonts.ready) {
        await document.fonts.ready;
      }
    });

    await page.pdf({
      path: outputPath,
      format: "A4",
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate,
      footerTemplate,
      margin: {
        top: "1.15in",
        bottom: "0.5in",
        left: "0.4in",
        right: "0.4in",
      },
      preferCSSPageSize: false,
    });

    console.log("Yazildi:", outputPath);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
