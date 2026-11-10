# Protocole de validation

## Vérifications automatisées

Depuis la racine : `python -m pytest -q`. Les tests utilisent des signaux générés en mémoire et ne requièrent aucun enregistrement personnel. `python scripts/evaluate.py` affiche les SNR avant/après sur deux bruits et trois graines aléatoires, ainsi que le temps de calcul et les caractéristiques de la machine.

Les seuils des tests indiquent uniquement qu’un comportement attendu est conservé sur ces cas. Ils ne démontrent ni une qualité universelle ni une amélioration perceptive sur toutes les voix.

## Campagne sur des voix réelles à réaliser

Préparer au moins trois extraits vocaux de 10 à 30 secondes et deux bruits (souffle ou ventilation, puis un bruit plus variable). Utiliser uniquement des enregistrements autorisés. Conserver les fichiers dans un dossier ignoré par Git, par exemple `data/`.

Pour une comparaison objective, conserver une version propre, lui ajouter un bruit à plusieurs niveaux connus et traiter le mélange. Les signaux doivent être alignés avant de calculer le SNR. Un enregistrement réel sans référence propre sera évalué par écoute, sans présenter de SNR supposé.

Pour chaque essai, consigner :

| Champ | Information attendue |
|---|---|
| Enregistrement | Identifiant anonyme, durée, fréquence, canaux |
| Bruit | Type et niveau, si connu |
| Profil | Début et fin du passage de bruit seul |
| Paramètres | Intensité et atténuation maximale |
| Performance | Temps de traitement et machine |
| Mesure | SNR avant/après uniquement si référence disponible |
| Écoute | Intelligibilité, bruit résiduel, voix métallique, consonnes perdues |
| Conclusion | Compromis retenu et limites |

Ne pas confondre réduction du bruit et simple baisse du volume. Écouter l’original et le résultat dans les mêmes conditions. Les graphiques utilisent des échelles communes.

## Échantillonnage

Sur un même extrait, comparer les versions 8, 16 et 48 kHz, en gardant le nombre de canaux et l’encodage de sortie identiques. Relever la durée, la taille WAV et les différences de bande passante. Rééchantillonner à une fréquence plus élevée ne restitue pas les détails perdus.

## Critères fonctionnels

Vérifier l’import, les messages d’erreur, l’écoute du profil, le blocage d’un intervalle invalide, les deux lecteurs audio, les graphiques, le téléchargement et la lecture du WAV dans un lecteur indépendant. Vérifier qu’un changement de fichier ou de paramètres invalide l’ancien résultat.
