# Audio Denoising DSP

Application locale de **réduction du bruit vocal** et d’étude de **l’échantillonnage**, réalisée dans le cadre du module Vision artificielle. Approche classique de traitement numérique du signal : **aucun deep learning, aucun entraînement, aucune API audio externe**.

## Fonctionnalités

- Import WAV et MP3 lorsque le codec est disponible.
- Écoute de l’original et sélection explicite de 1 à 5 passages contenant uniquement du bruit (avant et après la parole, par exemple).
- Soustraction spectrale de puissance : STFT, profil de bruit, masque lissé et reconstruction.
- Réglage de l’intensité et du plancher d’atténuation.
- Écoute et export WAV PCM 16 bits du résultat.
- Comparaison des formes d’onde et spectrogrammes avec des échelles communes.
- Rééchantillonnage anti-repliement à 8, 16, 22,05, 44,1 ou 48 kHz, séparé du débruitage.
- Démonstration synthétique avec référence connue pour mesurer le SNR.

La fréquence d’origine, la durée et les canaux sont conservés pendant le débruitage. L’expérience d’échantillonnage conserve la durée à l’arrondi d’un échantillon près et ne change pas la hauteur du son.

## Installation

Python **3.11 à 3.13** est requis. L’environnement de développement validé utilise Python 3.12 sous Windows. Les versions exactes testées sont consignées dans `requirements.lock.txt`. Le couple NumPy 2.2.6 / SciPy 1.15.3 a été retenu après vérification du chargement des bibliothèques natives sur cette machine.

```powershell
git clone https://github.com/YoussefElGharbaouiDevs/audio-denoising-dsp.git
cd audio-denoising-dsp
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

Le dépôt étant privé, le clonage nécessite un compte GitHub autorisé. Sur macOS/Linux, utilisez `python3 -m venv .venv`, puis `.venv/bin/python` à la place du chemin Windows.

Pour un environnement différent, `python -m pip install -e ".[dev]"` permet de résoudre des dépendances compatibles à partir du projet ; les versions obtenues peuvent différer du fichier figé.

## Lancer l’application

Depuis le dossier du projet :

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ouvrir **http://127.0.0.1:8501**. Le serveur écoute uniquement sur la machine locale. `Ctrl+C` arrête le serveur. Le script `launch.ps1` propose également le lancement sous Windows et crée l’environnement s’il n’existe pas.

### Essai rapide sans fichier personnel

1. Choisir **Démonstration synthétique** dans la barre latérale.
2. Conserver le profil de bruit de **0 à 0,6 seconde**.
3. Écouter ce passage puis cocher la confirmation.
4. Cliquer sur **Débruiter l’enregistrement**.
5. Écouter le résultat, examiner les graphiques et les mesures de SNR.
6. Essayer l’onglet **Échantillonnage**, par exemple à 8 kHz.

Le signal de démonstration est harmonique et modulé : ce n’est pas une voix réelle et il ne prouve pas à lui seul la qualité perceptive du traitement sur la parole.

### Utiliser une voix réelle

1. Importer un WAV ou MP3 contenant principalement une seule voix.
2. Trouver un passage contenant le bruit seul, sans parole. L’application ne suppose pas que le début du fichier convient.
3. Sélectionner au moins **0,15 s** ; si disponible, préférer **0,5 à 1 s** de bruit représentatif.
4. Écouter le profil et confirmer sa sélection.
5. Commencer avec l’intensité **1,5** et l’atténuation maximale **18 dB**.
6. Comparer la compréhension des mots, les consonnes, le bruit résiduel et les artefacts. Réduire l’intensité si la voix devient métallique.
7. Télécharger le WAV débruité.

Si aucun passage ne contient uniquement du bruit, cette première méthode ne dispose pas d’un profil fiable. Choisir un autre enregistrement ou enregistrer quelques instants de bruit ambiant avec les mêmes conditions de captation.

## Limites et confidentialité

- Le traitement cible surtout les bruits relativement stationnaires : souffle, ventilation. Il ne garantit pas une suppression complète du bruit.
- La séparation de plusieurs voix, la séparation musicale, la transcription et le temps réel sont hors périmètre.
- Limites : **25 Mo, 120 secondes, mono/stéréo, 8 à 96 kHz et 12 millions de valeurs audio**. La dernière limite peut restreindre davantage les fichiers stéréo à haute fréquence.
- Le MP3 dépend du codec disponible dans libsndfile. Un WAV PCM est le format de secours.
- L’export utilise PCM 16 bits, sans dither dans cette première version. Un gain de sécurité signalé prévient l’écrêtage si nécessaire ; aucun relèvement automatique du volume n’est appliqué.
- Les fichiers sont traités en mémoire. Le code ne les écrit pas sur disque et n’utilise pas de service distant. Les téléchargements sont enregistrés par le navigateur à la demande de l’utilisateur.
- La télémétrie Streamlit est désactivée. L’installation initiale des dépendances et les opérations GitHub nécessitent Internet ; le traitement audio fonctionne ensuite localement.
- Les fichiers audio, secrets, résultats et environnements virtuels sont exclus de Git. Ne pas ajouter d’enregistrements privés avec `git add -f`.

## Méthode et évaluation

Consulter [la description DSP](docs/METHODE_DSP.md) et [le protocole de validation](docs/VALIDATION.md).

Le SNR n’est présenté que pour la démonstration avec une référence propre alignée. Pour une voix réelle sans référence, les spectrogrammes et l’écoute servent à comparer ; une simple diminution de l’énergie ne prouve pas une meilleure intelligibilité.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/evaluate.py
```

Les tests couvrent le filtrage anti-repliement, la conservation des canaux et de la durée, les fichiers invalides, l’absence d’écrêtage à l’export, le silence, le traitement désactivé, la préservation d’un signal propre avec profil silencieux, les profils invalides, l’amélioration sur des signaux contrôlés et le parcours de l’interface.

## Organisation

```text
app.py                       Interface Streamlit
src/audio_dsp/audio.py       Lecture, export et rééchantillonnage
src/audio_dsp/denoise.py      Traitement spectral classique
src/audio_dsp/evaluation.py  Référence synthétique et SNR
src/audio_dsp/plots.py       Comparaison des signaux
tests/                      Tests DSP et interface
docs/                       Méthode et protocole d’évaluation
scripts/evaluate.py         Mesures reproductibles
launch.ps1                  Lanceur Windows
requirements.lock.txt       Versions testées
```

## Développement séquentiel

Chaque partie est testée, commitée puis poussée séparément : documentation initiale, base audio, moteur DSP, interface. Les améliorations suivantes suivront le même principe. Ne pas regrouper plusieurs fonctionnalités indépendantes dans un seul push.

## Références

- [SciPy — resample_poly](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html)
- [SciPy — STFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.stft.html)
- [SciPy — STFT inverse](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.istft.html)
- [Streamlit — fichiers importés](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
- [Streamlit — lecture audio](https://docs.streamlit.io/develop/api-reference/media/st.audio)
