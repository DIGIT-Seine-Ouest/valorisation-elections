# Environnement de développement préconfiguré de la DIGIT

## Prérequis
### Installations de modules
1. Node.js installé
```bash
npm --version
```
> Si le terminal renvoie 8.19.4 c'est qu'il est installé

2. Gulp installé
```bash
gulp --version
```
> Si le terminal renvoie "CLI version: 3.0.0 Local version: 4.0.2" c'est qu'il est installé

Sinon, lancer la commande pour l'installer : 
```bash
npm install -g gulp
```

### Installation du package dev-kit
```bash
npm install
```

1. Copié les fichiers de configurations (cf. OneDrive ou PC) 
IMPORTANT c'est le fichier : config.js qu'on va stocker sur le PC

3.Vérifier que tout est bon en lançant la commande : 
```bash
gulp --tasks
```
> Devrait renvoyer : "Tasks for /workspaces/ods-dev-kit/gulpfile.js"

## Commandes utiles 

### Lancer pour voir le résultats de la page 
```bash
gulp server
```

### Compiler le code pour copier-coller sur ods
```bash
gulp compile
```
## Fichiers utiles 

-> [output](/output/) (On y retroue les fichiers à coller sur ODS)


-> Les fichiers CSS sont ici (en SCSS mais c'est une variante du CSS) [page/styles](/pages/styles/)

-> Les fichiers HTML sont ici (en ejs mais on peut mettre du html dedans) [page/views](/pages/views/)

