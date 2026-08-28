import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Patrimoine de la vallée de la Bruche", page_icon="🗺️", layout="wide")

st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding: 0 !important; max-width: 100% !important;}

        /* Empêche tout scroll sur la page Streamlit et force l'iframe
           à occuper exactement 100% de la fenêtre du navigateur. */
        html, body {
            overflow: hidden !important;
            height: 100vh !important;
            margin: 0 !important;
        }
        iframe {
            display: block;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw !important;
            height: 100vh !important;
            border: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

STORY_HEIGHT = 900 

STORY_HTML = r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />


<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

<style>

  #map{
    width:100%;
    height:100%;
    z-index:0;
  }
  #stage{
    position:relative;
    width:100%;
    height:100vh;
  }

  :root{
    --bg-ink:#10151c;
    --panel-glass: rgba(23,30,41,0.72);
    --panel-glass-strong: rgba(16,21,28,0.88);
    --panel-border: rgba(201,162,75,0.35);
    --accent-gold:#B5745C;
    --accent-gold-soft: rgba(201,162,75,0.18);
    --text-cream:#f3ecdf;
    --text-muted:#b9c0c9;
    --radius: 14px;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;background:var(--bg-ink);font-family:'Inter',sans-serif;color:var(--text-cream);overflow:hidden;height:100%;}


  .eyebrow{
    font-family:'Inter',sans-serif;
    font-size:11px;
    letter-spacing:.16em;
    text-transform:uppercase;
    color:var(--accent-gold);
    font-weight:600;
    margin-bottom:8px;
    display:block;
  }

  /* ---------- Overlay d'introduction ---------- */
  #intro-overlay{
    position:absolute; inset:0;
    background:radial-gradient(circle at 50% 40%, rgba(16,21,28,0.55), rgba(10,13,18,0.86));
    display:flex; align-items:center; justify-content:center;
    z-index:500;
    transition:opacity .5s ease, visibility .5s ease;
  }
  #intro-overlay.hidden{opacity:0; visibility:hidden; pointer-events:none;}
  #intro-box{
    width:min(520px, 88%);
    background:var(--panel-glass-strong);
    border:1px solid var(--panel-border);
    border-radius:var(--radius);
    padding:34px 32px 26px;
    backdrop-filter: blur(10px);
    text-align:center;
    box-shadow:0 20px 60px rgba(0,0,0,0.5);
  }
  #intro-box h1{
    font-family:'Fraunces', serif;
    font-size:28px;
    font-weight:600;
    margin:0 0 14px;
    line-height:1.25;
  }
  #intro-box p{
    font-size:14.5px;
    line-height:1.65;
    color:var(--text-muted);
    margin:0 0 26px;
  }
  #intro-dismiss{
    display:inline-flex;
    align-items:center;
    gap:8px;
    background:var(--accent-gold);
    color:#1b1608;
    border:none;
    padding:11px 26px;
    border-radius:999px;
    font-family:'Inter',sans-serif;
    font-weight:600;
    font-size:13.5px;
    letter-spacing:.02em;
    cursor:pointer;
    transition:transform .15s ease, box-shadow .15s ease;
  }
  #intro-dismiss:hover{transform:translateY(-1px); box-shadow:0 8px 22px rgba(201,162,75,0.35);}

  /* ---------- Panneaux flottants (texte) ---------- */
  .story-panel{
    position:absolute;
    z-index:200;
    width:500px;
    max-width:40vw;
    background:var(--panel-glass);
    border:1px solid var(--panel-border);
    border-left:1px solid var(--accent-gold);
    border-radius:var(--radius);
    padding:10px 26px;
    backdrop-filter: blur(8px);
    box-shadow:0 16px 40px rgba(0,0,0,0.35);
    opacity:0; transform:translateX(-16px);
    transition:opacity .55s ease, transform .55s ease;
    pointer-events:none;
  }
  .story-panel.left{left:1%; top:50%; transform:translate(-16px,-50%);}
  .story-panel.visible{opacity:1; pointer-events:auto;}
  .story-panel.left.visible{transform:translate(0,-50%);}

  .story-panel h2{
    font-family:'Fraunces', serif;
    font-size:23px;
    font-weight:600;
    margin:0 0 12px;
    line-height:1.3;
  }
  .story-panel p{
    font-size:14px;
    line-height:1.7;
    color:var(--text-muted);
    margin:0;
  }

  /* ---------- Photo flottante simple (étape 1) ---------- */
  .float-photo{
    position:absolute;
    z-index:200;
    right:6%;
    top:50%;
    height:auto;
    transform:translate(16px,-50%) rotate(2deg);
    opacity:0;
    transition:opacity .6s ease .1s, transform .6s ease .1s;
    pointer-events:none;
  }
  .float-photo.visible{opacity:1; transform:translate(0,-50%) rotate(2deg); pointer-events:auto;}
  .diapo-arrow{
    position:absolute;
    top:50%; transform:translateY(-50%);
    z-index:2;
    width:42px; height:42px;
    border-radius:50%;
    background:rgba(16,21,28,0.72);
    border:1px solid var(--panel-border);
    color:var(--text-cream);
    font-size:16px;
    display:flex; align-items:center; justify-content:center;
    cursor:pointer;
    opacity:0;
    transition:opacity .2s ease, background .2s ease;
    backdrop-filter: blur(4px);
  }
  .diapo-frame:hover .diapo-arrow{opacity:1;}
  .diapo-arrow:hover{background:var(--accent-gold); color:#1b1608;}
  .diapo-arrow.prev{left:10px;}
  .diapo-arrow.next{right:10px;}
  .diapo-dots span{cursor:pointer;}
  .float-photo img{
    width:auto;
    max-width:32vw;
    max-height:60vh;
    height:auto;
    border-radius:10px;
    border:8px solid var(--panel-glass-strong);
    box-shadow:0 18px 40px rgba(0,0,0,0.45);
    display:block;
  }
  .float-photo figcaption{
    text-align:center;
    font-size:11px;
    color:var(--text-muted);
    margin-top:8px;
    letter-spacing:.02em;
  }


  /* ---------- Diaporama flottant (étape 2) : cadre adapté largeur + hauteur à chaque photo ---------- */
  .float-diapo{
    position:absolute;
    z-index:200;
    right:5%;
    bottom:12%;
    width:auto;
    max-width:36vw;
    opacity:0;
    transform:translateY(20px);
    transition:opacity .6s ease .1s, transform .6s ease .1s;
    pointer-events:none;
  }
  .float-diapo.visible{opacity:1; transform:translateY(0); pointer-events:auto;}
  .diapo-frame{
    position:relative;
    width:280px;   
    height:280px;  
    max-width:36vw;
    max-height:60vh;
    border-radius:10px;
    overflow:hidden;
    border:5px solid var(--panel-glass-strong);
    box-shadow:0 18px 18px rgba(0,0,0,0.45);
    transition:width .45s ease, height .45s ease;
  }
  .diapo-frame img{
    position:absolute; inset:0;
    width:100%; height:100%; object-fit:contain;
    opacity:0;
    transition:opacity .8s ease;
  }
  .diapo-frame img.active{opacity:1;}
  .diapo-dots{display:flex; gap:6px; justify-content:center; margin-top:10px;}
  .diapo-dots span{width:3px;height:3px;border-radius:50%;background:rgba(255,255,255,0.25);transition:background .3s;}
  .diapo-dots span.active{background:var(--accent-gold);}
  .diapo-caption{
    text-align:center;
    font-size:11px;
    color:var(--text-muted);
    margin-top:8px;
    letter-spacing:.02em;
    min-height:14px;
    color:#000000;
  }


  /* ---------- Navigation bas de page ---------- */
  #nav-bar{
    position:absolute;
    left:50%; bottom:26px;
    transform:translateX(-50%);
    z-index:300;
    display:flex; align-items:center; gap:18px;
    background:var(--panel-glass-strong);
    border:1px solid var(--panel-border);
    border-radius:999px;
    padding:10px 14px;
    backdrop-filter: blur(8px);
    box-shadow:0 12px 30px rgba(0,0,0,0.4);
    opacity:0; visibility:hidden;
    transition:opacity .4s ease, visibility .4s ease;
  }
  #nav-bar.visible{opacity:1; visibility:visible;}
  .nav-arrow{
    width:38px; height:38px;
    border-radius:50%;
    border:1px solid var(--panel-border);
    background:transparent;
    color:var(--text-cream);
    display:flex; align-items:center; justify-content:center;
    cursor:pointer;
    font-size:16px;
    transition:background .2s, opacity .2s;
  }
  .nav-arrow:hover:not(:disabled){background:var(--accent-gold-soft);}
  .nav-arrow:disabled{opacity:0.25; cursor:default;}
  #nav-steps{display:flex; align-items:center; gap:8px;}
  .step-dot{
    width:7px; height:7px; border-radius:50%;
    background:rgba(255,255,255,0.22);
    transition:background .3s, transform .3s;
  }
  .step-dot.active{background:var(--accent-gold); transform:scale(1.3);}
  #nav-label{
    font-size:11px; letter-spacing:.12em; text-transform:uppercase;
    color:var(--text-muted); margin:0 4px; min-width:64px; text-align:center;
  }

  /* ---------- Marqueurs carte ---------- */
  .city-pin{
    width:16px; height:16px; border-radius:50%;
    background:var(--accent-gold);
    box-shadow:0 0 0 rgba(201,162,75,0.6);
    border:2px solid #fff8ea;
  }
  .city-pin.active{animation:pulse 1.8s infinite;}
  @keyframes pulse{
    0%{box-shadow:0 0 0 0 rgba(201,162,75,0.55);}
    70%{box-shadow:0 0 0 16px rgba(201,162,75,0);}
    100%{box-shadow:0 0 0 0 rgba(201,162,75,0);}
  }
  .route-line{
    stroke-dasharray: 10 8;
  }
  @keyframes dash{ to{ stroke-dashoffset:-1000; } }
</style>
</head>
<body>

<div id="stage">
  <div id="map"></div>

  <!-- Popup d'introduction -->
  <div id="intro-overlay">
    <div id="intro-box">
      <span class="eyebrow">Regard sur l'histoire</span>
      <h1>L'histoire du patrimoine de la vallée de la Bruche</h1>
      <p>
        Le territoire de la vallée de la Bruche possède un patrimoine singulier en raison de son histoire et de sa situation aux frontières de différents territoires aux cultures diverses. Chacun des bâtiments présentés est visible sur la carte dynamique, n'hésitez pas à fouiller !
      </p>
      <button id="intro-dismiss">Commencer le voyage ↓</button>
    </div>
  </div>

  <!-- Panneau de texte (gauche) -->
  <div class="story-panel left" id="panel-text">
    <span class="eyebrow" id="panel-eyebrow">Étape 01</span>
    <h2 id="panel-title">Titre</h2>
    <p id="panel-body">Texte</p>
  </div>

  <!-- Photo simple (étape 1) -->
  <figure class="float-photo" id="panel-photo">
    <img id="panel-photo-img" src="" alt="" />
    <figcaption id="panel-photo-caption"></figcaption>
  </figure>

  <!-- Diaporama (étape 2+) : navigation manuelle par flèches ou points -->
  <div class="float-diapo" id="panel-diapo">
    <div class="diapo-frame" id="diapo-frame">
      <button class="diapo-arrow prev" id="diapo-prev" type="button" aria-label="Photo précédente">‹</button>
      <button class="diapo-arrow next" id="diapo-next" type="button" aria-label="Photo suivante">›</button>
    </div>
    <div class="diapo-dots" id="diapo-dots"></div>
    <p class="diapo-caption" id="diapo-caption"></p>
  </div>

  <!-- Navigation -->
  <div id="nav-bar">
    <button class="nav-arrow" id="btn-prev" aria-label="Étape précédente">←</button>
    <div id="nav-steps"></div>
    <span id="nav-label">01 / 02</span>
    <button class="nav-arrow" id="btn-next" aria-label="Étape suivante">→</button>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>

  const FRANCE_VIEW = { coords:[48.478429, 7.219095], zoom:12 };

  const steps = [
    {
      city: "Strasbourg",
      coords: [48.476489, 7.219572],
      zoom: 10,
      eyebrow: "Étape 1 — La vallée",
      title: "Avant 1789...",
      text: "La vallée de la Bruche était divisée en quatre territoires : la principauté de Salm-Salm, le bailliage épiscopal de Schirmeck, le comté du Ban de la Roche et la seigneurie de Villé. Pourtant, les habitants vivent ensemble les essors et les épisodes de crises qui surgissent dans la vallée.",
      layout: "diapo-bottom-right",
      photos: [
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/Carte_avant1789.jpg", caption: "Audrey Schneider, 2005" }
      ]
    },

    {
      city: "Paris",
      coords: [48.493318, 7.148869],
      zoom: 13,
      eyebrow: "Étape 2 — L'industrie du fer",
      title: "L'industrie du fer",
      text: "Les gisements de fer sont importants dans la vallée. Son exploitation est attestée depuis le VIIe siècle dans la commune de Grandfontaine même si une mine est mentionnée depuis 1257. Ces exploitations se sont surtout développées au XIXe siècle comme l'attestent les haldes de 1825. De nombreuses mines ont ouvert dans la vallée et ont employé environ 1000 habitants à son apogée ce qui permet de développer certaines communes du territoire. Toutefois, la saturation du marché et la révolution industrielle provoque son déclin et désormais, les mines sont abandonnées.",
      layout: "diapo-bottom-right",
      photos: [
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/Mine_Granfontaine.jpg", caption: "Mine de Grandfontaine, (valleedelabruche.fr)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/Mine_Grandfontaine.jpg", caption: "Galerie d'évacuation d'eau de la mine (Mathile Cybulski)" }
      ]
    },

    {
      city: "Lyon",
      coords: [48.456056, 7.209297],
      zoom: 13,
      eyebrow: "Étape 3 - L'industrie textile",
      title: "L'essor économique de la vallée",
      text: "L'industrie textile à été très importante pour le développement de la vallée. La première filature de coton ouvre en 1795 à Schirmeck puis, au XIXe siècle, des industriels s'installent dans la vallée et construisent des usines de textiles mais aussi de plus modestes filatures voient le jour en premier lieu. Cette industrie fleuri ici, car la main d'oeuvre est nombreuse et peu chère en comparaison des localités voisines. Le cours d'eau de la Bruche favorise l'exploitation du coton, très évergivore. en 1870, 9 établissements emploient 1720 métiers, en 1907, 70% des ouvriers travaillent pour ces usines (8500 métiers à tisser). C'est aussi le lieu de nombreuses revendications ouvrières. La mécanisation du travail avait permis aux femmes et aux enfants de travailler, grâce à ces revendications en 1840 les horaires des enfants sont recadrés avec : 8h / jour entre 8 à 12 ans et 12h / jour pour ceux de 12 à 16 ans. A la fin du XXe siècle, l'industrie est en déclin et la dernière usine ferme en 1981. La concurrence asiatique et la perte des colonies françaises qui représentaient un tiers des exportations expliquent la fin de cette industrie dans la vallée. Encore aujourd'hui, il reste de nombreuses marques de cette époque. Certaines usines sont abandonnées, les maisons des industriels ayant fait fortune dans la vallée sont également présentes dans les villages, tout comme des enclos funéraires appartenant aux familles d'industriels.",
      layout: "diapo-bottom-right",
      photos: [
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012122.jpg", caption: "Ancienne filature de coton Claude Frères, puis filature de Wasselone de Neuviller-la-Roche (Menninger C)"},
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012886.jpg", caption: "Ancienne usine de tissage et filature Thormann de Plaine (Fritsch F et Haegel O)"},
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012123.jpg", caption: "Ancien tissage de coton Pramberger, puis filature Jacquel de Neuviller-le-Roche (Menninger C)"},
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012882.jpg", caption: "Ancienne usine de tissage Rey, puis Thormann-Dutruel de Plaine (Fritsch F et Haegel O)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012721.jpg", caption: "Immeuble de logements ouvriers (Menninger C)"},
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013299.jpg", caption: "Enclos funéraire de la famille d'industriels Heywood-Seillière de La Broque (Fritsch F et Haegel O)"}
        ]
    },

    {
      city: "Bordeaux",
      coords: [48.421549, 7.187030],
      zoom: 13,
      eyebrow: "Étape 4 - Regard sur le patrimoine religieux",
      title: "Le patrimoine religieux",
      text: "L'histoire religieuse de la vallée est riche. Son identité s'est forgée avec la présence de différents territoires à ses frontières. Dans ce cadre, chacun des territoires dont elle était composée a évolué différemment d'un point de vue religieux. La tour coeur de Fouday est l'un des seuls témoins de l'architecture religieuse médiévale. Le territoire de Ban-de-la-Roche est de confession protestante symbolisée par la présence de J.-F Oberlin, pasteur connu pour son élévation du territoire et plus globalement son apport pour de nombreux domaines tel que l'éducation périscolaire. Un musée est présent à Waldersbach pour présenter son oeuvre. Concernant les autres confessions, une petite communauté ménonnite s'est réfugiée dans le comté de Salm après son expulsion de l'Alsace. Le judaïsme est également présent dans la vallée dont la seule synagogue se situe à Schirmeck. Le catholicisme et le protestantisme sont les deux confessions majoritaires, lieus de culte sont présents dans chaque village où les deux églises peuvent cohexiter.",
      layout: "diapo-bottom-right",
      photos: [
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013097.jpg", caption: "Eglise Saint-Jean-Baptiste de Fouday (Fritsch F et Haegel O)"},
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013088.jpg", caption: "Temple luthérien de Rothau (Menninger C)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013085.jpg", caption: "Eglise Notre-Dame-de-Bon-Secours de La Broque (Fritsch F et Haegel O)"},
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013057.jpg", caption: "Eglise paroissiale de Schirmeck (Fritsch F et Haegel O)"},
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013058.jpg", caption: "Synagogue de Schirmeck (Fritsch F et Haegel O)"},
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67011248.jpg", caption: "Chapelle Notre-Dame-de-Bon-Secours de Lutzelhouse (Parent B et Fritsch E)"},
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67011289.jpg", caption: "Chapelle funéraire de la famille d'industriels Muller à Muhlbach-sur-Bruche (Erfurth J)"}
      ]
    },

    {
      city: "Marseille",
      coords: [48.454313, 7.254450],
      zoom: 13,
      eyebrow: "Étape 5 - La guerre dans la Vallée",
      title: "L'enjeu de la guerre",
      text: "La localisation de la vallée à l'est de la France la positionne en proie aux conflits internationnaux par son intervention mais aussi par le déploiement de la guerre sur ce territoire. La Guerre de Trente ans (1618-1648) a dans la vallée causée la disparition et la mort de plus de 70% de sa population. Ensuite, la première et la Seconde guerre mondiale ont également causés de nombreux dommages humains. La Seconde guerre mondiale a marqué le territoire avec la construction du camps de concentration du Struthof dans les hauteurs de la commune de Natzwiller. La vallée est encore aujourd'hui associée à cette époque dans les mémoires mais aussi dans la matérialité avec la mise en place de visites mémorielles du camps mais aussi du mémoriel d'Alsace-Moselle décrivant cette période.",
      layout: "diapo-bottom-right",
      photos: [
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013276.jpg", caption: "Monument commémoratif de la flamme du souvenir à Natzwiller (Fritsch F et Haegel O)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/memoriel.jpg", caption: "Mémoriel d'Alsace-Lorraine à Schirmeck" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013364.jpg", caption: "Champ de bataille de 1914 au petit Donon dans la commune de Wisches (Fritsch F et Haegel O)" }
      ]
    },
        {
      city: "Fermes",
      coords: [48.404827, 7.169566],
      zoom: 13,
      eyebrow: "Étape 5 - Agriculture",
      title: "Patrimoine particulier",
      text: "L'histoire de la vallée est riche et marquée par une certaine instabilité économiques et sociales. Les habitants du territoire ont connu de grands épisodes de crises économiques et sociale. L'agriculture a toujours été présente, sous différentes formes. Les terres ne sont pas très fertiles mais des parcelles agricoles sont présentes en fond de vallée pour nourrir les habitants. La sylviculture est une industrie qui s'est développée dès le Moyen Age jusqu'à atteindre 250 scieries en 1900 dans la vallée. Cela permettrait notamment de marchander avec les territoires voisins. Aujourd'hui, cette industrie a un rôle important pour l'économie de la vallée, notamment avec la présence de la plus grande scierie de résineux d'Europe. Ce travail des ressources marque ainsi le paysage du territoire, les habitats sont en grande majorité des fermes, typiques de la région avec des grandes portes, parfois une architecture monobloc qui se répartissent de manière homogène notamment dans le sud de la vallée.",
      layout: "diapo-bottom-right",
      photos: [
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012801.jpg", caption: "Ferme monobloc de Saint-Blaise-la-Roche (Fritsch F et Haegel O)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012785.jpg", caption: "Ferme monobloc de Colroy-la-Roche (Fritsch F et Haegel O)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012820.jpg", caption: "Ferme monobloc de Ranrupt (Fritsch F et Haegel O)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013170.jpg", caption: "Ferme de Belmont (Fritsch F et Haegel O)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013382.jpg", caption: "Maison forestière de Granfontaine (Fritsch F et Haegel O)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/Scierie.jpg", caption: "Scierie de Urmatt " }
      ]
    }, 

        {
      city: "Autre",
      coords: [48.512689, 7.165184],
      zoom: 13,
      eyebrow: "Étape 6 - Patrimoine singulier",
      title: "Le point d'arrivée",
      text: "Certains bâtiments ne rentrent pas forcément dans les thèmes précédents pourtant, ce patrimoine mérite d'être connu dans la vallée pour son esthétique et son cachet",
      layout: "diapo-bottom-right",
      photos: [
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67013403.jpg", caption: "Temple du Donon de Grandfontaine (Fritsch F et Haegel O)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012888.jpg", caption: "Viaduc ferroviaire de Plaine (Menninger C)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012777.jpg", caption: "Ancien sanatorium de Schirmeck (Menninger C)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012758.jpg", caption: "Mairie de Schirmeck (Menninger C)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67012755.jpg", caption: "Gare de Schirmeck-La Broque (Menninger C)" },
        { src: "https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/static/IM67011288.jpg", caption: "Château de Muhlbach-sur-Bruche (Parent B et Fritsch E)" }
      ]
    }, 


  ];


  const map = L.map('map', {
    zoomControl:false,
    attributionControl:false,
    scrollWheelZoom:false,
    dragging:false,
    doubleClickZoom:false,
    boxZoom:false,
    keyboard:false,
    touchZoom:false
  }).setView(FRANCE_VIEW.coords, FRANCE_VIEW.zoom);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  subdomains: 'abc',
  maxZoom: 19
}).addTo(map);


window.addEventListener('load', () => {
  setTimeout(() => map.invalidateSize(), 100);
});
const mapContainer = document.getElementById('map');
if (window.ResizeObserver) {
  const ro = new ResizeObserver(() => map.invalidateSize());
  ro.observe(mapContainer);
}
window.addEventListener('resize', () => map.invalidateSize());


fetch("https://huggingface.co/datasets/AodRic/Data_SIP/resolve/main/Shapefile/Communes_2.geojson")
  .then(r => r.json())
  .then(geojson => {
    L.geoJSON(geojson, {
      style: {
        color: "#B3B3B3",
        weight: 1.5,
        opacity: 0.7,
        fillColor: "#c9a24b",
        fillOpacity: 0.02
      },
      onEachFeature: function (feature, layer) {
        if (feature.properties && feature.properties.NOM) {
          layer.bindTooltip(feature.properties.NOM, { sticky: true });
        }
      }
    }).addTo(map);
  })
  .catch(err => console.error("Erreur chargement communes :", err));


  const markers = steps.map(s => {
    const icon = L.divIcon({ className:'', html:'<div class="city-pin"></div>', iconSize:[16,16] });
    return L.marker(s.coords, { icon }).addTo(map);
  });

  
  const routeLine = L.polyline(steps.map(s => s.coords), {
    color:'#c9a24b', weight:2, opacity:0, className:'route-line'
  }).addTo(map);


  const introOverlay = document.getElementById('intro-overlay');
  const introDismiss = document.getElementById('intro-dismiss');
  const navBar = document.getElementById('nav-bar');
  const navSteps = document.getElementById('nav-steps');
  const navLabel = document.getElementById('nav-label');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');

  const panelText = document.getElementById('panel-text');
  const panelEyebrow = document.getElementById('panel-eyebrow');
  const panelTitle = document.getElementById('panel-title');
  const panelBody = document.getElementById('panel-body');

  const panelPhoto = document.getElementById('panel-photo');
  const panelPhotoImg = document.getElementById('panel-photo-img');
  const panelPhotoCaption = document.getElementById('panel-photo-caption');

  const panelDiapo = document.getElementById('panel-diapo');
  const diapoFrame = document.getElementById('diapo-frame');
  const diapoDots = document.getElementById('diapo-dots');
  const diapoCaption = document.getElementById('diapo-caption');

  const diapoPrev = document.getElementById('diapo-prev');
  const diapoNext = document.getElementById('diapo-next');

  // Points de navigation (dots)
  steps.forEach((_, i) => {
    const dot = document.createElement('div');
    dot.className = 'step-dot';
    dot.dataset.index = i;
    navSteps.appendChild(dot);
  });

  let current = -1;       // -1 = intro affichée, pas encore commencé
  let diapoIndex = 0;
  let currentCaptions = []; // légendes de l'étape affichée, dans l'ordre des photos

  function hideAllContentPanels(){
    panelPhoto.classList.remove('visible');
    panelDiapo.classList.remove('visible');
  }


  function setDiapoSizeForImage(img){
    if (!img || !img.naturalWidth || !img.naturalHeight) return;
    const maxWidth = window.innerWidth * 0.36;   // équivalent de 36vw
    const maxHeight = window.innerHeight * 0.6;  // équivalent de 60vh
    const scale = Math.min(maxWidth / img.naturalWidth, maxHeight / img.naturalHeight);
    const width = Math.round(img.naturalWidth * scale);
    const height = Math.round(img.naturalHeight * scale);
    diapoFrame.style.width = width + 'px';
    diapoFrame.style.height = height + 'px';
  }

  function goToDiapoSlide(i){
    const imgs = diapoFrame.querySelectorAll('img');
    const dots = diapoDots.querySelectorAll('span');
    if (!imgs.length) return;
    imgs[diapoIndex].classList.remove('active');
    dots[diapoIndex].classList.remove('active');
    diapoIndex = (i + imgs.length) % imgs.length;
    const newImg = imgs[diapoIndex];
    newImg.classList.add('active');
    dots[diapoIndex].classList.add('active');
    diapoCaption.textContent = currentCaptions[diapoIndex] || '';

    if (newImg.complete && newImg.naturalWidth){
      setDiapoSizeForImage(newImg);
    } else {
      newImg.addEventListener('load', () => setDiapoSizeForImage(newImg), { once:true });
    }
  }

  function renderDiapo(photos){
    diapoFrame.querySelectorAll('img').forEach(img => img.remove());
    diapoDots.innerHTML = '';
    currentCaptions = photos.map(p => p.caption || '');
    photos.forEach((p, i) => {
      const img = document.createElement('img');
      img.src = p.src; img.alt = p.caption || '';
      if (i === 0) {
        img.classList.add('active');
        diapoCaption.textContent = currentCaptions[0] || '';
        if (img.complete && img.naturalWidth){
          setDiapoSizeForImage(img);
        } else {
          img.addEventListener('load', () => setDiapoSizeForImage(img), { once:true });
        }
      }
      diapoFrame.insertBefore(img, diapoPrev);
      const dot = document.createElement('span');
      if (i === 0) dot.classList.add('active');
      dot.addEventListener('click', () => goToDiapoSlide(i));
      diapoDots.appendChild(dot);
    });
    diapoIndex = 0;
  }

  
  window.addEventListener('resize', () => {
    const activeImg = diapoFrame.querySelector('img.active');
    if (activeImg) setDiapoSizeForImage(activeImg);
  });

  diapoPrev.addEventListener('click', () => goToDiapoSlide(diapoIndex - 1));
  diapoNext.addEventListener('click', () => goToDiapoSlide(diapoIndex + 1));

  function updateMarkers(activeIdx){
    markers.forEach((m, i) => {
      const el = m.getElement();
      if (!el) return;
      const pin = el.querySelector('.city-pin');
      if (pin) pin.classList.toggle('active', i === activeIdx);
    });
  }

  function updateNav(idx){
    navBar.classList.add('visible');
    const dots = navSteps.querySelectorAll('.step-dot');
    dots.forEach((d,i) => d.classList.toggle('active', i === idx));
    navLabel.textContent = String(idx+1).padStart(2,'0') + ' / ' + String(steps.length).padStart(2,'0');
    btnPrev.disabled = idx <= 0;
    btnNext.disabled = idx >= steps.length - 1;
  }

  function fillPanels(step){
    panelEyebrow.textContent = step.eyebrow;
    panelTitle.textContent = step.title;
    panelBody.textContent = step.text;

    hideAllContentPanels();
    if (step.layout === 'photo-right'){
      const p = step.photos[0];
      panelPhotoImg.src = p.src;
      panelPhotoImg.alt = p.caption || step.city;
      panelPhotoCaption.textContent = p.caption || '';
      panelPhoto.classList.add('visible');
    } else if (step.layout === 'diapo-bottom-right'){
      renderDiapo(step.photos);
      panelDiapo.classList.add('visible');
    }
  }

  function goToStep(idx, viaOverview){
    const step = steps[idx];
    panelText.classList.remove('visible');

    const flyToTarget = () => {
      map.flyTo(step.coords, step.zoom, { duration: 1.3 });
      setTimeout(() => {
        fillPanels(step);
        panelText.classList.add('visible');
        updateMarkers(idx);
      }, 500);
    };

    if (viaOverview){
      map.flyTo(FRANCE_VIEW.coords, FRANCE_VIEW.zoom, { duration: 0.9 });
      setTimeout(flyToTarget, 950);
    } else {
      flyToTarget();
    }

    if (idx > 0) {
      routeLine.setStyle({ opacity: 0.85 });
    }

    current = idx;
    updateNav(idx);
  }

  introDismiss.addEventListener('click', () => {
    introOverlay.classList.add('hidden');
    goToStep(0, false);
  });

  btnNext.addEventListener('click', () => {
    if (current < steps.length - 1) goToStep(current + 1, true);
  });
  btnPrev.addEventListener('click', () => {
    if (current > 0) goToStep(current - 1, true);
  });

  // Navigation clavier (bonus)
  document.addEventListener('keydown', (e) => {
    if (introOverlay.classList.contains('hidden')){
      if (e.key === 'ArrowRight') btnNext.click();
      if (e.key === 'ArrowLeft') btnPrev.click();
    }
  });
</script>
</body>
</html>
"""

components.html(STORY_HTML, height=STORY_HEIGHT, scrolling=False)
