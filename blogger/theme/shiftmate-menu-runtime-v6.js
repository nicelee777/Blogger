/* ShiftMate Blogger language/menu runtime v6 — 10 locales, Page-based FAQ/Guide. */
(function () {
  'use strict';

  var LOCALES = {
    en: {name:'English', tag:'en', path:['lang','lang-en','English'], blog:'/search/label/lang', legacyBlog:'/search/label/lang-en', faq:'/p/faq.html', notice:'/search/label/lang+notice', guide:'/p/guide.html', story:'/search/label/lang+story', legacyStory:'/search/label/lang-en+story'},
    es: {name:'Español', tag:'es', path:['lang-es','español','Español'], blog:'/search/label/lang-es', faq:'/p/faq-es.html', notice:'/search/label/lang-es+notice', guide:'/p/guide-es.html', story:'/search/label/lang-es+story'},
    de: {name:'Deutsch', tag:'de', path:['lang-de','Deutsch'], blog:'/search/label/lang-de', faq:'/p/faq-de.html', notice:'/search/label/lang-de+notice', guide:'/p/guide-de.html', story:'/search/label/lang-de+story'},
    fr: {name:'Français', tag:'fr', path:['lang-fr','Français','Francais'], blog:'/search/label/lang-fr', faq:'/p/faq-fr.html', notice:'/search/label/lang-fr+notice', guide:'/p/guide-fr.html', story:'/search/label/lang-fr+story'},
    'pt-BR': {name:'Português (Brasil)', tag:'pt-BR', path:['lang-pt-br','Português (Brasil)','Português','Portugues'], blog:'/search/label/lang-pt-br', faq:'/p/faq-pt-br.html', notice:'/search/label/lang-pt-br+notice', guide:'/p/guide-pt-br.html', story:'/search/label/lang-pt-br+story'},
    'zh-CN': {name:'简体中文', tag:'zh-CN', path:['lang-zh-cn','lang-zh-hans','简体中文','中文'], blog:'/search/label/lang-zh-cn', faq:'/p/faq-cn.html', notice:'/search/label/lang-zh-cn+notice', guide:'/p/guide-cn.html', story:'/search/label/lang-zh-cn+story'},
    'zh-TW': {name:'繁體中文', tag:'zh-TW', path:['lang-zh-tw','lang-zh-hant','繁體中文'], blog:'/search/label/lang-zh-tw', faq:'/p/faq-tw.html', notice:'/search/label/lang-zh-tw+notice', guide:'/p/guide-tw.html', story:'/search/label/lang-zh-tw+story'},
    ko: {name:'한국어', tag:'ko', path:['lang-ko','한국어'], blog:'/search/label/lang-ko', faq:'/p/faq-ko.html', notice:'/search/label/lang-ko+notice', guide:'/p/guide-ko.html', story:'/search/label/lang-ko+story'},
    ja: {name:'日本語', tag:'ja', path:['lang-ja','日本語'], blog:'/search/label/lang-ja', faq:'/p/faq-ja.html', notice:'/search/label/lang-ja+notice', guide:'/p/guide-ja.html', story:'/search/label/lang-ja+story'},
    vi: {name:'Tiếng Việt', tag:'vi', path:['lang-vi','Tiếng Việt'], blog:'/search/label/lang-vi', faq:'/p/faq-vi.html', notice:'/search/label/lang-vi+notice', guide:'/p/guide-vi.html', story:'/search/label/lang-vi+story'}
  };

  var ORDER = ['en','es','de','fr','pt-BR','zh-CN','zh-TW','ko','ja','vi'];

  var TEXT = {
    en: {desc:'News, guides and stories for your shift-working life.', help:'Explore ShiftMate', tag:'Your shifts. Your rhythm.', notice:'Notices', noticeDesc:'Check important updates and announcements.', guide:'User guide', guideDesc:'Learn how to use ShiftMate.', faq:'FAQ', faqDesc:'Find answers and troubleshooting tips.', story:'Stories', storyDesc:'Read posts in this language.', soon:'Coming soon', all:'Show all', filter:'Posts in English', search:'Search', searchHint:'Search this blog', read:'Read more'},
    es: {desc:'Noticias, guías e historias para tu vida por turnos.', help:'Explora ShiftMate', tag:'Tus turnos. Tu ritmo.', notice:'Avisos', noticeDesc:'Consulta novedades y anuncios importantes.', guide:'Guía de uso', guideDesc:'Aprende a usar ShiftMate.', faq:'Preguntas frecuentes', faqDesc:'Encuentra respuestas y soluciones.', story:'Historias', storyDesc:'Lee artículos en este idioma.', soon:'Próximamente', all:'Ver todo', filter:'Artículos en español', search:'Buscar', searchHint:'Buscar en el blog', read:'Leer más'},
    de: {desc:'Neuigkeiten, Anleitungen und Geschichten rund um Schichtarbeit mit ShiftMate.', help:'ShiftMate entdecken', tag:'Deine Schichten. Dein Rhythmus.', notice:'Mitteilungen', noticeDesc:'Wichtige Updates und Mitteilungen ansehen.', guide:'Benutzerhandbuch', guideDesc:'Erfahren Sie, wie Sie ShiftMate verwenden.', faq:'FAQ', faqDesc:'Antworten und Tipps zur Problemlösung finden.', story:'Geschichten', storyDesc:'Beiträge auf Deutsch lesen.', soon:'Demnächst', all:'Alle anzeigen', filter:'Beiträge auf Deutsch', search:'Suchen', searchHint:'Blog durchsuchen', read:'Weiterlesen'},
    fr: {desc:'Actualités, guides et récits sur le travail posté avec ShiftMate.', help:'Découvrir ShiftMate', tag:'Vos services. Votre rythme.', notice:'Annonces', noticeDesc:'Consultez les mises à jour et annonces importantes.', guide:'Guide d’utilisation', guideDesc:'Découvrez comment utiliser ShiftMate.', faq:'Questions fréquentes', faqDesc:'Trouvez des réponses et des conseils de dépannage.', story:'Récits', storyDesc:'Lisez les articles en français.', soon:'Bientôt disponible', all:'Tout afficher', filter:'Articles en français', search:'Rechercher', searchHint:'Rechercher dans le blog', read:'Lire la suite'},
    'pt-BR': {desc:'Notícias, guias e histórias sobre a vida em turnos com o ShiftMate.', help:'Conheça o ShiftMate', tag:'Seus turnos. Seu ritmo.', notice:'Avisos', noticeDesc:'Confira atualizações e comunicados importantes.', guide:'Guia de uso', guideDesc:'Aprenda a usar o ShiftMate.', faq:'Perguntas frequentes', faqDesc:'Encontre respostas e dicas para resolver problemas.', story:'Histórias', storyDesc:'Leia publicações em português.', soon:'Em breve', all:'Ver tudo', filter:'Publicações em português (Brasil)', search:'Pesquisar', searchHint:'Pesquisar no blog', read:'Leia mais'},
    'zh-CN': {desc:'ShiftMate 最新消息、使用指南与轮班生活故事。', help:'探索 ShiftMate', tag:'你的班次，你的节奏。', notice:'公告', noticeDesc:'查看重要更新与公告。', guide:'使用指南', guideDesc:'了解各项功能的使用方法。', faq:'常见问题', faqDesc:'查找问题解答与解决方法。', story:'故事', storyDesc:'阅读此语言的博客文章。', soon:'即将推出', all:'显示全部', filter:'简体中文文章', search:'搜索', searchHint:'搜索博客', read:'继续阅读'},
    'zh-TW': {desc:'ShiftMate 最新消息、使用指南與輪班生活故事。', help:'探索 ShiftMate', tag:'你的班表，你的節奏。', notice:'公告', noticeDesc:'查看重要更新與公告。', guide:'使用指南', guideDesc:'了解各項功能的使用方法。', faq:'常見問題', faqDesc:'查找問題解答與解決方法。', story:'故事', storyDesc:'閱讀此語言的部落格文章。', soon:'即將推出', all:'顯示全部', filter:'繁體中文文章', search:'搜尋', searchHint:'搜尋部落格', read:'繼續閱讀'},
    ko: {desc:'ShiftMate 소식과 사용 가이드, 교대근무 이야기를 전합니다.', help:'ShiftMate 둘러보기', tag:'내 근무, 내 리듬대로', notice:'공지사항', noticeDesc:'중요한 업데이트와 안내를 확인하세요.', guide:'사용 가이드', guideDesc:'기능별 사용 방법을 확인하세요.', faq:'자주 묻는 질문', faqDesc:'궁금한 점과 해결 방법을 찾아보세요.', story:'스토리', storyDesc:'한국어 블로그 글을 모아보세요.', soon:'준비 중', all:'전체 글', filter:'한국어로 작성된 글', search:'검색', searchHint:'블로그에서 검색', read:'더 읽기'},
    ja: {desc:'ShiftMateのお知らせ、使い方、シフト勤務にまつわる読みもの。', help:'ShiftMateをもっと知る', tag:'シフトも、毎日も、自分のリズムで。', notice:'お知らせ', noticeDesc:'重要な更新情報とお知らせを確認できます。', guide:'使い方ガイド', guideDesc:'機能ごとの使い方を確認できます。', faq:'よくある質問', faqDesc:'疑問や困ったときの解決方法。', story:'ストーリー', storyDesc:'日本語の記事を読む。', soon:'準備中', all:'すべての記事', filter:'日本語の記事', search:'検索', searchHint:'ブログ内を検索', read:'続きを読む'},
    vi: {desc:'Tin tức, hướng dẫn và câu chuyện về cuộc sống làm ca với ShiftMate.', help:'Khám phá ShiftMate', tag:'Ca trực của bạn. Nhịp sống của bạn.', notice:'Thông báo', noticeDesc:'Xem cập nhật và thông báo quan trọng.', guide:'Hướng dẫn sử dụng', guideDesc:'Tìm hiểu cách dùng ShiftMate.', faq:'Câu hỏi thường gặp', faqDesc:'Tìm câu trả lời và cách khắc phục.', story:'Câu chuyện', storyDesc:'Đọc bài viết bằng ngôn ngữ này.', soon:'Sắp ra mắt', all:'Tất cả bài viết', filter:'Bài viết bằng tiếng Việt', search:'Tìm kiếm', searchHint:'Tìm kiếm trong blog', read:'Đọc thêm'}
  };

  var current = 'ko';
  function byClass(name) { return document.getElementsByClassName ? document.getElementsByClassName(name) : []; }
  function hasClass(el, c) { return (' ' + (el.className || '') + ' ').indexOf(' ' + c + ' ') > -1; }
  function setTextByClass(c, v) { var n=byClass(c); for (var i=0; i<n.length; i++) n[i].textContent = v; }
  function safeGet(k) { try { return localStorage.getItem(k); } catch(e) { return null; } }
  function safeSet(k, v) { try { localStorage.setItem(k, v); } catch(e) {} }
  function qs(key) { var m = location.search.match(new RegExp('[?&]' + key + '=([^&]+)')); return m ? decodeURIComponent(m[1].replace(/\+/g, ' ')) : ''; }

  function norm(v) {
    if (!v) return '';
    v = String(v).toLowerCase();
    if (v === 'ko' || v.indexOf('korean') > -1) return 'ko';
    if (v === 'ja' || v.indexOf('japanese') > -1) return 'ja';
    if (v === 'es' || v.indexOf('spanish') > -1) return 'es';
    if (v === 'de' || v.indexOf('german') > -1 || v.indexOf('deutsch') > -1) return 'de';
    if (v === 'fr' || v.indexOf('french') > -1 || v.indexOf('français') > -1 || v.indexOf('francais') > -1) return 'fr';
    if (v === 'pt' || v.indexOf('pt-br') > -1 || v.indexOf('portugu') > -1) return 'pt-BR';
    if (v === 'vi') return 'vi';
    if (v.indexOf('zh-tw') > -1 || v.indexOf('hant') > -1) return 'zh-TW';
    if (v.indexOf('zh') > -1 || v.indexOf('hans') > -1) return 'zh-CN';
    if (v === 'en' || v.indexOf('english') > -1) return 'en';
    return '';
  }

  function detect() {
    var fromParam = norm(qs('sm-lang'));
    if (fromParam && LOCALES[fromParam]) return fromParam;
    var href = decodeURIComponent(location.href).toLowerCase();
    if (href.indexOf('faq-ko.html') > -1 || href.indexOf('guide-ko.html') > -1 || href.indexOf('lang-ko') > -1 || href.indexOf('한국어') > -1) return 'ko';
    if (href.indexOf('faq-ja.html') > -1 || href.indexOf('guide-ja.html') > -1 || href.indexOf('lang-ja') > -1) return 'ja';
    if (href.indexOf('faq-es.html') > -1 || href.indexOf('guide-es.html') > -1 || href.indexOf('lang-es') > -1) return 'es';
    if (href.indexOf('faq-de.html') > -1 || href.indexOf('guide-de.html') > -1 || href.indexOf('lang-de') > -1) return 'de';
    if (href.indexOf('faq-fr.html') > -1 || href.indexOf('guide-fr.html') > -1 || href.indexOf('lang-fr') > -1) return 'fr';
    if (href.indexOf('faq-pt-br.html') > -1 || href.indexOf('guide-pt-br.html') > -1 || href.indexOf('lang-pt-br') > -1) return 'pt-BR';
    if (href.indexOf('faq-vi.html') > -1 || href.indexOf('guide-vi.html') > -1 || href.indexOf('lang-vi') > -1) return 'vi';
    if (href.indexOf('faq-tw.html') > -1 || href.indexOf('guide-tw.html') > -1 || href.indexOf('lang-zh-tw') > -1) return 'zh-TW';
    if (href.indexOf('faq-cn.html') > -1 || href.indexOf('guide-cn.html') > -1 || href.indexOf('lang-zh-cn') > -1) return 'zh-CN';
    if (href.indexOf('/p/faq.html') > -1 || href.indexOf('/p/guide.html') > -1 || href.indexOf('/search/label/lang') > -1 || href.indexOf('lang-en') > -1) return 'en';
    var saved = norm(safeGet('shiftmate.blog.locale.v2'));
    if (saved && LOCALES[saved]) return saved;
    return 'en';
  }

  function url(id, kind) {
    var v = LOCALES[id] && LOCALES[id][kind];
    if (!v) return '';
    if (v.indexOf('/p/') === 0) return v + '?sm-lang=' + encodeURIComponent(id);
    return v;
  }

  function sectionKind() {
    var href = decodeURIComponent(location.href).toLowerCase();
    if (href.indexOf('/p/guide') > -1 || href.indexOf('+guide') > -1) return 'guide';
    if (href.indexOf('/p/faq') > -1) return 'faq';
    if (href.indexOf('+notice') > -1) return 'notice';
    if (href.indexOf('+story') > -1) return 'story';
    return 'blog';
  }

  function menuHtml(id, compact) {
    var t = TEXT[id] || TEXT.en;
    var rows = [['notice',t.notice,t.noticeDesc],['guide',t.guide,t.guideDesc],['faq',t.faq,t.faqDesc],['story',t.story,t.storyDesc]];
    var h='';
    if (!compact) h += '<div class="sm-support-heading"><h2>' + t.help + '</h2><span class="sm-locale-chip">' + LOCALES[id].name + '</span></div>';
    h += '<nav class="' + (compact ? 'sm-quick-menu' : 'sm-menu') + '" aria-label="' + t.help + '">';
    for (var i=0; i<rows.length; i++) {
      var k=rows[i][0], href=url(id,k), unavailable=!href, tag=unavailable?'span':'a';
      h += '<' + tag + ' class="sm-menu-item' + (unavailable?' sm-unavailable':'') + '"';
      if (!unavailable) h += ' href="' + href + '" data-sm-menu="' + k + '" data-sm-locale-link="' + id + '"' + (sectionKind()===k?' aria-current="page"':'');
      h += '><span class="sm-menu-icon">•</span><span class="sm-menu-copy"><span class="sm-menu-title">' + rows[i][1] + '</span>';
      if (unavailable) h += '<span class="sm-menu-pending">' + t.soon + '</span>';
      else if (!compact) h += '<span class="sm-menu-description">' + rows[i][2] + '</span>';
      h += '</span>'; if (!compact && !unavailable) h += '<span class="sm-menu-arrow">›</span>'; h += '</' + tag + '>';
    }
    h += '</nav>';
    if (!compact) {
      h += '<details class="sm-other-languages"><summary>' + (id==='ko'?'다른 언어의 FAQ':'FAQ languages') + '</summary><div class="sm-faq-language-links">';
      for (var j=0; j<ORDER.length; j++) { var other=ORDER[j]; if (other!==id) h += '<a href="' + url(other,'faq') + '" lang="' + LOCALES[other].tag + '">' + LOCALES[other].name + '</a>'; }
      h += '</div></details>';
    }
    return h;
  }

  function languageNavHtml(id) {
    var h='<ul class="sm-language-list">', kind=sectionKind();
    for (var i=0; i<ORDER.length; i++) {
      var k=ORDER[i], l=LOCALES[k], selected=k===id, href=url(k,kind)||l.blog;
      h += '<li' + (selected?' class="selected"':'') + '><a class="sm-language-link" href="' + href + '" lang="' + l.tag + '" hreflang="' + l.tag + '" data-sm-locale-link="' + k + '"' + (selected?' aria-current="true"':'') + '>' + l.name + '</a></li>';
    }
    return h + '</ul>';
  }

  function updateFilter(id) {
    var t=TEXT[id]||TEXT.en, descs=byClass('post-filter-description');
    for (var i=0; i<descs.length; i++) descs[i].textContent=t.filter;
    var links=document.querySelectorAll?document.querySelectorAll('.post-filter-message a'):[];
    for (var j=0; j<links.length; j++) links[j].textContent=t.all;
  }

  function render(id) {
    if (!LOCALES[id]) id=detect();
    current=id; safeSet('shiftmate.blog.locale.v2',id);
    document.documentElement.setAttribute('data-sm-locale',id);
    document.documentElement.setAttribute('lang',LOCALES[id].tag);
    var t=TEXT[id]||TEXT.en;
    setTextByClass('sm-header-description',t.desc);
    setTextByClass('sm-sidebar-tagline',t.tag);
    setTextByClass('search-expand-text',t.search);
    var q=document.querySelectorAll?document.querySelectorAll('#search_top input[name="q"]'):[];
    for (var qi=0; qi<q.length; qi++) { q[qi].placeholder=t.searchHint; q[qi].setAttribute('aria-label',t.searchHint); }
    var navs=byClass('sm-language-nav'); for (var n=0; n<navs.length; n++) navs[n].innerHTML=languageNavHtml(id);
    var mounts=byClass('sm-js-support'); for (var m=0; m<mounts.length; m++) mounts[m].innerHTML=menuHtml(id,hasClass(mounts[m],'sm-js-support-compact'));
    updateFilter(id);
    var reads=document.querySelectorAll?document.querySelectorAll('.jump-link > a'):[];
    for (var r=0; r<reads.length; r++) reads[r].textContent=t.read;
  }

  function clickHandler(e) {
    e=e||window.event; var a=e.target||e.srcElement;
    while (a && a.tagName!=='A') a=a.parentNode;
    if (!a) return;
    var id=a.getAttribute('data-sm-locale-link');
    if (id && LOCALES[id]) { safeSet('shiftmate.blog.locale.v2',id); render(id); }
  }

  function boot() { render(detect()); }
  if (document.addEventListener) document.addEventListener('click',clickHandler,true);
  else if (document.attachEvent) document.attachEvent('onclick',clickHandler);
  boot(); setTimeout(boot,50); setTimeout(boot,250); setTimeout(boot,1000); setTimeout(boot,2500);
  if (window.addEventListener) window.addEventListener('load',boot,false);
  window.ShiftMateBlog={refresh:boot,getLanguage:function(){return current;}};
}());
