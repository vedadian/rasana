const HTML_SAFE_ALTERNATIVES = {
    "&": "&amp;",
    "\"": "&quot;",
    "'": "&apos;",
    "<": "&lt;",
    ">":"&gt;"
};
const escapeForHtml = s => s.replace(/[&"'<>]/g, c => HTML_SAFE_ALTERNATIVES[c]);
class JalaliDate {
    constructor(date) {
        this.year = date.year;
        this.month = date.month;
        this.day = date.day;
    }
    toShortFormJalali() {
        return toFarsiDigits(this.year + '/' + this.month + '/' + this.day);
    }
    toLongFormJalali() {
        return ordinals[this.day - 1] + ' ' + monthNames[this.month - 1] + ' ماه ' + toFarsiDigits(String(this.year));
    }
    compare(other) {
        if (this.year > other.year)
            return 1;
        else if (this.year < other.year)
            return -1;
        if (this.month > other.month)
            return 1;
        else if (this.month < other.month)
            return -1;
        if (this.day > other.day)
            return 1;
        else if (this.day < other.day)
            return -1;
        return 0;
    }
}

var monthNames = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
];
var ordinals = [
    'یکم', 'دوم', 'سوم', 'چهارم', 'پنجم', 'ششم', 'هفتم', 'هشتم', 'نهم', 'دهم', 'یازدهم', 'دوازدهم',
    'سیزدهم', 'چهاردهم', 'پانزدهم', 'شانزدهم', 'هفدهم', 'هجدهم', 'نوزدهم', 'بیستم', 'بیست و یکم', 'بیست و دوم',
    'بیست و سوم', 'بیست و چهارم', 'بیست و پنجم', 'بیست و ششم', 'بیست و هفتم', 'بیست و هشتم',
    'بیست و نهم', 'سی‌ام', 'سی و یکم'
];
function toFarsiDigits(text) {
    return text.replace(/\d/g, function(digit) {
        return String.fromCharCode(0x6f0 + digit.charCodeAt(0) - '0'.charCodeAt(0));
    });
}
function convertDates(o) {
    for(k in o) {
        if(!(o[k] instanceof Object))
            continue;
        if(k.toLowerCase().endsWith('date'))
            o[k] = new JalaliDate(o[k]);
        else
            convertDates(o[k]);
    }
}
function render({websiteSpecs, themeSpecs, items, nodeSpecs, breadCrumb}) {
    convertDates(websiteSpecs);
    convertDates(themeSpecs);
    convertDates(nodeSpecs);
    convertDates(items);
    let result='';
    // body_of_rendered_ejs_function
    return result;
}