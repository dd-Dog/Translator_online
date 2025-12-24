/**
 * 语言映射工具
 * 支持英文简写、全称、中文名称识别
 */

// 语言映射表：简写 -> 标准代码
const languageMap = {
  // 英文简写
  'en': 'en',
  'zh': 'zh',
  'ja': 'ja',
  'fr': 'fr',
  'de': 'de',
  'es': 'es',
  'ru': 'ru',
  'ko': 'ko',
  'it': 'it',
  'pt': 'pt',
  'ar': 'ar',
  'hi': 'hi',
  'th': 'th',
  'vi': 'vi',
  'nl': 'nl',
  'pl': 'pl',
  'tr': 'tr',
  'id': 'id',
  'cs': 'cs',
  'sv': 'sv',
  'da': 'da',
  'fi': 'fi',
  'no': 'no',
  'he': 'he',
  'uk': 'uk',
  'ro': 'ro',
  'hu': 'hu',
  'el': 'el',
  'bg': 'bg',
  'hr': 'hr',
  'sk': 'sk',
  'sl': 'sl',
  'et': 'et',
  'lv': 'lv',
  'lt': 'lt',
  'mt': 'mt',
  'ga': 'ga',
  'cy': 'cy',
  
  // 英文全称（小写）
  'english': 'en',
  'chinese': 'zh',
  'japanese': 'ja',
  'french': 'fr',
  'german': 'de',
  'spanish': 'es',
  'russian': 'ru',
  'korean': 'ko',
  'italian': 'it',
  'portuguese': 'pt',
  'arabic': 'ar',
  'hindi': 'hi',
  'thai': 'th',
  'vietnamese': 'vi',
  'dutch': 'nl',
  'polish': 'pl',
  'turkish': 'tr',
  'indonesian': 'id',
  'czech': 'cs',
  'swedish': 'sv',
  'danish': 'da',
  'finnish': 'fi',
  'norwegian': 'no',
  'hebrew': 'he',
  'ukrainian': 'uk',
  'romanian': 'ro',
  'hungarian': 'hu',
  'greek': 'el',
  'bulgarian': 'bg',
  'croatian': 'hr',
  'slovak': 'sk',
  'slovenian': 'sl',
  'estonian': 'et',
  'latvian': 'lv',
  'lithuanian': 'lt',
  'maltese': 'mt',
  'irish': 'ga',
  'welsh': 'cy',
  
  // 中文名称
  '英语': 'en',
  '英文': 'en',
  '中文': 'zh',
  '汉语': 'zh',
  '日语': 'ja',
  '日文': 'ja',
  '法语': 'fr',
  '法文': 'fr',
  '德语': 'de',
  '德文': 'de',
  '西班牙语': 'es',
  '西班牙文': 'es',
  '俄语': 'ru',
  '俄文': 'ru',
  '韩语': 'ko',
  '韩文': 'ko',
  '意大利语': 'it',
  '意大利文': 'it',
  '葡萄牙语': 'pt',
  '葡萄牙文': 'pt',
  '阿拉伯语': 'ar',
  '阿拉伯文': 'ar',
  '印地语': 'hi',
  '印地文': 'hi',
  '泰语': 'th',
  '泰文': 'th',
  '越南语': 'vi',
  '越南文': 'vi',
  '荷兰语': 'nl',
  '荷兰文': 'nl',
  '波兰语': 'pl',
  '波兰文': 'pl',
  '土耳其语': 'tr',
  '土耳其文': 'tr',
  '印尼语': 'id',
  '印尼文': 'id',
  '捷克语': 'cs',
  '捷克文': 'cs',
  '瑞典语': 'sv',
  '瑞典文': 'sv',
  '丹麦语': 'da',
  '丹麦文': 'da',
  '芬兰语': 'fi',
  '芬兰文': 'fi',
  '挪威语': 'no',
  '挪威文': 'no',
  '希伯来语': 'he',
  '希伯来文': 'he',
  '乌克兰语': 'uk',
  '乌克兰文': 'uk',
  '罗马尼亚语': 'ro',
  '罗马尼亚文': 'ro',
  '匈牙利语': 'hu',
  '匈牙利文': 'hu',
  '希腊语': 'el',
  '希腊文': 'el',
  '保加利亚语': 'bg',
  '保加利亚文': 'bg',
  '克罗地亚语': 'hr',
  '克罗地亚文': 'hr',
  '斯洛伐克语': 'sk',
  '斯洛伐克文': 'sk',
  '斯洛文尼亚语': 'sl',
  '斯洛文尼亚文': 'sl',
  '爱沙尼亚语': 'et',
  '爱沙尼亚文': 'et',
  '拉脱维亚语': 'lv',
  '拉脱维亚文': 'lv',
  '立陶宛语': 'lt',
  '立陶宛文': 'lt',
  '马耳他语': 'mt',
  '马耳他文': 'mt',
  '爱尔兰语': 'ga',
  '爱尔兰文': 'ga',
  '威尔士语': 'cy',
  '威尔士文': 'cy',
  
  // 自动检测
  'auto': 'auto',
  '自动': 'auto',
  '自动检测': 'auto',
  'automatic': 'auto'
}

/**
 * 识别语言代码
 * @param {string} input - 用户输入的语言标识
 * @returns {string} - 标准语言代码，如果无法识别则返回原值
 */
export function recognizeLanguage(input) {
  if (!input || typeof input !== 'string') {
    return 'auto'
  }
  
  // 去除空格并转为小写
  const normalized = input.trim().toLowerCase()
  
  // 直接匹配
  if (languageMap[normalized]) {
    return languageMap[normalized]
  }
  
  // 如果输入已经是标准代码，直接返回
  if (normalized.length === 2 && /^[a-z]{2}$/.test(normalized)) {
    return normalized
  }
  
  // 无法识别，返回原值（后端会处理）
  return input.trim()
}

/**
 * 获取语言显示名称
 * @param {string} langCode - 语言代码
 * @returns {string} - 显示名称
 */
export function getLanguageName(langCode) {
  const names = {
    'auto': '自动检测',
    'en': '英语',
    'zh': '中文',
    'ja': '日语',
    'fr': '法语',
    'de': '德语',
    'es': '西班牙语',
    'ru': '俄语',
    'ko': '韩语',
    'it': '意大利语',
    'pt': '葡萄牙语',
    'ar': '阿拉伯语',
    'hi': '印地语',
    'th': '泰语',
    'vi': '越南语',
    'nl': '荷兰语',
    'pl': '波兰语',
    'tr': '土耳其语',
    'id': '印尼语'
  }
  return names[langCode] || langCode
}

/**
 * 获取所有支持的语言列表
 * @returns {Array} - 语言列表 [{code, name, english}]
 */
export function getSupportedLanguages() {
  return [
    { code: 'auto', name: '自动检测', english: 'Auto' },
    { code: 'en', name: '英语', english: 'English' },
    { code: 'zh', name: '中文', english: 'Chinese' },
    { code: 'ja', name: '日语', english: 'Japanese' },
    { code: 'fr', name: '法语', english: 'French' },
    { code: 'de', name: '德语', english: 'German' },
    { code: 'es', name: '西班牙语', english: 'Spanish' },
    { code: 'ru', name: '俄语', english: 'Russian' },
    { code: 'ko', name: '韩语', english: 'Korean' },
    { code: 'it', name: '意大利语', english: 'Italian' },
    { code: 'pt', name: '葡萄牙语', english: 'Portuguese' },
    { code: 'ar', name: '阿拉伯语', english: 'Arabic' },
    { code: 'hi', name: '印地语', english: 'Hindi' },
    { code: 'th', name: '泰语', english: 'Thai' },
    { code: 'vi', name: '越南语', english: 'Vietnamese' },
    { code: 'nl', name: '荷兰语', english: 'Dutch' },
    { code: 'pl', name: '波兰语', english: 'Polish' },
    { code: 'tr', name: '土耳其语', english: 'Turkish' },
    { code: 'id', name: '印尼语', english: 'Indonesian' }
  ]
}

