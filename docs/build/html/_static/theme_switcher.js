const SITE_THEMES = [
    {
        id: 'light',
        icon: '☼',
        name: 'Light'
    },
    {
        id: 'dark',
        icon: '☽',
        name: 'Dark'
    }
];

const SYNTAX_THEMES = [
    {
        id: 'friendly',
        name: 'Friendly',
        stylesheet: 'pygments.css',
        style: 'background: #f0f0f0;  color: #bb60d5 '
    },
    {
        id: 'monokai',
        name: 'Monokai',
        stylesheet: 'pygments_dark.css',
        style: 'background: #272822;  color: #f8f8f2 '
    },
    {
        id: 'cobalt2',
        name: 'Cobalt2',
        stylesheet: 'pygments-cobalt2.css',
        style: 'background: #193549;  color: #e1efff '
    }
];

// === UTILITY FUNCTIONS ===

function storageAvailable(type) {
    let storage;
    try {
        storage = window[type];
        const x = '__storage_test__';
        storage.setItem(x, x);
        storage.removeItem(x);
        return true;
    } catch(e) {
        return e instanceof DOMException && (
            // everything except Firefox
            e.code === 22 ||
            // Firefox
            e.code === 1014 ||
            // test name field too, because code might not be present
            // everything except Firefox
            e.name === 'QuotaExceededError' ||
            // Firefox
            e.name === 'NS_ERROR_DOM_QUOTA_REACHED') &&
            // acknowledge QuotaExceededError only if there's something already stored
            (storage && storage.length !== 0);
    }
}

function saveValue(key, value){
    if (storageAvailable('localStorage')){
        localStorage.setItem(key, value);
    }
}

function loadValue(key){
    if (!storageAvailable('localStorage')){
        return null;
    }
    
    return localStorage.getItem(key);
}

// === THEME SWITCHER CREATION FUNCTIONS ===

function getThemeSwitcherLocation(){
    return document.getElementById("theme-switcher");
}

function createThemeSelectorButton(){
    const button = document.createElement('button');
    button.classList.add('theme-button');
    
    return button;
}

function createThemeSwitcher(){
    const parent = getThemeSwitcherLocation();
    if (parent === null){
        throw "Error creating theme switcher: Parent element not found";
    }

    // site themes
    const siteThemes = document.createElement('div');
    siteThemes.id = 'site-themes-container';
    siteThemes.classList.add('themes-container');
    
    for (const theme of SITE_THEMES){
        const button = createSiteThemeButton(theme);
        siteThemes.appendChild(button);
    }
    
    parent.appendChild(siteThemes);
    
    const siteThemeId = getPreferredSiteThemeId();
    document.getElementById(siteThemeId + '-site-theme-button').click();
    
    // syntax themes
    const syntaxThemes = document.createElement('div');
    syntaxThemes.id = 'syntax-themes-container';
    syntaxThemes.classList.add('themes-container');
    
    for (const theme of SYNTAX_THEMES){
        const button = createSyntaxThemeButton(theme);
        syntaxThemes.appendChild(button);
    }
    
    parent.appendChild(syntaxThemes);
    
    const syntaxThemeId = getPreferredSyntaxThemeId(siteThemeId);
    document.getElementById(syntaxThemeId + '-syntax-theme-button').click();
    
    // If a pygments_dark_style is set, sphinx will generate a link to
    // the dark stylesheet, which will override our syntax theme. So if
    // it exists, we have to remove it.
    const dark_stylesheet = document.getElementById("pygments_dark_css");
    if (dark_stylesheet !== null){
        dark_stylesheet.remove();
    }
}

// === SITE THEME FUNCTIONS ===

function applySiteTheme(themeId){
    const oldThemeClass = [...document.body.classList].find(cls => cls.endsWith('-theme'));
    if (oldThemeClass === themeId + '-theme'){
        return;
    }
    
    saveValue('siteTheme', themeId);

    document.body.classList.add(themeId + '-theme');
    
    if (oldThemeClass !== undefined){
        document.body.classList.remove(oldThemeClass);
    }
    
    const button = document.querySelector('#site-themes-container .theme-button.active');
    if (button !== null){
        button.classList.remove('active');
    }
    document.getElementById(themeId + '-site-theme-button').classList.add('active');
}

function createSiteThemeButton(theme){
    const button = createThemeSelectorButton();
    
    button.id = theme.id + '-site-theme-button';
    button.textContent = theme.icon;
    button.title = `Site theme: ${theme.name}`;
    
    button.onclick = event => applySiteTheme(theme.id);
    
    return button;
}

function isValidSiteThemeId(themeId){
    return document.getElementById(themeId + '-site-theme-button') !== null;
}

function getPreferredSiteThemeId(){
    const themeGetters = [
        () => loadValue('siteTheme'),
        getDefaultSiteThemeId,
    ];
    
    for (const getter of themeGetters){
        const themeId = getter();
        
        if (isValidSiteThemeId(themeId)){
            return themeId;
        }
    }
    
    return SITE_THEMES[0].id;
}

function getDefaultSiteThemeId(){
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "monokai" : "friendly";
}

// === SYNTAX THEME FUNCTIONS ===

function applySyntaxTheme(theme){
    const stylesheet = '_static/' + theme.stylesheet;

    const elem = document.head.querySelector('link[rel="stylesheet"][href^="_static/pygments"]');
    
    if (elem.href === stylesheet){
        return;
    }
    
    saveValue('syntaxTheme', theme.id);
    
    elem.href = stylesheet;
    
    const button = document.querySelector('#syntax-themes-container .theme-button.active');
    if (button !== null){
        button.classList.remove('active');
    }
    document.getElementById(theme.id + '-syntax-theme-button').classList.add('active');
}

function createSyntaxThemeButton(theme){
    const button = createThemeSelectorButton();
    
    button.id = theme.id + '-syntax-theme-button';
    button.textContent = 'Aa';
    button.title = `Syntax theme: ${theme.name}`;
    
    button.style.cssText = theme.style;
    
    button.onclick = event => applySyntaxTheme(theme);
    
    return button;
}

function isValidSyntaxThemeId(themeId){
    return document.getElementById(themeId + '-syntax-theme-button') !== null;
}

function getPreferredSyntaxThemeId(siteThemeId){
    const themeGetters = [
        siteTheme => loadValue('syntaxTheme'),
        getDefaultSyntaxThemeId,
    ];
    
    for (const getter of themeGetters){
        const themeId = getter();
        
        if (isValidSyntaxThemeId(themeId)){
            return themeId;
        }
    }
    
    return SYNTAX_THEMES[0].id;
}

function getDefaultSyntaxThemeId(siteThemeId){
    return siteThemeId === "dark" ? "monokai" : "friendly";
}

window.onload = createThemeSwitcher;
