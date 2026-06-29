type JsPDF = import("jspdf").jsPDF;

const PAGE_MARGIN_MM = 8;

/** html2canvas cannot parse modern CSS color functions (oklab, oklch) from Tailwind v4. */
const UNSUPPORTED_COLOR_RE = /\b(oklab|oklch|lab|lch)\(/i;

const INLINE_STYLE_PROPS = [
  "color",
  "background-color",
  "background-image",
  "border-top-color",
  "border-right-color",
  "border-bottom-color",
  "border-left-color",
  "border-top-width",
  "border-right-width",
  "border-bottom-width",
  "border-left-width",
  "border-top-style",
  "border-right-style",
  "border-bottom-style",
  "border-left-style",
  "border-radius",
  "font-size",
  "font-family",
  "font-weight",
  "font-style",
  "font-variation-settings",
  "line-height",
  "letter-spacing",
  "text-align",
  "text-transform",
  "padding-top",
  "padding-right",
  "padding-bottom",
  "padding-left",
  "margin-top",
  "margin-right",
  "margin-bottom",
  "margin-left",
  "width",
  "height",
  "min-width",
  "min-height",
  "max-width",
  "max-height",
  "display",
  "flex-direction",
  "flex-wrap",
  "flex-grow",
  "flex-shrink",
  "align-items",
  "justify-content",
  "gap",
  "grid-template-columns",
  "grid-column",
  "opacity",
  "box-shadow",
  "overflow",
  "position",
  "top",
  "right",
  "bottom",
  "left",
  "z-index",
  "white-space",
  "word-wrap",
  "direction",
  "vertical-align",
] as const;

function waitForPaint(ms = 50): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isSafeCssValue(value: string): boolean {
  return value.length > 0 && !UNSUPPORTED_COLOR_RE.test(value);
}

function stripUnsupportedStylesheets(clonedDoc: Document): void {
  clonedDoc.querySelectorAll('link[rel="stylesheet"], style').forEach((node) => {
    node.parentNode?.removeChild(node);
  });
}

function inlineComputedStyles(sourceRoot: HTMLElement, cloneRoot: HTMLElement): void {
  const sourceNodes = [sourceRoot, ...Array.from(sourceRoot.querySelectorAll("*"))] as HTMLElement[];
  const cloneNodes = [cloneRoot, ...Array.from(cloneRoot.querySelectorAll("*"))] as HTMLElement[];

  for (let i = 0; i < sourceNodes.length && i < cloneNodes.length; i++) {
    const computed = window.getComputedStyle(sourceNodes[i]);
    const target = cloneNodes[i];

    for (const prop of INLINE_STYLE_PROPS) {
      const value = computed.getPropertyValue(prop);
      if (!isSafeCssValue(value)) continue;
      if (value === "none" || value === "auto" || value === "normal") continue;
      target.style.setProperty(prop, value);
    }

    const color = computed.color;
    const bg = computed.backgroundColor;
    if (isSafeCssValue(color)) target.style.setProperty("color", color);
    if (isSafeCssValue(bg)) target.style.setProperty("background-color", bg);

    const bgImage = computed.backgroundImage;
    if (bgImage && bgImage !== "none" && isSafeCssValue(bgImage)) {
      target.style.setProperty("background-image", bgImage);
    }
  }
}

function addCanvasSlicesToPdf(pdf: JsPDF, canvas: HTMLCanvasElement, isFirstPage: boolean) {
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const usableWidth = pageWidth - PAGE_MARGIN_MM * 2;
  const usableHeight = pageHeight - PAGE_MARGIN_MM * 2;
  const scale = usableWidth / canvas.width;
  const sliceHeightPx = Math.floor(usableHeight / scale);

  let offsetY = 0;
  let first = isFirstPage;

  while (offsetY < canvas.height) {
    if (!first) pdf.addPage();
    first = false;

    const height = Math.min(sliceHeightPx, canvas.height - offsetY);
    const slice = document.createElement("canvas");
    slice.width = canvas.width;
    slice.height = height;
    const ctx = slice.getContext("2d");
    if (!ctx) break;

    ctx.drawImage(canvas, 0, offsetY, canvas.width, height, 0, 0, canvas.width, height);
    const imgHeightMm = height * scale;
    pdf.addImage(
      slice.toDataURL("image/png"),
      "PNG",
      PAGE_MARGIN_MM,
      PAGE_MARGIN_MM,
      usableWidth,
      imgHeightMm,
    );
    offsetY += height;
  }
}

export async function exportPagesToPdf(
  pageElements: HTMLElement[],
  filename: string,
): Promise<void> {
  const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
    import("html2canvas"),
    import("jspdf"),
  ]);

  await document.fonts.ready;
  await waitForPaint(300);

  const pdf = new jsPDF("p", "mm", "a4");
  let isFirst = true;

  for (const el of pageElements) {
    const canvas = await html2canvas(el, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: "#0a0a0b",
      logging: false,
      windowWidth: el.scrollWidth,
      width: el.scrollWidth,
      height: el.scrollHeight,
      onclone: (clonedDoc, cloneEl) => {
        stripUnsupportedStylesheets(clonedDoc);
        inlineComputedStyles(el, cloneEl as HTMLElement);
      },
    });
    addCanvasSlicesToPdf(pdf, canvas, isFirst);
    isFirst = false;
  }

  pdf.save(filename);
}

export function reportFilename(): string {
  const date = new Date().toISOString().slice(0, 10);
  return `music-discovery-insights-${date}.pdf`;
}
