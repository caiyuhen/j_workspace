import { makeEmptyPrismaSvg } from './makeEmptyPrismaSvg';
import { downloadBlob, downloadDataUrl } from './downloadDiagnosticText';

export function exportPRISMA(
  chartRoot?: HTMLElement | null,
  opts?: { scale?: 1 | 2 | 3; quality?: number }
): Promise<{ svgBlob: Blob; pngDataUrl: string; warnings: string[] }> {
  const warnings: string[] = [];
  const scale = opts?.scale ?? 1;
  const quality = opts?.quality ?? 0.92;

  return new Promise((resolve) => {
    try {
      let root = chartRoot;
      if (!root) {
        root = document.getElementById('prisma-chart');
      }

      let svgString: string;
      const svgEl = root?.querySelector?.('svg');

      if (!root || !svgEl) {
        const reason = !root ? '未找到 prisma-chart 容器' : '容器内未找到 SVG 元素';
        warnings.push(`${reason}，使用 makeEmptyPrismaSvg 兜底 SVG`);
        svgString = makeEmptyPrismaSvg(0, reason);
      } else {
        try {
          const serializer = new XMLSerializer();
          svgString = serializer.serializeToString(svgEl);
        } catch (serializeErr) {
          const reason = `XMLSerializer 失败: ${serializeErr instanceof Error ? serializeErr.message : String(serializeErr)}`;
          warnings.push(`${reason}，使用 makeEmptyPrismaSvg 兜底 SVG`);
          svgString = makeEmptyPrismaSvg(0, reason);
        }
      }

      const xmlHeader = '<?xml version="1.0" encoding="UTF-8"?>';
      const doctype = '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">';
      const fullSvg = `${xmlHeader}\n${doctype}\n${svgString}`;
      const svgBlob = new Blob([fullSvg], { type: 'image/svg+xml;charset=utf-8' });

      let pngDataUrl = '';
      const svgUrl = URL.createObjectURL(svgBlob);
      const img = new Image();
      const timeoutId = setTimeout(() => {
        warnings.push('PNG 浏览器限制 跳过已下 SVG (1500ms timeout)');
        try { URL.revokeObjectURL(svgUrl); } catch {}
        resolve({ svgBlob, pngDataUrl: '', warnings });
      }, 1500);

      img.onload = () => {
        clearTimeout(timeoutId);
        try {
          const canvas = document.createElement('canvas');
          canvas.width = (img.naturalWidth || 800) * scale;
          canvas.height = (img.naturalHeight || 600) * scale;
          const ctx = canvas.getContext('2d');
          if (!ctx) {
            warnings.push('PNG 浏览器限制 跳过已下 SVG (canvas 2d context 不可用)');
            try { URL.revokeObjectURL(svgUrl); } catch {}
            resolve({ svgBlob, pngDataUrl: '', warnings });
            return;
          }
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          try {
            pngDataUrl = canvas.toDataURL('image/png', quality);
          } catch (toDataUrlErr) {
            if (toDataUrlErr instanceof DOMException && toDataUrlErr.name === 'SecurityError') {
              warnings.push('PNG 浏览器限制 跳过已下 SVG (SecurityError CORS tainted canvas)');
            } else {
              warnings.push(`PNG 浏览器限制 跳过已下 SVG (${toDataUrlErr instanceof Error ? toDataUrlErr.message : String(toDataUrlErr)})`);
            }
            pngDataUrl = '';
          }
          try { URL.revokeObjectURL(svgUrl); } catch {}
          resolve({ svgBlob, pngDataUrl, warnings });
        } catch (drawErr) {
          warnings.push(`PNG 浏览器限制 跳过已下 SVG (${drawErr instanceof Error ? drawErr.message : String(drawErr)})`);
          try { URL.revokeObjectURL(svgUrl); } catch {}
          resolve({ svgBlob, pngDataUrl: '', warnings });
        }
      };

      img.onerror = () => {
        clearTimeout(timeoutId);
        warnings.push('PNG 浏览器限制 跳过已下 SVG (img.onerror 加载 SVG 失败)');
        try { URL.revokeObjectURL(svgUrl); } catch {}
        resolve({ svgBlob, pngDataUrl: '', warnings });
      };

      img.src = svgUrl;
    } catch (outerErr) {
      warnings.push(`exportPRISMA 异常: ${outerErr instanceof Error ? outerErr.message : String(outerErr)}`);
      try {
        const fallbackSvg = makeEmptyPrismaSvg(0, 'exportPRISMA 异常兜底');
        const xmlHeader = '<?xml version="1.0" encoding="UTF-8"?>';
        const doctype = '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">';
        const fullSvg = `${xmlHeader}\n${doctype}\n${fallbackSvg}`;
        const svgBlob = new Blob([fullSvg], { type: 'image/svg+xml;charset=utf-8' });
        resolve({ svgBlob, pngDataUrl: '', warnings });
      } catch {
        resolve({ svgBlob: new Blob(['<svg xmlns="http://www.w3.org/2000/svg"/>'], { type: 'image/svg+xml;charset=utf-8' }), pngDataUrl: '', warnings });
      }
    }
  });
}

export { downloadBlob, downloadDataUrl };
