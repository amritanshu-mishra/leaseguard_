/** Indian digit grouping, including paise. No floating-point money. */
export function formatPaise(paise: number | null | undefined): string {
  if (paise === null || paise === undefined) return '—';
  const sign = paise < 0 ? '-' : '';
  const rupees = Math.floor(Math.abs(paise) / 100);
  const remainder = Math.abs(paise) % 100;
  const grouped = groupIndian(rupees);
  return `${sign}₹${grouped}${remainder ? `.${String(remainder).padStart(2, '0')}` : ''}`;
}

export function groupIndian(value: number): string {
  const s = String(value);
  if (s.length <= 3) return s;
  const tail = s.slice(-3);
  const head = s.slice(0, -3);
  const parts: string[] = [];
  let rest = head;
  while (rest.length > 2) {
    parts.unshift(rest.slice(-2));
    rest = rest.slice(0, -2);
  }
  if (rest) parts.unshift(rest);
  return [...parts, tail].join(',');
}

export function formatDate(iso: string | undefined, lang: 'en' | 'hi' = 'en'): string {
  if (typeof iso !== 'string') return '—';
  const [year, month, day] = iso.split('-').map(Number);
  if (!year || !month || !day) return iso;
  const months =
    lang === 'hi'
      ? ['जन', 'फर', 'मार', 'अप्र', 'मई', 'जून', 'जुल', 'अग', 'सित', 'अक्टू', 'नव', 'दिस']
      : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${day} ${months[month - 1]} ${year}`;
}

export function formatMonth(iso: string | undefined, lang: 'en' | 'hi' = 'en'): string {
  if (typeof iso !== 'string') return '—';
  const [year, month] = iso.split('-').map(Number);
  if (!year || !month) return iso;
  if (lang === 'hi') {
    const names = ['जनवरी', 'फरवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', 'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर'];
    return `${names[month - 1]} ${year}`;
  }
  const names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  return `${names[month - 1]} ${year}`;
}

export function shortNumber(n: number): string {
  if (n >= 60) return `${Math.floor(n / 60)}h ${n % 60}m`;
  return `${n}m`;
}
